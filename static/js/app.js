// Main Dashboard Application Controller

let currentFilter = {
  sheet_id: 'all',
  tab_name: '',
  poc: 'all',
  status: 'all',
  gender: 'all',
  date_from: '',
  date_to: '',
  search: ''
};

let tableState = {
  page: 1,
  pageSize: 25,
  sortBy: 'id',
  sortOrder: 'asc',
  totalRecords: 0
};

// Expose fetchAnalyticsData globally for sheet_manager
window.fetchAnalyticsData = fetchAnalyticsData;

document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await loadSheetsRegistry();
  await fetchAnalyticsData();
  await fetchTableRecords();
});

function setupEventListeners() {
  // Sheet select changed
  const sheetSelect = document.getElementById('sheetSelect');
  if (sheetSelect) {
    sheetSelect.addEventListener('change', () => {
      currentFilter.sheet_id = sheetSelect.value;
      updateTabSelectorForCurrentSheet();
      const tabSelect = document.getElementById('tabSelect');
      currentFilter.tab_name = tabSelect && !tabSelectContainer.classList.contains('hidden') ? tabSelect.value : '';
      fetchAnalyticsData();
      fetchTableRecords();
    });
  }

  // Tab select changed
  const tabSelect = document.getElementById('tabSelect');
  if (tabSelect) {
    tabSelect.addEventListener('change', () => {
      currentFilter.tab_name = tabSelect.value;
      fetchAnalyticsData();
      fetchTableRecords();
    });
  }

  // POC Filter
  const pocFilter = document.getElementById('pocFilter');
  if (pocFilter) {
    pocFilter.addEventListener('change', (e) => {
      currentFilter.poc = e.target.value;
      fetchAnalyticsData();
      fetchTableRecords();
    });
  }

  // Status Filter
  const statusFilter = document.getElementById('statusFilter');
  if (statusFilter) {
    statusFilter.addEventListener('change', (e) => {
      currentFilter.status = e.target.value;
      fetchAnalyticsData();
      fetchTableRecords();
    });
  }

  // Gender Filter
  const genderFilter = document.getElementById('genderFilter');
  if (genderFilter) {
    genderFilter.addEventListener('change', (e) => {
      currentFilter.gender = e.target.value;
      fetchAnalyticsData();
      fetchTableRecords();
    });
  }

  // Date filters
  const dateFrom = document.getElementById('dateFrom');
  const dateTo = document.getElementById('dateTo');
  if (dateFrom && dateTo) {
    dateFrom.addEventListener('change', (e) => {
      currentFilter.date_from = e.target.value;
      fetchAnalyticsData();
      fetchTableRecords();
    });
    dateTo.addEventListener('change', (e) => {
      currentFilter.date_to = e.target.value;
      fetchAnalyticsData();
      fetchTableRecords();
    });
  }

  // Search input debounce
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentFilter.search = e.target.value;
        tableState.page = 1;
        fetchAnalyticsData();
        fetchTableRecords();
      }, 350);
    });
  }

  // Reset Filters
  const resetBtn = document.getElementById('resetFiltersBtn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      currentFilter.poc = 'all';
      currentFilter.status = 'all';
      currentFilter.gender = 'all';
      currentFilter.date_from = '';
      currentFilter.date_to = '';
      currentFilter.search = '';

      if (pocFilter) pocFilter.value = 'all';
      if (statusFilter) statusFilter.value = 'all';
      if (genderFilter) genderFilter.value = 'all';
      if (dateFrom) dateFrom.value = '';
      if (dateTo) dateTo.value = '';
      if (searchInput) searchInput.value = '';

      fetchAnalyticsData();
      fetchTableRecords();
    });
  }

  // Sync All / Refresh Button
  const refreshBtn = document.getElementById('refreshAllBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      refreshBtn.classList.add('animate-spin');
      if (currentFilter.sheet_id === 'all') {
        for (const s of registeredSheets) {
          await syncSingleSheet(s.id);
        }
      } else {
        await syncSingleSheet(currentFilter.sheet_id);
      }
      refreshBtn.classList.remove('animate-spin');
    });
  }

  // Add sheet form
  const addSheetForm = document.getElementById('addSheetForm');
  if (addSheetForm) {
    addSheetForm.addEventListener('submit', handleAddSheetSubmit);
  }
  // cut karne k liye
  function closeRepoModal() {
    const modal = document.getElementById('repoModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none'; // Forcefully hide karne ke liye
    }
}

  // CSV Export button
  const exportCsvBtn = document.getElementById('exportCsvBtn');
  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => {
      const params = new URLSearchParams({
        sheet_id: currentFilter.sheet_id,
        tab_name: currentFilter.tab_name || '',
        poc: currentFilter.poc || '',
        status: currentFilter.status || '',
        gender: currentFilter.gender || '',
        date_from: currentFilter.date_from || '',
        date_to: currentFilter.date_to || '',
        search: currentFilter.search || ''
      });
      window.location.href = `/api/export-csv?${params.toString()}`;
    });
  }
}

async function fetchAnalyticsData() {
  const params = new URLSearchParams({
    sheet_id: currentFilter.sheet_id,
    tab_name: currentFilter.tab_name || '',
    poc: currentFilter.poc || '',
    status: currentFilter.status || '',
    gender: currentFilter.gender || '',
    date_from: currentFilter.date_from || '',
    date_to: currentFilter.date_to || '',
    search: currentFilter.search || ''
  });

  try {
    const res = await fetch(`/api/analytics?${params.toString()}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to fetch analytics');

    renderKpiCards(data.analytics, data.total_rows);
    renderCharts(data.analytics);
    renderPocLeaderboard(data.analytics.poc_summary || []);
    updateFilterOptions(data.filter_options);
  } catch (err) {
    console.error('Analytics fetch error:', err);
  }
}

function renderKpiCards(analytics, totalRows) {
  if (!analytics) return;

  const totalCalls = analytics.total_calls || 0;
  const ansCalls = analytics.answered_calls || 0;
  const notAnsCalls = analytics.not_answered_calls || 0;
  const ansRate = analytics.answer_rate_pct || 0;
  const dropRate = analytics.drop_rate_pct || 0;

  const maleCount = (analytics.gender_breakdown && analytics.gender_breakdown['Male']) || 0;
  const femaleCount = (analytics.gender_breakdown && analytics.gender_breakdown['Female']) || 0;
  const knownGenderTotal = maleCount + femaleCount;
  const maleRatio = knownGenderTotal > 0 ? ((maleCount / knownGenderTotal) * 100).toFixed(0) : 0;
  const femaleRatio = knownGenderTotal > 0 ? ((femaleCount / knownGenderTotal) * 100).toFixed(0) : 0;

  const memYes = (analytics.membership_summary && analytics.membership_summary['Yes']) || 0;
  const donYes = (analytics.donation_summary && analytics.donation_summary['Yes']) || 0;

  // DOM elements
  document.getElementById('kpiTotalCalls').textContent = totalCalls.toLocaleString();
  document.getElementById('kpiAnswered').textContent = ansCalls.toLocaleString();
  document.getElementById('kpiAnswerRate').textContent = `${ansRate}% Answer Rate`;
  document.getElementById('kpiNotAnswered').textContent = notAnsCalls.toLocaleString();
  document.getElementById('kpiDropRate').textContent = `${dropRate}% Unanswered / Drop`;

  document.getElementById('kpiMaleCount').textContent = maleCount.toLocaleString();
  document.getElementById('kpiFemaleCount').textContent = femaleCount.toLocaleString();
  document.getElementById('kpiGenderRatio').textContent = `${maleRatio}% M / ${femaleRatio}% F`;

  document.getElementById('kpiMembershipYes').textContent = memYes.toLocaleString();
  document.getElementById('kpiDonationYes').textContent = donYes.toLocaleString();
}

function updateFilterOptions(options) {
  if (!options) return;

  // Update POC dropdown if empty
  const pocSelect = document.getElementById('pocFilter');
  if (pocSelect && options.pocs && pocSelect.options.length <= 1) {
    options.pocs.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = p;
      pocSelect.appendChild(opt);
    });
  }

  // Update Status dropdown if empty
  const statusSelect = document.getElementById('statusFilter');
  if (statusSelect && options.statuses && statusSelect.options.length <= 3) {
    options.statuses.forEach(s => {
      if (!['Answered', 'Not Answered'].includes(s)) {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        statusSelect.appendChild(opt);
      }
    });
  }
}

function renderPocLeaderboard(pocList) {
  const tbody = document.getElementById('pocLeaderboardBody');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (pocList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-gray-400">No POC records found</td></tr>`;
    return;
  }

  pocList.forEach((p, idx) => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-gray-800/40 transition border-b border-gray-800/60 text-sm';
    
    let rankBadge = `<span class="text-gray-400 font-mono text-xs">#${idx + 1}</span>`;
    if (idx === 0) rankBadge = `<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">🥇 1st</span>`;
    else if (idx === 1) rankBadge = `<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-slate-300/20 text-slate-200 border border-slate-400/30">🥈 2nd</span>`;
    else if (idx === 2) rankBadge = `<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-700/20 text-amber-500 border border-amber-600/30">🥉 3rd</span>`;

    let rateBadgeClass = 'badge-rate-low';
    if (p.answer_rate >= 40) rateBadgeClass = 'badge-rate-high';
    else if (p.answer_rate >= 15) rateBadgeClass = 'badge-rate-mid';

    tr.innerHTML = `
      <td class="py-3 px-3">${rankBadge}</td>
      <td class="py-3 px-3 font-semibold text-white">
        <button onclick="filterBySinglePoc('${p.poc}')" class="hover:text-blue-400 hover:underline text-left">
          ${p.poc}
        </button>
      </td>
      <td class="py-3 px-3 font-mono text-gray-200">${p.total.toLocaleString()}</td>
      <td class="py-3 px-3 font-mono text-emerald-400">${p.answered.toLocaleString()}</td>
      <td class="py-3 px-3 font-mono text-rose-400">${p.not_answered.toLocaleString()}</td>
      <td class="py-3 px-3">
        <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold ${rateBadgeClass}">
          ${p.answer_rate}%
        </span>
      </td>
      <td class="py-3 px-3 text-xs text-gray-300">
        <span class="text-blue-400">${p.male} M</span> / <span class="text-pink-400">${p.female} F</span>
      </td>
      <td class="py-3 px-3 text-xs">
        <span class="text-emerald-400 font-medium">${p.membership_yes} Mem</span> • <span class="text-cyan-400 font-medium">${p.donation_yes} Don</span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterBySinglePoc(pocName) {
  const pocSelect = document.getElementById('pocFilter');
  if (pocSelect) {
    pocSelect.value = pocName;
    currentFilter.poc = pocName;
    fetchAnalyticsData();
    fetchTableRecords();
  }
}

async function fetchTableRecords() {
  const params = new URLSearchParams({
    sheet_id: currentFilter.sheet_id,
    tab_name: currentFilter.tab_name || '',
    poc: currentFilter.poc || '',
    status: currentFilter.status || '',
    gender: currentFilter.gender || '',
    date_from: currentFilter.date_from || '',
    date_to: currentFilter.date_to || '',
    search: currentFilter.search || '',
    page: tableState.page,
    page_size: tableState.pageSize,
    sort_by: tableState.sortBy,
    sort_order: tableState.sortOrder
  });

  try {
    const res = await fetch(`/api/records?${params.toString()}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to fetch table records');

    tableState.totalRecords = data.total;
    renderRecordsTable(data.records);
    renderPagination(data.total, data.page, data.total_pages);
  } catch (err) {
    console.error('Table fetch error:', err);
  }
}

function renderRecordsTable(records) {
  const tbody = document.getElementById('recordsTableBody');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-gray-400">No records matching the filter criteria</td></tr>`;
    return;
  }

  records.forEach(r => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-gray-800/50 border-b border-gray-800/60 transition text-xs';
    
    const ansBadge = r.is_answered
      ? `<span class="px-2 py-0.5 rounded-full font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">Answered</span>`
      : `<span class="px-2 py-0.5 rounded-full font-medium bg-rose-500/15 text-rose-400 border border-rose-500/20">${r.status || 'Not Answered'}</span>`;

    const genderBadge = r.gender === 'Male'
      ? `<span class="text-blue-400 font-medium">Male</span>`
      : (r.gender === 'Female' ? `<span class="text-pink-400 font-medium">Female</span>` : `<span class="text-gray-500">-</span>`);

    tr.innerHTML = `
      <td class="py-2.5 px-3 font-mono text-gray-400">${r.id}</td>
      <td class="py-2.5 px-3 text-gray-300 font-mono">${r.calling_date || '-'}</td>
      <td class="py-2.5 px-3 font-medium text-white">${r.poc || '-'}</td>
      <td class="py-2.5 px-3 font-mono text-gray-300">${r.customer_no || '-'}</td>
      <td class="py-2.5 px-3 text-gray-200">${r.name || '-'}</td>
      <td class="py-2.5 px-3">${ansBadge}</td>
      <td class="py-2.5 px-3">${genderBadge}</td>
      <td class="py-2.5 px-3 text-gray-300">${r.district || '-'}</td>
      <td class="py-2.5 px-3">
        <span class="${r.membership === 'Yes' ? 'text-emerald-400 font-semibold' : 'text-gray-400'}">${r.membership || '-'}</span>
      </td>
      <td class="py-2.5 px-3">
        <span class="${r.donation_status === 'Yes' ? 'text-cyan-400 font-semibold' : 'text-gray-400'}">${r.donation_status || '-'}</span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderPagination(total, page, totalPages) {
  const infoEl = document.getElementById('paginationInfo');
  const btnsEl = document.getElementById('paginationButtons');
  if (!infoEl || !btnsEl) return;

  const start = total === 0 ? 0 : (page - 1) * tableState.pageSize + 1;
  const end = Math.min(page * tableState.pageSize, total);
  infoEl.textContent = `Showing ${start.toLocaleString()} to ${end.toLocaleString()} of ${total.toLocaleString()} records`;

  btnsEl.innerHTML = `
    <button onclick="goToTablePage(${page - 1})" ${page <= 1 ? 'disabled class="px-2.5 py-1 rounded bg-gray-800 text-gray-600 cursor-not-allowed"' : 'class="px-2.5 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300"'}>
      Prev
    </button>
    <span class="px-3 py-1 text-xs text-gray-300 font-mono">Page ${page} of ${totalPages}</span>
    <button onclick="goToTablePage(${page + 1})" ${page >= totalPages ? 'disabled class="px-2.5 py-1 rounded bg-gray-800 text-gray-600 cursor-not-allowed"' : 'class="px-2.5 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300"'}>
      Next
    </button>
  `;
}

function goToTablePage(page) {
  if (page < 1) return;
  tableState.page = page;
  fetchTableRecords();
}

function changePageSize(size) {
  tableState.pageSize = parseInt(size, 10);
  tableState.page = 1;
  fetchTableRecords();
}

// Modal open/close helpers
function openRepositoryModal() {
  const modal = document.getElementById('repoModal');
  if (modal) {
    modal.classList.remove('hidden');
    renderRepositoryModalList();
  }
}

function closeRepositoryModal() {
  const modal = document.getElementById('repoModal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

