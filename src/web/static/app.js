let currentSessionId = "web_session_" + Math.random().toString(36).substring(2, 9);

function setPrompt(text) {
  document.getElementById("queryInput").value = text;
}

function switchTab(tabId, btn) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  
  const target = document.getElementById(tabId);
  if (target) target.classList.add("active");
  if (btn) btn.classList.add("active");
}

function showLoader(show) {
  document.getElementById("loader").style.display = show ? "block" : "none";
}

async function runAnalysis() {
  const query = document.getElementById("queryInput").value.trim();
  const requireHitl = document.getElementById("requireHitlCheckbox").checked;
  if (!query) {
    alert("Please enter an analysis query.");
    return;
  }

  showLoader(true);
  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        session_id: currentSessionId,
        user_id: "web_user",
        require_hitl: requireHitl
      })
    });

    const data = await res.json();
    if (data.status === "success") {
      renderBriefing(data.data);
      loadTelemetry();
      loadMemory();
      loadHITL();
      switchTab("briefingTab", document.querySelector(".tab-btn:nth-child(1)"));
    } else {
      alert("Error: " + JSON.stringify(data));
    }
  } catch (err) {
    alert("Request failed: " + err.message);
  } finally {
    showLoader(false);
  }
}

function renderBriefing(data) {
  const briefingContainer = document.getElementById("briefingContent");
  if (data.status === "GUARDRAIL_VIOLATION") {
    briefingContainer.innerHTML = `
      <div style="background: rgba(244, 63, 94, 0.15); border: 1px solid var(--accent-rose); border-radius: 10px; padding: 1.5rem;">
        <h3 style="color: var(--accent-rose); margin-bottom: 0.5rem;">🛡️ Guardrail Intercept Activated</h3>
        <p><strong>Code:</strong> ${data.violation_code || "SAFETY_POLICY_VIOLATION"}</p>
        <p style="margin-top: 0.5rem;">${data.error}</p>
      </div>
    `;
    return;
  }

  const b = data.executive_briefing || {};
  const riskClass = `risk-${b.composite_risk_rating || "MODERATE"}`;
  const routing = data.model_routing || {};
  const rootModel = routing.recommended_root_model || "gemini-2.5-pro";

  let findingsHtml = (b.key_findings || []).map(f => `<li style="margin-bottom: 0.4rem;">${f}</li>`).join("");
  let actionsHtml = (b.strategic_action_items || []).map(a => `<li style="margin-bottom: 0.4rem;">✓ ${a}</li>`).join("");

  briefingContainer.innerHTML = `
    <div class="briefing-box">
      <div class="briefing-header">
        <div>
          <h2 style="font-size: 1.25rem; font-weight: 700; color: #fff;">${b.title || "Executive Intelligence Briefing"}</h2>
          <div style="display: flex; gap: 0.5rem; margin-top: 0.4rem; font-size: 0.8rem; color: var(--text-muted);">
            <span>Session: ${data.session_id}</span>
            <span>•</span>
            <span>Latency: ${data.latency_ms}ms</span>
            <span>•</span>
            <span style="color: var(--accent-cyan);">Model: ${rootModel}</span>
          </div>
        </div>
        <div style="display: flex; gap: 0.5rem; align-items: center;">
          <span class="risk-badge ${riskClass}">${b.composite_risk_rating || "MODERATE"} RISK</span>
          <span class="pill" style="background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald);">
            ${data.hitl_status || "APPROVED"}
          </span>
        </div>
      </div>

      <div style="margin-bottom: 1.25rem;">
        <h4 style="color: var(--accent-cyan); font-size: 0.95rem; margin-bottom: 0.4rem;">Executive Summary</h4>
        <p style="line-height: 1.6; color: #e5e7eb;">${b.executive_summary || "Summary not available."}</p>
      </div>

      <div class="grid-2">
        <div class="metric-tile">
          <h4 style="color: var(--text-main); font-size: 0.95rem;">Key Analytical Findings</h4>
          <ul style="margin-top: 0.6rem; padding-left: 1.2rem; color: var(--text-muted); font-size: 0.88rem;">
            ${findingsHtml || "<li>No specific findings logged.</li>"}
          </ul>
        </div>
        <div class="metric-tile">
          <h4 style="color: var(--text-main); font-size: 0.95rem;">Strategic Action Items</h4>
          <ul style="margin-top: 0.6rem; padding-left: 1.2rem; color: var(--accent-emerald); font-size: 0.88rem; list-style: none;">
            ${actionsHtml || "<li>Standard quarterly cadence review.</li>"}
          </ul>
        </div>
      </div>

      <div style="margin-top: 1.25rem; font-size: 0.78rem; color: var(--text-muted); padding: 0.75rem; background: rgba(0, 0, 0, 0.3); border-radius: 6px;">
        <strong>Regulatory Notice:</strong> ${b.disclaimer || "Generated autonomously by ADK Agent System."}
      </div>
    </div>
  `;
}

async function loadTelemetry() {
  const container = document.getElementById("traceContent");
  try {
    const res = await fetch("/api/telemetry");
    const data = await res.json();
    const spans = data.spans || [];
    const summary = data.summary || {};

    let html = `
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
        <div class="metric-tile"><div>Total Spans</div><div class="metric-value">${summary.total_spans || 0}</div></div>
        <div class="metric-tile"><div>Avg Latency</div><div class="metric-value">${summary.avg_duration_ms || 0}ms</div></div>
        <div class="metric-tile"><div>Success Rate</div><div class="metric-value">${Math.round((summary.success_rate || 1) * 100)}%</div></div>
        <div class="metric-tile"><div>Tool Calls</div><div class="metric-value">${summary.total_tool_calls || 0}</div></div>
      </div>
      <h4 style="margin-bottom: 0.75rem; color: var(--text-main);">Distributed Execution Spans (PII Scrubbed)</h4>
    `;

    spans.slice(-10).reverse().forEach(span => {
      const modelTag = span.model_tier ? `<span style="color: var(--accent-purple); font-size: 0.75rem;">[${span.model_tier}]</span>` : "";
      html += `
        <div class="trace-item">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
            <strong>${span.name}</strong> ${modelTag}
            <span style="color: ${span.status === 'OK' ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">${span.status} (${span.duration_ms || 0}ms)</span>
          </div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">
            Trace: ${span.trace_id} | Component: ${span.component}
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = `<p style="color: var(--accent-rose);">Failed to load telemetry: ${e.message}</p>`;
  }
}

async function loadMemory() {
  const container = document.getElementById("memoryContent");
  try {
    const res = await fetch(`/api/memory/${currentSessionId}`);
    const data = await res.json();
    const history = data.history || [];
    const memories = data.vector_memory_store || [];

    let historyHtml = history.map(h => `
      <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(255, 255, 255, 0.02); border-radius: 6px; font-size: 0.85rem;">
        <strong style="color: ${h.role === 'user' ? 'var(--accent-cyan)' : 'var(--accent-purple)'};">${h.role.toUpperCase()}:</strong>
        <span style="color: #e5e7eb; margin-left: 0.5rem;">${h.content}</span>
      </div>
    `).join("") || "<p style='color: var(--text-muted);'>No turns recorded yet.</p>";

    let memoryHtml = memories.map(m => `
      <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(0,0,0,0.25); border-left: 3px solid var(--accent-cyan); font-size: 0.85rem;">
        <strong>${m.key}:</strong> <span style="color: var(--text-muted);">${m.content}</span>
      </div>
    `).join("") || "<p style='color: var(--text-muted);'>No long-term memories indexed yet.</p>";

    container.innerHTML = `
      <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
          <h4 style="color: var(--text-main);">Session Messages (${data.storage_backend})</h4>
          <span style="font-size: 0.8rem; color: var(--text-muted);">Session ID: ${data.session_id}</span>
        </div>
        ${historyHtml}
      </div>
      <div>
        <h4 style="color: var(--text-main); margin-bottom: 0.75rem;">Semantic Vector Memory Index</h4>
        ${memoryHtml}
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<p style="color: var(--accent-rose);">Failed to load memory: ${e.message}</p>`;
  }
}

async function loadHITL() {
  const container = document.getElementById("hitlContent");
  try {
    const res = await fetch("/api/hitl/pending");
    const data = await res.json();
    const pending = data.pending_approvals || [];

    if (pending.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          <h4>✅ No Approvals Pending</h4>
          <p style="font-size: 0.85rem; margin-top: 0.4rem;">High-risk decisions requiring human sign-off will automatically appear here with review controls.</p>
        </div>
      `;
      return;
    }

    let html = "";
    pending.forEach(item => {
      html += `
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <h4 style="color: #f59e0b;">⚠️ ${item.title}</h4>
            <span class="risk-badge risk-${item.risk_level}">${item.risk_level} RISK</span>
          </div>
          <p style="font-size: 0.9rem; color: var(--text-main); margin-bottom: 0.75rem;">${item.description}</p>
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn-primary" style="padding: 0.5rem 1rem; font-size: 0.85rem; background: var(--accent-emerald);" onclick="decideHITL('${item.approval_id}', 'APPROVE')">
              ✅ Approve Release
            </button>
            <button class="btn-primary" style="padding: 0.5rem 1rem; font-size: 0.85rem; background: var(--accent-rose);" onclick="decideHITL('${item.approval_id}', 'REJECT')">
              ❌ Reject
            </button>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = `<p style="color: var(--accent-rose);">Failed to load HITL: ${e.message}</p>`;
  }
}

async function decideHITL(approvalId, decision) {
  try {
    const res = await fetch("/api/hitl/decision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approval_id: approvalId, decision: decision, notes: "Processed via Web Dashboard" })
    });
    const data = await res.json();
    if (data.status === "success") {
      alert(`Decision '${decision}' applied successfully.`);
      loadHITL();
    }
  } catch (e) {
    alert("HITL decision failed: " + e.message);
  }
}

async function runGoldenBenchmark() {
  switchTab("evalTab", document.querySelector(".tab-btn:nth-child(5)"));
  const container = document.getElementById("evalContent");
  container.innerHTML = `
    <div style="text-align: center; padding: 2rem;">
      <div class="spinner"></div>
      <p style="color: var(--accent-cyan); font-weight: 600;">Executing Golden Dataset Benchmark Suite across 6 scenarios...</p>
    </div>
  `;

  try {
    const res = await fetch("/api/evaluate/golden", { method: "POST" });
    const data = await res.json();

    let rowsHtml = (data.results || []).map(r => `
      <tr style="border-bottom: 1px solid var(--border-color);">
        <td style="padding: 0.75rem; font-weight: 600;">${r.id}</td>
        <td style="padding: 0.75rem; color: var(--text-muted);">${r.category}</td>
        <td style="padding: 0.75rem; font-weight: 700; color: var(--accent-cyan);">${r.score}/100</td>
        <td style="padding: 0.75rem;">
          <span style="color: ${r.passed ? 'var(--accent-emerald)' : 'var(--accent-rose)'}; font-weight: 700;">
            ${r.passed ? '✅ PASS' : '❌ FAIL'}
          </span>
        </td>
        <td style="padding: 0.75rem; color: var(--text-muted);">${r.latency_ms}ms</td>
      </tr>
    `).join("");

    container.innerHTML = `
      <div style="margin-bottom: 1.5rem;">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
          <div class="metric-tile"><div>Pass Rate</div><div class="metric-value" style="color: var(--accent-emerald);">${data.pass_rate_pct}%</div></div>
          <div class="metric-tile"><div>Average Score</div><div class="metric-value">${data.avg_score}/100</div></div>
          <div class="metric-tile"><div>Test Scenarios</div><div class="metric-value">${data.total_cases}</div></div>
          <div class="metric-tile"><div>Execution Time</div><div class="metric-value">${data.duration_sec}s</div></div>
        </div>

        <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem; text-align: left;">
          <thead>
            <tr style="border-bottom: 2px solid var(--border-color); color: var(--text-muted);">
              <th style="padding: 0.75rem;">Test ID</th>
              <th style="padding: 0.75rem;">Category</th>
              <th style="padding: 0.75rem;">Score</th>
              <th style="padding: 0.75rem;">Status</th>
              <th style="padding: 0.75rem;">Latency</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<p style="color: var(--accent-rose);">Benchmark failed: ${e.message}</p>`;
  }
}
