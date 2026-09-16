import React, { useState } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [query, setQuery] = useState('');
  const [sessionState, setSessionState] = useState(null);
  const [selections, setSelections] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmitQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setSelections({});
    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_query: query }),
      });
      const data = await res.json();
      setSessionState(data);
      
      if (data.status === 'READY_TO_GENERATE') {
        compileSQL(data, []);
      }
    } catch (err) {
      console.error("Query Error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionSelect = (term, optionId) => {
    setSelections({ ...selections, [term]: optionId });
  };

  const handleFinalSubmit = () => {
    const formattedClarifications = Object.entries(selections).map(([term, selected_option_id]) => ({
      term,
      selected_option_id,
    }));
    compileSQL(sessionState, formattedClarifications);
  };

  const compileSQL = async (stateObj, resolvedClarifications) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/clarify-and-compile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: stateObj?.session_id || "sess_default",
          raw_query: stateObj?.raw_query || query,
          resolved_clarifications: Array.isArray(resolvedClarifications) ? resolvedClarifications : [],
        }),
      });
      const data = await res.json();
      setSessionState(data);
    } catch (err) {
      console.error("Compilation Error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="landing-container">
      
      {/* Top Navbar */}
      <nav className="nav-bar">
        <div className="brand">
          <div className="brand-icon-box">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <ellipse cx="12" cy="5" rx="8" ry="3" stroke="#00ff80" />
              <path d="M4 5v6c0 1.66 3.58 3 8 3s8-1.34 8-3V5" stroke="#a1a1aa" />
              <path d="M4 11v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" stroke="#a1a1aa" />
              <path
                d="M17 2l.8 2.2L20 5l-2.2.8L17 8l-.8-2.2L14 5l2.2-.8L17 2z"
                fill="#00ff80"
                stroke="#00ff80"
                strokeWidth="0.8"
                style={{ filter: 'drop-shadow(0 0 4px #00ff80)' }}
              />
            </svg>
          </div>
          <span className="brand-text">
            Mahant <span className="brand-accent">AI</span>
          </span>
        </div>

        <div className="nav-actions">
          <div className="dev-badge">
            <span className="live-dot" />
            <span>Built by a <strong style={{ color: '#fff', fontWeight: 600 }}>BCA Student</strong></span>
          </div>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="nav-btn"
          >
            Developer Profile ➔
          </a>
        </div>
      </nav>

      {/* Hero Content */}
      <h1 className="hero-heading">Generate flawless SQL<br/>powered by AI</h1>
      <p className="hero-subtitle">
        Translate plain English into precise database queries. Let the AI clarify ambiguities and handle complex schemas while you focus on extracting insights.
      </p>

      {/* Trust Badges */}
      <button className="badge-btn">View Sandbox Schema ➔</button>
      <div className="trust-section">
        <span>High Precision Engine</span>
        <div style={{ color: '#00ff66', letterSpacing: '2px' }}>
          ★★★★★ <span style={{ color: '#fff', marginLeft: '4px' }}>99.9%</span>
        </div>
      </div>

      {/* Interactive Engine Area */}
      <div className="engine-container">
        
        {/* State 1: Input Box */}
        {(!sessionState || sessionState.status === 'IDLE') && (
          <>
            <form className="prompt-box" onSubmit={handleSubmitQuery}>
              <textarea
                className="query-input"
                rows="3"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Describe your data request (e.g., Show me top revenue for active users)..."
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmitQuery(e);
                  }
                }}
              />
              <div className="prompt-footer">
                <div className="prompt-tools">
                  <div className="tool-icon">🎙️</div>
                  <div className="tool-icon">📎</div>
                </div>
                <button type="submit" className="submit-circle" disabled={loading || !query.trim()}>
                  {loading ? '...' : '➔'}
                </button>
              </div>
            </form>
            
            <div className="chip-container">
              <span className="chip active">users</span>
              <span className="chip">orders</span>
              <span className="chip">products</span>
              <span className="chip">categories</span>
              <span className="chip">order_items</span>
            </div>
          </>
        )}

        {/* State 2: Clarification Panel */}
        {sessionState?.status === 'NEEDS_CLARIFICATION' && (
          <div className="prompt-box" style={{ padding: '30px' }}>
            <h3 style={{ margin: '0 0 5px 0', color: 'var(--accent-green)' }}>Clarification Required</h3>
            <p style={{ margin: '0 0 20px 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Resolve these ambiguities to generate exact SQL.
            </p>
            
            {sessionState.detected_ambiguities.map((amb) => (
              <div key={amb.term} className="clarify-group">
                <p style={{ margin: '0 0 12px 0', fontWeight: '500' }}>{amb.question}</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {amb.options.map((opt) => (
                    <label 
                      key={opt.id} 
                      className={`clarify-option ${selections[amb.term] === opt.id ? 'selected' : ''}`}
                    >
                      <input
                        type="radio"
                        name={amb.term}
                        value={opt.id}
                        checked={selections[amb.term] === opt.id}
                        onChange={() => handleOptionSelect(amb.term, opt.id)}
                        style={{ accentColor: '#00ff80' }}
                      />
                      <span style={{ fontSize: '0.9rem' }}>{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
            
            <button 
              onClick={handleFinalSubmit} 
              className="badge-btn" 
              style={{ margin: '10px auto 0', display: 'flex' }} 
              disabled={loading}
            >
              {loading ? 'Compiling...' : 'Confirm & Execute'}
            </button>
          </div>
        )}

        {/* State 3: Success Data View */}
        {sessionState?.status === 'SUCCESS' && (
          <div className="prompt-box results-box">
            <div className="results-header">
              <div>
                <div className="status-tag">Query Executed</div>
                <h3 className="query-title">"{sessionState.raw_query}"</h3>
              </div>
              <button 
                onClick={() => { setSessionState(null); setQuery(''); }} 
                className="reset-btn"
              >
                Start Over
              </button>
            </div>

            {/* Generated SQL */}
            <div className="section-wrapper">
              <span className="section-label">Generated SQL</span>
              <div className="sql-block">
                <code>{sessionState.generated_sql}</code>
              </div>
            </div>

            {/* Data Preview Table */}
            <div className="section-wrapper">
              <span className="section-label">
                Data Preview ({sessionState.query_results?.length || 0} rows)
              </span>
              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      {sessionState.query_results?.[0] && Object.keys(sessionState.query_results[0]).map((key) => (
                        <th key={key}>{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sessionState.query_results?.length > 0 ? (
                      sessionState.query_results.map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((val, i) => (
                            <td key={i}>{String(val ?? '')}</td>
                          ))}
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="100%" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                          No records returned.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}