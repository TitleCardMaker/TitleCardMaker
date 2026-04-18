{% if False %}
import {
  Episode,
  Page,
  ReducedEpisodeData,
  ReturnUnloadedCardSchema,
  Series
} from './.types.js';
{% endif %}


/** Current page size for the Missing Title Cards section. */
let missingCardsPageSize = 100;


/**
 * Set the page size for the Missing Title Cards section and re-query page 1.
 * @param {number} size
 */
function setMissingCardsPageSize(size) {
  missingCardsPageSize = size;

  // Update active pill
  document.querySelectorAll('#missing-cards-size-filter .pill-filter-btn').forEach(btn => {
    btn.classList.toggle('active', Number(btn.dataset.value) === size);
  });

  queryMissingCards(1);
}


/** Current page size for the Unloaded Cards section. */
let unloadedCardsPageSize = 100;


/**
 * Set the page size for the Unloaded Cards section and re-query page 1.
 * @param {number} size
 */
function setUnloadedCardsPageSize(size) {
  unloadedCardsPageSize = size;

  document.querySelectorAll('#unloaded-cards-size-filter .pill-filter-btn').forEach(btn => {
    btn.classList.toggle('active', Number(btn.dataset.value) === size);
  });

  queryUnloadedCards(1);
}


/**
 * Format a season/episode number pair as a zero-padded code, e.g. "S01E03".
 * @param {number} season
 * @param {number} episode
 * @returns {string}
 */
function formatEpisodeCode(season, episode) {
  return `S${String(season).padStart(2, '0')}E${String(episode).padStart(2, '0')}`;
}


/**
 * Toggle the expanded detail panel inside a .missing-series-row.
 * @param {HTMLElement} panel - The detail panel element.
 * @param {HTMLElement} button - The expand/collapse button.
 */
function togglePanel(panel, button) {
  const isHidden = panel.style.display === 'none';
  panel.style.display = isHidden ? '' : 'none';
  const icon = button.querySelector('i');
  if (icon) {
    icon.className = isHidden ? 'chevron up icon' : 'chevron down icon';
  }
}


/**
 * Show an empty state inside a container element.
 * @param {HTMLElement} container
 * @param {string} icon - Fomantic icon class string (e.g. "check circle outline").
 * @param {string} title
 * @param {string} desc
 */
function showEmptyState(container, icon, title, desc) {
  container.innerHTML = `
    <div class="missing-empty-state">
      <i class="${icon} icon"></i>
      <div class="missing-empty-title">${title}</div>
      <div class="missing-empty-desc">${desc}</div>
    </div>`;
}


/**
 * Update the header count badge for a given section.
 * @param {string} badgeId
 * @param {number} count
 */
function updateHeaderBadge(badgeId, count) {
  const badge = document.getElementById(badgeId);
  if (!badge) return;
  if (count > 0) {
    badge.textContent = count;
    badge.style.display = '';
  } else {
    badge.style.display = 'none';
  }
}


/**
 * Query all Episodes which are missing a Card and display them in the panel.
 * @param {number} page
 */
function queryMissingCards(page=1) {
  $.ajax({
    type: 'GET',
    url: `/api/v2/missing/cards?page=${page}&size=${missingCardsPageSize}`,
    /**
     * @param {Page<ReducedEpisodeData>} episodeData
     */
    success: episodeData => {
      const list = document.getElementById('missing-cards-list');

      /** @type {Object.<number, ReducedEpisodeData[]>} */
      const groupedEpisodes = {};
      episodeData.items.forEach(episode => {
        if (!groupedEpisodes[episode.series_id]) {
          groupedEpisodes[episode.series_id] = [];
        }
        groupedEpisodes[episode.series_id].push(episode);
      });

      const seriesCount = Object.keys(groupedEpisodes).length;
      updateHeaderBadge('missing-cards-header-count', seriesCount);

      list.replaceChildren();

      if (episodeData.items.length === 0) {
        showEmptyState(
          list,
          'check circle outline',
          'No missing Title Cards',
          'All tracked Episodes have Title Cards created.',
        );
      } else {
        const rowTemplate = document.getElementById('missing-card-template');
        const pillTemplate = document.getElementById('missing-episode-template');

        for (const [series_id, episodes] of Object.entries(groupedEpisodes)) {
          const frag = rowTemplate.content.cloneNode(true);
          const rowEl = frag.querySelector('.missing-series-row');

          rowEl.querySelector('.missing-series-poster').src = episodes[0].series.small_poster_url;
          rowEl.querySelector('[data-value="name"]').innerText = episodes[0].series.name;
          rowEl.querySelector('[data-row="count"]').innerText = episodes.length;

          // Click on header (but not on a button) → navigate to series page
          rowEl.querySelector('.missing-series-header').addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
              window.location.href = `/series/${series_id}#files`;
            }
          });

          // Populate episode pills
          const pillsContainer = rowEl.querySelector('[data-row="episodes-container"]');
          episodes.forEach(episode => {
            const pillFrag = pillTemplate.content.cloneNode(true);
            pillFrag.querySelector('[data-row="episode-info"]').innerText =
              formatEpisodeCode(episode.season_number, episode.episode_number);
            pillFrag.querySelector('[data-row="episode-title"]').innerText = episode.title;
            pillsContainer.appendChild(pillFrag);
          });

          // Expand / collapse
          const detailPanel = rowEl.querySelector('[data-row="detail"]');
          rowEl.querySelector('[data-action="expand"]').addEventListener('click', (e) => {
            e.stopPropagation();
            togglePanel(detailPanel, e.currentTarget);
          });

          list.appendChild(rowEl);
        }
      }

      updatePagination({
        paginationElementId: 'card-pagination',
        navigateFunction: queryMissingCards,
        page: episodeData.page,
        pages: episodeData.pages,
        amountVisible: isSmallScreen() ? 5 : 10,
        hideIfSinglePage: true,
      });

      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Querying Missing Cards', response}),
  });
}


/**
 * Query all Series which are missing logos and display them in the panel.
 */
function queryMissingLogos() {
  $.ajax({
    url: '/api/v2/missing/logos',
    /**
     * @param {Series[]} allSeries
     */
    success: allSeries => {
      const list = document.getElementById('missing-logos-list');
      list.replaceChildren();

      updateHeaderBadge('missing-logos-header-count', allSeries.length);

      if (allSeries.length === 0) {
        showEmptyState(
          list,
          'check circle outline',
          'No missing Logos',
          'All Series have a logo available.',
        );
      } else {
        const template = document.getElementById('missing-logo-template');

        allSeries.forEach(series => {
          const frag = template.content.cloneNode(true);
          const item = frag.querySelector('.missing-logo-item');

          item.href = `/series/${series.id}#files`;
          item.querySelector('.missing-series-poster').src = series.small_poster_url;
          item.querySelector('[data-value="name"]').innerText = series.name;

          list.appendChild(item);
        });
      }

      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Querying Missing Logos', response}),
  });
}


/**
 * Query all Cards without a Loaded record and display them in the panel.
 * @param {number} page
 */
function queryUnloadedCards(page=1) {
  $.ajax({
    type: 'GET',
    url: `/api/v2/missing/cards-without-loaded?page=${page}&size=${unloadedCardsPageSize}`,
    /**
     * @param {Page<ReturnUnloadedCardSchema>} cardData
     */
    success: cardData => {
      const list = document.getElementById('unloaded-cards-list');

      /** @type {Object.<number, ReturnUnloadedCardSchema[]>} */
      const groupedCards = {};
      cardData.items.forEach(card => {
        if (!groupedCards[card.series_id]) {
          groupedCards[card.series_id] = [];
        }
        groupedCards[card.series_id].push(card);
      });

      const seriesCount = Object.keys(groupedCards).length;
      updateHeaderBadge('unloaded-cards-header-count', seriesCount);

      list.replaceChildren();

      if (cardData.items.length === 0) {
        showEmptyState(
          list,
          'check circle outline',
          'No unloaded Cards',
          'All Title Cards have been loaded to your media server.',
        );
      } else {
        const rowTemplate = document.getElementById('unloaded-card-template');
        const thumbTemplate = document.getElementById('unloaded-card-image-template');

        for (const [series_id, cards] of Object.entries(groupedCards)) {
          const frag = rowTemplate.content.cloneNode(true);
          const rowEl = frag.querySelector('.missing-series-row');

          rowEl.querySelector('.missing-series-poster').src = `/assets/${series_id}/poster-750.jpg`;
          rowEl.querySelector('[data-value="name"]').innerText = cards[0].series.name;
          rowEl.querySelector('[data-row="count"]').innerText = cards.length;

          // Click on header (but not on a button) → navigate to series page
          rowEl.querySelector('.missing-series-header').addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
              window.location.href = `/series/${series_id}#files`;
            }
          });

          // Populate card thumbnails
          const cardsContainer = rowEl.querySelector('[data-row="cards-container"]');
          cards.forEach(card => {
            const thumbFrag = thumbTemplate.content.cloneNode(true);
            thumbFrag.querySelector('img').src = card.file_url;
            thumbFrag.querySelector('[data-row="episode-info"]').innerText = card.episode
              ? formatEpisodeCode(card.episode.season_number, card.episode.episode_number)
              : '—';
            cardsContainer.appendChild(thumbFrag);
          });

          // Expand / collapse
          const detailPanel = rowEl.querySelector('[data-row="detail"]');
          rowEl.querySelector('[data-action="expand"]').addEventListener('click', (e) => {
            e.stopPropagation();
            togglePanel(detailPanel, e.currentTarget);
          });

          // Load cards for this series
          rowEl.querySelector('[data-action="load"]').addEventListener('click', (e) => {
            e.stopPropagation();
            loadSeriesCards(series_id, e.currentTarget);
          });

          list.appendChild(rowEl);
        }
      }

      updatePagination({
        paginationElementId: 'unloaded-pagination',
        navigateFunction: queryUnloadedCards,
        page: cardData.page,
        pages: cardData.pages,
        amountVisible: isSmallScreen() ? 5 : 10,
        hideIfSinglePage: false,
      });

      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Querying Unloaded Cards', response}),
  });
}


/**
 * Load all unloaded Cards for a specific Series.
 * @param {number} seriesId
 * @param {HTMLElement} button - The Load button element.
 */
function loadSeriesCards(seriesId, button) {
  const $icon = setLoadingIcon($(button.querySelector('i')));
  button.disabled = true;

  $.ajax({
    type: 'PUT',
    url: `/api/v2/cards/series/${seriesId}/load`,
    success: () => {
      showInfoToast('Cards loaded successfully');
      queryUnloadedCards();
    },
    error: response => showErrorToast({title: 'Error Loading Cards', response}),
    complete: () => {
      removeLoadingIcon($icon);
      button.disabled = false;
    },
  });
}


function initAll() {
  queryMissingCards();
  queryMissingLogos();
  queryUnloadedCards();
}
