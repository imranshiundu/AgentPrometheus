import React, { useState, useEffect } from 'react';
import { 
  Terminal, 
  Shield, 
  Cpu, 
  Activity, 
  Database, 
  FileCode, 
  Search, 
  Settings,
  Zap,
  CheckCircle2,
  Clock,
  ArrowRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Dashboard = () => {
  const [logs, setLogs] = useState([
    { id: 1, type: 'ceo', time: '12:00:01', msg: '🔱 Prometheus Prime Online. Initializing multi-agent bridge...' },
    { id: 2, type: 'scout', time: '12:00:15', msg: 'Hermès connecting to internet gateway... Secure tunnel active.' },
    { id: 3, type: 'specialist', time: '12:00:20', msg: 'Hephaestus loading sandboxed coding environments...' },
    { id: 4, type: 'ceo', time: '12:05:10', msg: 'New task received via Telegram: "Build a React-based CRM prototype".' },
    { id: 5, type: 'scout', time: '12:05:12', msg: 'Scouting for documentation on modern CRM schemas...' },
  ]);

  const stats = [
    { label: 'Total Tokens Consumed', value: '42.8k', icon: <Zap size={20} color="#f1c40f" /> },
    { label: 'System Health', value: 'OPTIMAL', icon: <Shield size={20} color="#2ecc71" /> },
    { label: 'Active Agents', value: '3 / 5', icon: <Cpu size={20} color="#9b59b6" /> },
    { label: 'Token Cache efficiency', value: '92.4%', icon: <Activity size={20} color="#3498db" /> }
  ];

  return (
    <>
      {/* Sidebar */}
      <div className="sidebar">
        <div className="logo-section">
          <div className="logo-icon">
            <Shield color="white" fill="white" size={24} />
          </div>
          <h2 style={{ fontWeight: 800, letterSpacing: '-1px' }}>PROMETHEUS</h2>
        </div>
        
        <div className="nav-links">
          <div className="nav-item active"><Terminal size={18} /> Command Center</div>
          <div className="nav-item"><Database size={18} /> Hive Mind Memory</div>
          <div className="nav-item"><FileCode size={18} /> Artifact Registry</div>
          <div className="nav-item"><Search size={18} /> Scout Reports</div>
          <div className="nav-item"><Settings size={18} /> Switchboard Settings</div>
        </div>

        <div style={{ marginTop: 'auto', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
          <p style={{ fontSize: '0.75rem', color: var('--text-muted') }}>CURRENT MODEL</p>
          <p style={{ fontSize: '0.9rem', fontWeight: 600 }}>Claude 3.5 Sonnet</p>
          <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', marginTop: '8px' }}>
            <div style={{ width: '85%', height: '100%', background: 'var(--primary)', borderRadius: '2px' }}></div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div className="header">
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Command Center</h1>
            <p style={{ color: 'var(--text-muted)' }}>Real-time telemetry from the Titan's Forge</p>
          </div>
          <div className="status-badge" style={{ padding: '0.5rem 1rem', background: 'rgba(46, 204, 113, 0.1)', border: '1px solid #2ecc71', borderRadius: '20px', color: '#2ecc71', fontSize: '0.8rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="status-dot"></div>
            HIVE NODE ACTIVE
          </div>
        </div>

        <div className="stats-grid">
          {stats.map((stat, i) => (
            <motion.div 
              key={i}
              className="stat-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
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
              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f56' }}></div>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ffbd2e' }}></div>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#27c93f' }}></div>
              </div>
            </div>
            <div className="log-stream">
              {logs.map((log) => (
                <div key={log.id} className={`log-entry ${log.type}`}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>[{log.time}]</span>
                  <span style={{ fontWeight: 600, minWidth: '80px', textTransform: 'uppercase', fontSize: '0.8rem' }}>{log.type}:</span>
                  <span>{log.msg}</span>
                </div>
              ))}
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 1, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                style={{ width: '8px', height: '18px', background: 'white', display: 'inline-block' }}
              />
            </div>
          </div>

          <div className="agent-status-list">
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.5rem' }}>Active Processes</h3>
            
            <div className="agent-item">
              <div className="status-dot"></div>
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Prometheus Prime (CEO)</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Managing Hierarchical Process</p>
              </div>
            </div>

            <div className="agent-item">
              <div className="status-dot"></div>
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Hermès (The Scout)</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Searching: React CRM Best Practices</p>
              </div>
            </div>

            <div className="agent-item">
              <div className="status-dot"></div>
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>Hephaestus (Specialist)</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Testing Docker Sandbox Connectivity</p>
              </div>
            </div>

            <div className="agent-item">
              <div className="status-dot idle"></div>
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>The Architect</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>IDLE - Waiting for Spec approval</p>
              </div>
            </div>

            <div style={{ marginTop: 'auto', background: 'rgba(241, 196, 15, 0.05)', border: '1px solid var(--accent-gold)', borderRadius: '12px', padding: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-gold)', marginBottom: '4px' }}>
                <Zap size={14} />
                <span style={{ fontSize: '0.75rem', fontWeight: 800 }}>BUDGET WARNING</span>
              </div>
              <p style={{ fontSize: '0.8rem' }}>Session reaching $4.50. Automatic kill-switch active at $5.00.</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;
