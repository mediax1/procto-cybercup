(() => {
  'use strict';
  const API = '/api/v1';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  const state = {
    token: localStorage.getItem('atelier_token') || '',
    user: null,
    route: 'products',
    products: [],
    category: '',
    query: '',
    page: 1,
    pageSize: 9,
    cart: [],
  };

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const money = v => new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', maximumFractionDigits: 0,
  }).format(Number(v || 0));

  // ── Core API helper ─────────────────────────────────────────────────────────
  // Only ever calls one of the 6 live endpoints:
  //   POST /api/v1/auth/login       (documented)
  //   GET  /api/v1/products         (documented)
  //   POST /api/v1/orders           (documented)
  //   POST /api/v1/auth/signup      (shadow)
  //   GET  /api/v1/orders/{id}      (shadow – IDOR)
  //   GET  /api/v1/customers/{id}   (shadow – no auth)
  async function api(path, { method = 'GET', body, auth = true } = {}) {
    const headers = { 'Accept': 'application/json' };
    if (body) headers['Content-Type'] = 'application/json';
    if (auth && state.token) headers.Authorization = `Bearer ${state.token}`;
    let response, data;
    try {
      response = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
      const text = await response.text();
      try { data = text ? JSON.parse(text) : null; } catch { data = text; }
    } catch {
      data = { detail: 'Network error' };
      response = { status: 0, ok: false };
    }
    return { ok: response.ok, status: response.status, data };
  }

  // ── UI helpers ───────────────────────────────────────────────────────────────
  function updateSession() {
    const logged = !!state.user;
    $('#user-label').textContent = logged ? state.user.name.split(' ')[0] : 'Guest';
    $('#user-chip').href = logged ? '#profile' : '#login';
    $('#user-chip .avatar').textContent = logged ? state.user.name.charAt(0).toUpperCase() : 'G';
  }

  function toast(message, type = 'ok', time = 2600) {
    const box = document.createElement('div');
    box.className = 'toast ' + (type === 'error' ? 'error' : '');
    box.innerHTML = `<span class="toast-mark">${type === 'error' ? '!' : '&#10003;'}</span><span>${esc(message)}</span>`;
    $('#toast-stack').append(box);
    setTimeout(() => {
      box.style.opacity = '0';
      box.style.transform = 'translateY(8px)';
      setTimeout(() => box.remove(), 250);
    }, time);
  }

  function skeletons(n = 6) {
    return `<div class="catalog-grid">${Array.from({ length: n }, () => '<div class="skeleton skeleton-card"></div>').join('')}</div>`;
  }

  function productImage(p) {
    const imgs = ['acid-wash-tee.png', 'layered-tee.png', 'ringer-tee.png', 'washed-hoodie.png'];
    return `<img class="product-photo" src="/static/products/${imgs[(p.id - 1) % 4]}" alt="${esc(p.name)}" loading="lazy">`;
  }

  function productCard(p, i) {
    const compare = Math.round(p.price * 1.8 / 100) * 100 - 1;
    const saving = Math.max(1, Math.round((1 - p.price / compare) * 100));
    return `<article class="product-card" style="--i:${i}">
      <div class="product-visual" data-product="${p.id}">
        ${productImage(p)}
        <span class="product-tag">${esc(p.category)}</span>
        <span class="sale-tag">-${saving}%</span>
        <button class="quick-view" type="button" aria-label="Quick view ${esc(p.name)}">Quick view</button>
      </div>
      <div class="product-info" data-product="${p.id}">
        <span class="product-category">${esc(p.category)}</span>
        <div class="product-title-row"><h3>${esc(p.name)}</h3></div>
        <div class="product-price-row"><b>${money(p.price)}</b><s>${money(compare)}</s></div>
        <div class="product-rating"><span class="rating-stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span><span class="rating-copy">4.7 (3)</span></div>
        <div class="stock-note">${p.stock > 0 ? 'In stock &middot; Ships in 2&ndash;4 days' : 'Currently unavailable'}</div>
      </div>
    </article>`;
  }

  // Opens product detail from already-fetched catalog data — no extra API call
  function openProduct(p) {
    const compare = Math.round(p.price * 1.8 / 100) * 100 - 1;
    const saving = Math.max(1, Math.round((1 - p.price / compare) * 100));
    modal(`
      <button class="icon-btn modal-close" id="modal-close">&times;</button>
      <div class="modal-visual">${productImage(p)}</div>
      <div class="modal-body">
        <div class="section-kicker">${esc(p.category)}</div>
        <h2>${esc(p.name)}</h2>
        <div class="modal-price">
          <b>${money(p.price)}</b><s>${money(compare)}</s>
          <span class="sale-tag">-${saving}%</span>
        </div>
        <p class="modal-description">${esc(p.description)}</p>
        <div class="modal-buy-row">
          <span class="stock-note">${p.stock > 0 ? 'In stock' : 'Currently unavailable'}</span>
          <button class="primary-btn" id="add-to-cart" ${p.stock < 1 ? 'disabled' : ''}>Add to bag</button>
        </div>
      </div>`);
    $('#add-to-cart').onclick = () => {
      state.cart = [{ product_id: p.id, quantity: 1 }];
      closeModal();
      if (!state.token) {
        toast('Sign in to place an order', 'error');
        location.hash = '#login';
      } else {
        createCartOrder();
      }
    };
  }

  function modal(html) {
    $('#modal-root').innerHTML = `<div class="modal-backdrop" id="modal-backdrop"><section class="modal">${html}</section></div>`;
    $('#modal-backdrop').onclick = e => { if (e.target.id === 'modal-backdrop') closeModal(); };
    $('#modal-close')?.addEventListener('click', closeModal);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); }, { once: true });
  }

  function closeModal() { $('#modal-root').innerHTML = ''; }

  function setNav(route) {
    $$('.main-nav a').forEach(a => a.classList.toggle('active', a.dataset.route === route));
  }

  // ── Products page (documented: GET /api/v1/products) ─────────────────────────
  async function fetchProducts() {
    const params = new URLSearchParams({ page: String(state.page), page_size: String(state.pageSize) });
    if (state.category) params.set('category', state.category);
    if (state.query.trim()) params.set('q', state.query.trim());
    const r = await api('/products?' + params, { auth: false });
    if (!r.ok) throw Error(r.data?.detail || 'Could not load products');
    state.products = r.data;
    return r.data;
  }

  async function renderProducts() {
    setNav('products');
    $('#main').innerHTML = `
      <section class="hero fashion-hero">
        <div class="hero-copy">
          <div class="hero-kicker">THE ATELIER STREET EDIT &middot; DROP 01</div>
          <h1>Wear your<br>own wave.</h1>
          <p>Oversized fits, washed textures, and original graphics made for everyday self-expression.</p>
          <button class="hero-cta" id="explore-drop" type="button">Explore the drop <span>&#8600;</span></button>
          <div class="hero-benefits"><span>Easy 7-day exchanges</span><i></i><span>Free shipping over &#8377;1,999</span></div>
        </div>
        <div class="hero-art">
          <div class="hero-orbit orbit-one"></div>
          <div class="hero-orbit orbit-two"></div>
          <span class="hero-drop-label">NEW DROP <b>01 / 18</b></span>
          <img src="/static/products/acid-wash-tee.png" alt="Charcoal oversized graphic tee from the new drop">
          <span class="hero-side-note">BUILT FOR<br>YOUR EVERYDAY</span>
        </div>
      </section>
      <section id="catalog" class="catalog-section">
        <div class="section-head">
          <div><div class="section-kicker">THE COLLECTION</div><h2 style="margin-top:6px">Find your next favorite</h2></div>
          <span class="subtle" id="result-count"></span>
        </div>
        <div class="catalog-toolbar">
          <label class="search-box"><span>&#8981;</span>
            <input id="search-input" placeholder="Search tees, fits, and graphics&hellip;" value="${esc(state.query)}">
          </label>
          <div class="category-chips" id="category-chips">
            ${['All','Oversized Tees','Acid Wash','Layered Tees','Ringer Tees','Long Sleeves','Hoodies','Vests','Half Sleeves']
              .map(c => `<button class="chip ${state.category === (c === 'All' ? '' : c) ? 'active' : ''}" data-category="${c === 'All' ? '' : c}">${c}</button>`)
              .join('')}
          </div>
        </div>
        <div id="catalog-state">${skeletons()}</div>
        <div id="pagination"></div>
      </section>`;

    $('#explore-drop').onclick = () => $('#catalog')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    $('#category-chips').onclick = e => {
      const b = e.target.closest('[data-category]');
      if (!b) return;
      state.category = b.dataset.category;
      state.page = 1;
      renderCatalog();
    };
    let timer;
    $('#search-input').oninput = e => {
      clearTimeout(timer);
      state.query = e.target.value;
      state.page = 1;
      timer = setTimeout(renderCatalog, 280);
    };
    renderCatalog();
  }

  async function renderCatalog() {
    const root = $('#catalog-state');
    if (!root) return;
    root.innerHTML = skeletons(6);
    const pagination = $('#pagination');
    if (pagination) pagination.innerHTML = '';
    try {
      await fetchProducts();
      if (!root.isConnected) return;
      $('#result-count').textContent = `${state.products.length} pieces`;
      root.innerHTML = state.products.length
        ? `<div class="catalog-grid">${state.products.map(productCard).join('')}</div>`
        : '<div class="empty-state"><strong>No pieces found</strong>Try a different search or category.</div>';
      $$('[data-product]', root).forEach(el => el.onclick = () => {
        const p = state.products.find(x => x.id === Number(el.dataset.product));
        if (p) openProduct(p);
      });
      if (!pagination) return;
      pagination.innerHTML = `<div class="pagination">
        <button id="prev-page" ${state.page === 1 ? 'disabled' : ''}>&#8592; Previous</button>
        <span>Page ${state.page}</span>
        <button id="next-page" ${state.products.length < state.pageSize ? 'disabled' : ''}>Next &#8594;</button>
      </div>`;
      $('#prev-page').onclick = () => { state.page--; renderCatalog(); };
      $('#next-page').onclick = () => { state.page++; renderCatalog(); };
    } catch (err) {
      if (!root.isConnected) return;
      root.innerHTML = `<div class="error-state"><strong>Catalog unavailable</strong>${esc(err.message)}<br>
        <button class="secondary-btn" id="retry-catalog">Try again</button></div>`;
      $('#retry-catalog').onclick = renderCatalog;
    }
  }

  // ── Login page (documented: POST /api/v1/auth/login + shadow: POST /api/v1/auth/signup) ──
  function renderLogin() {
    setNav('');
    $('#main').innerHTML = `
      <div class="login-wrap"><div class="login-card">
        <div class="section-kicker">WELCOME TO ATELIER</div>
        <h1 id="auth-heading">A better everyday.</h1>
        <p id="auth-copy">Sign in to manage orders, save your details and keep the good things close.</p>
        <div class="quick-logins">
          <button class="quick-login" data-email="alice@example.com">Alice Morgan</button>
          <button class="quick-login" data-email="bob@example.com">Bob Chen</button>
          <button class="quick-login" data-email="carol@example.com">Carol Singh</button>
        </div>
        <div class="divider">or use your account</div>
        <form id="auth-form">
          <div class="field" id="name-field" hidden>
            <label for="auth-name">Name</label>
            <input id="auth-name" minlength="2" placeholder="Your name">
          </div>
          <div class="field">
            <label for="auth-email">Email</label>
            <input id="auth-email" type="email" required placeholder="you@example.com">
          </div>
          <div class="field">
            <label for="auth-password">Password</label>
            <input id="auth-password" type="password" minlength="8" required placeholder="At least 8 characters">
          </div>
          <button class="primary-btn" id="auth-submit" style="width:100%;margin-top:5px">Sign in</button>
        </form>
        <div style="text-align:center;margin-top:17px">
          <button class="login-toggle" id="toggle-auth">New here? Create an account</button>
        </div>
        <div id="login-error"></div>
      </div></div>`;

    let signup = false;
    $('#toggle-auth').onclick = () => {
      signup = !signup;
      $('#name-field').hidden = !signup;
      $('#auth-heading').textContent = signup ? 'Make room for good things.' : 'A better everyday.';
      $('#auth-copy').textContent = signup
        ? 'Create an account and begin your collection.'
        : 'Sign in to manage orders, save your details and keep the good things close.';
      $('#auth-submit').textContent = signup ? 'Create account' : 'Sign in';
      $('#toggle-auth').textContent = signup ? 'Already have an account? Sign in' : 'New here? Create an account';
    };

    $$('.quick-login').forEach(b => b.onclick = async () => {
      const r = await api('/auth/login', { method: 'POST', body: { email: b.dataset.email, password: 'Password123!' }, auth: false });
      if (!r.ok) return loginError(r);
      acceptToken(r.data, b.dataset.email);
      toast(`Welcome back, ${b.textContent.split(' ')[0]}`);
      location.hash = '#products';
    });

    $('#auth-form').onsubmit = async e => {
      e.preventDefault();
      const body = { email: $('#auth-email').value, password: $('#auth-password').value };
      if (signup) {
        body.name = $('#auth-name').value;
        // shadow endpoint: POST /api/v1/auth/signup
        const r = await api('/auth/signup', { method: 'POST', body, auth: false });
        if (!r.ok) return loginError(r);
        toast('Account created. Sign in to continue.');
        signup = false;
        $('#toggle-auth').click();
        return;
      }
      const r = await api('/auth/login', { method: 'POST', body, auth: false });
      if (!r.ok) return loginError(r);
      acceptToken(r.data, body.email);
      toast('You are signed in');
      location.hash = '#products';
    };
  }

  function loginError(r) {
    $('#login-error').innerHTML = `<div class="error-state" style="padding:10px;margin-top:12px">${esc(r.data?.detail || 'Sign in failed')}</div>`;
  }

  function acceptToken(data, email = '') {
    state.token = data.access_token;
    localStorage.setItem('atelier_token', state.token);
    const account = (email || '').toLowerCase();
    const known = { 'alice@example.com': 'Alice Morgan', 'bob@example.com': 'Bob Chen', 'carol@example.com': 'Carol Singh' };
    const fallback = account.split('@')[0].replace(/[._-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    state.user = { name: known[account] || fallback || 'Customer', email: account };
    updateSession();
  }

  // ── Place order (documented: POST /api/v1/orders) ───────────────────────────
  async function createCartOrder() {
    if (!state.cart.length) return;
    if (!state.token) { location.hash = '#login'; return; }
    const r = await api('/orders', {
      method: 'POST',
      body: { items: state.cart, shipping_address: '12 Willow Lane, Portland, Oregon 97205' },
    });
    if (!r.ok) { toast(r.data?.detail || 'Order could not be placed', 'error'); return; }
    state.cart = [];
    toast('Order placed successfully');
    location.hash = '#orders';
  }

  // ── Orders page — no live API calls, just a static confirmation view ─────────
  function renderOrders() {
    setNav('orders');
    $('#main').innerHTML = `
      <div class="page-title">
        <div class="section-kicker">YOUR ATELIER</div>
        <h1>Orders</h1>
        <p>Your order has been placed. Check your confirmation below.</p>
      </div>
      <div id="orders-state">
        <div class="empty-state">
          <strong>Order history coming soon</strong>
          Place an order from the catalog and it will appear here.<br>
          <a class="primary-btn" style="display:inline-block;margin-top:15px" href="#products">Explore the collection</a>
        </div>
      </div>`;
  }

  // ── Profile page — no live API calls ─────────────────────────────────────────
  function renderProfile() {
    setNav('profile');
    if (!state.token) {
      $('#main').innerHTML = `
        <div class="page-title"><div class="section-kicker">YOUR DETAILS</div><h1>Profile</h1></div>
        <div class="empty-state"><strong>Sign in to view your profile</strong>
          <a class="primary-btn" style="display:inline-block;margin-top:15px" href="#login">Sign in</a>
        </div>`;
      return;
    }
    $('#main').innerHTML = `
      <div class="page-title"><div class="section-kicker">YOUR DETAILS</div><h1>Profile</h1></div>
      <div class="profile-layout">
        <section class="panel-card">
          <h2>Signed in as</h2>
          <p>${esc(state.user?.name || '')}</p>
          <p class="subtle">${esc(state.user?.email || '')}</p>
          <div style="border-top:1px solid var(--border);margin:18px 0 12px"></div>
          <button id="logout-button" class="secondary-btn">Sign out</button>
        </section>
      </div>`;
    $('#logout-button').onclick = () => {
      state.user = null;
      state.token = '';
      localStorage.removeItem('atelier_token');
      updateSession();
      toast('Signed out');
      location.hash = '#products';
    };
  }

  // ── API guide page ────────────────────────────────────────────────────────────
  function markdownToHtml(markdown) {
    const tick = String.fromCharCode(96);
    const inlinePattern = new RegExp(tick + '([^' + tick + ']+)' + tick, 'g');
    const inline = s => esc(s).replace(inlinePattern, '<code>$1</code>').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    const lines = markdown.split(/\r?\n/);
    let html = '', paragraph = [], list = '', code = [], table = [], inCode = false;
    const flushParagraph = () => { if (paragraph.length) { html += '<p>' + paragraph.map(inline).join(' ') + '</p>'; paragraph = []; } };
    const flushList = () => { if (list) { html += '</' + list + '>'; list = ''; } };
    const flushTable = () => {
      if (!table.length) return;
      const rows = table.map(row => row.split('|').slice(1, -1).map(c => c.trim())).filter(cells => cells.length && !cells.every(c => /^:?-{3,}:?$/.test(c)));
      if (rows.length) html += '<div class="api-table-wrap"><table><thead><tr>' + rows[0].map(c => '<th>' + inline(c) + '</th>').join('') + '</tr></thead><tbody>' + rows.slice(1).map(row => '<tr>' + row.map(c => '<td>' + inline(c) + '</td>').join('') + '</tr>').join('') + '</tbody></table></div>';
      table = [];
    };
    const flushBlocks = () => { flushParagraph(); flushList(); flushTable(); };
    for (const line of lines) {
      const trimmed = line.trim(), fence = tick.repeat(3);
      if (trimmed.startsWith(fence)) { if (inCode) { html += '<pre><code>' + esc(code.join('\n')) + '</code></pre>'; code = []; inCode = false; } else { flushBlocks(); inCode = true; } continue; }
      if (inCode) { code.push(line); continue; }
      if (trimmed.startsWith('|')) { flushParagraph(); flushList(); table.push(trimmed); continue; } else flushTable();
      if (!trimmed) { flushBlocks(); continue; }
      const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
      if (heading) { flushBlocks(); const lv = heading[1].length; html += '<h' + lv + '>' + inline(heading[2]) + '</h' + lv + '>'; continue; }
      const ordered = trimmed.match(/^\d+\.\s+(.+)$/), bullet = trimmed.match(/^[-*]\s+(.+)$/);
      if (ordered || bullet) { flushParagraph(); const next = ordered ? 'ol' : 'ul'; if (list && list !== next) flushList(); if (!list) { list = next; html += '<' + list + '>'; } html += '<li>' + inline((ordered || bullet)[1]) + '</li>'; continue; }
      paragraph.push(trimmed);
    }
    if (inCode) html += '<pre><code>' + esc(code.join('\n')) + '</code></pre>';
    flushBlocks();
    return html;
  }

  async function renderApiGuide() {
    setNav('api');
    $('#main').innerHTML = `<div class="developer-docs">
      <aside class="docs-sidebar">
        <div class="docs-sidebar-title">Atelier API</div>
        <label class="docs-search"><span>&#8981;</span><input id="docs-search" type="search" placeholder="Search the reference" aria-label="Search API reference"></label>
        <nav id="docs-nav" class="docs-nav" aria-label="API reference sections"><div class="loading-state">Loading sections&hellip;</div></nav>
      </aside>
      <section class="docs-content">
        <div class="docs-hero">
          <div class="section-kicker">DEVELOPER DOCUMENTATION</div>
          <h1>Store API reference</h1>
          <p>Build against the same endpoints that power the Atelier storefront.</p>
          <div class="api-guide-actions">
            <a class="primary-btn" href="/docs" target="_blank" rel="noreferrer">Open interactive API</a>
            <a class="secondary-btn" href="/redoc" target="_blank" rel="noreferrer">Open ReDoc</a>
          </div>
        </div>
        <article id="api-guide-content" class="api-doc"><div class="loading-state">Loading the API reference&hellip;</div></article>
        <footer class="docs-footer">Atelier Commerce API &middot; Local development reference</footer>
      </section>
      <aside class="docs-toc-wrap">
        <div class="docs-toc-label">ON THIS PAGE</div>
        <nav id="docs-toc" class="docs-toc" aria-label="On this page"></nav>
      </aside>
    </div>`;
    const root = $('#api-guide-content');
    try {
      const result = await fetch('/static/api-reference.md').then(r => r.text());
      if (root.isConnected) root.innerHTML = markdownToHtml(result);
    } catch (err) {
      if (root.isConnected) root.innerHTML = `<div class="error-state"><strong>API reference unavailable</strong>${esc(err.message)}</div>`;
    }
  }

  // ── Router ────────────────────────────────────────────────────────────────────
  function parseRoute() {
    const name = location.hash.slice(1).split('/')[0] || 'products';
    state.route = ['products', 'orders', 'profile', 'login', 'api'].includes(name) ? name : 'products';
  }

  function render() {
    parseRoute();
    if (state.route === 'products') return renderProducts();
    if (state.route === 'login')    return renderLogin();
    if (state.route === 'orders')   return renderOrders();
    if (state.route === 'profile')  return renderProfile();
    if (state.route === 'api')      return renderApiGuide();
  }

  window.addEventListener('hashchange', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    render();
  });

  updateSession();
  render();
})();
