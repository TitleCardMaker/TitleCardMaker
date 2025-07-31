{% if False %}
import {Duration, Snapshot} from './.types.js';
{% endif %}

/**
 * Get a string representation of the given frequency.
 * @param {int} freq - Frequency (in seconds).
 * @returns {string} String representation of the frequency.
 */
function timeFreqString(freq, top=-1) {
  const seconds = Math.floor(freq);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) { return `${days} day${days > 1 ? 's' : ''}`; }
  if (hours % 24 > 0) { return `${hours%24} hour${hours%24 > 1 ? 's' : ''}`; }
  if (minutes % 60 > 0) { return `${minutes%60} minute${minutes%60 > 1 ? 's' : ''}`; }
  if (seconds % 60 < 1) { return `<1 second`; }
  return `${seconds%60} second${seconds%60 != 1 ? 's' : ''}`;
}

let cardGraph, countsGraph, taskDurationsGraph;

/**
 * Convert a date string from Fomantic UI calendar format to ISO string
 * @param {string} dateStr - Date string from calendar input
 * @returns {string} ISO date string or empty string
 */
function formatDateForAPI(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return isNaN(date.getTime()) ? '' : date.toISOString();
}

/**
 * Format a date for display in the calendar input
 * @param {Date} date - Date object
 * @returns {string} Formatted date string
 */
function formatDateForDisplay(date) {
  if (!date) return '';
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

function getSnapshots() {
  // Get search params from URL
  const params = new URLSearchParams(window.location.search);
  
  // Get filter values from form inputs
  const startDate = formatDateForAPI($('input[name="start_date"]').val());
  const endDate = formatDateForAPI($('input[name="end_date"]').val());
  const days = $('input[name="days"]').val();
  const slice = $('input[name="slice"]').val() || params.get('slice') || 1;

  // Build query parameters
  const queryParams = new URLSearchParams();
  
  if (startDate) {
    queryParams.set('start', startDate);
  }
  if (endDate) {
    queryParams.set('end', endDate);
  }
  if (days && !startDate && !endDate) {
    // Only use days if no specific dates are set
    const previousDays = parseInt(days) || 14;
    const after = new Date(new Date().setDate(new Date().getDate() - previousDays));
    queryParams.set('start', after.toISOString());
  }
  if (slice) {
    queryParams.set('slice', slice);
  }

  // Write params to URL for bookmarking
  const urlParams = new URLSearchParams();
  if (startDate) urlParams.set('start_date', $('input[name="start_date"]').val());
  if (endDate) urlParams.set('end_date', $('input[name="end_date"]').val());
  if (days) urlParams.set('days', days);
  if (slice) urlParams.set('slice', slice);
  window.history.pushState({}, '', `${window.location.origin}${window.location.pathname}?${urlParams.toString()}`);

  $.ajax({
    type: 'GET',
    url: `/api/v2/statistics/snapshots?${queryParams.toString()}`,
    /**
     * Snapshots queried, populate graph
     * @param {Snapshot} snapshots - Snapshots to populate the graph with.
     */
    success: snapshots => {
      const labels = snapshots.map(snapshot => new Date(snapshot.timestamp));
      const datasets = [
        {
          label: 'Series',
          data: snapshots.map(snapshot => snapshot.series),
        },
        {
          label: 'Episodes',
          data: snapshots.map(snapshot => snapshot.episodes),
          yAxisID: 'yCards',
          fill: '+1', // Fill to total number of Cards
        },
        // {
        //   label: 'Blueprints',
        //   data: snapshots.map(snapshot => snapshot.blueprints),
        // },
        {
          label: 'Title Cards',
          data: snapshots.map(snapshot => snapshot.cards),
          yAxisID: 'yCards',
          fill: '+1', // Fill to number of loaded Cards
        },
        // {
        //   label: 'Fonts',
        //   data: snapshots.map(snapshot => snapshot.fonts),
        // },
        {
          label: 'Loaded Title Cards',
          data: snapshots.map(snapshot => snapshot.loaded),
          yAxisID: 'yCards',
        },
        // {
        //   label: 'Syncs',
        //   data: snapshots.map(snapshot => snapshot.syncs),
        // },
        // {
        //   label: 'Templates',
        //   data: snapshots.map(snapshot => snapshot.templates),
        // },
        {
          label: 'Title Cards Created',
          data: snapshots.map(snapshot => snapshot.cards_created),
          // fill: 'origin',
          yAxisID: 'yTotalCards',
        },
        {
          label: 'Title Card Filesize',
          data: snapshots.map(snapshot => snapshot.filesize / 1e6),
          yAxisID: 'yFilesize'
        }
      ];

      // If graph already exists, destroy and recreate
      if (cardGraph) { cardGraph.destroy(); }

      const ctx = document.getElementById('graph');
      cardGraph = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          fill: true,
          stepped: true,
          datasets: datasets
        },
        options: {
          responsive: true,
          stacked: false,
          pointStyle: false,
          stepped: 'before',
          interaction: {
            intersect: false,
            axis: 'x'
          },
          plugins: {},
          scales: {
            x: {
              type: 'time',
              time: {
                // Luxon format string
                tooltipFormat: 'DD T',
                unit: 'day',
              },
              grid: {
                // drawOnChartArea: false,
              },
              title: {
                display: true,
                text: 'Date'
              },
            },
            y: {
              type: 'linear',
              display: true,
              position: 'left',
            },
            yCards: {
              type: 'linear',
              display: true,
              position: 'left',
              grid: {
                drawOnChartArea: false,
              },
            },
            yTotalCards: {
              type: 'linear',
              display: true,
              position: 'right',
              title: {
                display: true,
                text: '# Title Cards',
              },
              grid: {
                drawOnChartArea: false,
              }
            },
            yFilesize: {
              type: 'linear',
              display: true,
              position: 'right',
              title: {
                display: true,
                text: 'Megabytes',
              },
              grid: {
                drawOnChartArea: false,
              }
            }
          }
        }
      });

      // Counts graph data
      const countDatasets = [
        {
          label: 'Blueprints',
          data: snapshots.map(snapshot => snapshot.blueprints),
        },
        {
          label: 'Fonts',
          data: snapshots.map(snapshot => snapshot.fonts),
        },
        {
          label: 'Syncs',
          data: snapshots.map(snapshot => snapshot.syncs),
        },
        {
          label: 'Templates',
          data: snapshots.map(snapshot => snapshot.templates),
        },
      ];

      // Graph already exists, destroy and recreate
      if (countsGraph) { countsGraph.destroy(); }

      const countCtx = document.getElementById('dbCountsGraph');
      countsGraph = new Chart(countCtx, {
        type: 'line',
        data: {
          labels: labels,
          fill: true,
          stepped: true,
          datasets: countDatasets,
        },
        options: {
          responsive: true,
          stacked: false,
          pointStyle: false,
          stepped: 'before',
          interaction: {
            intersect: false,
            axis: 'x'
          },
          plugins: {},
          scales: {
            x: {
              type: 'time',
              time: {
                // Luxon format string
                tooltipFormat: 'DD T',
                unit: 'day',
              },
              grid: {
                // drawOnChartArea: false,
              },
              title: {
                display: true,
                text: 'Date'
              }
            },
            y: {
              type: 'linear',
              display: true,
              position: 'left',
            },
          }
        }
      });

    },
  });
}

/**
 * Submit an API request to get task durations and populate the graph.
 */
function getTaskDurations() {
  // Get filter values
  const startDate = formatDateForAPI($('input[name="start_date"]').val());
  const endDate = formatDateForAPI($('input[name="end_date"]').val());
  const days = $('input[name="days"]').val();
  
  let after;
  if (startDate) {
    after = new Date(startDate);
  } else if (days) {
    const previousDays = parseInt(days) || 7;
    after = new Date(new Date().setDate(new Date().getDate() - previousDays));
  } else {
    after = new Date(new Date().setDate(new Date().getDate() - 7));
  }

  $.ajax({
    type: 'GET',
    url: `/api/v2/statistics/task-durations?after=${after.toISOString()}`,
    /**
     * Task durations queried, populate graph
     * @param {Duration[]} taskDurations - Task durations to populate the graph with.
     **/
    success: taskDurations => {
      // Populate task durations graph
      if (taskDurationsGraph) { taskDurationsGraph.destroy(); }

      // Group durations by task_name
      const grouped = {};
      taskDurations.forEach(d => {
        // Skip SnapshotDatabase tasks
        if ((d.task_name === 'SnapshotDatabase')) { return; }
        if (!grouped[d.task_name]) {
          grouped[d.task_name] = [];
        }
        grouped[d.task_name].push(d);
      });

      const datasets = Object.entries(grouped).map(([taskName, entries]) => {
        // Sort by time just in case
        entries.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
        
        const data = [];
        entries.forEach(entry => {
          data.push({ x: entry.start_time, y: taskName }); // "start" point
          data.push({ x: entry.end_time, y: taskName });   // "end" point
          data.push({ x: entry.end_time, y: null });       // break continuity
        });

        return {
          label: taskName,
          data: data,
          spanGaps: false, // Don't connect across nulls
          fill: false,
          tension: 0.3
        };
      });

      taskDurationsGraph = new Chart($('#taskDurationsGraph'), {
        type: 'line',
        data: {
          datasets: datasets
        },
        options: {
          responsive: true,
          interaction: {
            intersect: false,
            axis: 'x'
          },
          scales: {
            x: {
              type: 'time',
              title: {
                display: true,
                text: 'Time'
              },
              grid: {
                drawOnChartArea: true,
              },
              time: {
                unit: 'day',
              }
            },
            y: {
              type: 'category',
              labels: Object.keys(grouped),
              title: {
                display: true,
                text: 'Task'
              },
            }
          },
          plugins: {
            legend: {
              position: 'bottom'
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const dataset = context.dataset;
                  const index = context.dataIndex;
                  const point = dataset.data[index];
      
                  // Check if there's a valid previous/next point to compute duration
                  if (index % 3 === 0 && dataset.data[index + 1]) {
                    const start = new Date(point.x);
                    const end = new Date(dataset.data[index + 1].x);
                    return ' Took ' + timeFreqString((end - start) / 1000, 1);
                  }
                  else if (index > 0 && dataset.data[index - 1]) {
                    const start = new Date(dataset.data[index - 1].x);
                    const end = new Date(point.x);
                    return ' Took ' + timeFreqString((end - start) / 1000, 1);
                  }
      
                  return dataset.label;
                }
              }
            }
          },
        },
      });
    },
  });
}

/**
 * Reset all filters to default values
 */
function resetFilters() {
  $('input[name="start_date"]').val('');
  $('input[name="end_date"]').val('');
  $('input[name="days"]').val('14');
  $('input[name="slice"]').val('1');
  
  // Clear calendar inputs
  $('.ui.calendar').calendar('clear');
  
  getSnapshots();
  getTaskDurations();
}

/**
 * Load filter values from URL parameters on page load
 */
function loadFiltersFromURL() {
  const params = new URLSearchParams(window.location.search);
  
  if (params.get('start_date')) {
    $('input[name="start_date"]').val(params.get('start_date'));
  }
  if (params.get('end_date')) {
    $('input[name="end_date"]').val(params.get('end_date'));
  }
  if (params.get('days')) {
    $('input[name="days"]').val(params.get('days'));
  }
  if (params.get('slice')) {
    $('input[name="slice"]').val(params.get('slice'));
  }
}

/**
 * Initialize Fomantic UI calendar components
 */
function initializeCalendars() {
  $('.ui.calendar').calendar({
    type: 'datetime',
    formatter: {
      datetime: function (date, settings) {
        if (!date) return '';
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day} ${hours}:${minutes}`;
      }
    },
    parser: {
      datetime: function (text, settings) {
        if (!text) return null;
        const date = new Date(text);
        return isNaN(date.getTime()) ? null : date;
      }
    }
  });
}

function initAll() {
  // Initialize Fomantic UI calendars
  initializeCalendars();
  
  // Load filters from URL
  loadFiltersFromURL();
  
  // Query snapshots to initialize charts
  getSnapshots();

  // Query task durations to initialize charts
  getTaskDurations();

  // Re-query when inputs are changed
  $('input[name="days"], input[name="slice"]').on('change', () => {
    getSnapshots();
    getTaskDurations();
  });
  
  // Re-query when calendar inputs change
  $('.ui.calendar').on('change', () => {
    getSnapshots();
    getTaskDurations();
  });
}