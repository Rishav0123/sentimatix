// sidebar.js — Left navigation sidebar

const SIDEBAR_GROUPS = [
  {
    label: 'News Data',
    links: [
      { method: 'GET', path: '/api/v1/news', label: 'Get Financial News', id: 'news' },
    ]
  },
  {
    label: 'Reference Data',
    links: [
      { method: 'GET', path: '/api/v1/entities', label: 'List Stocks', id: 'entities' },
    ]
  },
  {
    label: 'Intelligence (Pro+)',
    links: [
      { method: 'GET', path: '/api/v1/sentiment', label: 'Stock Sentiment', id: 'sentiment' },
      { method: 'GET', path: '/api/v1/sentiment/sectors', label: 'Sector Sentiment', id: 'sector-sentiment' },
    ]
  }
];

function methodClass(method) {
  if (method === 'GET') return 'badge-get';
  if (method === 'POST') return 'badge-post';
  return 'badge-delete';
}

function renderSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  let html = '';
  for (const group of SIDEBAR_GROUPS) {
    html += `<div class="sidebar-group">
      <div class="sidebar-group-label">${group.label}</div>`;
    for (const link of group.links) {
      html += `<div class="sidebar-link" onclick="scrollToSection('${link.id}')" data-id="${link.id}">
        <span class="method-badge ${methodClass(link.method)}">${link.method}</span>
        <span>${link.label}</span>
      </div>`;
    }
    html += `</div>`;
  }
  sidebar.innerHTML = html;
}

function scrollToSection(id) {
  const el = document.getElementById('section-' + id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
  const active = document.querySelector(`.sidebar-link[data-id="${id}"]`);
  if (active) active.classList.add('active');
  if (typeof updatePanel === 'function') updatePanel(id);
}

// Highlight sidebar link on scroll
function setupScrollSpy() {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        const id = entry.target.id.replace('section-', '');
        document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
        const active = document.querySelector(`.sidebar-link[data-id="${id}"]`);
        if (active) active.classList.add('active');
      }
    }
  }, { rootMargin: '-20% 0px -70% 0px' });

  document.querySelectorAll('[id^="section-"]').forEach(el => observer.observe(el));
}

renderSidebar();
document.addEventListener('DOMContentLoaded', setupScrollSpy);
