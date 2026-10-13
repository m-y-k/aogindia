// AOG India Lead Dashboard & Sheet Inspector

let leadsData = [];
let catalogBrands = [];
let systemConfig = {};
let isPaused = true;

// On Page Load
document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();
});

// Load all data from API
async function loadDashboardData() {
  try {
    const res = await fetch('/api/data');
    if (!res.ok) throw new Error('Failed to load data');
    const data = await res.json();

    leadsData = data.leads || [];
    catalogBrands = data.catalog_brands || [];
    systemConfig = data.config || {};
    isPaused = !!(systemConfig.paused || (systemConfig.autopilot && systemConfig.autopilot.paused));

    updateSystemStatusUI();
    populateCategoryFilter();
    renderLeadsTable();
    updateKPICards();
    renderApolloCatalogChips();
  } catch (err) {
    showToast('Failed to load dashboard data: ' + err.message, 'error');
  }
}

// Update Pause / Resume status indicator
function updateSystemStatusUI() {
  const pill = document.getElementById('systemStatusPill');
  const text = document.getElementById('systemStatusText');
  const btnIcon = document.getElementById('btnTogglePauseIcon');
  const btnText = document.getElementById('btnTogglePauseText');
  const banner = document.getElementById('safetyBanner');
  const bannerReason = document.getElementById('safetyBannerReason');

  if (isPaused) {
    pill.className = 'pause-pill is-paused';
    text.textContent = 'OUTREACH PAUSED';
    btnIcon.textContent = '▶';
    btnText.textContent = 'Resume Outreach';
    banner.style.display = 'flex';
    bannerReason.textContent = systemConfig.pause_reason || 'Outreach paused by user request - reviewing contacts and templates. No emails will be sent.';
  } else {
    pill.className = 'pause-pill is-active';
    text.textContent = 'OUTREACH ACTIVE';
    btnIcon.textContent = '⏸';
    btnText.textContent = 'Pause Outreach';
    banner.style.display = 'none';
  }
}

// Toggle Pause State via API
async function toggleSystemPause() {
  const targetAction = isPaused ? 'resume' : 'pause';
  const confirmMsg = isPaused
    ? 'Are you sure you want to RESUME automated outreach? (Emails will be scheduled to send during business hours).'
    : 'Are you sure you want to PAUSE outreach? (All email sending will be locked immediately).';

  if (!confirm(confirmMsg)) return;

  try {
    const res = await fetch('/api/toggle-pause', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: targetAction })
    });
    const result = await res.json();
    if (result.success) {
      isPaused = result.paused;
      systemConfig.paused = result.paused;
      updateSystemStatusUI();
      showToast(result.message, 'success');
    } else {
      showToast(result.error || 'Failed to update pause state', 'error');
    }
  } catch (err) {
    showToast('Error toggling status: ' + err.message, 'error');
  }
}

// Populate Categories Dropdown
function populateCategoryFilter() {
  const select = document.getElementById('categoryFilter');
  const currentVal = select.value;
  const categories = new Set();
  leadsData.forEach(l => {
    if (l.category) categories.add(l.category);
  });
  catalogBrands.forEach(b => {
    if (b.cat) categories.add(b.cat);
  });

  select.innerHTML = '<option value="">All Categories</option>';
  Array.from(categories).sort().forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat;
    opt.textContent = cat;
    if (cat === currentVal) opt.selected = true;
    select.appendChild(opt);
  });
}

// Render Apollo Brands Quick-Picker
function renderApolloCatalogChips() {
  const container = document.getElementById('apolloBrandChips');
  container.innerHTML = '';
  catalogBrands.forEach(brand => {
    const chip = document.createElement('div');
    chip.className = 'brand-chip';
    chip.innerHTML = `<strong>${escapeHtml(brand.company)}</strong><span>${escapeHtml(brand.domain)} • ${escapeHtml(brand.cat)}</span>`;
    chip.onclick = () => {
      document.getElementById('apolloDomainInput').value = brand.domain;
      queryApolloLive();
    };
    container.appendChild(chip);
  });
}

// Render Main Leads Table
function renderLeadsTable() {
  const tbody = document.getElementById('leadsTableBody');
  const search = document.getElementById('searchInput').value.toLowerCase().trim();
  const categoryFilter = document.getElementById('categoryFilter').value;
  const statusFilter = document.getElementById('statusFilter').value.toLowerCase();

  const filtered = leadsData.filter((lead, idx) => {
    lead._originalIndex = idx;
    const matchSearch = !search ||
      (lead.company_name && lead.company_name.toLowerCase().includes(search)) ||
      (lead.contact_name && lead.contact_name.toLowerCase().includes(search)) ||
      (lead.email && lead.email.toLowerCase().includes(search)) ||
      (lead.designation && lead.designation.toLowerCase().includes(search));

    const matchCategory = !categoryFilter || lead.category === categoryFilter;
    const matchStatus = !statusFilter || (lead.status && lead.status.toLowerCase() === statusFilter);

    return matchSearch && matchCategory && matchStatus;
  });

  document.getElementById('visibleRowCount').textContent = filtered.length;
  tbody.innerHTML = '';

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 3rem; color: var(--text-dim);">
          No leads match your current filter. Try clearing your search or add a new prospect.
        </td>
      </tr>
    `;
    return;
  }

  filtered.forEach((lead, displayIdx) => {
    const tr = document.createElement('tr');

    const statusVal = (lead.status || 'paused').toLowerCase();
    const isVerified = (lead.verification_status || 'unverified').toLowerCase() === 'verified';

    tr.innerHTML = `
      <td style="color: var(--text-dim); font-size: 0.8rem;">${displayIdx + 1}</td>
      <td>
        <span class="company-name">${escapeHtml(lead.company_name || '—')}</span>
        <span class="badge badge-category" style="margin-top: 4px;">${escapeHtml(lead.category || 'Gaming')}</span>
      </td>
      <td>
        <span class="contact-name">${escapeHtml(lead.contact_name || 'Marketing Lead')}</span>
        <span class="contact-title">${escapeHtml(lead.designation || 'Marketing')}</span>
      </td>
      <td>
        <a href="mailto:${escapeHtml(lead.email)}" class="email-link">${escapeHtml(lead.email || '—')}</a>
        <div style="margin-top: 4px;">
          <span class="badge ${isVerified ? 'badge-verified' : 'badge-unverified'}">
            ${isVerified ? '✔ Verified' : '❓ Pattern / Unverified'}
          </span>
        </div>
      </td>
      <td>
        <span class="badge badge-category">${escapeHtml(lead.category || 'General')}</span>
      </td>
      <td>
        <div class="compliment-text" title="${escapeHtml(lead.custom_compliment || '')}">
          ${escapeHtml(lead.custom_compliment || '—')}
        </div>
      </td>
      <td>
        <select class="select-filter" style="padding: 0.3rem 0.5rem; font-size: 0.775rem;" onchange="updateLeadStatus(${lead._originalIndex}, this.value)">
          <option value="paused" ${statusVal === 'paused' ? 'selected' : ''}>⏸ Paused</option>
          <option value="pending" ${statusVal === 'pending' ? 'selected' : ''}>⏳ Pending</option>
          <option value="sent" ${statusVal === 'sent' ? 'selected' : ''}>✔ Sent</option>
          <option value="skip" ${statusVal === 'skip' ? 'selected' : ''}>✕ Skip</option>
        </select>
      </td>
      <td style="text-align: right;">
        <div style="display: inline-flex; gap: 0.35rem;">
          <button class="btn btn-secondary btn-sm" onclick="previewEmailPitch(${lead._originalIndex})" title="Preview exact email pitch">
            👁️
          </button>
          <button class="btn btn-secondary btn-sm" onclick="openEditLeadModal(${lead._originalIndex})" title="Edit details">
            ✏️
          </button>
          <button class="btn btn-danger btn-sm" onclick="deleteLead(${lead._originalIndex})" title="Remove from sheet">
            🗑️
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Update KPI Stats
function updateKPICards() {
  document.getElementById('kpiTotalLeads').textContent = leadsData.length;
  const paused = leadsData.filter(l => (l.status || '').toLowerCase() === 'paused').length;
  document.getElementById('kpiPausedLeads').textContent = paused;
  const verified = leadsData.filter(l => (l.verification_status || '').toLowerCase() === 'verified').length;
  document.getElementById('kpiVerifiedLeads').textContent = verified;
  document.getElementById('kpiTotalBrands').textContent = catalogBrands.length ? `${catalogBrands.length}+` : '50+';
}

// Handle Search and Filter
function handleSearchFilter() {
  renderLeadsTable();
}

// Update In-Memory Lead Status
function updateLeadStatus(index, newStatus) {
  if (leadsData[index]) {
    leadsData[index].status = newStatus;
    updateKPICards();
    showToast(`Updated status to '${newStatus}'. Click 'Save Changes' to persist to CSV.`, 'info');
  }
}

// Preview Pitch Modal
async function previewEmailPitch(index) {
  const lead = leadsData[index];
  if (!lead) return;

  document.getElementById('previewModalTitle').textContent = `Email Pitch Preview — ${lead.company_name}`;
  document.getElementById('previewToEmail').textContent = `${lead.contact_name} <${lead.email}>`;

  try {
    const res = await fetch(`/api/preview-email?idx=${index}`);
    const data = await res.json();
    document.getElementById('previewSubject').textContent = data.subject || 'Sponsorship Inquiries';
    document.getElementById('previewTabHtml').innerHTML = data.html || '<p>Preview unavailable</p>';
    document.getElementById('previewTabText').textContent = data.plain || 'Preview unavailable';

    switchPreviewTab('html');
    openModal('previewModal');
  } catch (err) {
    showToast('Failed to generate preview: ' + err.message, 'error');
  }
}

function switchPreviewTab(tab) {
  const htmlBox = document.getElementById('previewTabHtml');
  const textBox = document.getElementById('previewTabText');
  const tabs = document.querySelectorAll('.tab-btn');

  if (tab === 'html') {
    htmlBox.style.display = 'block';
    textBox.style.display = 'none';
    tabs[0].classList.add('is-active');
    tabs[1].classList.remove('is-active');
  } else {
    htmlBox.style.display = 'none';
    textBox.style.display = 'block';
    tabs[0].classList.remove('is-active');
    tabs[1].classList.add('is-active');
  }
}

// Add / Edit Lead Modal Handlers
function openAddLeadModal() {
  document.getElementById('editLeadIndex').value = '-1';
  document.getElementById('leadModalTitle').textContent = 'Add New Sponsor Prospect';
  document.getElementById('leadCompany').value = '';
  document.getElementById('leadContact').value = '';
  document.getElementById('leadTitle').value = '';
  document.getElementById('leadEmail').value = '';
  document.getElementById('leadCategory').value = 'Gaming Hardware';
  document.getElementById('leadCompliment').value = '';
  document.getElementById('leadStatus').value = 'paused';
  document.getElementById('leadVerification').value = 'unverified';
  openModal('leadModal');
}

function openEditLeadModal(index) {
  const lead = leadsData[index];
  if (!lead) return;

  document.getElementById('editLeadIndex').value = index;
  document.getElementById('leadModalTitle').textContent = `Edit Lead: ${lead.company_name}`;
  document.getElementById('leadCompany').value = lead.company_name || '';
  document.getElementById('leadContact').value = lead.contact_name || '';
  document.getElementById('leadTitle').value = lead.designation || '';
  document.getElementById('leadEmail').value = lead.email || '';
  document.getElementById('leadCategory').value = lead.category || '';
  document.getElementById('leadCompliment').value = lead.custom_compliment || '';
  document.getElementById('leadStatus').value = (lead.status || 'paused').toLowerCase();
  document.getElementById('leadVerification').value = (lead.verification_status || 'unverified').toLowerCase();
  openModal('leadModal');
}

function saveLeadFromModal() {
  const idx = parseInt(document.getElementById('editLeadIndex').value, 10);
  const company = document.getElementById('leadCompany').value.trim();
  const contact = document.getElementById('leadContact').value.trim();
  const title = document.getElementById('leadTitle').value.trim();
  const email = document.getElementById('leadEmail').value.trim();
  const category = document.getElementById('leadCategory').value.trim();
  const compliment = document.getElementById('leadCompliment').value.trim();
  const status = document.getElementById('leadStatus').value;
  const verification = document.getElementById('leadVerification').value;

  if (!company || !email) {
    alert('Please enter both Company Name and Email.');
    return;
  }

  const leadObj = {
    company_name: company,
    contact_name: contact,
    designation: title,
    email: email,
    category: category,
    custom_compliment: compliment,
    deck_angle: 'title_sponsor',
    verification_status: verification,
    status: status,
    sent_at: idx >= 0 ? (leadsData[idx].sent_at || '') : '',
    notes: idx >= 0 ? (leadsData[idx].notes || 'Updated via Dashboard') : 'Added manually via Dashboard'
  };

  if (idx >= 0) {
    leadsData[idx] = leadObj;
    showToast(`Updated '${company}' lead. Remember to save to CSV!`, 'success');
  } else {
    leadsData.unshift(leadObj);
    showToast(`Added '${company}' to sheet. Remember to save to CSV!`, 'success');
  }

  closeModal('leadModal');
  populateCategoryFilter();
  renderLeadsTable();
  updateKPICards();
}

// Delete Lead Handler
function deleteLead(index) {
  const lead = leadsData[index];
  if (!lead) return;

  if (confirm(`Are you sure you want to remove ${lead.contact_name} (${lead.company_name}) from the sheet?`)) {
    leadsData.splice(index, 1);
    renderLeadsTable();
    updateKPICards();
    showToast(`Removed contact. Click 'Save Changes' to update CSV.`, 'info');
  }
}

// Save All In-Memory Changes to Server & CSV
async function saveAllChangesToServer() {
  const btn = document.getElementById('btnSaveLeads');
  const originalText = btn.innerHTML;
  btn.innerHTML = '⏳ Saving...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/leads/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ leads: leadsData })
    });
    const result = await res.json();
    if (result.success) {
      showToast(`Successfully saved ${leadsData.length} leads to leads_template.csv!`, 'success');
    } else {
      showToast(result.error || 'Failed to save leads', 'error');
    }
  } catch (err) {
    showToast('Save error: ' + err.message, 'error');
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

// Copy to Google Sheets (TSV format)
function copyForGoogleSheets() {
  const headers = ['company_name', 'contact_name', 'designation', 'email', 'category', 'custom_compliment', 'deck_angle', 'verification_status', 'status', 'sent_at', 'notes'];
  const rows = [headers.join('\t')];

  leadsData.forEach(lead => {
    const row = headers.map(h => (lead[h] || '').replace(/[\t\n\r]/g, ' '));
    rows.push(row.join('\t'));
  });

  const tsvText = rows.join('\n');
  navigator.clipboard.writeText(tsvText).then(() => {
    showToast('Copied to Clipboard! You can now open Google Sheets and press Ctrl+V to paste.', 'success');
  }).catch(err => {
    showToast('Clipboard error: ' + err.message, 'error');
  });
}

// Export CSV
function exportCSV() {
  const headers = ['company_name', 'contact_name', 'designation', 'email', 'category', 'custom_compliment', 'deck_angle', 'verification_status', 'status', 'sent_at', 'notes'];
  const csvRows = [headers.join(',')];

  leadsData.forEach(lead => {
    const row = headers.map(h => {
      let val = (lead[h] || '').replace(/"/g, '""');
      return `"${val}"`;
    });
    csvRows.push(row.join(','));
  });

  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `aog_india_sponsor_leads_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Live Apollo Search / Inspection
function openApolloModal() {
  document.getElementById('apolloResultsSection').style.display = 'none';
  openModal('apolloModal');
}

async function queryApolloLive() {
  const domain = document.getElementById('apolloDomainInput').value.trim();
  if (!domain) {
    alert('Please enter a company domain (e.g. asus.com or redbull.com)');
    return;
  }

  const loader = document.getElementById('apolloLoading');
  const resultsSec = document.getElementById('apolloResultsSection');
  const resultsBody = document.getElementById('apolloResultsBody');
  const resultsCount = document.getElementById('apolloResultsCount');

  loader.style.display = 'block';
  resultsSec.style.display = 'none';

  try {
    const res = await fetch('/api/apollo/fetch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain: domain })
    });
    const data = await res.json();
    loader.style.display = 'none';

    if (!data.success) {
      showToast(data.error || 'Apollo fetch failed', 'error');
      return;
    }

    const contacts = data.leads || [];
    resultsCount.textContent = contacts.length;
    resultsBody.innerHTML = '';

    if (contacts.length === 0) {
      resultsBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-dim);">No marketing decision-makers returned by Apollo for ${domain}.</td></tr>`;
    } else {
      contacts.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${escapeHtml(c.contact_name)}</strong></td>
          <td style="color: var(--text-muted); font-size: 0.825rem;">${escapeHtml(c.designation || c.title || 'Marketing')}</td>
          <td><code style="color: var(--accent-blue);">${escapeHtml(c.email)}</code></td>
          <td>
            <button class="btn btn-primary btn-sm" onclick='addDiscoveredLeadToSheet(${JSON.stringify(c)})'>
              ➕ Add to Sheet
            </button>
          </td>
        `;
        resultsBody.appendChild(tr);
      });
    }

    resultsSec.style.display = 'block';
  } catch (err) {
    loader.style.display = 'none';
    showToast('Apollo query error: ' + err.message, 'error');
  }
}

// Add an Apollo Discovered Lead to Sheet
function addDiscoveredLeadToSheet(lead) {
  // Always set new discovered leads as paused so they are safe
  const newLead = {
    company_name: lead.company_name,
    contact_name: lead.contact_name,
    designation: lead.designation || lead.title || 'Marketing',
    email: lead.email,
    category: lead.category || 'Gaming Hardware',
    custom_compliment: lead.custom_compliment || '',
    deck_angle: 'title_sponsor',
    verification_status: lead.verification_status || 'verified',
    status: 'paused',
    sent_at: '',
    notes: 'Discovered via live Apollo API'
  };

  leadsData.unshift(newLead);
  renderLeadsTable();
  updateKPICards();
  populateCategoryFilter();
  showToast(`Added ${newLead.contact_name} (${newLead.company_name}) to sheet as PAUSED.`, 'success');
}

// Modal Helpers
function openModal(id) {
  document.getElementById(id).classList.add('is-open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('is-open');
}

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast';
  const icon = type === 'success' ? '✔' : type === 'error' ? '❌' : 'ℹ';
  toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// Escape HTML utility
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
