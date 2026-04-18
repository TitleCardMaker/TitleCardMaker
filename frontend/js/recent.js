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
 * Activate a time-period pill for the given section prefix and trigger a
 * query. Also shows/hides the custom date picker for that section.
 * @param {'cards'|'series'} prefix Section identifier.
 * @param {'6h'|'24h'|'1w'|'custom'} value Selected period value.
 */
function setTimePeriod(prefix, value) {
  // Update active pill
  document.querySelectorAll(`#${prefix}-time-filter .time-filter-btn`).forEach(btn => {
    btn.classList.toggle('active', btn.dataset.value === value);
  });

  // Show/hide custom date picker
  const customField = document.getElementById(`${prefix}-custom-date`);
  if (value === 'custom') {
    customField.style.display = '';
  } else {
    customField.style.display = 'none';
    // Trigger query immediately for non-custom values
    if (prefix === 'cards') { queryLatestCards(); }
    else                     { queryLatestSeries(); }
  }
}

/**
 * Return the cutoff Date for the given section based on its active pill.
 * @param {'cards'|'series'} prefix
 * @returns {Date}
 */
function getSelectedDate(prefix) {
  const activeBtn = document.querySelector(`#${prefix}-time-filter .time-filter-btn.active`);
  const value = activeBtn?.dataset.value ?? '24h';

  switch (value) {
    case '6h':    return new Date(Date.now() - 6 * 60 * 60 * 1000);
    case '24h':   return new Date(Date.now() - 24 * 60 * 60 * 1000);
    case '1w':    return new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    case 'custom':
      return $(`#${prefix}-after`).calendar('get date')
        ?? new Date(Date.now() - 24 * 60 * 60 * 1000);
    default:      return new Date(Date.now() - 24 * 60 * 60 * 1000);
  }
}

/**
 * Query the given page of recently created Title Cards.
 * @param {number} [page=1]
 */
function queryLatestCards(page=1) {
  const args = new URLSearchParams({
    after: getSelectedDate('cards').toISOString(),
    page,
    size: 8,
  });

  $.ajax({
    type: 'GET',
    url: `/api/v2/cards/recent?${args.toString()}`,
    /** @param {import('./.types.js').Page<import('./.types.js').TitleCardExtended>} cardPage */
    success: cardPage => {
      const template = document.getElementById('card-template');

      const cards = cardPage.items.map(card => {
        const base = template.content.cloneNode(true);
        base.querySelector('.card').href = `/series/${card.series_id}`;
        base.querySelector('.image img').src = card.file_url;
        base.querySelector('[data-label="series_name"]').innerText = card.series?.name;
        base.querySelector('[data-label="episode"]').innerText = card.episode
          ? `Season ${card.episode.season_number} Episode ${card.episode.episode_number}`
          : 'No associated episode';
        base.querySelector('[data-label="creation"]').innerText = timeDiffString(
          _utcToLocal(new Date(card.created)), undefined, undefined, 1,
        );
        return base;
      });

      document.getElementById('loader')?.remove();

      const isEmpty = cards.length === 0;
      document.getElementById('empty-state').style.display           = isEmpty ? '' : 'none';
      document.querySelector('.cards[data-label="cards"]').style.display = isEmpty ? 'none' : '';
      document.getElementById('card-pagination').style.display       = isEmpty ? 'none' : '';

      if (!isEmpty) {
        document.querySelector('.cards[data-label="cards"]').replaceChildren(...cards);
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
      document.getElementById('loader')?.remove();
      document.getElementById('empty-state').style.display               = '';
      document.querySelector('.cards[data-label="cards"]').style.display = 'none';
      document.getElementById('card-pagination').style.display           = 'none';
    },
  });
}

/**
 * Query the given page of recently added Series.
 * @param {number} [page=1]
 */
function queryLatestSeries(page=1) {
  const args = new URLSearchParams({
    after: getSelectedDate('series').toISOString(),
    page,
    size: 8,
  });

  $.ajax({
    type: 'GET',
    url: `/api/v2/series/recent?${args.toString()}`,
    /** @param {import('./.types.js').Page<import('./.types.js').Series>} seriesPage */
    success: seriesPage => {
      const template = document.getElementById('series-template');

      const series = seriesPage.items.map(s => {
        const base = template.content.cloneNode(true);
        base.querySelector('.card').href = `/series/${s.id}`;
        base.querySelector('.image img').src = s.poster_url;
        base.querySelector('[data-label="series_name"]').innerText = s.name;
        base.querySelector('[data-label="creation"]').innerText = timeDiffString(
          _utcToLocal(new Date(s.created)), undefined, undefined, 1,
        );
        base.querySelector('[data-label="card_count"]').innerText = `${s.card_count || 'No'} Cards`;
        return base;
      });

      document.getElementById('series-loader')?.remove();

      const isEmpty = series.length === 0;
      document.getElementById('series-empty-state').style.display            = isEmpty ? '' : 'none';
      document.querySelector('.cards[data-label="series"]').style.display    = isEmpty ? 'none' : '';
      document.getElementById('series-pagination').style.display             = isEmpty ? 'none' : '';

      if (!isEmpty) {
        document.querySelector('.cards[data-label="series"]').replaceChildren(...series);
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
      document.getElementById('series-loader')?.remove();
      document.getElementById('series-empty-state').style.display             = '';
      document.querySelector('.cards[data-label="series"]').style.display     = 'none';
      document.getElementById('series-pagination').style.display              = 'none';
    },
  });
}

function initAll() {
  // Initialize custom date calendars (one per section)
  const calendarConfig = (prefix, queryFn) => ({
    initialDate: new Date(getLastLoginTime()),
    maxDate: new Date(),
    onChange: () => queryFn(),
  });

  $('#cards-after').calendar(calendarConfig('cards', queryLatestCards));
  $('#series-after').calendar(calendarConfig('series', queryLatestSeries));

  // Query on load
  queryLatestCards();
  queryLatestSeries();

  // Store the most recent login time
  storeLastLoginTime();
}
