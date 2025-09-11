{% if False %}
import {
  Page,
  TitleCardExtended,
} from './.types.js';
{% endif %}

/**
 * Convert the given UTC date to the local time.
 * @param {Date} date Date being converted. Assumed to be UTC.
 * @returns {Date} 
 */
function _utcToLocal(date) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60 * 1000);
}

function storeLastLoginTime() {
  localStorage.setItem('recent:lastLogin', new Date().toISOString());
}

function getLastLoginTime() {
  const lastLogin = localStorage.getItem('recent:lastLogin');
  if (!lastLogin) {
    return new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  }
  return lastLogin;
}

/**
 * Get the selected time period and calculate the appropriate date.
 * @returns {Date} The calculated date based on the selected time period.
 */
function getSelectedDate() {
  const timePeriod = $('#time-period-dropdown').dropdown('get value');
  
  switch (timePeriod) {
    case '6h':
      return new Date(Date.now() - 6 * 60 * 60 * 1000);
    case '24h':
      return new Date(Date.now() - 24 * 60 * 60 * 1000);
    case '1w':
      return new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    case 'custom':
      return $('#after').calendar('get date') || new Date(Date.now() - 24 * 60 * 60 * 1000);
    default:
      return new Date(Date.now() - 24 * 60 * 60 * 1000);
  }
}

/**
 * Reset the filter form to default values.
 */
function resetFilters() {
  $('#recent-filters').form('clear');
  $('#time-period-dropdown').dropdown('set selected', '24h');
  $('#time-period-dropdown').dropdown('set value', '24h');
  $('#time-period-dropdown').dropdown('set text', 'Last 24 hours');
  $('#custom-date-field').hide();
  
  // Reset series display state
  document.getElementById('series-empty-state').style.display = 'none';
  document.querySelector('.cards[data-label="series"]').style.display = 'block';
  document.getElementById('series-pagination').style.display = 'block';
}

/**
 * Query the given page of recently created Title Cards.
 * @param {number} page Page number of recent Cards to display.
 */
function queryLatestCards(page=1) {
  // Submit API request
  const args = new URLSearchParams({
    after: getSelectedDate().toISOString(),
    page: page,
    size: 8,
  });

  $.ajax({
    type: 'GET',
    url: `/api/v2/cards/recent?${args.toString()}`,
    /**
     * Recent cards queried, populate card elements on the page.
     * @param {Page<TitleCardExtended>} cardPage Page of recent Title Cards.
     */
    success: cardPage => {
      const template = document.getElementById('card-template');

      const cards = cardPage.items.map(card => {
        const base = template.content.cloneNode(true);

        // Populate template
        base.querySelector('.card').href = `/series/${card.series_id}`;
        base.querySelector('.image img').src = card.file_url;
        base.querySelector('[data-label="series_name"]').innerText = card.series?.name;
        base.querySelector('[data-label="episode"]').innerText = card.episode
          ? `Season ${card.episode.season_number} Episode ${card.episode.episode_number}`
          : 'No associated episode';
        base.querySelector('[data-label="creation"]').innerText = timeDiffString(
          _utcToLocal(new Date(card.created)), undefined, undefined, 1,
        )

        return base;
      });

      // Add elements to the page
      document.getElementById('loader')?.remove();
      
      if (cards.length === 0) {
        // Show empty state message
        document.getElementById('empty-state').style.display = '';
        document.querySelector('.cards[data-label="cards"]').style.display = 'none';
        document.getElementById('card-pagination').style.display = 'none';
      } else {
        // Hide empty state and show cards
        document.getElementById('empty-state').style.display = 'none';
        document.querySelector('.cards[data-label="cards"]').style.display = '';
        document.getElementById('card-pagination').style.display = '';
        
        document.querySelector('.cards[data-label="cards"]').replaceChildren(...cards);

        // Update pagination
        updatePagination({
          paginationElementId: 'card-pagination',
          navigateFunction: queryLatestCards,
          page: cardPage.page,
          pages: cardPage.pages,
          amountVisible: isSmallScreen() ? 5 : 15,
          hideIfSinglePage: false,
        });
      }
    },
    error: response => {
      showErrorToast({response, title: 'Error Querying Recent Cards'});
      // Show empty state on error
      document.getElementById('loader')?.remove();
      document.getElementById('empty-state').style.display = 'block';
      document.querySelector('.cards[data-label="cards"]').style.display = 'none';
      document.getElementById('card-pagination').style.display = 'none';
    },
  });
}

/**
 * Query the given page of recently added Series.
 * @param {number} page Page number of recent Series to display.
 */
function queryLatestSeries(page=1) {
  // Submit API request
  const args = new URLSearchParams({
    after: getSelectedDate().toISOString(),
    page: page,
    size: 8,
  });

  $.ajax({
    type: 'GET',
    url: `/api/v2/series/recent?${args.toString()}`,
    /**
     * Recent series queried, populate series elements on the page.
     * @param {Page[Series]} seriesPage Page of recent Series.
     */
    success: seriesPage => {
      const template = document.getElementById('series-template');

      const series = seriesPage.items.map(series => {
        const base = template.content.cloneNode(true);

        // Populate template
        base.querySelector('.card').href = `/series/${series.id}`;
        base.querySelector('.image img').src = series.poster_url;
        base.querySelector('[data-label="series_name"]').innerText = series.name;
        base.querySelector('[data-label="year"]').innerText = series.year;
        base.querySelector('[data-label="creation"]').innerText = timeDiffString(
          _utcToLocal(new Date(series.created)), undefined, undefined, 1,
        );
        base.querySelector('[data-label="card_count"]').innerText = series.card_count || 'No';

        return base;
      });

      // Add elements to the page
      document.getElementById('series-loader')?.remove();
      console.log(series);
      
      if (series.length === 0) {
        // Show empty state message
        document.getElementById('series-empty-state').style.display = '';
        document.querySelector('.cards[data-label="series"]').style.display = 'none';
        document.getElementById('series-pagination').style.display = 'none';
      } else {
        // Hide empty state and show series
        document.getElementById('series-empty-state').style.display = 'none';
        document.querySelector('.cards[data-label="series"]').style.display = '';
        document.getElementById('series-pagination').style.display = '';
        
        document.querySelector('.cards[data-label="series"]').replaceChildren(...series);

        // Update pagination
        updatePagination({
          paginationElementId: 'series-pagination',
          navigateFunction: queryLatestSeries,
          page: seriesPage.page,
          pages: seriesPage.pages,
          amountVisible: isSmallScreen() ? 5 : 15,
          hideIfSinglePage: false,
        });
      }
    },
    error: response => {
      showErrorToast({response, title: 'Error Querying Recent Series'});
      // Show empty state on error
      document.getElementById('series-loader')?.remove();
      document.getElementById('series-empty-state').style.display = 'block';
      document.querySelector('.cards[data-label="series"]').style.display = 'none';
      document.getElementById('series-pagination').style.display = 'none';
    },
  });
}

function initAll() {
  // Initialize dropdown
  $('.ui.dropdown').dropdown();
  
  // Initialize calendar with last login time
  getLastLoginTime();
  $('.ui.calendar').calendar({
    initialDate: getLastLoginTime(),
    maxDate: new Date(),
    onChange: () => {
      // Reset display state when date changes
      document.getElementById('empty-state').style.display = 'none';
      document.querySelector('.cards[data-label="cards"]').style.display = 'block';
      document.getElementById('card-pagination').style.display = 'block';
      document.getElementById('series-empty-state').style.display = 'none';
      document.querySelector('.cards[data-label="series"]').style.display = 'block';
      document.getElementById('series-pagination').style.display = 'block';
      queryLatestCards();
      queryLatestSeries();
    },
  });

  // Handle time period dropdown changes
  $('#time-period-dropdown').dropdown({
    onChange: function(value) {
      if (value === 'custom') {
        $('#custom-date-field').show();
      } else {
        $('#custom-date-field').hide();
        // Reset display state when period changes
        document.getElementById('empty-state').style.display = 'none';
        document.querySelector('.cards[data-label="cards"]').style.display = 'block';
        document.getElementById('card-pagination').style.display = 'block';
        document.getElementById('series-empty-state').style.display = 'none';
        document.querySelector('.cards[data-label="series"]').style.display = 'block';
        document.getElementById('series-pagination').style.display = 'block';
        queryLatestCards();
        queryLatestSeries();
      }
    }
  });

  // Query recent cards and series on page load
  queryLatestCards();
  queryLatestSeries();

  // Store the most recent login time
  storeLastLoginTime();
}
