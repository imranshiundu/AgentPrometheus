import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Cpu,
  Database,
  FileCode,
  Search,
  Settings,
  Shield,
  Terminal,
  Zap,
} from 'lucide-react';
import { motion } from 'framer-motion';

type Section = 'command' | 'memory' | 'artifacts' | 'reports' | 'settings';

type RuntimeLog = { id?: number | string; type?: string; time?: string; msg?: string };
type RuntimeStats = {
  tokens?: string;
  health?: string;
  active_agents?: string;
  queue_depth?: number;
  log_count?: number;
  notification_count?: number;
  artifact_count?: number;
  kill_switch?: boolean;
  runtime?: string;
  app_name?: string;
};
type RuntimeConfig = {
  app_name?: string;
  runtime?: string;
  consultant_model?: string;
  cheap_model?: string;
  auto_apply?: boolean;
  workspace?: string;
  task_queue?: string;
  log_stream?: string;
  notification_channel?: string;
};
type RuntimeFile = { name: string; size?: number; modified?: number };
type RuntimeRoute = { path: string; methods: string[] };

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000';
const FALLBACK_APP_NAME = import.meta.env.VITE_APP_NAME || 'Workspace Runtime';

const bytes = (value?: number) => {
  if (!value) return '0 B';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
};

const Dashboard = () => {
  const [section, setSection] = useState<Section>('command');
  const [logs, setLogs] = useState<RuntimeLog[]>([]);
  const [statsData, setStatsData] = useState<RuntimeStats>({});
  const [config, setConfig] = useState<RuntimeConfig>({});
  const [task, setTask] = useState('');
  const [apiStatus, setApiStatus] = useState<'connecting' | 'online' | 'offline'>('connecting');
  const [artifacts, setArtifacts] = useState<RuntimeFile[]>([]);
  const [reports, setReports] = useState<RuntimeFile[]>([]);
  const [queue, setQueue] = useState<Record<string, unknown>[]>([]);
  const [notifications, setNotifications] = useState<Record<string, unknown>[]>([]);
  const [routes, setRoutes] = useState<RuntimeRoute[]>([]);

  const appName = config.app_name || statsData.app_name || FALLBACK_APP_NAME;

  const loadJson = async <T,>(path: string, fallback: T): Promise<T> => {
    try {
      const response = await fetch(`${API_BASE}${path}`);
      if (!response.ok) throw new Error(`${path} failed`);
      setApiStatus('online');
      return await response.json();
    } catch {
      setApiStatus('offline');
      return fallback;
    }
  };

  const refreshRuntime = async () => {
    const [stats, runtimeConfig, artifactList, reportList, queueList, notificationList, routeList] = await Promise.all([
      loadJson<RuntimeStats>('/stats', {}),
      loadJson<RuntimeConfig>('/runtime/config', {}),
      loadJson<RuntimeFile[]>('/artifacts', []),
      loadJson<RuntimeFile[]>('/reports', []),
      loadJson<Record<string, unknown>[]>('/queue', []),
      loadJson<Record<string, unknown>[]>('/notifications', []),
      loadJson<RuntimeRoute[]>('/runtime/routes', []),
    ]);
    setStatsData(stats);
    setConfig(runtimeConfig);
    setArtifacts(artifactList);
    setReports(reportList);
    setQueue(queueList);
    setNotifications(notificationList);
    setRoutes(routeList);
  };

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!cancelled) await refreshRuntime();
    };
    run();
    const timer = window.setInterval(run, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const socket = new WebSocket(`${WS_BASE}/ws/logs`);
    socket.onopen = () => setApiStatus('online');
    socket.onerror = () => setApiStatus('offline');
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        setLogs(Array.isArray(payload) ? payload : [payload]);
      } catch {
        setLogs([{ type: 'system', time: new Date().toLocaleTimeString(), msg: event.data }]);
      }
    };
    return () => socket.close();
  }, []);

  const stats = useMemo(
    () => [
      { label: 'Runtime Tokens', value: statsData.tokens || '0', icon: <Zap size={20} /> },
      { label: 'System Health', value: statsData.health || apiStatus.toUpperCase(), icon: <Shield size={20} /> },
      { label: 'Active Runtime', value: statsData.runtime || config.runtime || 'consultant', icon: <Cpu size={20} /> },
      { label: 'Queue Depth', value: String(statsData.queue_depth ?? queue.length), icon: <Activity size={20} /> },
    ],
    [apiStatus, config.runtime, queue.length, statsData]
  );

  const submitTask = async (event: React.FormEvent) => {
    event.preventDefault();
    const cleanTask = task.trim();
    if (!cleanTask) return;
    const response = await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task: cleanTask }),
    });
    if (response.ok) {
      setTask('');
      await refreshRuntime();
    }
  };

  const toggleKillSwitch = async () => {
    await fetch(`${API_BASE}/control/kill-switch`, { method: statsData.kill_switch ? 'DELETE' : 'POST' });
    await refreshRuntime();
  };

  const nav = [
    { id: 'command' as Section, label: 'Command Center', icon: <Terminal size={18} /> },
    { id: 'memory' as Section, label: 'Runtime Memory', icon: <Database size={18} /> },
    { id: 'artifacts' as Section, label: 'Artifact Registry', icon: <FileCode size={18} /> },
    { id: 'reports' as Section, label: 'Evidence Reports', icon: <Search size={18} /> },
    { id: 'settings' as Section, label: 'Runtime Settings', icon: <Settings size={18} /> },
  ];

  const renderList = (items: Record<string, unknown>[], empty: string) => (
    <div className="log-stream">
      {items.length === 0 ? <div className="log-entry system"><span>{empty}</span></div> : items.map((item, index) => (
        <div key={index} className="log-entry system"><span>{JSON.stringify(item)}</span></div>
      ))}
    </div>
  );

  const renderSection = () => {
    if (section === 'artifacts') {
      return <div className="console-box"><div className="box-header"><span>Artifact Registry</span></div><div className="log-stream">{artifacts.length === 0 ? <div className="log-entry system">No artifacts found.</div> : artifacts.map((file) => <div key={file.name} className="log-entry system"><a href={`${API_BASE}/artifacts/${file.name}`} target="_blank" rel="noreferrer">{file.name}</a><span>{bytes(file.size)}</span></div>)}</div></div>;
    }
    if (section === 'reports') {
      return <div className="console-box"><div className="box-header"><span>Evidence Reports</span></div><div className="log-stream">{reports.length === 0 ? <div className="log-entry system">No reports found.</div> : reports.map((file) => <div key={file.name} className="log-entry system"><a href={`${API_BASE}/artifacts/${file.name}`} target="_blank" rel="noreferrer">{file.name}</a><span>{bytes(file.size)}</span></div>)}</div></div>;
    }
    if (section === 'memory') {
      return <div className="console-section"><div className="console-box"><div className="box-header"><span>Queued Work</span></div>{renderList(queue, 'No queued tasks.')}</div><div className="console-box"><div className="box-header"><span>Notifications</span></div>{renderList(notifications, 'No notifications.')}</div></div>;
    }
    if (section === 'settings') {
      return <div className="console-section"><div className="console-box"><div className="box-header"><span>Runtime Config</span><button onClick={toggleKillSwitch}>{statsData.kill_switch ? 'Clear Kill Switch' : 'Trigger Kill Switch'}</button></div><div className="log-stream"><div className="log-entry system"><span>{JSON.stringify(config, null, 2)}</span></div></div></div><div className="console-box"><div className="box-header"><span>Connected API Routes</span></div><div className="log-stream">{routes.map((route) => <div key={route.path} className="log-entry system"><span>{route.methods.join(', ') || 'WS'}</span><span>{route.path}</span></div>)}</div></div></div>;
    }
    return <div className="console-section"><div className="console-box"><div className="box-header"><div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><Terminal size={16} /><span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Live Execution Stream</span></div></div><div className="log-stream">{logs.length === 0 ? <div className="log-entry system"><span>No runtime logs yet.</span></div> : logs.map((log, index) => <div key={`${log.time || 'log'}-${index}`} className={`log-entry ${log.type || 'system'}`}><span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>[{log.time || '--:--:--'}]</span><span style={{ fontWeight: 600, minWidth: '90px', textTransform: 'uppercase', fontSize: '0.8rem' }}>{log.type || 'system'}:</span><span>{log.msg || JSON.stringify(log)}</span></div>)}</div></div><div className="agent-status-list"><h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.5rem' }}>Unified Runtime</h3><div className="agent-item"><div className="status-dot"></div><div style={{ flex: 1 }}><p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Evidence Scanner</p><p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Collects files, routes, diagnostics, and repo index.</p></div></div><div className="agent-item"><div className="status-dot"></div><div style={{ flex: 1 }}><p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Consultant Runtime</p><p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Asks the model for structured plans, not blind execution.</p></div></div><div className="agent-item"><div className="status-dot idle"></div><div style={{ flex: 1 }}><p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Patch Gate</p><p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Auto-apply is off unless explicitly enabled.</p></div></div></div></div>;
  };

  return (
    <>
      <div className="sidebar">
        <div className="logo-section">
          <div className="logo-icon"><Shield color="white" fill="white" size={24} /></div>
          <h2 style={{ fontWeight: 800, letterSpacing: '-1px' }}>{appName}</h2>
        </div>
        <div className="nav-links">
          {nav.map((item) => <button key={item.id} className={`nav-item ${section === item.id ? 'active' : ''}`} onClick={() => setSection(item.id)}>{item.icon} {item.label}</button>)}
        </div>
        <div style={{ marginTop: 'auto', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CURRENT MODEL ROUTE</p>
          <p style={{ fontSize: '0.9rem', fontWeight: 600 }}>{config.consultant_model || 'consultant-model'}</p>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>API: {apiStatus}</p>
        </div>
      </div>
      <div className="main-content">
        <div className="header">
          <div><h1 style={{ fontSize: '2rem', fontWeight: 800 }}>{nav.find((item) => item.id === section)?.label}</h1><p style={{ color: 'var(--text-muted)' }}>One runtime, one queue, one route map, one goal.</p></div>
          <div className="status-badge" style={{ padding: '0.5rem 1rem', background: statsData.kill_switch ? 'rgba(231, 76, 60, 0.1)' : 'rgba(46, 204, 113, 0.1)', border: statsData.kill_switch ? '1px solid #e74c3c' : '1px solid #2ecc71', borderRadius: '20px', color: statsData.kill_switch ? '#e74c3c' : '#2ecc71', fontSize: '0.8rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}><div className="status-dot"></div>{statsData.kill_switch ? 'KILL SWITCH ACTIVE' : 'RUNTIME ACTIVE'}</div>
        </div>
        <form onSubmit={submitTask} style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <input value={task} onChange={(event) => setTask(event.target.value)} placeholder={`Send a task to ${appName}...`} style={{ flex: 1, padding: '0.9rem 1rem', borderRadius: '12px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.03)', color: 'white' }} />
          <button type="submit" style={{ padding: '0.9rem 1.2rem', borderRadius: '12px', border: 'none', fontWeight: 700, cursor: 'pointer' }}>Queue Task</button>
        </form>
        <div className="stats-grid">{stats.map((stat, i) => <motion.div key={stat.label} className="stat-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><span className="stat-label">{stat.label}</span>{stat.icon}</div><span className="stat-value">{stat.value}</span></motion.div>)}</div>
        {renderSection()}
      </div>
    </>
  );
};

export default Dashboard;
