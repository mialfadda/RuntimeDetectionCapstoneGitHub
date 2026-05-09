// Listen for threat alerts from background script
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'THREAT_DETECTED') {
    showWarningOverlay(msg.data);
  }
});

function showWarningOverlay(scanResult) {
  // Don't show duplicate overlays
  if (document.getElementById('rd-warning-overlay')) return;

  const overlay = document.createElement('div');
  overlay.id = 'rd-warning-overlay';
  overlay.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.85); z-index: 2147483647;
    display: flex; align-items: center; justify-content: center;
    font-family: system-ui, -apple-system, sans-serif;
  `;

  const card = document.createElement('div');
  card.style.cssText = `
    background: white; border-radius: 16px; padding: 40px;
    max-width: 480px; width: 90%; text-align: center;
    border: 3px solid #ef4444; box-shadow: 0 25px 50px rgba(0,0,0,0.3);
  `;

  const confidence = Math.round(scanResult.confidence * 100);

  card.innerHTML = `
    <div style="font-size: 48px; margin-bottom: 12px;">&#x26A0;</div>
    <h1 style="color: #ef4444; font-size: 28px; margin: 0 0 8px; font-weight: 800;">WARNING!</h1>
    <p style="color: #666; font-size: 16px; margin: 0 0 8px;">This site may be malicious</p>
    <p style="color: #999; font-size: 13px; margin: 0 0 24px;">
      Threat: <strong style="color:#333">${scanResult.threat_category}</strong> &middot;
      Confidence: <strong style="color:#333">${confidence}%</strong>
    </p>
    <div style="display: flex; flex-direction: column; gap: 10px;">
      <button id="rd-go-back" style="
        background: #2D5FA6; color: white; border: none; padding: 12px 24px;
        border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer;
      ">Go Back to Safety</button>
      <button id="rd-proceed" style="
        background: white; color: #666; border: 1px solid #ddd; padding: 10px 24px;
        border-radius: 8px; font-size: 13px; cursor: pointer;
      ">Proceed Anyway</button>
    </div>
  `;

  overlay.appendChild(card);
  document.body.appendChild(overlay);

  document.getElementById('rd-go-back').addEventListener('click', () => {
    history.back();
  });

  document.getElementById('rd-proceed').addEventListener('click', () => {
    overlay.remove();
  });
}
