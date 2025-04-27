{% if False %}
import {
  Series,
  SeriesPage,
  Statistic
} from './.types.js';
{% endif %}

/** @type {number[]} */
let allIds = [];

/** @type {boolean} */
const library_unique_cards = {{ preferences.library_unique_cards|tojson }};
/** @type {boolean} */
const stylize_unmonitored_posters = {{ preferences.stylize_unmonitored_posters|tojson }};
/** @type {boolean} */
const reduced_animations = {{ preferences.reduced_animations|tojson }};
/** @type {boolean} */
const home_page_table_view = {{ preferences.home_page_table_view|tojson }};
/** @type {Object.<number, string[]>} Mapping of Connection IDs to library names */
const libraryMap = {{ preferences.libraries | safe }};

/**
 * Refresh the Card data (progress and card counts) for the Series with the
 * given ID.
 * @param {number} seriesId: ID of the Series to update the card data of.
 */
function refreshCardData(seriesId) {
  $.ajax({
    type: 'GET',
    url: `/api/series/series/${seriesId}`,
    success: series => {
      $(`#series-id${series.id} span[data-value="card_count"]`).transition('fade out');
      $(`#series-id${series.id} span[data-value="card_count"]`)[0].innerText = `${series.card_count} / ${series.episode_count} Cards`;
      $(`#series-id${series.id} [data-row="card_count"] .progress`)
        .progress({
          percent: [
            series.card_count / series.episode_count * 100,
            (series.episode_count - series.card_count) / series.episode_count * 100
          ],
          duration: 2000,
        });
      $(`#series-id${series.id} span[data-value="card_count"]`).transition('fade in');
    },
    error: response => showErrorToast({title: 'Error Updating Data', response}),
  });
}

/**
 * Submit an API request to toggle the monitored status of the Series with the
 * given ID. This also updates the poster class and the monitored icon.
 * @param {number} seriesId - ID of the Series to toggle.
 */
function toggleMonitoredStatus(seriesId) {
  const $icon = setLoadingIcon($(`#series-id${seriesId} [data-row="status"] .icon`));
  $.ajax({
    type: 'PUT',
    url: `/api/series/series/${seriesId}/toggle-monitor`,
    success: series => {
      // Show toast, toggle text and icon to show new status
      $(`#series-id${series.id} img`).toggleClass('unmonitored', series.status !== 'monitored');
      const statusRow = document.querySelector(`#series-id${series.id} td[data-row="status"] a`);
      if (series.status === 'monitored') {
        showInfoToast(`Started Monitoring ${series.name}`);
        statusRow.innerHTML = '<i class="ui eye outline green icon"></i>';
      } else if (series.status === 'unmonitored') {
        showInfoToast(`Stopped Monitoring ${series.name}`);
        statusRow.innerHTML = '<i class="ui eye slash outline yellow icon"></i>';
      } else {
        showInfoToast(`Disabled ${series.name}`);
        statusRow.innerHTML = '<i class="ui times circle outline red icon"></i>';
      }
      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Changing Status', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Submit an API request to update the config of the Series with the given ID.
 * @param {number} seriesId - ID of the Series to update. 
 * @param {Object} data - An `UpdateSeries` object to pass to the PATCH request.
 */
function _updateSeriesConfig(seriesId, data) {
  $.ajax({
    type: 'PATCH',
    url: `/api/series/series/${seriesId}`,
    data: JSON.stringify(data),
    contentType: 'application/json',
    success: () => showInfoToast('Updated Series'),
    error: response => showErrorToast({title: 'Error Updating Series', response}),
  });
}
const updateSeriesConfig = debounce((...args) => _updateSeriesConfig(...args));

/**
 * Submit an API request to begin Processing the Series with the given ID.
 * @param {number} seriesId - ID of the Series to process.
 */
function processSeries(seriesId) {
  const $icon = setLoadingIcon($(`#series-id${seriesId} td[data-row="process"] .icon`));
  $.ajax({
    type: 'POST',
    url: `/api/series/series/${seriesId}/process`,
    success: () => showInfoToast('Started Processing Series'),
    error: response => showErrorToast({title: 'Error Processing Series', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/** @type {number[]} */
let selectedSeries = [];
/** @type {number} */
let lastSelection;

/**
 * Toggle the series with the given ID's selection status. This modifies the
 * row's class, checkbox, and updates the `selectedSeries` list.
 * @param {number} seriesId - ID of the Series to toggle the selection of.
 * @param {boolean} [force] - Selection value to force for the given Series.
 * @param {PointerEvent} [event] - Click Event triggering the toggle.
 */
function toggleSeriesSelection(seriesId, force=undefined, event=undefined) {
  const _select = (id, status) => {
    $(`#series-id${id}`).toggleClass('selected', status);
    $(`#series-id${id} .checkbox[data-value="select"]`).checkbox(status ? 'check' : 'uncheck');
    // Add or remove from selection
    if (status) { selectedSeries.push(id); }
    else        { selectedSeries = selectedSeries.filter(id_ => id_ !== id); }
  }

  // Unselect if forced or Series is selected (and not being forced)
  if (force === false || (!force && selectedSeries.includes(seriesId))) {
    _select(seriesId,false);
  }
  // Select if forced or Series is not selected
  else if (force || !selectedSeries.includes(seriesId)) {
    _select(seriesId, true);

    // If shift was held, select all between this and last selection
    if (event !== undefined && event.shiftKey && lastSelection !== undefined) {
      const startIndex = allIds.indexOf(lastSelection);
      const endIndex = allIds.indexOf(seriesId);
      if (startIndex < endIndex) {
        allIds.slice(startIndex, endIndex+1).forEach(id => _select(id, true));
      } else if (startIndex > endIndex) {
        allIds.slice(endIndex, startIndex+1).forEach(id => _select(id, true));
      }
    }
    lastSelection = seriesId;
  }

  // If any/none series are selected, ensure toolbar is proper state
  if (selectedSeries.length > 0) {
    $('#toolbar .item[data-action="edit"]').toggleClass('disabled', false);
    $('#toolbar .item[data-action="unselect"]').toggleClass('disabled', false);
  } else {
    $('#toolbar .item[data-action="edit"]').toggleClass('disabled', true);
    $('#toolbar .item[data-action="unselect"]').toggleClass('disabled', true);
  }
}

/** Toggle all currently displayed Series selection status. */
function toggleAllSelection() {
  $('#series-table tr')
    .each((index, row) => {
      toggleSeriesSelection(Number.parseInt(row.dataset.id))
    });
}

/** Unselect all currently displayed Series. */
function clearSelection() {
  $('#series-table tr')
    .each((index, row) => {
      toggleSeriesSelection(Number.parseInt(row.dataset.id), false)
    });
}

/**
 * Navigate to the Series page for the Series with the given ID. This only
 * navigates the page if no Series are selected.
 * @param {number} seriesId - ID of the Series to open the page of.
 */
function openSeries(seriesId) {
  if (selectedSeries.length === 0) {
    window.location.href = `/series/${seriesId}`;
  }
}

/**
 * 
 * @param {boolean} toggle New state of displaying count data.
 */
function toggleCounts(toggle) {
  // Write new state to the localstorage
  window.localStorage.setItem('home:include-counts', toggle);
  if (toggle) {
    document.querySelector('#toolbar .item[data-action="enable-counts"]').classList.add('invisible');
    document.querySelector('#toolbar .item[data-action="disable-counts"]').classList.remove('invisible');
  } else {
    document.querySelector('#toolbar .item[data-action="enable-counts"]').classList.remove('invisible');
    document.querySelector('#toolbar .item[data-action="disable-counts"]').classList.add('invisible');
  }
  getAllSeries();
}

/**
 * Populate a <tr> element whose base content is provided as `template` with the
 * data defined in the `Series` object `series`.
 * @param {Series} series - Series whose data is used to populate the row.
 * @param {HTMLTemplateElement} template - Template to clone and populate with
 * data.
 * @returns {HTMLElement} The populated HTML <tr> element which can be added to
 * the DOM.
 */
function _populateSeriesRow(series, template) {
  // Clone Template
  const row = template.content.cloneNode(true);

  // Add ID to row dataset (for querying)
  row.querySelector('tr').dataset.id = series.id;
  row.querySelector('tr').id = `series-id${series.id}`;

  // Determine maximum number of Cards based on libraries
  let maxCards = series.episode_count * (library_unique_cards ? series.libraries.length : 1);

  // Make row red / yellow depending on Card count
  if (series.card_count === 0 && series.episode_count > 0) {
    row.querySelector('td').classList.add('left', 'red', 'marked');
  } else if (maxCards - series.card_count > 0) {
    row.querySelector('td').classList.add('left', 'orange', 'marked'); 
  }

  // Add "select row" action to select cell
  row.querySelector('a[data-action="select"]').onclick = (event) => toggleSeriesSelection(series.id, undefined, event);

  // Link name cell to Series page
  // row.querySelector('td[data-row="name"] a').onclick = () => openSeries(series.id);
  row.querySelector('td[data-row="name"] a').href = `/series/${series.id}`;
  row.querySelector('td[data-row="name"]').dataset.sortValue = `_${series.sort_name}`; // Add _ so numbers are still parsed as text

  // Add Series Name
  row.querySelector('td[data-row="name"] [data-value="name"]').innerText = series.name;

  // Set poster image src
  const poster = row.querySelector('td[data-row="name"] img');
  poster.src = series.small_poster_url || `/assets/${series.id}/poster-750.jpg`;

  // Populate library dropdown
  if (series.libraries) {
    row.querySelector('.dropdown[data-value="libraries"] > input').value = series.libraries.map(library => `${library.interface}::${library.interface_id}::${library.name}`).join(',');
  }

  // Add unmonitored class if styling
  if (stylize_unmonitored_posters && series.status !== 'monitored') {
    poster.classList.add('unmonitored');
  }

  // Add year
  row.querySelector('td[data-row="year"').innerText = series.year;

  // Sort libraries on the number of libraries
  row.querySelector('td[data-row="libraries"]').dataset.sortValue = series.libraries.length;

  // Populate Card counts
  const includeCounts = window.localStorage.getItem('home:include-counts') === 'true' || false;
  if (includeCounts) {
    // Fill out Card and episode text
    row.querySelector('td[data-row="card_count"] span[data-value="card_count"]').innerText = `${series.card_count} / ${maxCards} Cards`;

    // Refresh Card data when the card count cell is clicked
    row.querySelector('td[data-row="card_count"] a').onclick = () => refreshCardData(series.id);

    // Populate progress bars
    row.querySelector('td[data-row="card_count"] .progress').dataset.value = `${Math.min(series.card_count, maxCards)},${Math.max(0, maxCards - series.card_count)}`;
    row.querySelector('td[data-row="card_count"] .progress').dataset.total = maxCards;
    row.querySelector('td[data-row="card_count"]').dataset.sortValue = Math.max(0, maxCards - series.card_count);
  } else {
    row.querySelector('td[data-row="card_count"]').remove();
  }

  // Toggle status when cell is clicked
  row.querySelector('td[data-row="status"] a').onclick = () => toggleMonitoredStatus(series.id);

  // Sort by monitored boolean status
  row.querySelector('td[data-row="status"]').dataset.sortValue = series.status;

  // Set icon for monitored cell
  if (series.status === 'monitored') {
    row.querySelector('td[data-row="status"] a').innerHTML = '<i class="ui eye outline green icon"></i>';
  } else if (series.status === 'unmonitored') {
    row.querySelector('td[data-row="status"] a').innerHTML = '<i class="ui eye slash outline yellow icon"></i>';
  } else {
    row.querySelector('td[data-row="status"] a').innerHTML = '<i class="ui times circle outline red icon"></i>';
  }

  // Process Series when process cell is clicked
  row.querySelector('td[data-row="process"] a').onclick = () => processSeries(series.id);

  return row;
}

/**
 * 
 * @param {Series} series - Series whose data is used to populate the card.
 * @param {HTMLTemplateElement} template - Template to clone and populate with
 * data.
 * @returns {HTMLElement} The populated HTML <div> element which can be added to
 * the DOM.
 */
function _populateSeriesCard(series, template) {
  const clone = template.content.cloneNode(true);

  // Set poster image src and alt text
  const img = clone.querySelector('img');
  img.src = series.small_poster_url || `/assets/${series.id}/poster-750.jpg`;

  // Grayscale if unmonitored (and enabled)
  if (stylize_unmonitored_posters && series.status !== 'monitored') {
    img.classList.add('unmonitored'); 
  }

  // Link name and poster to the Series page
  const as = clone.querySelectorAll('a');
  as[0].href = `/series/${series.id}`;
  as[1].href = `/series/${series.id}`;

  // Go to Series page on Enter event for keyboard navigation
  clone.querySelector('.text.content').addEventListener('keydown', event => {
    // Check if the pressed key is Enter (key code 13)
    if (event.keyCode === 13) { window.location.href = `/series/${series.id}`; }
  });

  // Populate title
  const title = clone.querySelector('.series-name');
  title.setAttribute('title', `${series.name} (${series.year})`);
  title.innerText = series.name;

  // Progress bar
  const includeCounts = window.localStorage.getItem('home:include-counts') === 'true' || false;
  const progressBar = clone.querySelector('.progress');
  if (includeCounts) {
    const cardVal = Math.min(series.card_count, series.episode_count);
    if (cardVal > 0) {
      if (series.status === 'monitored') {
        progressBar.setAttribute('data-value', `${cardVal},${series.episode_count-cardVal},0,0`);
      } else {
        progressBar.setAttribute('data-value', `0,0,${cardVal},${series.episode_count-cardVal}`);
      }
      progressBar.setAttribute('data-total', series.episode_count);
    }
  } else {
    progressBar.remove();
  }

  return clone;
}

let currentFilter = null;

/**
 * Submit an API request to get all the Series at the given page number and add
 * their content to the page.
 * @param {number} [page] - Page number of Series to load 
 * @param {boolean} [keepSelection=false] - Whether to keep the current selection of
 * Series.
 */
async function getAllSeries(page=undefined, keepSelection=false) {
  document.querySelector('#main-content .loader').style.display = 'block';
  // Get page from URL param if provided
  page = page || new URLSearchParams(window.location.search).get('page') || 1;

  // Get associated sort query param
  const sortParam = window.localStorage.getItem('sort-by') || 'alphabetical'

  // Determine API URL and queries based on the counts toggle
  const includeCounts = window.localStorage.getItem('home:include-counts') === 'true' || false;
  const apiUrl = includeCounts ? '/api/series/all-extended' : '/api/series/all';
  const params = new URLSearchParams({
    order_by: sortParam,
    size: '{{ preferences.home_page_size }}',
    page,
  });
  if (currentFilter) { params.append('filter', JSON.stringify(currentFilter)); }

  // Fade out existing posters
  if (!reduced_animations) {
    if (home_page_table_view) {
      $('#series-table tr').transition({animation: 'scale', interval: 10, reverse: true});
    } else {
      $('#series-list .card').transition({animation: 'scale', interval: 10, reverse: true});
    }
  }

  // Get this page of Series data
  /** @type {SeriesPage} */
  let allSeriesData = await fetch(`${apiUrl}?${params.toString()}`).then(resp => resp.json());
  // await queryLibraries();
  let allSeries = allSeriesData.items;
  allIds = allSeries.map(series => series.id);

  // Hide loader
  document.querySelector('#main-content .loader').style.display = 'none';

  // Create elements of each Series
  if (home_page_table_view) {
    const template = document.getElementById('series-row-template');
    // Display/hiden the card count column
    if (includeCounts) {
      document.querySelector('table th[data-column="card_count"]').style.removeProperty('display');
    } else {
      document.querySelector('table th[data-column="card_count"]').style.display = 'none';
    } 

    // Clear selected series if indicated
    if (!keepSelection) { selectedSeries = []; }

    // Generate table rows
    let rows = allSeries.map(series => _populateSeriesRow(series, template));
  
    // Add rows, transition them in (if enabled)
    document.getElementById('series-table').replaceChildren(...rows);
    if (!reduced_animations) {
      $('#series-table tr').transition({animation: 'scale', interval: 15});
    }
    if (includeCounts) {
      $('.progress').progress({duration: 1800});
    }

    // Set selected statuses
    selectedSeries.forEach(seriesId => {
      $(`#series-id${seriesId}`).toggleClass('selected', true);
      $(`#series-id${seriesId} .checkbox[data-value="select"]`).checkbox('check');
    });

    // Prevent the mouse down event from triggering to disable text selection for shift-clicking multiple rows
    $('#series-table').mousedown(function (event) { event.preventDefault(); });

    // Initialize library dropdown for each Series
    $('.ui.dropdown[data-value="libraries"]').dropdown({
      placeholder: 'None',
      clearable: false,
      useLabels: false,
      onChange: function(value, text, $selectedItem) {
        // Current value of the library dropdown
        let libraries = [];
        if (value) {
          libraries = value.split(',').map(libraryStr => {
            const libraryData = libraryStr.split('::');
            return {interface: libraryData[0], interface_id: libraryData[1], name: libraryData[2]};
          });
        }
        // Get series ID
        const seriesId = $selectedItem.closest('tr').data('id');
        updateSeriesConfig(seriesId, {libraries});
      },
    });
  } else {
    const template = document.getElementById('series-template');
    let allSeriesCards = allSeries.map(series => _populateSeriesCard(series, template));

    // Add new cards, transition them in (if enabled)
    document.getElementById('series-list').replaceChildren(...allSeriesCards);
    if (!reduced_animations) {
      $('#series-list .card').transition({animation: 'scale', interval: 15});
    }
    if (includeCounts) {
      $('.progress').progress({duration: 2000});
    }

    // Dim Series posters on hover
    $('.ui.cards .image').dimmer({on: 'ontouchstart' in document.documentElement ? 'click' : 'hover'});
  }

  // Update pagination
  updatePagination({
    paginationElementId: 'pagination',
    navigateFunction: getAllSeries,
    page: allSeriesData.page,
    pages: allSeriesData.pages,
    amountVisible: isSmallScreen() ? 5 : 25,
    hideIfSinglePage: false,
  });

  // Update page search param field for the current page
  const url = new URL(location.href);
  url.searchParams.set('page', page);
  history.pushState(null, '', url);

  // Refresh theme for any newly added HTML
  refreshTheme();
}


const statisticMap = [
  {description: 'Number of Series', dataValue: 'series'},
  {description: 'Number of Monitored Series', dataValue: 'monitored'},
  {description: 'Number of Unmonitored Series', dataValue: 'unmonitored'},
  {description: 'Number of Disabled Series', dataValue: 'disabled'},
  //
  {description: 'Number of Named Fonts', dataValue: 'fonts'},
  {description: 'Number of Templates', dataValue: 'templates'},
  {description: 'Number of Syncs', dataValue: 'syncs'},
  //
  {description: 'Number of Episodes', dataValue: 'episodes'},
  {description: 'Number of Title Cards', dataValue: 'title-cards'},
  {description: 'Number of loaded Title Cards', dataValue: 'loaded-title-cards'},
  //
  {description: 'File size of all Title Cards', dataValue: 'filesize'},
];

/** Get all statistics and load them into the DOM */
function getAllStatistics() {
  $.ajax({
    type: 'GET',
    url: '/api/statistics/system',
    /**
     * API call was successful, populate statistic elements.
     * @param {Statistic[]} statistics 
     */
    success: statistics => {
      statistics.forEach(statistic => {
        const map = statisticMap.filter(({description}) => statistic.description === description);
        if (!map || map.length === 0) { return; }

        const element = document.querySelector(`.statistics .statistic[data-value="${map[0].dataValue}"]`);
        if (element) {
          element.querySelector('.value').innerText = statistic.value_text;
          element.querySelector('.label').innerText = statistic.unit;
        }
      });
    },
  });
}

/** Initialize the page by querying for Series and statistics */
function initAll() {
  toggleCounts(window.localStorage.getItem('home:include-counts') === 'true'); // This calls getAllSeries
  getAllStatistics();
  // Initialize table sorting and dropdowns
  $('table').tablesort();
  $('.ui.dropdown').dropdown();
  initializeFilterTemplate();
}

const sortStates = {
  cards: ['cards',        'reverse-cards'],
  id:    ['reverse-id',   'id',],
  name:  ['alphabetical', 'reverse-alphabetical'],
  sync:  ['sync',         'sync'],
  year:  ['year',         'reverse-year'],
};
/**
 * Adjust how the Series are sorted on the home page. This updates the local
 * storage for the sort parameter, and re-queries the current page.
 * @param {"cards" | "id" | "name" | "sync" | "year"} sortBy - How to sort the
 * Series on the page.
 */
function sortSeries(sortBy) {
  // Get current sort state
  const currentSortState = window.localStorage.getItem('sort-by') || 'alphabetical';

  // Get new sort state, update local storage
  const newSortState = sortStates[sortBy][(sortStates[sortBy].indexOf(currentSortState) + 1) % sortStates[sortBy].length];
  window.localStorage.setItem('sort-by', newSortState);

  // Re-query current page if modified
  if (currentSortState !== newSortState) { getAllSeries(); }
}

/**
 * Submit an API request to change the status of all the currently selected Series.
 * @param {"monitored" | "unmonitored" | "disabled"} status The status to set
 * all the currently selected Series to.
 */
function batchChangeStatus(status) {
  if (selectedSeries.length === 0) { return; }

  const $icon = setLoadingIcon($('#toolbar [data-action="edit"] > .icon'));

  $.ajax({
    type: 'PATCH',
    url: `/api/series/batch/status/${status}`,
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: updatedSeries => {
      showInfoToast(`Updated the Status of ${updatedSeries.length} Series`);
      getAllSeries(undefined, false);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Updating Series', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Submit an API request to begin processing all the currently selected Series.
 */
function batchProcess() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'POST',
    url: '/api/series/batch/process',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: () => {
      showInfoToast(`Started Processing ${selectedSeries.length} Series`);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Processing Series', response}),
  });
}

/**
 * Submit an API request to load the Title Cards all the currently selected
 * Series.
 * @param {boolean} reload - Whether to force reload the Title Cards.
 */
function batchLoad(reload=false) {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'PUT',
    url: `/api/cards/batch/load?reload=${reload}`,
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: () => showInfoToast(`Loaded Title Cards`),
    error: response => showErrorToast({title: 'Error Loading Title Cards', response}),
  });
}

/**
 * Submit an API request to delete all the Episodes of all the currently
 * selected Series.
 */
function batchDeleteEpisodes() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'DELETE',
    url: '/api/episodes/batch/delete',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: actions => {
      showInfoToast(`Deleted Episodes and Title Cards`);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Deleting Episodes', response}),
  });
}

/**
 * Submit an API request to delete the Title Cards of all the currently selected
 * Series.
 */
function batchDeleteCards() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'DELETE',
    url: '/api/cards/batch',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: actions => {
      showInfoToast(`Deleted ${actions.deleted} Title Cards`);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Deleting Title Cards', response}),
  });
}

/**
 * Submit an API request to delete all the currently selected Series.
 */
function batchDeleteSeries() {
  if (selectedSeries.length === 0) { return; }
  $.ajax({
    type: 'DELETE',
    url: '/api/series/batch/delete',
    data: JSON.stringify(selectedSeries),
    contentType: 'application/json',
    success: () => {
      showInfoToast(`Deleted ${selectedSeries.length} Series`);
      getAllStatistics();
    },
    error: response => showErrorToast({title: 'Error Deleting Series', response}),
  });
}

/**
 * Change the global display style to the poster or tabular view. This submits
 * an API request and, if successful, reloads the page.
 * @param {"poster" | "table"} style 
 */
function toggleGlobalDisplayStyle(style) {
  $.ajax({
    type: 'PATCH',
    url: '/api/settings/update',
    data: JSON.stringify({home_page_table_view: style === 'table'}),
    contentType: 'application/json',
    success: () => location.reload(),
    error: response => showErrorToast({title: 'Error Changing View', response}),
  });
}

// Filter Functions ------------------------------------------------------------

/** "Live" update the title of the tab containing this filter name input. **/
function updateTitle(inputElement) {
  const tabName = inputElement.closest('.tab.segment').dataset.tab;
  document.querySelector(`#filter-modal .tabular.menu .item[data-tab="${tabName}"]`).innerText = inputElement.value;
}

/**
 * Add a new tab to the filter modal.
 * @param {SeriesFilter} filter Existing filter to populate the new tab from.
 * @returns {HTMLDivElement} Newly added tab.
 */
function addTab(filter=null) {
  // Determine tab number - check for existence in case a middle tab was deleted
  let tabNumber = document.querySelectorAll('#filter-modal .tabular.menu .item').length - 1;
  while (document.querySelector(`#filter-modal .tabular.menu .item[data-tab="tab${tabNumber}"]`)) {
    tabNumber += 1;
  }

  // Add new tab selector to menu, just before add tab item
  const $tabHeader = $('<div>', {
    class: 'item',
    'data-tab': 'tab' + tabNumber,
    text: filter?.name || 'New Filter',
  });
  $('#filter-modal .tabular.menu .item.add-tab').before($tabHeader);

  // Add blank tab
  const newTab = document.getElementById('blank-tab-template').content.cloneNode(true);
  newTab.querySelector('.tab').dataset.tab = 'tab' + tabNumber;
  if (filter) {
    newTab.querySelector('input[name="filter_name"]').value = filter.name;
  }
  document.querySelector('#filter-modal .content').appendChild(newTab);
  $('#filter-modal .tabular.menu .item').tab();

  const tabs = document.querySelectorAll('#filter-modal .content .tab.segment');
  return tabs[tabs.length - 1];
}

/**
 * Add a dropdown item (or header) to the dropdown.
 * @param {HTMLDivElement} element Dropdown menu which the item should be added
 * to as a child.
 * @param {ItemArgs} args Arguments for the new item.
 * @param {?string} args.className Class name of the new item.
 * @param {string} args.innerText Display text of the new item.
 * @param {?string} args.value Value of the item.
 */
function addDropdownItem(element, args) {
  // Get arguments
  const {className = 'item', innerText, value = null} = args;

  // Create element
  const newItem = document.createElement('div');
  newItem.className = className;
  newItem.innerText = innerText;
  if (value !== null) { newItem.dataset.value = value; }

  element.appendChild(newItem);
}

/**
 * Delete the Filter associated with the clicked button.
 * @param {HTMLButtonElement} deleteButton Button which was clicked.
 */
function deleteFilter(deleteButton) {
  const tabID = deleteButton.closest('.tab.segment').dataset.tab;
  document.querySelectorAll(`#filter-modal [data-tab="${tabID}"]`).forEach(tab => tab.remove());
  $('#filter-modal .tabular.menu .item').tab('change tab', 'tab0');
}

const filterSettings = [
  //      name                        value                     type
  ['Auto-Split Titles',         'auto_split_titles',      'boolean'         ],
  ['Card Filename Format',      'card_filename_format',   'nullable string' ],
  ['Card Type',                 'card_type',              'nullable string' ],
  ['Episode Data Source ID',    'data_source_id',         'nullable numeric'],
  ['Card Directory',            'directory',              'nullable string' ],
  ['Emby Database ID',          'emby_id',                'nullable string' ],
  ['Episode Text Format',       'episode_text_format',    'nullable string' ],
  ['Extras',                    'extras',                 'nullable list'   ],
  ['Hide Episode Text',         'hide_episode_text',      'nullable boolean'],
  ['Hide Season Text',          'hide_season_text',       'nullable boolean'],
  ['Series ID',                 'id',                     'numeric'         ],
  ['Image Source Priority',     'image_source_priority',  'list'            ],
  ['IMDb Database ID',          'imdb_id',                'nullable string' ],
  ['Font Color',                'font_color',             'nullable string' ],
  ['Font ID',                   'font_id',                'nullable numeric'],
  ['Font Interline Spacing',    'font_interline_spacing', 'nullable numeric'],
  ['Font Interword Spacing',    'font_interword_spacing', 'nullable numeric'],
  ['Font Kerning',              'font_kerning',           'nullable numeric'],
  ['Font Size',                 'font_size',              'nullable numeric'],
  ['Font Stroke Width',         'font_stroke_width',      'nullable numeric'],
  ['Font Title Case',           'font_title_case',        'nullable string' ],
  ['Font Vertical Shift',       'font_vertical_shift',    'nullable numeric'],
  ['Jellyfin Database ID',      'jellyfin_id',            'nullable string' ],
  ['List of Libraries',         'libraries',              'list'            ],
  ['Match Titles',              'match_titles',           'boolean'         ],
  ['Has Missing Title Cards',   'missing_cards',          'boolean',        ],
  ['Series Status',             'status',                 'string'          ],
  ['Series Name',               'name',                   'string'          ],
  ['Season Title List',         'season_titles',          'nullable list'   ],
  ['Localized Image Rejection', 'skip_localized_images',  'nullable boolean'],
  ['Sonarr Database ID',        'sonarr_id',              'nullable string' ],
  ['Sync ID',                   'sync_id',                'nullable numeric'],
  ['Enable Specials',           'sync_specials',          'nullable boolean'],
  ['TMDb Database ID',          'tmdb_id',                'nullable numeric'],
  ['List of Translations',      'translations',           'list'            ],
  ['TVDb Database ID',          'tvdb_id',                'nullable numeric'],
  ['TVRage Database ID',        'tvrage_id',              'nullable string' ],
  ['Unwatched Card Style',      'unwatched_style',        'nullable string' ],
  ['Per-Season Assets',         'use_per_season_assets',  'boolean'         ],
  ['Watched Card Style',        'watched_style',          'nullable string' ],
  ['Series Year',               'year',                   'numeric'         ],
  ['Has No Episodes',           'has_no_episodes',        'boolean'         ],
].sort((a, b) => a[0].localeCompare(b[0])).map(setting => {
  return { name: setting[0], value: setting[1], type: setting[2] };
});

const filterChoices = {
  'string': [
    {name: 'equals',              requiresInput: true},
    {name: 'does not equal',      requiresInput: true},
    {name: 'contains',            requiresInput: true},
    {name: 'does not contain',    requiresInput: true},
    {name: 'starts with',         requiresInput: true},
    {name: 'does not start with', requiresInput: true},
    {name: 'ends with',           requiresInput: true},
    {name: 'does not end with',   requiresInput: true},
    {name: 'matches',             requiresInput: true},
    {name: 'does not match',      requiresInput: true},
  ],
  'nullable string': [
    {name: 'equals',              requiresInput: true },
    {name: 'does not equal',      requiresInput: true },
    {name: 'contains',            requiresInput: true },
    {name: 'does not contain',    requiresInput: true },
    {name: 'starts with',         requiresInput: true },
    {name: 'does not start with', requiresInput: true },
    {name: 'ends with',           requiresInput: true },
    {name: 'does not end with',   requiresInput: true },
    {name: 'matches',             requiresInput: true },
    {name: 'does not match',      requiresInput: true },
    {name: 'is null',             requiresInput: false},
    {name: 'is not null',         requiresInput: false},
  ],
  'numeric': [
    {name: 'is less than',                requiresInput: true},
    {name: 'is less than or equal to',    requiresInput: true},
    {name: 'equals',                      requiresInput: true},
    {name: 'is greater than',             requiresInput: true},
    {name: 'is greater than or equal to', requiresInput: true},
  ],
  'nullable numeric': [
    {name: 'is less than',                requiresInput: true },
    {name: 'is less than or equal to',    requiresInput: true },
    {name: 'equals',                      requiresInput: true },
    {name: 'is greater than',             requiresInput: true },
    {name: 'is greater than or equal to', requiresInput: true },
    {name: 'is null',                     requiresInput: false},
    {name: 'is not null',                 requiresInput: false},
  ],
  'boolean': [
    {name: 'is true',  requiresInput: false},
    {name: 'is false', requiresInput: false},
  ],
  'nullable boolean': [
    {name: 'is true',     requiresInput: false},
    {name: 'is false',    requiresInput: false},
    {name: 'is null',     requiresInput: false},
    {name: 'is not null', requiresInput: false},
  ],
  'list': [
    {name: 'is empty',         requiresInput: false},
    {name: 'is not empty',     requiresInput: false},
    {name: 'includes',         requiresInput: true },
    {name: 'does not include', requiresInput: true },
  ],
  'nullable list': [
    {name: 'is empty',         requiresInput: false},
    {name: 'is not empty',     requiresInput: false},
    {name: 'includes',         requiresInput: true },
    {name: 'does not include', requiresInput: true },
    {name: 'is null',          requiresInput: false},
    {name: 'is not null',      requiresInput: false},
  ],
};


function updateConditions(obj) {
  // Disable and clear reference field until condition is selected
  const referenceField = $(obj).closest('.fields').find('.field[data-label="reference"]');
  referenceField.toggleClass('disabled', true);
  referenceField.find('input').val('');

  // No value means the field was cleared
  if (!obj.value) {
    // Clear condition dropdown
    $(obj).closest('.fields').find('[data-label="condition"] .ui.dropdown').dropdown({
      values: []
    });
    return;
  }

  // Get the type of the newly selected filter field
  const fieldType = filterSettings.find(filter => filter.value === obj.value).type;

  // Initialize associated dropdown with condition choices for this type
  $(obj).closest('.fields').find('[data-label="condition"] .ui.dropdown').dropdown({
    onChange: (condition, text, $selectedItem) => {
      // Enable/disable the dropdown based on the selected condition
      const requiresInput = filterChoices[fieldType].find(choice => choice.name === condition).requiresInput;
      $($selectedItem).closest('.fields').find('.field[data-label="reference"]').toggleClass('disabled', !requiresInput);
    },
    placeholder: 'Condition Type',
    values: filterChoices[fieldType].map(choice => {
      return {
        name: choice.name,
        value: choice.name,
        selected: false,
      };
    }),
  });
}

function initializeFilterTemplate() {
  const template = document.getElementById('filter-template').content;
  filterSettings.forEach(filter => {
    const item = document.createElement('div');
    item.className = 'item'; item.dataset.value = filter.value; item.innerText = filter.name;
    template.querySelector('.dropdown .menu').appendChild(item);
  });

  const filterData = JSON.parse(window.localStorage.getItem('home:filters'));
  const existingFilters = filterData?.filters || [];
  existingFilters.forEach(filter => {
    // Add blank tab for this filter
    const tab = addTab(filter);
  
    // Add each condition
    filter.conditions.forEach((condition, index) => {
      // Add new filter row for this condition
      const newFields = document.getElementById('filter-template').content.cloneNode(true);
  
      // Remove labels for all but the first condition
      if (index > 0) {
        newFields.querySelectorAll('.field label').forEach(label => label.remove());
      }
  
      // Initialize field
      newFields.querySelector('.field[data-label="field"] div.dropdown > input').value = condition.field;

      // Initialize condition items
      const fieldType = filterSettings.find(filter => filter.value === condition.field)?.type;
      if (!fieldType) { return; }

      filterChoices[fieldType].forEach(choice => {
        addDropdownItem(
          newFields.querySelector('.field[data-label="condition"] div.dropdown .menu'),
          {className: 'item', innerText: choice.name, value: choice.name}
        );
      });
      newFields.querySelector('.field[data-label="condition"] div.dropdown > input').value = condition.expression;
      if (condition.reference !== null) {
        newFields.querySelector('.field[data-label="reference"] input').value = condition.reference;
      }
      // Enable/disable reference field
      if (filterChoices[fieldType].find(choice => choice.name === condition.expression)?.requiresInput) {
        newFields.querySelector('.field[data-label="reference"]').classList.remove('disabled');
      }

      // Add to page so dropdowns can be populated
      tab.querySelector('.form').appendChild(newFields);
    });
  });
  $('#filter-modal div.dropdown').dropdown();

  // Set active tab
  if (filterData?.activeTab !== undefined) {
    $('#filter-modal .tabular.menu').tab('change tab', `tab${filterData.activeTab}`);
  }
}

function addFilterCondition(addButton, removeLabels=true) {
  const newFields = document.getElementById('filter-template').content.cloneNode(true);
  if (removeLabels) {
    newFields.querySelectorAll('.field label').forEach(label => label.remove());
  }

  // Add to page, initialize dropdowns
  addButton.closest('.tab.segment').querySelector('.form').appendChild(newFields);
  $('#filter-modal .form .dropdown').dropdown();
}

// Function to serialize form inputs into a list of objects
function serializeAllFilters() {
  const filters = [];
  let activeTab = null;

  // Serialize each tab
  document.querySelectorAll('#filter-modal .content .tab.segment').forEach((tab, index) => {
    const data = {
      name: tab.querySelector('input[name="filter_name"]').value,
      conditions: [],
    };

    // Update active tab number if needed
    if (activeTab === null && tab.classList.contains('active')) {
      activeTab = index;
    }

    // Loop through each group of fields and gather inputs
    tab.querySelectorAll('.fields').forEach((fieldDiv) => {
      // Get the values of all input fields
      const fieldInput = fieldDiv.querySelector('input[name="field"]');
      const conditionInput = fieldDiv.querySelector('input[name="condition"]');
      const referenceInput = fieldDiv.querySelector('input[name="reference"]');

      // An input is required if the reference field is not disabled
      const requiresInput = !fieldDiv.querySelector('.field[data-label="reference"]').className.includes('disabled');

      // Ensure all inputs exist and retrieve their values
      if (fieldInput && conditionInput && referenceInput) {
        const field = fieldInput.value,
          expression = conditionInput.value,
          reference = referenceInput.value || null;

        if (field && expression && (reference || !requiresInput)) {
          data.conditions.push({ field, expression, reference, });
        }
      }
    });

    filters.push(data);
  });

  // Add new filter data to local storage
  window.localStorage.setItem('home:filters', JSON.stringify({ filters, activeTab }));

  // Set current filter, re-query Series, hide the filter modal
  currentFilter = filters[activeTab];
  getAllSeries();
  $('#filter-modal').modal('hide');
}
