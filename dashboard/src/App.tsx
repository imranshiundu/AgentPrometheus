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

type RuntimeLog = {
  id?: number | string;
  type?: string;
  time?: string;
  msg?: string;
};

type RuntimeStats = {
  tokens?: string;
  health?: string;
  active_agents?: string;
  queue_depth?: number;
  log_count?: number;
  notification_count?: number;
  kill_switch?: boolean;
  runtime?: string;
};

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000';

const Dashboard = () => {
  const [logs, setLogs] = useState<RuntimeLog[]>([]);
  const [statsData, setStatsData] = useState<RuntimeStats>({});
  const [task, setTask] = useState('');
  const [apiStatus, setApiStatus] = useState<'connecting' | 'online' | 'offline'>('connecting');

  useEffect(() => {
    let cancelled = false;

    const loadStats = async () => {
      try {
        const response = await fetch(`${API_BASE}/stats`);
        if (!response.ok) throw new Error(`Stats request failed: ${response.status}`);
        const data = await response.json();
        if (!cancelled) {
          setStatsData(data);
          setApiStatus('online');
        }
      } catch {
        if (!cancelled) setApiStatus('offline');
      }
    };

    loadStats();
    const timer = window.setInterval(loadStats, 3000);
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
      { label: 'Active Runtime', value: statsData.runtime || 'consultant', icon: <Cpu size={20} /> },
      { label: 'Queue Depth', value: String(statsData.queue_depth ?? 0), icon: <Activity size={20} /> },
    ],
    [apiStatus, statsData]
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
    if (response.ok) setTask('');
  };

  return (
    <>
      <div className="sidebar">
        <div className="logo-section">
          <div className="logo-icon">
            <Shield color="white" fill="white" size={24} />
          </div>
          <h2 style={{ fontWeight: 800, letterSpacing: '-1px' }}>PROMETHEUS</h2>
        </div>

        <div className="nav-links">
          <div className="nav-item active"><Terminal size={18} /> Command Center</div>
          <div className="nav-item"><Database size={18} /> Runtime Memory</div>
          <div className="nav-item"><FileCode size={18} /> Artifact Registry</div>
          <div className="nav-item"><Search size={18} /> Evidence Reports</div>
          <div className="nav-item"><Settings size={18} /> Runtime Settings</div>
        </div>

        <div style={{ marginTop: 'auto', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CURRENT MODEL ROUTE</p>
          <p style={{ fontSize: '0.9rem', fontWeight: 600 }}>consultant-model</p>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>API: {apiStatus}</p>
        </div>
      </div>

      <div className="main-content">
        <div className="header">
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Command Center</h1>
            <p style={{ color: 'var(--text-muted)' }}>Real-time telemetry from the unified Prometheus runtime</p>
          </div>
          <div className="status-badge" style={{ padding: '0.5rem 1rem', background: statsData.kill_switch ? 'rgba(231, 76, 60, 0.1)' : 'rgba(46, 204, 113, 0.1)', border: statsData.kill_switch ? '1px solid #e74c3c' : '1px solid #2ecc71', borderRadius: '20px', color: statsData.kill_switch ? '#e74c3c' : '#2ecc71', fontSize: '0.8rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="status-dot"></div>
            {statsData.kill_switch ? 'KILL SWITCH ACTIVE' : 'RUNTIME ACTIVE'}
          </div>
        </div>

        <form onSubmit={submitTask} style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <input
            value={task}
            onChange={(event) => setTask(event.target.value)}
            placeholder="Send a task to Agent Prometheus..."
            style={{ flex: 1, padding: '0.9rem 1rem', borderRadius: '12px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.03)', color: 'white' }}
          />
          <button type="submit" style={{ padding: '0.9rem 1.2rem', borderRadius: '12px', border: 'none', fontWeight: 700, cursor: 'pointer' }}>Queue Task</button>
        </form>

        <div className="stats-grid">
          {stats.map((stat, i) => (
            <motion.div key={stat.label} className="stat-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="stat-label">{stat.label}</span>
                {stat.icon}
              </div>
              <span className="stat-value">{stat.value}</span>
            </motion.div>
          ))}
        </div>

        <div className="console-section">
          <div className="console-box">
            <div className="box-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Terminal size={16} />
                <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Live Execution Stream</span>
              </div>
            </div>
            <div className="log-stream">
              {logs.length === 0 ? (
                <div className="log-entry system"><span>No runtime logs yet.</span></div>
              ) : (
                logs.map((log, index) => (
                  <div key={`${log.time || 'log'}-${index}`} className={`log-entry ${log.type || 'system'}`}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>[{log.time || '--:--:--'}]</span>
                    <span style={{ fontWeight: 600, minWidth: '90px', textTransform: 'uppercase', fontSize: '0.8rem' }}>{log.type || 'system'}:</span>
                    <span>{log.msg || JSON.stringify(log)}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="agent-status-list">
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.5rem' }}>Unified Runtime</h3>
            <div className="agent-item">
              <div className="status-dot"></div>
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Evidence Scanner</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Collects files, routes, diagnostics, and repo index.</p>
              </div>
            </div>
            <div className="agent-item">
              <div className="status-dot"></div>
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Consultant Runtime</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Asks the model for structured plans, not blind execution.</p>
              </div>
            </div>
            <div className="agent-item">
              <div className="status-dot idle"></div>
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Patch Gate</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Auto-apply is off unless explicitly enabled.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;
