document.addEventListener('DOMContentLoaded', () => {
  // State
  let currentJobs = [];
  let currentScrapedCsv = '';
  let appSettings = {};

  // DOM Elements
  const form = document.getElementById('jobScraperForm');
  const keywordInput = document.getElementById('keywordInput');
  const locationInput = document.getElementById('locationInput');
  const maxResultsInput = document.getElementById('maxResultsInput');
  const autoSyncToggle = document.getElementById('autoSyncToggle');
  const scrapeBtn = document.getElementById('scrapeBtn');
  const resetFormBtn = document.getElementById('resetFormBtn');
  const selectAllSourcesBtn = document.getElementById('selectAllSources');
  const clearAllSourcesBtn = document.getElementById('clearAllSources');
  
  const progressCard = document.getElementById('progressCard');
  const downloadCsvBtn = document.getElementById('downloadCsvBtn');
  const syncSheetsBtn = document.getElementById('syncSheetsBtn');
  
  const statTotalJobs = document.getElementById('statTotalJobs');
  const statTodayJobs = document.getElementById('statTodayJobs');
  const statSourcesCount = document.getElementById('statSourcesCount');
  const statSheetTab = document.getElementById('statSheetTab');
  const statSheetSub = document.getElementById('statSheetSub');
  
  const tableFilterInput = document.getElementById('tableFilterInput');
  const sourceFilterSelect = document.getElementById('sourceFilterSelect');
  const sortSelect = document.getElementById('sortSelect');
  const jobsTableBody = document.getElementById('jobsTableBody');
  const resultsSubtext = document.getElementById('resultsSubtext');
  
  // Modals
  const settingsModal = document.getElementById('settingsModal');
  const openSettingsBtn = document.getElementById('openSettingsBtn');
  const closeSettingsBtn = document.getElementById('closeSettingsBtn');
  const cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
  const saveSettingsBtn = document.getElementById('saveSettingsBtn');
  const testWebhookBtn = document.getElementById('testWebhookBtn');
  const copyAppsScriptBtn = document.getElementById('copyAppsScriptBtn');
  const appsScriptCodeDisplay = document.getElementById('appsScriptCodeDisplay');
  const webhookUrlInput = document.getElementById('webhookUrlInput');
  const spreadsheetIdInput = document.getElementById('spreadsheetIdInput');
  const tabPrefixInput = document.getElementById('tabPrefixInput');
  const serviceAccountFileInput = document.getElementById('serviceAccountFileInput');
  const saStatusBadge = document.getElementById('saStatusBadge');

  const historyModal = document.getElementById('historyModal');
  const openHistoryBtn = document.getElementById('openHistoryBtn');
  const closeHistoryBtn = document.getElementById('closeHistoryBtn');
  const historyModalContent = document.getElementById('historyModalContent');

  const detailsModal = document.getElementById('detailsModal');
  const closeDetailsBtn = document.getElementById('closeDetailsBtn');
  const modalJobTitle = document.getElementById('modalJobTitle');
  const modalJobContent = document.getElementById('modalJobContent');

  const toastContainer = document.getElementById('toastContainer');
  const currentDateDisplay = document.getElementById('currentDateDisplay');

  // Initialize Date & Live Pill
  function updateDateDisplay() {
    const now = new Date();
    const isoDate = now.toISOString().split('T')[0];
    const options = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
    currentDateDisplay.textContent = `📅 ${isoDate} (${now.toLocaleDateString('en-US', options)})`;
  }
  updateDateDisplay();

  // Load Settings
  async function loadSettings() {
    try {
      const res = await fetch('/api/settings');
      if (res.ok) {
        appSettings = await res.json();
        webhookUrlInput.value = appSettings.apps_script_url || '';
        spreadsheetIdInput.value = appSettings.spreadsheet_id || '';
        tabPrefixInput.value = appSettings.tab_name_prefix || 'Jobs_';
        autoSyncToggle.checked = appSettings.google_sync_enabled || false;

        if (appSettings.service_account_exists) {
          saStatusBadge.textContent = 'Status: ✅ service_account.json installed';
          saStatusBadge.style.color = '#34d399';
        } else {
          saStatusBadge.textContent = 'Status: ⚠️ No service_account.json found';
          saStatusBadge.style.color = '#94a3b8';
        }

        // Update sheet stat status
        if (appSettings.apps_script_url || appSettings.service_account_exists) {
          statSheetTab.textContent = 'Connected';
          statSheetTab.style.color = '#34d399';
          statSheetSub.textContent = `Tab prefix: ${appSettings.tab_name_prefix || 'Jobs_'}`;
        } else {
          statSheetTab.textContent = 'Setup Needed';
          statSheetTab.style.color = '#f59e0b';
          statSheetSub.textContent = 'Click "Google Sheet Setup"';
        }
      }
    } catch (e) {
      console.error('Failed to load settings:', e);
    }
  }
  loadSettings();

  // Load Apps Script Code
  async function loadAppsScriptCode() {
    try {
      const res = await fetch('/api/sheets/script-code');
      if (res.ok) {
        const data = await res.json();
        appsScriptCodeDisplay.textContent = data.script_code;
      }
    } catch (e) {
      appsScriptCodeDisplay.textContent = '// Failed to load Apps Script template';
    }
  }
  loadAppsScriptCode();

  // Toast Helper
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // Dynamic Deep Search Links Generator (Google, Social, LinkedIn)
  function updateDeepSearchLinks() {
    const kw = keywordInput.value.trim() || 'Software Engineer';
    const loc = locationInput.value === 'Any' ? 'Remote' : locationInput.value;
    
    const googleAts = document.getElementById('deepSearchGoogleAts');
    if (googleAts) {
      googleAts.href = `https://www.google.com/search?q=site:greenhouse.io+OR+site:lever.co+OR+site:jobs.ashbyhq.com+${encodeURIComponent('"' + kw + '"')}`;
    }

    const googleJobs = document.getElementById('deepSearchGoogleJobs');
    if (googleJobs) {
      googleJobs.href = `https://www.google.com/search?q=jobs+${encodeURIComponent(kw + ' ' + loc)}&ibp=htl;jobs`;
    }

    const linkedIn = document.getElementById('deepSearchLinkedIn');
    if (linkedIn) {
      linkedIn.href = `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(kw)}&location=${encodeURIComponent(loc)}&f_TPR=r86400`;
    }

    const twitter = document.getElementById('deepSearchTwitter');
    if (twitter) {
      twitter.href = `https://x.com/search?q=${encodeURIComponent('"' + kw + '" ("we are hiring" OR "hiring" OR "job opening")')}&f=live`;
    }

    const reddit = document.getElementById('deepSearchReddit');
    if (reddit) {
      reddit.href = `https://www.reddit.com/r/forhire+remotejobs/search/?q=${encodeURIComponent(kw)}&sort=new`;
    }

    const wellfound = document.getElementById('deepSearchWellfound');
    if (wellfound) {
      wellfound.href = `https://wellfound.com/jobs?query=${encodeURIComponent(kw)}`;
    }
  }

  keywordInput.addEventListener('input', updateDeepSearchLinks);
  locationInput.addEventListener('change', updateDeepSearchLinks);
  updateDeepSearchLinks();

  // Quick suggestion pills
  document.querySelectorAll('.pill-btn[data-kw]').forEach(pill => {
    pill.addEventListener('click', () => {
      keywordInput.value = pill.getAttribute('data-kw');
      updateDeepSearchLinks();
      keywordInput.focus();
    });
  });

  // Scope Category Pills (Where to Search)
  document.querySelectorAll('.scope-btn[data-scope]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.scope-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const scope = btn.getAttribute('data-scope');

      const allCbs = document.querySelectorAll('input[name="sources"]');
      if (scope === 'all') {
        allCbs.forEach(cb => cb.checked = true);
      } else if (scope === 'professional') {
        allCbs.forEach(cb => {
          cb.checked = (cb.value === 'LinkedIn');
        });
      } else if (scope === 'social') {
        allCbs.forEach(cb => {
          cb.checked = (cb.value === 'Reddit' || cb.value === 'HackerNews');
        });
      } else if (scope === 'jobboards') {
        allCbs.forEach(cb => {
          cb.checked = ['RemoteOK', 'WeWorkRemotely', 'Jobicy', 'Arbeitnow', 'Remotive'].includes(cb.value);
        });
      }
    });
  });

  // Source selection helpers
  if (selectAllSourcesBtn) {
    selectAllSourcesBtn.addEventListener('click', () => {
      document.querySelectorAll('input[name="sources"]').forEach(cb => cb.checked = true);
    });
  }

  if (clearAllSourcesBtn) {
    clearAllSourcesBtn.addEventListener('click', () => {
      document.querySelectorAll('input[name="sources"]').forEach(cb => cb.checked = false);
    });
  }

  // Reset form
  resetFormBtn.addEventListener('click', () => {
    form.reset();
    document.querySelectorAll('input[name="sources"]').forEach(cb => cb.checked = true);
    document.getElementById('dateAll').checked = true;
    document.querySelectorAll('.scope-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('.scope-btn[data-scope="all"]')?.classList.add('active');
    updateDeepSearchLinks();
  });

  // Form Submit / Scrape Handler
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const selectedSources = Array.from(document.querySelectorAll('input[name="sources"]:checked')).map(cb => cb.value);
    if (selectedSources.length === 0) {
      showToast('Please select at least one scrape source portal!', 'error');
      return;
    }

    const dateFilter = document.querySelector('input[name="dateFilter"]:checked')?.value || 'all';
    const keyword = keywordInput.value.trim();
    const location = locationInput.value;
    const maxResults = parseInt(maxResultsInput.value, 10) || 50;
    const autoSync = autoSyncToggle.checked;

    // UI in progress state
    scrapeBtn.disabled = true;
    scrapeBtn.innerHTML = `<div class="spinner" style="width:16px;height:16px;"></div> Scraping Portals...`;
    progressCard.style.display = 'block';

    // Reset source chip statuses
    document.querySelectorAll('.source-chip').forEach(chip => {
      chip.className = 'source-chip fetching';
      chip.textContent = `${chip.id.replace('chip', '')}: Scraping...`;
    });

    try {
      const response = await fetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyword: keyword,
          location: location,
          category: 'all',
          sources: selectedSources,
          date_filter: dateFilter,
          max_results: maxResults,
          auto_sync_sheets: autoSync
        })
      });

      const res = await response.json();
      if (!response.ok) {
        throw new Error(res.detail || 'Scraping failed');
      }

      const data = res.data;
      currentJobs = data.jobs || [];
      currentScrapedCsv = res.csv_filename || '';

      // Update counters
      statTotalJobs.textContent = data.total_found;
      statTodayJobs.textContent = data.today_jobs_count;
      statSourcesCount.textContent = data.sources_queried.length;

      // Update source chips
        const chipMap = {
          'LinkedIn': 'chipLinkedIn',
          'Reddit': 'chipReddit',
          'HackerNews': 'chipHN',
          'RemoteOK': 'chipRemoteOK',
          'WeWorkRemotely': 'chipWWR',
          'Jobicy': 'chipJobicy',
          'Arbeitnow': 'chipArbeitnow',
          'Remotive': 'chipRemotive'
        };
        for (const [src, count] of Object.entries(data.source_counts)) {
          const chipId = chipMap[src];
          const chip = chipId ? document.getElementById(chipId) : null;
          if (chip) {
            chip.className = 'source-chip done';
            chip.textContent = `${src}: ${count} jobs`;
          }
        }

      // Check Google Sheet sync status
      if (res.sheets_sync) {
        if (res.sheets_sync.success) {
          const tabName = res.sheets_sync.tab_name || 'Today';
          statSheetTab.textContent = `Synced: ${tabName}`;
          statSheetTab.style.color = '#34d399';
          statSheetSub.textContent = `Auto date-tab updated (${res.sheets_sync.rows_added || currentJobs.length} rows)`;
          showToast(`Successfully synced to Google Sheet tab: ${tabName}!`, 'success');
        } else {
          showToast(`Google Sheet Sync error: ${res.sheets_sync.error}`, 'error');
        }
      }

      // Render table
      renderJobsTable(currentJobs);

      // Enable export buttons
      downloadCsvBtn.disabled = currentJobs.length === 0;
      syncSheetsBtn.disabled = currentJobs.length === 0;

      resultsSubtext.textContent = `Found ${currentJobs.length} jobs for "${keyword || 'All Roles'}" (${data.today_jobs_count} posted today)`;
      showToast(`Scrape completed! ${currentJobs.length} verified jobs found.`, 'success');

    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      scrapeBtn.disabled = false;
      scrapeBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
        </svg>
        Scrape Latest Jobs
      `;
      setTimeout(() => {
        progressCard.style.display = 'none';
      }, 3000);
    }
  });

  // Render Table Function
  function renderJobsTable(jobsToRender) {
    if (!jobsToRender || jobsToRender.length === 0) {
      jobsTableBody.innerHTML = `
        <tr>
          <td colspan="9">
            <div class="empty-state">
              <div class="empty-icon">🔍</div>
              <h3>No matching jobs found</h3>
              <p>Try broadening your keywords or selecting additional source portals.</p>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    jobsTableBody.innerHTML = jobsToRender.map(job => {
      const companyInitial = (job.company || 'J').charAt(0).toUpperCase();
      
      // Date badge logic
      let dateBadgeClass = 'badge-older';
      if (job.date_relative === 'Today' || job.date_relative.includes('Today')) {
        dateBadgeClass = 'badge-today';
      } else if (job.date_relative === 'Yesterday' || job.date_relative.includes('1d') || job.date_relative.includes('2d')) {
        dateBadgeClass = 'badge-recent';
      }

      // Tags display
      const tagsList = (job.tags || []).slice(0, 3).map(t => `<span class="tag-pill">${escapeHtml(t)}</span>`).join('');

      return `
        <tr>
          <td>
            <div class="company-cell">
              <div class="company-avatar">${companyInitial}</div>
              <span class="company-name">${escapeHtml(job.company)}</span>
            </div>
          </td>
          <td>
            <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer" class="job-title-link">
              ${escapeHtml(job.title)}
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </td>
          <td><span style="font-size:0.8rem; color:#cbd5e1;">${escapeHtml(job.location)}</span></td>
          <td>
            <span class="badge ${dateBadgeClass}">
              ${escapeHtml(job.date_posted)} <small>(${escapeHtml(job.date_relative)})</small>
            </span>
          </td>
          <td><span style="font-size:0.78rem; color:#94a3b8;">${escapeHtml(job.job_type)}</span></td>
          <td><span class="salary-tag">${escapeHtml(job.salary)}</span></td>
          <td><span class="badge badge-source ${escapeHtml(job.source)}">${escapeHtml(job.source)}</span></td>
          <td><div class="table-tags">${tagsList}</div></td>
          <td>
            <div class="action-btns-cell">
              <button class="btn-icon-sm view-details-btn" data-job-id="${escapeHtml(job.id)}" title="View Description & Details">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
              </button>
              <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer" class="btn-icon-sm" title="Apply on Original Site">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
              </a>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    // Attach event listeners to Details buttons
    document.querySelectorAll('.view-details-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const jId = btn.getAttribute('data-job-id');
        const selected = currentJobs.find(x => x.id === jId);
        if (selected) {
          openJobDetails(selected);
        }
      });
    });
  }

  // Filter & Sort Pipeline
  function applyTableFilters() {
    let filtered = [...currentJobs];
    const searchTerm = tableFilterInput.value.toLowerCase().trim();
    const sourceFilter = sourceFilterSelect.value;
    const sortBy = sortSelect.value;

    if (sourceFilter !== 'ALL') {
      filtered = filtered.filter(j => j.source === sourceFilter);
    }

    if (searchTerm) {
      filtered = filtered.filter(j => {
        const text = `${j.title} ${j.company} ${j.location} ${j.salary} ${(j.tags || []).join(' ')}`.toLowerCase();
        return text.includes(searchTerm);
      });
    }

    // Sort
    if (sortBy === 'date_desc') {
      filtered.sort((a, b) => new Date(b.date_posted) - new Date(a.date_posted));
    } else if (sortBy === 'date_asc') {
      filtered.sort((a, b) => new Date(a.date_posted) - new Date(b.date_posted));
    } else if (sortBy === 'company') {
      filtered.sort((a, b) => a.company.localeCompare(b.company));
    } else if (sortBy === 'title') {
      filtered.sort((a, b) => a.title.localeCompare(b.title));
    }

    renderJobsTable(filtered);
  }

  tableFilterInput.addEventListener('input', applyTableFilters);
  sourceFilterSelect.addEventListener('change', applyTableFilters);
  sortSelect.addEventListener('change', applyTableFilters);

  // Download CSV Action
  downloadCsvBtn.addEventListener('click', async () => {
    if (currentJobs.length === 0) return;

    if (currentScrapedCsv) {
      window.location.href = `/api/download/${currentScrapedCsv}`;
      showToast(`Downloading ${currentScrapedCsv}...`, 'info');
      return;
    }

    // Direct stream export
    try {
      const res = await fetch('/api/export/csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jobs: currentJobs,
          keyword: keywordInput.value.trim() || 'jobs'
        })
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Jobs_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast('CSV downloaded successfully!', 'success');
      }
    } catch (e) {
      showToast('Error exporting CSV: ' + e.message, 'error');
    }
  });

  // Manual Google Sheets Sync Action
  syncSheetsBtn.addEventListener('click', async () => {
    if (currentJobs.length === 0) return;

    syncSheetsBtn.disabled = true;
    syncSheetsBtn.innerHTML = `<div class="spinner" style="width:14px;height:14px;"></div> Syncing Date Tab...`;

    try {
      const res = await fetch('/api/sheets/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jobs: currentJobs
        })
      });
      const data = await res.json();
      if (data.success) {
        const tabName = data.tab_name || 'Date Tab';
        statSheetTab.textContent = `Synced: ${tabName}`;
        statSheetTab.style.color = '#34d399';
        showToast(`Uploaded ${data.rows_added || currentJobs.length} jobs to sheet tab: ${tabName}!`, 'success');
      } else {
        showToast(data.error || 'Failed to sync. Please check Settings.', 'error');
      }
    } catch (e) {
      showToast('Sync error: ' + e.message, 'error');
    } finally {
      syncSheetsBtn.disabled = false;
      syncSheetsBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="3" y1="9" x2="21" y2="9"></line>
          <line x1="9" y1="21" x2="9" y2="9"></line>
        </svg>
        Sync to Google Sheet
      `;
    }
  });

  // Open Details Modal
  function openJobDetails(job) {
    modalJobTitle.textContent = job.title;
    const tagsHtml = (job.tags || []).map(t => `<span class="tag-pill" style="font-size:0.8rem; padding:0.25rem 0.6rem;">${escapeHtml(t)}</span>`).join('');
    
    modalJobContent.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
        <div>
          <h4 style="font-size:1.1rem; color:#f8fafc;">${escapeHtml(job.company)}</h4>
          <span style="color:#94a3b8; font-size:0.85rem;">📍 ${escapeHtml(job.location)} &bull; ${escapeHtml(job.job_type)}</span>
        </div>
        <div>
          <span class="badge badge-source ${escapeHtml(job.source)}" style="font-size:0.8rem;">${escapeHtml(job.source)}</span>
        </div>
      </div>

      <div style="background:rgba(30,41,59,0.5); padding:0.85rem; border-radius:10px; margin-bottom:1rem; display:flex; justify-content:space-between;">
        <div>
          <small style="color:#64748b; display:block;">Posted Date</small>
          <strong style="color:#38bdf8;">${escapeHtml(job.date_posted)} (${escapeHtml(job.date_relative)})</strong>
        </div>
        <div>
          <small style="color:#64748b; display:block;">Salary / Compensation</small>
          <strong style="color:#34d399;">${escapeHtml(job.salary)}</strong>
        </div>
      </div>

      <div style="margin-bottom:1rem;">
        <label style="font-size:0.78rem; text-transform:uppercase; color:#94a3b8; font-weight:700;">Skills & Keywords</label>
        <div style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-top:0.4rem;">
          ${tagsHtml || '<span style="color:#64748b;">No tags specified</span>'}
        </div>
      </div>

      <div style="margin-bottom:1.5rem;">
        <label style="font-size:0.78rem; text-transform:uppercase; color:#94a3b8; font-weight:700;">Overview / Snippet</label>
        <p style="font-size:0.88rem; color:#cbd5e1; line-height:1.6; margin-top:0.4rem; background:#090d16; padding:1rem; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
          ${escapeHtml(job.description_snippet || 'No extended snippet available. Click below to view the complete job description.')}
        </p>
      </div>

      <div style="display:flex; justify-content:flex-end; gap:0.75rem;">
        <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="width:100%; text-align:center;">
          Apply / View Full Job on ${escapeHtml(job.source)} &rarr;
        </a>
      </div>
    `;
    detailsModal.classList.add('active');
  }

  closeDetailsBtn.addEventListener('click', () => detailsModal.classList.remove('active'));

  // Settings Modal Controls
  openSettingsBtn.addEventListener('click', () => settingsModal.classList.add('active'));
  closeSettingsBtn.addEventListener('click', () => settingsModal.classList.remove('active'));
  cancelSettingsBtn.addEventListener('click', () => settingsModal.classList.remove('active'));

  // Tab switching in settings modal
  document.querySelectorAll('.modal-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      document.getElementById(targetId).style.display = 'block';
    });
  });

  // Copy Google Apps Script Code
  copyAppsScriptBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(appsScriptCodeDisplay.textContent).then(() => {
      copyAppsScriptBtn.textContent = 'Copied! ✅';
      setTimeout(() => copyAppsScriptBtn.textContent = 'Copy Code', 2000);
      showToast('Google Apps Script copied to clipboard!', 'success');
    });
  });

  // Test Webhook Ping
  testWebhookBtn.addEventListener('click', async () => {
    const url = webhookUrlInput.value.trim();
    if (!url) {
      showToast('Please enter a Webhook URL to test', 'error');
      return;
    }
    testWebhookBtn.disabled = true;
    testWebhookBtn.textContent = 'Testing...';
    try {
      const res = await fetch('/api/settings/test-sheets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ webhook_url: url })
      });
      const data = await res.json();
      if (data.success) {
        showToast('Webhook is working and reachable! ✅', 'success');
      } else {
        showToast('Webhook failed: ' + (data.error || 'Unreachable'), 'error');
      }
    } catch (e) {
      showToast('Error testing webhook: ' + e.message, 'error');
    } finally {
      testWebhookBtn.disabled = false;
      testWebhookBtn.textContent = 'Test Ping';
    }
  });

  // Save Settings
  saveSettingsBtn.addEventListener('click', async () => {
    const payload = {
      ...appSettings,
      apps_script_url: webhookUrlInput.value.trim(),
      spreadsheet_id: spreadsheetIdInput.value.trim(),
      tab_name_prefix: tabPrefixInput.value.trim() || 'Jobs_',
      google_sync_enabled: autoSyncToggle.checked,
      sheets_mode: document.querySelector('.modal-tab-btn.active').getAttribute('data-tab') === 'tabServiceAccount' ? 'service_account' : 'webhook'
    };

    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        appSettings = payload;
        showToast('Settings saved successfully!', 'success');
        settingsModal.classList.remove('active');
        loadSettings();
      }
    } catch (e) {
      showToast('Failed to save settings: ' + e.message, 'error');
    }
  });

  // Service account file upload
  serviceAccountFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('/api/settings/upload-service-account', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        showToast('service_account.json uploaded!', 'success');
        loadSettings();
      } else {
        showToast(data.detail || 'Upload failed', 'error');
      }
    } catch (err) {
      showToast('Upload error: ' + err.message, 'error');
    }
  });

  // Saved CSVs History Modal
  openHistoryBtn.addEventListener('click', async () => {
    historyModal.classList.add('active');
    historyModalContent.innerHTML = '<p style="color:#94a3b8;">Loading history...</p>';
    try {
      const res = await fetch('/api/history');
      const data = await res.json();
      const files = data.history || [];
      if (files.length === 0) {
        historyModalContent.innerHTML = '<p style="color:#94a3b8; text-align:center; padding:2rem;">No CSV exports saved yet. Scrape jobs to generate one!</p>';
        return;
      }
      historyModalContent.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:0.6rem;">
          ${files.map(f => `
            <div style="background:rgba(30,41,59,0.5); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:0.85rem 1rem; display:flex; justify-content:space-between; align-items:center;">
              <div>
                <strong style="color:#f8fafc; font-size:0.88rem; display:block;">${escapeHtml(f.filename)}</strong>
                <small style="color:#94a3b8;">📅 ${escapeHtml(f.created_at)} &bull; ${escapeHtml(String(f.size_kb))} KB</small>
              </div>
              <a href="/api/download/${escapeHtml(f.filename)}" class="btn btn-csv" style="padding:0.4rem 0.85rem; font-size:0.8rem;">
                📥 Download
              </a>
            </div>
          `).join('')}
        </div>
      `;
    } catch (e) {
      historyModalContent.innerHTML = '<p style="color:#f43f5e;">Failed to load history.</p>';
    }
  });
  closeHistoryBtn.addEventListener('click', () => historyModal.classList.remove('active'));

  // Close modals on clicking backdrop
  [settingsModal, historyModal, detailsModal].forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('active');
    });
  });

  // Utility HTML Escape
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
