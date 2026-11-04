// Chart.js visualizations manager

let pocChartInstance = null;
let statusChartInstance = null;
let timelineChartInstance = null;
let genderChartInstance = null;
let districtChartInstance = null;

// Dark theme Chart defaults
Chart.defaults.color = '#9ca3af';
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
Chart.defaults.plugins.tooltip.backgroundColor = '#1f2937';
Chart.defaults.plugins.tooltip.titleColor = '#f3f4f6';
Chart.defaults.plugins.tooltip.bodyColor = '#e5e7eb';
Chart.defaults.plugins.tooltip.borderColor = '#374151';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.cornerRadius = 8;

function renderCharts(analytics) {
  if (!analytics) return;

  renderPocChart(analytics.poc_summary || []);
  renderStatusChart(analytics.status_breakdown || {});
  renderTimelineChart(analytics.date_timeline || []);
  renderGenderChart(analytics.gender_breakdown || {});
  renderDistrictChart(analytics.top_districts || []);
}

function renderPocChart(pocList) {
  const ctx = document.getElementById('pocChart');
  if (!ctx) return;

  // Take top 12 POCs by volume
  const topPocs = pocList.slice(0, 12);
  const labels = topPocs.map(p => p.poc);
  const answered = topPocs.map(p => p.answered);
  const notAnswered = topPocs.map(p => p.not_answered);

  if (pocChartInstance) {
    pocChartInstance.destroy();
  }

  pocChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Answered',
          data: answered,
          backgroundColor: '#10b981',
          borderRadius: 4,
          stack: 'stack0'
        },
        {
          label: 'Not Answered / Other',
          data: notAnswered,
          backgroundColor: '#f43f5e',
          borderRadius: 4,
          stack: 'stack0'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#9ca3af', font: { size: 12 } }
        },
        tooltip: {
          callbacks: {
            footer: (items) => {
              const total = items.reduce((a, b) => a + b.raw, 0);
              const ans = items.find(i => i.dataset.label === 'Answered')?.raw || 0;
              const rate = total > 0 ? ((ans / total) * 100).toFixed(1) : 0;
              return `Total Calls: ${total}\nAnswer Rate: ${rate}%`;
            }
          }
        }
      },
      scales: {
        x: {
          stacked: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af', maxRotation: 45, minRotation: 25 }
        },
        y: {
          stacked: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af' }
        }
      }
    }
  });
}

function renderStatusChart(statusMap) {
  const ctx = document.getElementById('statusChart');
  if (!ctx) return;

  const labels = Object.keys(statusMap);
  const data = Object.values(statusMap);

  // Palette
  const colors = [
    '#10b981', // Answered - emerald
    '#f43f5e', // Not Answered - rose
    '#f59e0b', // Busy - amber
    '#8b5cf6', // Switch off - purple
    '#06b6d4', // Out of Network - cyan
    '#ec4899', // Incoming off - pink
    '#64748b', // Invalid - slate
    '#3b82f6', // Other - blue
  ];

  if (statusChartInstance) {
    statusChartInstance.destroy();
  }

  statusChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors.slice(0, labels.length),
        borderWidth: 2,
        borderColor: '#111827',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#d1d5db', boxWidth: 12, padding: 12, font: { size: 11 } }
        }
      },
      cutout: '68%'
    }
  });
}

function renderTimelineChart(timeline) {
  const ctx = document.getElementById('timelineChart');
  if (!ctx) return;

  const labels = timeline.map(t => t.date);
  const totals = timeline.map(t => t.total);
  const answered = timeline.map(t => t.answered);
  const notAnswered = timeline.map(t => t.not_answered);

  if (timelineChartInstance) {
    timelineChartInstance.destroy();
  }

  timelineChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Total Calls',
          data: totals,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 2.5,
          pointHoverRadius: 5
        },
        {
          label: 'Answered Calls',
          data: answered,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.05)',
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 2.5,
          pointHoverRadius: 5
        },
        {
          label: 'Not Answered Calls',
          data: notAnswered,
          borderColor: '#f43f5e',
          backgroundColor: 'transparent',
          borderDash: [4, 4],
          tension: 0.35,
          borderWidth: 1.5,
          pointRadius: 2,
          pointHoverRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#9ca3af', font: { size: 12 } }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af', maxRotation: 45, minRotation: 20 }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af' }
        }
      }
    }
  });
}

function renderGenderChart(genderMap) {
  const ctx = document.getElementById('genderChart');
  if (!ctx) return;

  const labels = ['Male', 'Female', 'Not Specified'];
  const data = [
    genderMap['Male'] || 0,
    genderMap['Female'] || 0,
    genderMap['Not Specified'] || 0
  ];

  if (genderChartInstance) {
    genderChartInstance.destroy();
  }

  genderChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: ['#3b82f6', '#ec4899', '#64748b'],
        borderWidth: 2,
        borderColor: '#111827',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#d1d5db', boxWidth: 12, padding: 10, font: { size: 11 } }
        }
      },
      cutout: '65%'
    }
  });
}

function renderDistrictChart(districtList) {
  const ctx = document.getElementById('districtChart');
  if (!ctx) return;

  const top10 = districtList.slice(0, 10);
  const labels = top10.map(d => d.district);
  const counts = top10.map(d => d.count);

  if (districtChartInstance) {
    districtChartInstance.destroy();
  }

  districtChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Calls Placed',
        data: counts,
        backgroundColor: '#06b6d4',
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af' }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#9ca3af', font: { size: 11 } }
        }
      }
    }
  });
}

