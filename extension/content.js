// Listen for threat alerts from the background script.
// Accept both message names so legacy + new senders both work.
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'THREAT_DETECTED') {
    showWarningOverlay({
      severity: msg.data.risk_level,
      confidence: msg.data.confidence,
      url: msg.data.url,
      threat_category: msg.data.threat_category,
      scan_id: msg.data.scan_id,
      reason: 'This site may be malicious',
      explanation: {},
    });
  } else if (msg.type === 'SHOW_WARNING') {
    showWarningOverlay(msg.data);
  }
});

function showWarningOverlay(payload) {
  // Don't show on chrome:// / extension pages (content scripts shouldn't
  // be injected there anyway, but belt-and-braces).
  if (location.protocol === 'chrome:' || location.protocol === 'chrome-extension:'
      || location.protocol === 'about:' || location.protocol === 'moz-extension:') {
    return;
  }
  // Don't show duplicate overlays
  if (document.getElementById('rd-warning-overlay')) return;

  const overlay = document.createElement('div');
  overlay.id = 'rd-warning-overlay';
  overlay.style.cssText = [
    'position:fixed','top:0','left:0','width:100%','height:100%',
    'background:rgba(0,0,0,0.85)','z-index:2147483647',
    'display:flex','align-items:center','justify-content:center',
    'font-family:system-ui,-apple-system,sans-serif'
  ].join(';');

  const card = document.createElement('div');
  card.style.cssText = [
    'background:white','border-radius:16px','padding:32px 40px',
    'max-width:560px','width:90%','text-align:center',
    'border:3px solid #ef4444','box-shadow:0 25px 50px rgba(0,0,0,0.3)',
    'max-height:90vh','overflow-y:auto'
  ].join(';');

  const confidence = payload.confidence != null
    ? Math.round(payload.confidence * 100) : '—';
  const category = payload.threat_category || 'malicious';

  card.innerHTML =
    '<div style="font-size:48px;margin-bottom:12px;">&#x26A0;</div>' +
    '<h1 style="color:#ef4444;font-size:28px;margin:0 0 8px;font-weight:800;">WARNING!</h1>' +
    '<p style="color:#666;font-size:16px;margin:0 0 8px;">' + escapeHtml(payload.reason || 'This site may be malicious') + '</p>' +
    (payload.url ? '<p style="color:#999;font-size:12px;margin:0 0 6px;word-break:break-all;font-family:monospace;">' + escapeHtml(payload.url) + '</p>' : '') +
    '<p style="color:#999;font-size:13px;margin:0 0 20px;">' +
      'Threat: <strong style="color:#333">' + escapeHtml(category) + '</strong> &middot; ' +
      'Confidence: <strong style="color:#333">' + confidence + '%</strong>' +
    '</p>' +
    '<div id="rd-explanation" style="display:none;text-align:left;background:#f5f7fb;border-radius:8px;padding:14px;margin-bottom:16px;font-size:13px;color:#333;"></div>' +
    '<div style="display:flex;flex-direction:column;gap:10px;">' +
      '<button id="rd-go-back" style="background:#2D5FA6;color:white;border:none;padding:12px 24px;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;">Go Back to Safety</button>' +
      '<button id="rd-view-exp" style="background:white;color:#2D5FA6;border:1px solid #2D5FA6;padding:10px 24px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;">View Explanation</button>' +
      '<button id="rd-proceed" style="background:white;color:#666;border:1px solid #ddd;padding:10px 24px;border-radius:8px;font-size:13px;cursor:pointer;">Proceed Anyway</button>' +
    '</div>';

  overlay.appendChild(card);
  document.body.appendChild(overlay);

  document.getElementById('rd-go-back').addEventListener('click', () => {
    window.history.back();
  });
  document.getElementById('rd-proceed').addEventListener('click', () => {
    overlay.remove();
  });

  const expBox = document.getElementById('rd-explanation');
  document.getElementById('rd-view-exp').addEventListener('click', async () => {
    if (expBox.style.display === 'block') { expBox.style.display = 'none'; return; }
    expBox.style.display = 'block';
    expBox.innerHTML = 'Loading explanation...';
    try {
      const exp = await new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(
          { type: 'GET_EXPLANATION', scan_id: payload.scan_id },
          (res) => res && res.ok ? resolve(res.data) : reject(new Error((res && res.error) || 'Load failed'))
        );
      });
      const features = exp.top_features || [];
      expBox.innerHTML =
        '<div style="font-weight:600;color:#1A3A6B;margin-bottom:6px;">' +
          (exp.method ? exp.method.toUpperCase() : 'SHAP') + ' Explanation' +
        '</div>' +
        '<div style="margin-bottom:10px;color:#444;">' + escapeHtml(exp.summary_text || 'No summary available.') + '</div>' +
        (features.length
          ? '<div style="font-weight:600;color:#1A3A6B;margin-bottom:4px;">Top indicators</div>' +
            features.map(([name, score]) =>
              '<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #e2e8f0;">' +
                '<span>' + escapeHtml(name) + '</span>' +
                '<span style="font-weight:600;">' + Math.round(score * 100) + '%</span>' +
              '</div>').join('')
          : '');
    } catch (e) {
      expBox.innerHTML = '<span style="color:#ef4444;">' + escapeHtml(e.message) + '</span>';
    }
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}
