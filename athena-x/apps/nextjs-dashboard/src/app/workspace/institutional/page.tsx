'use client';

import { useState, useEffect, useCallback } from 'react';

// ============================================================================
// Types — mirror the Python dataclasses
// ============================================================================

interface DiscoveredAgent {
  agent_id: string;
  name: string;
  category: string;
  layer: number | string;
  description: string;
  inputs: string[];
  outputs: string[];
  dependencies: string[];
  module_path: string;
  manifest: Record<string, unknown>;
  health: { agent_id: string; running: boolean; [k: string]: unknown };
}

interface TraceEvent {
  agent_id: string;
  layer: number | string;
  category: string;
  started_at_ms: number;
  duration_ms: number;
  success: boolean;
  output_summary: string;
  confidence: number | null;
  error: string;
}

interface TraceRecord {
  request_id: string;
  symbol: string;
  timeframe: string;
  started_at: string;
  finished_at: string | null;
  total_duration_ms: number;
  events: TraceEvent[];
  final_conclusion: string;
  contributor_chain: string[];
  data_provider: string;
  success: boolean;
  error: string;
}

interface EvidenceReport {
  request_id: string;
  symbol: string;
  timeframe: string;
  generated_at: string;
  final_conclusion: string;
  total_agents_executed: number;
  total_duration_ms: number;
  primary_contributors: EvidenceContribution[];
  supporting_contributors: EvidenceContribution[];
  contextual_contributors: EvidenceContribution[];
  layer_breakdown: Record<string, number>;
  failed_agents: EvidenceContribution[];
}

interface EvidenceContribution {
  agent_id: string;
  layer: number | string;
  category: string;
  output_summary: string;
  confidence: number | null;
  duration_ms: number;
  role: string;
}

// ============================================================================
// API helpers
// ============================================================================

const API_BASE = 'http://localhost:8000';

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ============================================================================
// Color + style helpers
// ============================================================================

const LAYER_COLORS: Record<string, string> = {
  '1': '#3b82f6', // blue
  '2': '#10b981', // green
  '3': '#f59e0b', // amber
  '4': '#8b5cf6', // violet
  '5': '#ef4444', // red
  'hub': '#ec4899', // pink
};

const CATEGORY_LABELS: Record<string, string> = {
  market_structure: 'Market Structure',
  indicator: 'Indicator',
  institutional: 'Institutional',
  consensus: 'Consensus',
  supervisor: 'Supervisor',
  snapshot: 'Snapshot',
  options: 'Options Hub',
  market: 'Market Hub',
  narrative: 'Narrative Hub',
  forecast: 'Forecast Hub',
  trade: 'Trade Hub',
  operations: 'Operations Hub',
};

function layerColor(layer: number | string): string {
  return LAYER_COLORS[String(layer)] || '#6b7280';
}

function confidenceColor(c: number | null): string {
  if (c === null) return '#6b7280';
  if (c >= 0.95) return '#10b981';
  if (c >= 0.8) return '#3b82f6';
  if (c >= 0.6) return '#f59e0b';
  return '#ef4444';
}

// ============================================================================
// Main page component
// ============================================================================

export default function InstitutionalWorkspacePage() {
  const [components, setComponents] = useState<DiscoveredAgent[]>([]);
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<DiscoveredAgent | null>(null);
  const [executeResult, setExecuteResult] = useState<Record<string, unknown> | null>(null);
  const [pipelineResult, setPipelineResult] = useState<Record<string, unknown> | null>(null);
  const [history, setHistory] = useState<TraceRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [symbol, setSymbol] = useState('SPY');
  const [timeframe, setTimeframe] = useState('15m');
  const [activeTab, setActiveTab] = useState<'components' | 'execute' | 'pipeline' | 'history'>('components');

  // ─── Load components on mount ─────────────────────────────────────
  const loadComponents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [compRes, sumRes] = await Promise.all([
        api<{ components: DiscoveredAgent[]; total: number }>('/workspace/components'),
        api<Record<string, unknown>>('/workspace/summary'),
      ]);
      setComponents(compRes.components);
      setSummary(sumRes);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load components');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadComponents();
  }, [loadComponents]);

  // ─── Execute single agent ─────────────────────────────────────────
  const executeAgent = async (agentId: string) => {
    setLoading(true);
    setError(null);
    setExecuteResult(null);
    try {
      const result = await api<Record<string, unknown>>(`/workspace/execute/${agentId}`, {
        method: 'POST',
        body: JSON.stringify({ symbol, timeframe }),
      });
      setExecuteResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Execution failed');
    } finally {
      setLoading(false);
    }
  };

  // ─── Execute full pipeline ────────────────────────────────────────
  const executePipeline = async () => {
    setLoading(true);
    setError(null);
    setPipelineResult(null);
    try {
      const result = await api<Record<string, unknown>>('/workspace/execute-request', {
        method: 'POST',
        body: JSON.stringify({ symbol, timeframe, data_provider: 'demo' }),
      });
      setPipelineResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Pipeline failed');
    } finally {
      setLoading(false);
    }
  };

  // ─── Load history ─────────────────────────────────────────────────
  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api<{ history: TraceRecord[]; count: number }>('/workspace/history');
      setHistory(res.history);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  // ─── Render ───────────────────────────────────────────────────────
  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: '#e2e8f0', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* Header */}
      <header style={{
        background: '#1e293b',
        borderBottom: '1px solid #334155',
        padding: '20px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, margin: 0, color: '#f1f5f9' }}>
            ATHENA-X · Institutional Workspace
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 0 0' }}>
            Stage 16.3 — Verified runtime integration · {components.length} agents discovered
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Symbol"
            style={{
              background: '#0f172a',
              border: '1px solid #334155',
              color: '#f1f5f9',
              padding: '8px 12px',
              borderRadius: '6px',
              fontSize: '13px',
              width: '100px',
            }}
          />
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            style={{
              background: '#0f172a',
              border: '1px solid #334155',
              color: '#f1f5f9',
              padding: '8px 12px',
              borderRadius: '6px',
              fontSize: '13px',
            }}
          >
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="30m">30m</option>
            <option value="1H">1H</option>
            <option value="4H">4H</option>
            <option value="1D">1D</option>
            <option value="1W">1W</option>
          </select>
          <button
            onClick={loadComponents}
            disabled={loading}
            style={{
              background: '#334155',
              color: '#f1f5f9',
              border: '1px solid #475569',
              padding: '8px 16px',
              borderRadius: '6px',
              fontSize: '13px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            Refresh
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav style={{ background: '#1e293b', borderBottom: '1px solid #334155', padding: '0 32px', display: 'flex', gap: '4px' }}>
        {(['components', 'execute', 'pipeline', 'history'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab);
              if (tab === 'history') loadHistory();
            }}
            style={{
              background: activeTab === tab ? '#0f172a' : 'transparent',
              color: activeTab === tab ? '#f1f5f9' : '#94a3b8',
              border: 'none',
              borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
              padding: '12px 20px',
              fontSize: '13px',
              cursor: 'pointer',
              textTransform: 'capitalize',
            }}
          >
            {tab === 'components' && `Components (${components.length})`}
            {tab === 'execute' && 'Standalone Execution'}
            {tab === 'pipeline' && 'Full Pipeline Trace'}
            {tab === 'history' && `History (${history.length})`}
          </button>
        ))}
      </nav>

      {/* Error banner */}
      {error && (
        <div style={{
          background: '#7f1d1d',
          color: '#fee2e2',
          padding: '12px 32px',
          fontSize: '13px',
          borderBottom: '1px solid #991b1b',
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Main content */}
      <main style={{ padding: '24px 32px' }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8', fontSize: '14px' }}>
            Loading…
          </div>
        )}

        {/* ─── Components Tab ─── */}
        {activeTab === 'components' && !loading && (
          <div>
            {/* Summary cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '24px' }}>
              <SummaryCard label="Total Agents" value={String(components.length)} color="#3b82f6" />
              <SummaryCard label="TA Layers" value={String(Object.entries(summary?.by_layer || {}).filter(([k]) => k !== 'hub').length)} color="#10b981" />
              <SummaryCard label="Intelligence Hubs" value={String((summary?.by_layer as Record<string, number>)?.hub || 0)} color="#ec4899" />
              <SummaryCard label="Categories" value={String(Object.keys(summary?.by_category || {}).length)} color="#f59e0b" />
            </div>

            {/* Layer groupings */}
            {['1', '2', '3', '4', '5', 'hub'].map((layer) => {
              const agents = components.filter((c) => String(c.layer) === layer);
              if (agents.length === 0) return null;
              const layerName = layer === 'hub'
                ? 'Intelligence Hubs'
                : `Layer ${layer}: ${layer === '1' ? 'Market Structure' : layer === '2' ? 'Indicators' : layer === '3' ? 'Institutional' : layer === '4' ? 'Consensus' : 'Supervisor'}`;
              return (
                <div key={layer} style={{ marginBottom: '24px' }}>
                  <h2 style={{
                    fontSize: '14px', fontWeight: 600, color: layerColor(layer),
                    margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px',
                    display: 'flex', alignItems: 'center', gap: '8px',
                  }}>
                    <span style={{ width: '4px', height: '16px', background: layerColor(layer), borderRadius: '2px' }} />
                    {layerName} ({agents.length})
                  </h2>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
                    {agents.map((agent) => (
                      <AgentCard
                        key={agent.agent_id}
                        agent={agent}
                        onClick={() => setSelectedAgent(agent)}
                        selected={selectedAgent?.agent_id === agent.agent_id}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ─── Execute Tab ─── */}
        {activeTab === 'execute' && !loading && (
          <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
            <div>
              <h2 style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8', margin: '0 0 12px 0', textTransform: 'uppercase' }}>
                Select Agent
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '70vh', overflowY: 'auto' }}>
                {components.map((agent) => (
                  <button
                    key={agent.agent_id}
                    onClick={() => {
                      setSelectedAgent(agent);
                      setExecuteResult(null);
                    }}
                    style={{
                      background: selectedAgent?.agent_id === agent.agent_id ? '#1e3a8a' : '#1e293b',
                      color: '#e2e8f0',
                      border: '1px solid #334155',
                      padding: '10px 14px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      cursor: 'pointer',
                      textAlign: 'left',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    <span style={{
                      width: '8px', height: '8px', borderRadius: '50%',
                      background: layerColor(agent.layer), flexShrink: 0,
                    }} />
                    <span style={{ fontFamily: 'monospace' }}>{agent.agent_id}</span>
                  </button>
                ))}
              </div>
            </div>
            <div>
              {selectedAgent ? (
                <div>
                  <div style={{
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    padding: '20px',
                    marginBottom: '16px',
                  }}>
                    <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', color: '#f1f5f9' }}>
                      {selectedAgent.name}
                      <span style={{
                        marginLeft: '12px', fontSize: '11px', padding: '2px 8px',
                        background: layerColor(selectedAgent.layer),
                        borderRadius: '4px', color: 'white', fontWeight: 600,
                      }}>
                        L{selectedAgent.layer} · {CATEGORY_LABELS[selectedAgent.category] || selectedAgent.category}
                      </span>
                    </h3>
                    <p style={{ fontSize: '13px', color: '#94a3b8', margin: '0 0 16px 0' }}>
                      {selectedAgent.description || '(no description)'}
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px' }}>
                      <div>
                        <div style={{ color: '#64748b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Inputs</div>
                        {selectedAgent.inputs.map((inp, i) => (
                          <div key={i} style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>{inp}</div>
                        ))}
                      </div>
                      <div>
                        <div style={{ color: '#64748b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Outputs</div>
                        {selectedAgent.outputs.map((out, i) => (
                          <div key={i} style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>{out}</div>
                        ))}
                      </div>
                    </div>
                    <button
                      onClick={() => executeAgent(selectedAgent.agent_id)}
                      disabled={loading}
                      style={{
                        marginTop: '16px',
                        background: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '6px',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: loading ? 'not-allowed' : 'pointer',
                      }}
                    >
                      ▶ Execute {selectedAgent.agent_id} on {symbol} {timeframe}
                    </button>
                  </div>

                  {executeResult && (
                    <ExecutionResultView result={executeResult} />
                  )}
                </div>
              ) : (
                <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
                  Select an agent to execute
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─── Pipeline Tab ─── */}
        {activeTab === 'pipeline' && !loading && (
          <div>
            <div style={{
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              padding: '20px',
              marginBottom: '16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '16px', color: '#f1f5f9' }}>Full Pipeline Trace</h3>
                <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#94a3b8' }}>
                  Executes Layer 1 → 2 → 3 → 4 → 5 in sequence with full tracing
                </p>
              </div>
              <button
                onClick={executePipeline}
                disabled={loading}
                style={{
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: loading ? 'not-allowed' : 'pointer',
                }}
              >
                ▶ Run Full Pipeline
              </button>
            </div>

            {pipelineResult && (
              <PipelineResultView result={pipelineResult} />
            )}
          </div>
        )}

        {/* ─── History Tab ─── */}
        {activeTab === 'history' && !loading && (
          <div>
            <h2 style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8', margin: '0 0 12px 0', textTransform: 'uppercase' }}>
              Recent Requests ({history.length})
            </h2>
            {history.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                No requests yet. Execute an agent or run the pipeline to see history.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {history.map((rec) => (
                  <HistoryRow key={rec.request_id} record={rec} />
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

// ============================================================================
// Sub-components
// ============================================================================

function SummaryCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{
      background: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '8px',
      padding: '16px',
    }}>
      <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
        {label}
      </div>
      <div style={{ fontSize: '28px', fontWeight: 700, color }}>
        {value}
      </div>
    </div>
  );
}

function AgentCard({ agent, onClick, selected }: { agent: DiscoveredAgent; onClick: () => void; selected: boolean }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: selected ? '#1e3a8a' : '#1e293b',
        border: selected ? '1px solid #3b82f6' : '1px solid #334155',
        borderRadius: '8px',
        padding: '14px',
        cursor: 'pointer',
        transition: 'border-color 0.15s',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{
          fontSize: '11px', fontWeight: 600, color: 'white',
          background: layerColor(agent.layer),
          padding: '2px 8px', borderRadius: '4px',
        }}>
          L{agent.layer}
        </span>
        <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
          {agent.category}
        </span>
      </div>
      <div style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9', marginBottom: '4px' }}>
        {agent.name}
      </div>
      <div style={{ fontSize: '11px', color: '#94a3b8', fontFamily: 'monospace' }}>
        {agent.agent_id}
      </div>
      <div style={{ marginTop: '8px', fontSize: '10px', color: '#64748b' }}>
        {agent.outputs.length} output{agent.outputs.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

function ExecutionResultView({ result }: { result: Record<string, unknown> }) {
  const trace = result.trace as TraceRecord | undefined;
  const evidence = result.evidence as EvidenceReport | undefined;
  const output = result.output;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '20px' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase' }}>
          Output
        </h4>
        <pre style={{
          background: '#0f172a', padding: '12px', borderRadius: '6px',
          fontSize: '12px', color: '#cbd5e1', margin: 0, overflow: 'auto',
          fontFamily: 'monospace', maxHeight: '300px',
        }}>
          {JSON.stringify(output, null, 2)}
        </pre>
      </div>

      {trace && (
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '20px' }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase' }}>
            Trace ({trace.total_duration_ms.toFixed(2)} ms)
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {trace.events.map((ev, i) => (
              <div key={i} style={{
                display: 'grid',
                gridTemplateColumns: '120px 60px 1fr 80px',
                gap: '12px', alignItems: 'center',
                fontSize: '12px',
                padding: '6px 0',
                borderBottom: i < trace.events.length - 1 ? '1px solid #334155' : 'none',
              }}>
                <span style={{ fontFamily: 'monospace', color: '#cbd5e1' }}>{ev.agent_id}</span>
                <span style={{ color: layerColor(ev.layer), fontSize: '11px', fontWeight: 600 }}>L{ev.layer}</span>
                <span style={{ color: '#94a3b8', fontFamily: 'monospace', fontSize: '11px' }}>{ev.output_summary}</span>
                <span style={{
                  color: confidenceColor(ev.confidence),
                  textAlign: 'right', fontFamily: 'monospace', fontSize: '11px',
                }}>
                  {ev.confidence !== null ? `${(ev.confidence * 100).toFixed(0)}%` : '—'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {evidence && (
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '20px' }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase' }}>
            Evidence Report
          </h4>
          <div style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '8px' }}>
            <strong>Final conclusion:</strong> {evidence.final_conclusion || '(none)'}
          </div>
          <div style={{ fontSize: '12px', color: '#cbd5e1' }}>
            <strong>Contributors:</strong> {evidence.total_agents_executed} agents · {evidence.total_duration_ms.toFixed(2)} ms
          </div>
        </div>
      )}
    </div>
  );
}

function PipelineResultView({ result }: { result: Record<string, unknown> }) {
  const trace = result.trace as TraceRecord;
  const evidence = result.evidence as EvidenceReport;
  const outputs = (result.all_outputs || {}) as Record<string, unknown>;
  const eventsByLayer: Record<string, TraceEvent[]> = {};
  trace.events.forEach((ev) => {
    const key = String(ev.layer);
    if (!eventsByLayer[key]) eventsByLayer[key] = [];
    eventsByLayer[key].push(ev);
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Pipeline summary */}
      <div style={{
        background: 'linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%)',
        border: '1px solid #3b82f6',
        borderRadius: '8px',
        padding: '24px',
      }}>
        <div style={{ fontSize: '11px', color: '#93c5fd', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>
          Final Conclusion
        </div>
        <div style={{ fontSize: '24px', fontWeight: 700, color: 'white', marginBottom: '12px' }}>
          {trace.final_conclusion || '(no conclusion)'}
        </div>
        <div style={{ display: 'flex', gap: '24px', fontSize: '13px' }}>
          <div>
            <span style={{ color: '#93c5fd' }}>Total duration: </span>
            <span style={{ color: 'white', fontWeight: 600 }}>{trace.total_duration_ms.toFixed(2)} ms</span>
          </div>
          <div>
            <span style={{ color: '#93c5fd' }}>Agents executed: </span>
            <span style={{ color: 'white', fontWeight: 600 }}>{trace.events.length}</span>
          </div>
          <div>
            <span style={{ color: '#93c5fd' }}>Contributors: </span>
            <span style={{ color: 'white', fontWeight: 600 }}>{trace.contributor_chain.length}</span>
          </div>
        </div>
      </div>

      {/* Pipeline flow visualization */}
      <div style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '20px',
      }}>
        <h4 style={{ margin: '0 0 16px 0', fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase' }}>
          Layer-by-Layer Flow
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {['1', '2', '3', '4', '5'].map((layer) => {
            const events = eventsByLayer[layer] || [];
            if (events.length === 0) return null;
            const layerLabels: Record<string, string> = {
              '1': 'Layer 1 · Market Structure',
              '2': 'Layer 2 · Indicators',
              '3': 'Layer 3 · Institutional',
              '4': 'Layer 4 · Consensus',
              '5': 'Layer 5 · Supervisor',
            };
            return (
              <div key={layer}>
                <div style={{
                  fontSize: '11px', fontWeight: 600, color: layerColor(layer),
                  marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px',
                }}>
                  <span style={{ width: '4px', height: '12px', background: layerColor(layer), borderRadius: '2px' }} />
                  {layerLabels[layer]} · {events.length} agent{events.length !== 1 ? 's' : ''}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', paddingLeft: '12px' }}>
                  {events.map((ev, i) => (
                    <div key={i} style={{
                      background: '#0f172a',
                      border: `1px solid ${layerColor(layer)}40`,
                      borderRadius: '4px',
                      padding: '6px 10px',
                      fontSize: '11px',
                      fontFamily: 'monospace',
                      color: '#cbd5e1',
                    }}>
                      <span style={{ color: layerColor(layer) }}>{ev.agent_id}</span>
                      <span style={{ color: '#64748b', marginLeft: '6px' }}>
                        {ev.duration_ms.toFixed(1)}ms
                      </span>
                      {ev.confidence !== null && (
                        <span style={{
                          marginLeft: '6px',
                          color: confidenceColor(ev.confidence),
                          fontWeight: 600,
                        }}>
                          {(ev.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Evidence report */}
      <div style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '20px',
      }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase' }}>
          Evidence · Contributors to Final Conclusion
        </h4>
        <EvidenceSection title="Primary" contributors={evidence.primary_contributors} color="#3b82f6" />
        <EvidenceSection title="Supporting" contributors={evidence.supporting_contributors} color="#10b981" />
        <EvidenceSection title="Contextual" contributors={evidence.contextual_contributors} color="#94a3b8" />
        {evidence.failed_agents.length > 0 && (
          <EvidenceSection title="Failed" contributors={evidence.failed_agents} color="#ef4444" />
        )}
      </div>

      {/* All outputs (collapsible) */}
      <details style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '20px',
      }}>
        <summary style={{ cursor: 'pointer', fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase' }}>
          All Agent Outputs ({Object.keys(outputs).length})
        </summary>
        <pre style={{
          background: '#0f172a', padding: '12px', borderRadius: '6px',
          fontSize: '11px', color: '#cbd5e1', margin: '12px 0 0 0',
          overflow: 'auto', fontFamily: 'monospace', maxHeight: '400px',
        }}>
          {JSON.stringify(outputs, null, 2)}
        </pre>
      </details>
    </div>
  );
}

function EvidenceSection({
  title,
  contributors,
  color,
}: {
  title: string;
  contributors: EvidenceContribution[];
  color: string;
}) {
  if (contributors.length === 0) return null;
  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ fontSize: '11px', color, fontWeight: 600, marginBottom: '6px' }}>
        {title} ({contributors.length})
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {contributors.map((c, i) => (
          <div key={i} style={{
            display: 'grid',
            gridTemplateColumns: '140px 60px 1fr 70px',
            gap: '8px',
            fontSize: '11px',
            padding: '4px 0',
            alignItems: 'center',
          }}>
            <span style={{ fontFamily: 'monospace', color: '#cbd5e1' }}>{c.agent_id}</span>
            <span style={{ color: layerColor(c.layer) }}>L{c.layer}</span>
            <span style={{ color: '#94a3b8', fontFamily: 'monospace' }}>{c.output_summary}</span>
            <span style={{
              color: confidenceColor(c.confidence),
              textAlign: 'right', fontFamily: 'monospace',
            }}>
              {c.confidence !== null ? `${(c.confidence * 100).toFixed(0)}%` : '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function HistoryRow({ record }: { record: TraceRecord }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div style={{
      background: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '6px',
      overflow: 'hidden',
    }}>
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: '12px 16px',
          display: 'grid',
          gridTemplateColumns: '1fr 100px 80px 100px 100px',
          gap: '12px',
          alignItems: 'center',
          cursor: 'pointer',
          fontSize: '12px',
        }}
      >
        <span style={{ fontFamily: 'monospace', color: '#cbd5e1' }}>
          {record.symbol} · {record.timeframe}
          <span style={{ color: '#64748b', marginLeft: '12px' }}>{record.final_conclusion}</span>
        </span>
        <span style={{ color: record.success ? '#10b981' : '#ef4444', fontFamily: 'monospace' }}>
          {record.success ? '✓ success' : '✗ failed'}
        </span>
        <span style={{ color: '#94a3b8', textAlign: 'center' }}>{record.events.length} events</span>
        <span style={{ color: '#94a3b8', textAlign: 'right', fontFamily: 'monospace' }}>
          {record.total_duration_ms.toFixed(1)} ms
        </span>
        <span style={{ color: '#64748b', textAlign: 'right', fontSize: '11px' }}>
          {new Date(record.started_at).toLocaleTimeString()}
        </span>
      </div>
      {expanded && (
        <div style={{
          borderTop: '1px solid #334155',
          padding: '12px 16px',
          background: '#0f172a',
        }}>
          {record.events.map((ev, i) => (
            <div key={i} style={{
              display: 'grid',
              gridTemplateColumns: '120px 50px 1fr 60px',
              gap: '12px', fontSize: '11px', padding: '3px 0',
              fontFamily: 'monospace',
            }}>
              <span style={{ color: '#cbd5e1' }}>{ev.agent_id}</span>
              <span style={{ color: layerColor(ev.layer) }}>L{ev.layer}</span>
              <span style={{ color: '#94a3b8' }}>{ev.output_summary}</span>
              <span style={{ color: confidenceColor(ev.confidence), textAlign: 'right' }}>
                {ev.confidence !== null ? `${(ev.confidence * 100).toFixed(0)}%` : '—'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
