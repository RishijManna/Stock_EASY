// Toggle left filter pane with Tab key (desktop convenience)
document.addEventListener('keydown', (e) => {
  if (e.key === 'Tab' && !e.shiftKey) {
    const pane = document.getElementById('filterPane');
    if (pane) { pane.classList.toggle('hidden'); }
  }
});

// Load details into right pane when a list item is clicked
function bindMedListLinks(scope) {
  (scope || document).querySelectorAll('#medList a[data-detail-url]').forEach(a => {
    a.addEventListener('click', async (ev) => {
      ev.preventDefault();
      const url = a.getAttribute('data-detail-url');
      await loadDetail(url);
    });
  });
}

async function loadDetail(url) {
  const pane = document.getElementById('detailPane');
  if (!pane) return;
  pane.innerHTML = '<div class="p-4 text-slate-500">Loading…</div>';
  const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
  pane.innerHTML = await resp.text();
}

async function refreshMedList() {
  const list = document.getElementById('medList');
  if (!list) return;
  const q = document.querySelector('input[name="q"]')?.value || '';
  const resp = await fetch(`/medlist/?q=${encodeURIComponent(q)}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
  list.innerHTML = await resp.text();
  bindMedListLinks(list); // re-bind new items
}

function bindDetailPaneActions() {
  const pane = document.getElementById('detailPane');
  if (!pane) return;

  // Load edit form
  pane.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-edit-url],[data-detail-url]');
    if (!btn) return;

    // open edit partial
    if (btn.hasAttribute('data-edit-url')) {
      e.preventDefault();
      const url = btn.getAttribute('data-edit-url');
      await loadDetail(url);
    }
    // go back to detail
    if (btn.hasAttribute('data-detail-url')) {
      e.preventDefault();
      const url = btn.getAttribute('data-detail-url');
      await loadDetail(url);
    }
  });

  // AJAX submit for forms inside pane (edit + delete)
  pane.addEventListener('submit', async (e) => {
    const form = e.target;
    if (!form.matches('form[data-ajax="true"]')) return;
    e.preventDefault();
    const resp = await fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const html = await resp.text();
    pane.innerHTML = html;
    await refreshMedList(); // update the left list after save/delete
  });
}

document.addEventListener('DOMContentLoaded', () => {
  bindMedListLinks(document);
  bindDetailPaneActions();
});
