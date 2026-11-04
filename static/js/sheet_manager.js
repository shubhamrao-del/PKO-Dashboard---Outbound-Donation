// Google Sheet Repository & Link Manager

let registeredSheets = [];

async function loadSheetsRegistry() {
  try {
    const res = await fetch('/api/sheets');
    const data = await res.json();
    registeredSheets = data.sheets || [];
    renderSheetSelectorDropdown();
    renderRepositoryModalList();
  } catch (err) {
    console.error('Failed to load sheets registry:', err);
  }
}

function renderSheetSelectorDropdown() {
  const select = document.getElementById('sheetSelect');
  if (!select) return;

  const currentVal = select.value;
  select.innerHTML = '';

  // All Sheets option
  const allOpt = document.createElement('option');
  allOpt.value = 'all';
  allOpt.textContent = `📊 All Sheets Combined (${registeredSheets.length} Sheets)`;
  select.appendChild(allOpt);

  registeredSheets.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = `📄 ${s.label || s.id} (${s.total_rows.toLocaleString()} rows)`;
    select.appendChild(opt);
  });

  if (currentVal && [...select.options].some(o => o.value === currentVal)) {
    select.value = currentVal;
  } else {
    select.value = 'all';
  }

  updateTabSelectorForCurrentSheet();
}

function updateTabSelectorForCurrentSheet() {
  const sheetSelect = document.getElementById('sheetSelect');
  const tabSelectContainer = document.getElementById('tabSelectContainer');
  const tabSelect = document.getElementById('tabSelect');
  const detectedBadge = document.getElementById('detectedTabBadge');
  
  if (!sheetSelect || !tabSelect) return;

  const currentSheetId = sheetSelect.value;
  
  if (currentSheetId === 'all') {
    tabSelectContainer.classList.add('hidden');
    return;
  }

  const sheet = registeredSheets.find(s => s.id === currentSheetId);
  if (!sheet || !sheet.tabs || sheet.tabs.length === 0) {
    tabSelectContainer.classList.add('hidden');
    return;
  }

  tabSelectContainer.classList.remove('hidden');
  tabSelect.innerHTML = '';

  sheet.tabs.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.name;
    const isWorkingMonth = t.type === 'monthly_calling';
    const isCompile = t.type === 'compile_records';
    let typeTag = isWorkingMonth ? ' [Auto-Detected Monthly]' : (isCompile ? ' [Compile / Records]' : '');
    opt.textContent = `${t.name}${typeTag}`;
    tabSelect.appendChild(opt);
  });

  tabSelect.value = sheet.active_tab || sheet.tabs[0].name;

  if (detectedBadge) {
    const activeTabObj = sheet.tabs.find(t => t.name === sheet.active_tab);
    if (activeTabObj && activeTabObj.type === 'monthly_calling') {
      detectedBadge.innerHTML = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Working Sheet: ${sheet.active_tab}</span>`;
    } else if (activeTabObj && activeTabObj.type === 'compile_records') {
      detectedBadge.innerHTML = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20"><span class="w-1.5 h-1.5 rounded-full bg-purple-400"></span> Compile Sheet: ${sheet.active_tab}</span>`;
    } else {
      detectedBadge.innerHTML = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">Tab: ${sheet.active_tab}</span>`;
    }
  }
}

function renderRepositoryModalList() {
  const container = document.getElementById('repositoryList');
  const countBadge = document.getElementById('repoCountBadge');
  if (!container) return;

  if (countBadge) {
    countBadge.textContent = `${registeredSheets.length} Connected`;
  }

  container.innerHTML = '';

  if (registeredSheets.length === 0) {
    container.innerHTML = `
      <div class="text-center py-8 text-gray-400 text-sm">
        No Google Sheets registered yet. Paste a link above to add one.
      </div>
    `;
    return;
  }

  registeredSheets.forEach(sheet => {
    const card = document.createElement('div');
    card.className = 'p-4 rounded-xl bg-gray-800/60 border border-gray-700/60 hover:border-blue-500/40 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4';
    
    // Find active tab info
    const activeTabObj = (sheet.tabs || []).find(t => t.name === sheet.active_tab);
    const isMonthSheet = activeTabObj?.type === 'monthly_calling';

    // Build tab options
    let tabOptionsHtml = (sheet.tabs || []).map(t => {
      const selected = t.name === sheet.active_tab ? 'selected' : '';
      const tag = t.type === 'monthly_calling' ? '⭐ (Working Month)' : (t.type === 'compile_records' ? '📋 (Compile Tab)' : '');
      return `<option value="${t.name}" ${selected}>${t.name} ${tag}</option>`;
    }).join('');

    card.innerHTML = `
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <h4 class="font-semibold text-white truncate text-base">${sheet.label || 'Google Sheet'}</h4>
          <span class="text-xs px-2 py-0.5 rounded-full ${isMonthSheet ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'}">
            ${isMonthSheet ? 'Auto-Detected Month Sheet' : 'Working Tab'}
          </span>
          <span class="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-300">
            ${sheet.total_rows.toLocaleString()} Records
          </span>
        </div>
        <div class="flex items-center gap-3 mt-1.5 text-xs text-gray-400 flex-wrap">
          <span>Synced: <strong class="text-gray-300">${sheet.last_synced || 'Just now'}</strong></span>
          <span>•</span>
          <span>Answer Rate: <strong class="${sheet.answer_rate > 30 ? 'text-emerald-400' : 'text-amber-400'}">${sheet.answer_rate}%</strong></span>
          <span>•</span>
          <a href="${sheet.url}" target="_blank" class="text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1">
            Open in Google Sheets ↗
          </a>
        </div>
        <div class="mt-3 flex items-center gap-2">
          <label class="text-xs text-gray-400 whitespace-nowrap">Active Tab:</label>
          <select onchange="changeSheetTab('${sheet.id}', this.value)" class="text-xs bg-gray-900 border border-gray-700 rounded-lg px-2.5 py-1 text-gray-200 focus:outline-none focus:border-blue-500">
            ${tabOptionsHtml}
          </select>
        </div>
      </div>

      <div class="flex items-center gap-2 self-end md:self-center">
        <button onclick="syncSingleSheet('${sheet.id}')" id="sync-btn-${sheet.id}" class="px-3 py-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-white text-xs font-medium flex items-center gap-1.5 transition">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          Sync
        </button>
        <button onclick="deleteSingleSheet('${sheet.id}')" class="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium transition">
          Remove
        </button>
      </div>
    `;

    container.appendChild(card);
  });
}

async function handleAddSheetSubmit(e) {
  e.preventDefault();
  const urlInput = document.getElementById('newSheetUrl');
  const labelInput = document.getElementById('newSheetLabel');
  const statusDiv = document.getElementById('addSheetStatus');
  const submitBtn = document.getElementById('addSheetBtn');

  const url = urlInput.value.trim();
  const label = labelInput.value.trim();

  if (!url) {
    statusDiv.innerHTML = '<span class="text-red-400 text-xs">Please paste a Google Sheets URL or ID.</span>';
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = `
    <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
    </svg>
    Fetching & Detecting Tabs...
  `;
  statusDiv.innerHTML = '<span class="text-blue-400 text-xs">Downloading spreadsheet & auto-detecting working month tabs...</span>';

  try {
    const res = await fetch('/api/sheets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, label })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to add sheet');
    }

    urlInput.value = '';
    labelInput.value = '';
    statusDiv.innerHTML = `<span class="text-emerald-400 text-xs font-medium">✓ Successfully added! Auto-detected working tab: <strong>${data.sheet.active_tab}</strong> (${data.sheet.total_rows.toLocaleString()} rows)</span>`;

    await loadSheetsRegistry();
    // Switch to this new sheet immediately
    document.getElementById('sheetSelect').value = data.sheet.id;
    updateTabSelectorForCurrentSheet();
    window.fetchAnalyticsData();

    setTimeout(() => {
      statusDiv.innerHTML = '';
    }, 5000);
  } catch (err) {
    statusDiv.innerHTML = `<span class="text-red-400 text-xs font-medium">Error: ${err.message}</span>`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
      Add & Analyze Sheet
    `;
  }
}

async function syncSingleSheet(sheetId) {
  const btn = document.getElementById(`sync-btn-${sheetId}`);
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block">↻</span> Syncing...`;
  }

  try {
    const res = await fetch(`/api/sheets/${sheetId}/sync`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Sync failed');
    await loadSheetsRegistry();
    window.fetchAnalyticsData();
  } catch (err) {
    alert(`Sync failed: ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `Sync`;
    }
  }
}

async function deleteSingleSheet(sheetId) {
  if (!confirm('Are you sure you want to remove this sheet from the repository?')) return;

  try {
    await fetch(`/api/sheets/${sheetId}`, { method: 'DELETE' });
    await loadSheetsRegistry();
    window.fetchAnalyticsData();
  } catch (err) {
    alert(`Delete failed: ${err.message}`);
  }
}

async function changeSheetTab(sheetId, tabName) {
  try {
    const res = await fetch(`/api/sheets/${sheetId}/tab`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tab_name: tabName })
    });
    if (!res.ok) throw new Error('Failed to switch tab');
    await loadSheetsRegistry();
    window.fetchAnalyticsData();
  } catch (err) {
    alert(`Error switching tab: ${err.message}`);
  }
}

