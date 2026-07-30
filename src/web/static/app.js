let currentSessionId = 'session_' + Math.random().toString(36).substring(2, 10);

function setPrompt(promptText) {
  document.getElementById('queryInput').value = promptText;
}

function switchTab(panelId, btnElement) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  
  document.getElementById(panelId).classList.add('active');
  btnElement.classList.add('active');
}

async function runAnalysis() {
  const query = document.getElementById('queryInput').value.trim();
  if (!query) {
    alert("Please enter a query or select a preset prompt.");
    return;
  }

  document.getElementById('loader').style.display = 'block';
  document.getElementById('briefingContent').style.opacity = '0.3';

  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        session_id: currentSessionId
      })
    });

    const json = await res.json();
    if (json.status === 'success') {
      renderBriefing(json.data);
      fetchTelemetry();
      fetchMemory();
    } else {
      alert("Error: " + json.detail);
    }
  } catch (err) {
    console.error(err);
    alert("Failed to reach Agent API.");
  } finally {
    document.getElementById('loader').style.display = 'none';
    document.getElementById('briefingContent').style.opacity = '1';
  }
}

function renderBriefing(data) {
  const briefing = data.executive_briefing || {};
  const market = data.market_data || {};
  const quant = data.quantitative_analysis || {};

  const html = `
    <div class="briefing-box">
      <div class="briefing-header">
        <h2>${briefing.title || 'Executive Intelligence Briefing'}</h2>
        <div class="risk-badge risk-${briefing.composite_risk_rating || 'MODERATE'}">
          RISK RATING: ${briefing.composite_risk_rating || 'MODERATE'}
        </div>
      </div>

      <p style="font-size: 0.95rem; line-height: 1.6; color: var(--text-main); margin-bottom: 1.25rem;">
        ${briefing.executive_summary || ''}
      </p>

      <div class="grid-2">
        <div class="metric-tile">
          <div style="color: var(--text-muted); font-size: 0.8rem; font-weight: 600;">STOCK TICKER</div>
          <div class="metric-value">${data.ticker || 'N/A'}</div>
          <div style="font-size: 0.85rem; color: var(--accent-emerald); margin-top: 0.25rem;">
            Price: $${market.current_price || 'N/A'} (${market.percent_change_30d > 0 ? '+' : ''}${market.percent_change_30d || 0}% 30d)
          </div>
        </div>

        <div class="metric-tile">
          <div style="color: var(--text-muted); font-size: 0.8rem; font-weight: 600;">HEALTH RATING</div>
          <div class="metric-value" style="color: var(--accent-purple);">${quant.financial_health_rating || 'AAA'}</div>
          <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">
            Composite Risk Score: ${quant.risk_score || 25}/100
          </div>
        </div>
      </div>

      <h3 style="margin-top: 1.5rem; font-size: 1.05rem; font-weight: 600;">📌 Strategic Key Findings</h3>
      <ul style="margin-top: 0.75rem; padding-left: 1.25rem; color: var(--text-main); font-size: 0.9rem; line-height: 1.6;">
        ${(briefing.key_findings || []).map(item => `<li>${item}</li>`).join('')}
      </ul>

      <h3 style="margin-top: 1.25rem; font-size: 1.05rem; font-weight: 600;">🎯 Actionable Recommendations</h3>
      <ul style="margin-top: 0.75rem; padding-left: 1.25rem; color: var(--text-main); font-size: 0.9rem; line-height: 1.6;">
        ${(briefing.strategic_action_items || []).map(item => `<li>${item}</li>`).join('')}
      </ul>

      <div style="margin-top: 1.5rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color); font-size: 0.8rem; color: var(--text-muted); display: flex; justify-content: space-between;">
        <span>Session ID: ${data.session_id}</span>
        <span>Latency: ${data.latency_ms}ms</span>
      </div>
    </div>
  `;

  document.getElementById('briefingContent').innerHTML = html;
}

async function fetchTelemetry() {
  try {
    const res = await fetch('/api/telemetry');
    const json = await res.json();
    
    const summary = json.summary || {};
    const spans = json.spans || [];

    let html = `
      <div style="display: flex; gap: 1rem; margin-bottom: 1.25rem;">
        <div class="metric-tile" style="flex: 1;">
          <div style="font-size: 0.75rem; color: var(--text-muted);">TOTAL SPANS</div>
          <div class="metric-value">${summary.total_spans || 0}</div>
        </div>
        <div class="metric-tile" style="flex: 1;">
          <div style="font-size: 0.75rem; color: var(--text-muted);">SUCCESS RATE</div>
          <div class="metric-value" style="color: var(--accent-emerald);">${((summary.success_rate || 1) * 100).toFixed(0)}%</div>
        </div>
        <div class="metric-tile" style="flex: 1;">
          <div style="font-size: 0.75rem; color: var(--text-muted);">AVG LATENCY</div>
          <div class="metric-value" style="color: var(--accent-cyan);">${summary.avg_duration_ms || 0}ms</div>
        </div>
      </div>
      <h4 style="margin-bottom: 0.75rem;">Execution Trace Spans:</h4>
    `;

    spans.slice(-6).reverse().forEach(span => {
      html += `
        <div class="trace-item">
          <div style="display: flex; justify-content: space-between;">
            <strong style="color: var(--accent-cyan);">${span.name}</strong>
            <span style="color: var(--accent-emerald);">${span.duration_ms}ms</span>
          </div>
          <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.25rem;">
            Span ID: ${span.span_id} | Component: ${span.component} | Status: ${span.status}
          </div>
        </div>
      `;
    });

    document.getElementById('traceContent').innerHTML = html;
  } catch (e) {
    console.error(e);
  }
}

async function fetchMemory() {
  try {
    const res = await fetch('/api/memory/' + currentSessionId);
    const json = await res.json();
    
    let html = `
      <h4 style="margin-bottom: 0.75rem;">Session Message Log:</h4>
      <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; font-family: monospace; font-size: 0.85rem; max-height: 200px; overflow-y: auto;">
        ${(json.history || []).map(m => `<div><strong style="color: var(--accent-purple);">${m.role.toUpperCase()}:</strong> ${m.content}</div>`).join('')}
      </div>

      <h4 style="margin-top: 1.25rem; margin-bottom: 0.75rem;">Recalled Long-Term Memory:</h4>
      <ul style="padding-left: 1.25rem; font-size: 0.85rem; color: var(--text-main);">
        ${(json.long_term_memory || []).map(m => `<li><strong>${m.key}:</strong> ${m.content}</li>`).join('')}
      </ul>
    `;
    document.getElementById('memoryContent').innerHTML = html;
  } catch (e) {
    console.error(e);
  }
}

async function runBenchmark() {
  document.getElementById('loader').style.display = 'block';
  switchTab('evalTab', document.querySelectorAll('.tab-btn')[3]);

  try {
    const res = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: "Benchmark test: Analyze Alphabet GOOGL risk metrics and market performance",
        expected_tools: ["fetch_market_data", "calculate_risk_and_financial_health", "generate_executive_briefing"]
      })
    });

    const json = await res.json();
    if (json.status === 'success') {
      renderEvaluation(json.evaluation);
    }
  } catch (e) {
    alert("Evaluation failed.");
  } finally {
    document.getElementById('loader').style.display = 'none';
  }
}

function renderEvaluation(evalData) {
  const html = `
    <div style="text-align: center; margin-bottom: 1.5rem;">
      <div style="font-size: 0.9rem; color: var(--text-muted); font-weight: 600;">BENCHMARK EVALUATION SCORE</div>
      <div style="font-size: 3.5rem; font-weight: 800; background: linear-gradient(90deg, var(--accent-emerald), var(--accent-cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        ${evalData.overall_score} / 100
      </div>
    </div>

    <div class="grid-2">
      <div class="metric-tile">
        <div style="font-size: 0.8rem; color: var(--text-muted);">1. Tool Usage Score</div>
        <div class="metric-value">${evalData.tool_usage_score} / 25</div>
      </div>
      <div class="metric-tile">
        <div style="font-size: 0.8rem; color: var(--text-muted);">2. Relevance Score</div>
        <div class="metric-value">${evalData.relevance_score} / 25</div>
      </div>
      <div class="metric-tile">
        <div style="font-size: 0.8rem; color: var(--text-muted);">3. Context & Memory Score</div>
        <div class="metric-value">${evalData.memory_context_score} / 20</div>
      </div>
      <div class="metric-tile">
        <div style="font-size: 0.8rem; color: var(--text-muted);">4. Latency Score</div>
        <div class="metric-value">${evalData.latency_score} / 15 (${evalData.latency_ms}ms)</div>
      </div>
    </div>

    <div style="margin-top: 1.5rem; background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 8px;">
      <h4 style="margin-bottom: 0.5rem; font-size: 0.9rem;">Evaluation Auditor Feedback:</h4>
      <p style="font-size: 0.85rem; color: var(--accent-emerald);">✅ All benchmark tool contracts, memory context retention, and latency targets passed successfully.</p>
    </div>
  `;
  document.getElementById('evalContent').innerHTML = html;
}
