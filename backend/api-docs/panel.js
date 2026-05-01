// panel.js — Right sidebar "Try It" request builder

const PANEL_EXAMPLES = {
  'news': { url: '/api/v1/news', params: { symbols: 'RELIANCE', limit: '3' } },
  'entities': { url: '/api/v1/entities', params: { search: 'tata' } },
  'sentiment': { url: '/api/v1/sentiment', params: { symbols: 'RELIANCE', period: '7d' } },
  'sector-sentiment': { url: '/api/v1/sentiment/sectors', params: { period: '7d' } },
};

const BASE_URL = (window.location.origin.includes('file://') || window.location.origin === 'null') 
  ? 'http://localhost:8000' 
  : window.location.origin;
let currentEndpoint = 'news';

function renderPanel(endpointId) {
  const panel = document.getElementById('panel');
  if (!panel) return;

  const ex = PANEL_EXAMPLES[endpointId] || PANEL_EXAMPLES['news'];
  const paramsHtml = Object.entries(ex.params).map(([k, v]) => `
    <div class="try-label">${k}</div>
    <input class="try-input" id="param-${k}" value="${v}" placeholder="${k}" />
  `).join('');

  const savedKey = localStorage.getItem('sentimatix_api_key') || '';

  panel.innerHTML = `
    <div class="panel-card">
      <div class="panel-title">🔑 Authentication</div>
      <div class="try-label">API Key</div>
      <input class="try-input" id="api-key-input" placeholder="Your API key..." value="${savedKey}" />
      <div style="font-size:11px;color:var(--muted);margin-top:4px">
        <a href="#" style="color:var(--accent-light)">Get a free API key →</a>
      </div>
    </div>

    <div class="panel-card">
      <div class="panel-title">⚡ Try It</div>
      <div class="try-label">Endpoint</div>
      <input class="try-input" id="try-url" value="${ex.url}" readonly style="color:var(--muted)" />
      ${paramsHtml}
      <button class="try-run-btn" onclick="runRequest('${endpointId}')">Run Request →</button>
      <div id="try-status" style="font-size:11px;color:var(--muted);margin-top:8px;"></div>
      <div class="try-response" id="try-response">// Response will appear here...</div>
    </div>

    <div class="panel-card">
      <div class="panel-title">📦 Quick Links</div>
      <div style="display:flex;flex-direction:column;gap:8px;font-size:12px">
        <a href="https://stockify-back.onrender.com/swagger" target="_blank" style="color:var(--accent-light)">🔗 Swagger UI (Live Docs)</a>
        <a href="https://stockify-back.onrender.com/openapi.json" target="_blank" style="color:var(--accent-light)">📄 OpenAPI Spec (JSON)</a>
        <a href="#pricing" style="color:var(--accent-light)">💳 View Pricing Plans</a>
      </div>
    </div>

    <div class="panel-card">
      <div class="panel-title">💡 Code Examples</div>
      <div style="font-size:11px;color:var(--muted);margin-bottom:10px">Copy & paste to get started</div>
      <pre style="font-family:var(--mono);font-size:10px;color:#86efac;background:var(--bg);padding:10px;border-radius:6px;overflow-x:auto;line-height:1.7">import requests

headers = {"Authorization": "Bearer YOUR_API_KEY"}
r = requests.get(
  "${BASE_URL}${ex.url}",
  headers=headers,
  params=${JSON.stringify(ex.params, null, 2)
    .replace(/"/g, '"')
    .replace(/\n/g, '\n  ')}
)
print(r.json())</pre>
    </div>
  `;
}

async function runRequest(endpointId) {
  const statusEl = document.getElementById('try-status');
  const responseEl = document.getElementById('try-response');
  const apiKey = document.getElementById('api-key-input')?.value || '';
  const ex = PANEL_EXAMPLES[endpointId] || PANEL_EXAMPLES['news'];

  // Collect current param values
  const params = new URLSearchParams();
  for (const key of Object.keys(ex.params)) {
    const inputEl = document.getElementById(`param-${key}`);
    if (inputEl && inputEl.value) params.append(key, inputEl.value);
  }

  let url = BASE_URL + ex.url;
  if ([...params].length) url += '?' + params.toString();

  statusEl.textContent = '⏳ Sending request...';
  responseEl.textContent = '';

  const headers = { 'Accept': 'application/json' };
  if (apiKey) headers['Authorization'] = 'Bearer ' + apiKey;

  try {
    const start = Date.now();
    const res = await fetch(url, { headers });
    const ms = Date.now() - start;
    const data = await res.json();
    statusEl.textContent = `✅ ${res.status} OK  •  ${ms}ms`;
    statusEl.style.color = 'var(--green)';
    responseEl.textContent = JSON.stringify(data, null, 2).slice(0, 2000);
  } catch (err) {
    statusEl.textContent = `❌ ${err.message}`;
    statusEl.style.color = 'var(--red)';
    responseEl.textContent = String(err);
  }
}

function updatePanel(endpointId) {
  currentEndpoint = endpointId;
  renderPanel(endpointId);
}

// Authentication handling
function initAuth() {
  const hash = window.location.hash.substring(1);
  const params = new URLSearchParams(hash);
  const key = params.get('key');
  const tier = params.get('tier');

  if (key && tier) {
    localStorage.setItem('sentimatix_api_key', key);
    localStorage.setItem('sentimatix_tier', tier);
    window.location.hash = ''; // Clear hash for security
  }

  const savedKey = localStorage.getItem('sentimatix_api_key');
  const savedTier = localStorage.getItem('sentimatix_tier');

  if (savedKey) {
    // Update API Key input
    const keyInput = document.getElementById('api-key-input');
    if (keyInput) keyInput.value = savedKey;

    // Update Nav bar
    const navAuth = document.getElementById('nav-auth-section');
    if (navAuth) {
      navAuth.innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;">
          <span style="font-size:13px;color:var(--muted);font-family:var(--mono)">Tier: <strong style="color:var(--accent-light);text-transform:uppercase">${savedTier}</strong></span>
          <button onclick="logout()" class="btn-ghost" style="padding:6px 12px;font-size:12px">Logout</button>
        </div>
      `;
    }
  }
}

function logout() {
  localStorage.removeItem('sentimatix_api_key');
  localStorage.removeItem('sentimatix_tier');
  window.location.reload();
}

async function upgradeToPro() {
  const savedKey = localStorage.getItem('sentimatix_api_key');
  if (!savedKey) {
    alert("Please log in / get a Free API Key before upgrading to Pro.");
    signupGoogle();
    return;
  }

  // Step 1 — Create a Razorpay order on the backend
  let orderData;
  try {
    const res = await fetch(BASE_URL + '/api/billing/create-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ authentication_key: savedKey }),
    });
    orderData = await res.json();
    if (!res.ok) {
      alert(orderData.detail || 'Could not create order. Please try again.');
      return;
    }
  } catch (err) {
    alert('Network error: ' + err.message);
    return;
  }

  // Step 2 — Open Razorpay checkout modal
  const options = {
    key:          orderData.key_id,
    amount:       orderData.amount,
    currency:     orderData.currency,
    name:         'Sentimatix',
    description:  'Pro API Subscription — ₹199/month',
    order_id:     orderData.order_id,
    prefill: {
      email: orderData.email,
    },
    theme: { color: '#6366f1' },

    // Step 3 — After successful payment, verify on the backend
    handler: async function(response) {
      try {
        const verifyRes = await fetch(BASE_URL + '/api/billing/verify-payment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            razorpay_order_id:   response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature:  response.razorpay_signature,
            authentication_key:  savedKey,
          }),
        });
        const result = await verifyRes.json();
        if (verifyRes.ok && result.status === 'success') {
          localStorage.setItem('sentimatix_tier', 'pro');
          alert('🎉 Payment successful! You are now on the Pro plan.');
          window.location.reload();
        } else {
          alert('Payment verification failed: ' + (result.detail || 'Unknown error'));
        }
      } catch (err) {
        alert('Verification error: ' + err.message);
      }
    },

    modal: {
      ondismiss: function() {
        console.log('Razorpay checkout closed by user');
      }
    }
  };

  const rzp = new Razorpay(options);
  rzp.open();
}

function loginGoogle() {
  window.location.href = BASE_URL + "/api/auth/google/login";
}

function signupGoogle() {
  window.location.href = BASE_URL + "/api/auth/google/signup";
}

// Initial render
renderPanel('news');
initAuth();
