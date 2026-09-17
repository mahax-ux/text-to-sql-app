import React, { useState } from 'react';

const API_BASE_URL = 'https://text-to-sql-app-4t3e.onrender.com';

export default function App() {
  const [query, setQuery] = useState('');
  const [sessionState, setSessionState] = useState(null);
  const [selections, setSelections] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmitQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setSelections({});

    try {
      const res = await fetch(`${API_BASE_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          raw_query: query.trim(), // Sent to support both backend payload schemas
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server responded with status ${res.status}`);
      }

      const data = await res.json();
      setSessionState(data);

      // Auto-compile if the query has no ambiguities detected
      if (data.status === 'READY_TO_GENERATE') {
        compileSQL(data, []);
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionSelect = (term, optionId) => {
    setSelections((prev) => ({ ...prev, [term]: optionId }));
  };

  const handleClarificationSubmit = () => {
    const formattedClarifications = Object.entries(selections).map(
      ([term, selected_option_id]) => ({
        term,
        selected_option_id,
      })
    );
    compileSQL(sessionState, formattedClarifications);
  };

  const compileSQL = async (stateObj, resolvedClarifications) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/clarify-and-compile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: stateObj.session_id || 'web_session',
          query: stateObj.raw_query || query.trim(),
          raw_query: stateObj.raw_query || query.trim(),
          resolved_clarifications: resolvedClarifications,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server responded with status ${res.status}`);
      }

      const data = await res.json();
      setSessionState(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '850px', margin: '40px auto', fontFamily: 'system-ui, sans-serif', padding: '0 20px' }}>
      <h1 style={{ fontSize: '24px', marginBottom: '8px' }}>Text-to-SQL Clarification Engine</h1>
      <p style={{ color: '#666', marginBottom: '24px' }}>
        Translates ambiguous business queries into unambiguous SQLite queries.
      </p>

      {/* Input Form */}
      <form onSubmit={handleSubmitQuery} style={{ display: 'flex', gap: '10px', marginBottom: '24px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Show me top revenue for active users"
          style={{
            flex: 1,
            padding: '12px 16px',
            fontSize: '15px',
            borderRadius: '6px',
            border: '1px solid #ccc',
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '12px 24px',
            fontSize: '15px',
            fontWeight: 600,
            color: '#fff',
            backgroundColor: loading ? '#888' : '#0070f3',
            border: 'none',
            borderRadius: '6px',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Processing...' : 'Run Query'}
        </button>
      </form>

      {/* Error Banner */}
      {error && (
        <div style={{ padding: '12px 16px', background: '#ffeef0', color: '#b31d28', borderRadius: '6px', marginBottom: '20px' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Clarification Options Screen */}
      {sessionState?.status === 'NEEDS_CLARIFICATION' && (
        <div style={{ background: '#f6f8fa', border: '1px solid #d0d7de', borderRadius: '8px', padding: '20px', marginBottom: '24px' }}>
          <h3 style={{ marginTop: 0, marginBottom: '16px', fontSize: '18px' }}>Clarification Needed</h3>
          {sessionState.detected_ambiguities?.map((amb, idx) => (
            <div key={amb.term || idx} style={{ marginBottom: '20px' }}>
              <p style={{ fontWeight: 600, marginBottom: '8px' }}>{amb.question}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {amb.options?.map((opt) => (
                  <label
                    key={opt.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      cursor: 'pointer',
                      padding: '8px 12px',
                      borderRadius: '4px',
                      border: '1px solid #e1e4e8',
                      background: selections[amb.term] === opt.id ? '#e7f3ff' : '#fff',
                    }}
                  >
                    <input
                      type="radio"
                      name={amb.term}
                      value={opt.id}
                      checked={selections[amb.term] === opt.id}
                      onChange={() => handleOptionSelect(amb.term, opt.id)}
                    />
                    <span>
                      <strong>{opt.label}</strong>
                      {opt.sql_snippet && (
                        <code style={{ marginLeft: '8px', fontSize: '12px', color: '#555' }}>
                          ({opt.sql_snippet})
                        </code>
                      )}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ))}

          <button
            onClick={handleClarificationSubmit}
            disabled={loading || Object.keys(selections).length === 0}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: 600,
              backgroundColor: '#2ea44f',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Compiling...' : 'Confirm Choices & Generate SQL'}
          </button>
        </div>
      )}

      {/* SQL & Execution Results */}
      {sessionState?.status === 'SUCCESS' && (
        <div>
          <h3 style={{ marginBottom: '8px' }}>Generated SQL Query</h3>
          <pre
            style={{
              background: '#0d1117',
              color: '#58a6ff',
              padding: '16px',
              borderRadius: '6px',
              overflowX: 'auto',
              fontSize: '14px',
            }}
          >
            {sessionState.generated_sql}
          </pre>

          <h3 style={{ marginTop: '24px', marginBottom: '8px' }}>Results</h3>
          {sessionState.query_results && sessionState.query_results.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: '#f6f8fa', borderBottom: '2px solid #d0d7de' }}>
                    {Object.keys(sessionState.query_results[0]).map((key) => (
                      <th key={key} style={{ textAlign: 'left', padding: '10px' }}>
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sessionState.query_results.map((row, rowIdx) => (
                    <tr key={rowIdx} style={{ borderBottom: '1px solid #e1e4e8' }}>
                      {Object.values(row).map((val, cellIdx) => (
                        <td key={cellIdx} style={{ padding: '10px' }}>
                          {val !== null ? String(val) : 'NULL'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: '#666', fontStyle: 'italic' }}>Query executed successfully but returned 0 rows.</p>
          )}
        </div>
      )}
    </div>
  );
}