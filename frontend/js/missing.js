{% if False %}
import {
  Episode,
  Page,
  ReducedEpisodeData,
  ReturnUnloadedCardSchema,
  Series
} from './.types.js';
{% endif %}


/**
 * Query all Episodes which are missing a Card and display them all on the page.
 */
function queryMissingCards(page=1) {
  $.ajax({
    type: 'GET',
    url: `/api/v2/missing/cards?page=${page}&size=100`,
    /**
     * Missing Episodes queried, populate table.
     * @param {Page<ReducedEpisodeData>} episodeData Episodes missing Cards.
     */
    success: episodeData => {
      /** @type {Object.<number, Episode[]>} Group Episodes by Series*/
      const groupedEpisodes = {};
      episodeData.items.forEach(episode => {
        if (!groupedEpisodes[episode.series_id]) {
          groupedEpisodes[episode.series_id] = [];
        }
        groupedEpisodes[episode.series_id].push(episode);
      });

      // Templates
      const table = document.getElementById('missing-cards');
      const tbody = table.querySelector('tbody');

      // Clear all existing content and reset any expanded states
      tbody.replaceChildren();

      const template = document.getElementById('missing-card-template');
      const detailTemplate = document.getElementById('missing-card-detail-template');
      const episodeTemplate = document.getElementById('missing-episode-template');

      // Add rows to the table
      for (const [series_id, episodes] of Object.entries(groupedEpisodes)) {
        // Create main series row
        const row = template.content.cloneNode(true);
        row.querySelector('td[data-row="series"]').onclick = () => window.location.href = `/series/${series_id}#files`;
        row.querySelector('td[data-row="series"] [data-value="name"]').innerText = episodes[0].series.name;
        row.querySelector('td[data-row="series"] img').src = episodes[0].series.small_poster_url;
        row.querySelector('td[data-row="count"]').innerText = episodes.length;
        
        // Add expand/collapse functionality
        const expandButton = row.querySelector('[data-action="expand"]');
        expandButton.onclick = (event) => {
          event.stopPropagation();
          toggleMissingEpisodes(series_id, episodes, expandButton);
        };
        
        tbody.appendChild(row);

        // Create detail row for episodes
        const detailRow = detailTemplate.content.cloneNode(true);
        const detailTr = detailRow.querySelector('tr');
        detailTr.id = `missing-detail-${series_id}`;
        const episodesContainer = detailTr.querySelector('[data-row="episodes-container"]');
        
        // Populate episodes
        episodes.forEach(episode => {
          const episodeElement = episodeTemplate.content.cloneNode(true);
          episodeElement.querySelector('[data-row="episode-info"]').innerText = 
            `Season ${episode.season_number} Episode ${episode.episode_number}`;
          episodeElement.querySelector('[data-row="episode-title"]').innerText = episode.title;
          episodesContainer.appendChild(episodeElement);
        });
        
        tbody.appendChild(detailTr);
      }

      // Update pagination
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
 * Toggle the display of missing episodes for a specific series.
 * @param {number} seriesId - The series ID to toggle.
 * @param {Episode[]} episodes - The episodes for this series.
 * @param {HTMLElement} button - The expand/collapse button.
 */
function toggleMissingEpisodes(seriesId, episodes, button) {
  const detailRow = document.getElementById(`missing-detail-${seriesId}`);
  const icon = button.querySelector('i');
  
  if (detailRow.style.display === 'none') {
    detailRow.style.display = '';
    icon.className = 'chevron up icon';
  } else {
    detailRow.style.display = 'none';
    icon.className = 'chevron down icon';
  }
}

/**
 * Query all Series which are missing logos and display them on the page.
 */
function queryMissingLogos() {
  $.ajax({
    url: '/api/v2/missing/logos',
    /**
     * Missing logos queried, populate the table.
     * @param {Series[]} allSeries - List of Series which are missing logos.
     */
    success: allSeries => {
      // Templates
      const template = document.getElementById('missing-logo-template');
      const table = document.getElementById('missing-logos');

      allSeries.forEach(series => {
        const row = template.content.cloneNode(true);

        row.querySelector('td[data-row="series"]').onclick = () => window.location.href = `/series/${series.id}#files`;
        row.querySelector('td[data-row="series"] [data-value="name"]').innerText = series.name;
        row.querySelector('td[data-row="series"] img').src = series.small_poster_url;

        row.querySelector('td[data-row="filename"]').innerText = 'logo.png';

        table.appendChild(row);
      });

      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Querying Missing Logos', response}),
  });
}

/**
 * Query all Cards that do not have an associated Loaded record and display them on the page.
 */
function queryUnloadedCards(page=1) {
  $.ajax({
    type: 'GET',
    url: `/api/v2/missing/cards-without-loaded?page=${page}&size=100`,
    /**
     * Unloaded Cards queried, populate table.
     * @param {Page<ReturnUnloadedCardSchema>} cardData Cards without loaded records.
     */
    success: cardData => {
      /** @type {Object.<number, ReturnUnloadedCardSchema[]>} Group Cards by Series*/
      const groupedCards = {};
      cardData.items.forEach(card => {
        if (!groupedCards[card.series_id]) {
          groupedCards[card.series_id] = [];
        }
        groupedCards[card.series_id].push(card);
      });

      // Templates
      const table = document.getElementById('unloaded-cards');
      const tbody = table.querySelector('tbody');

      // Clear all existing content and reset any expanded states
      tbody.replaceChildren();

      const template = document.getElementById('unloaded-card-template');
      const detailTemplate = document.getElementById('unloaded-card-detail-template');
      const imageTemplate = document.getElementById('unloaded-card-image-template');

      // Add rows to the table
      for (const [series_id, cards] of Object.entries(groupedCards)) {
        // Create main series row
        const row = template.content.cloneNode(true);
        row.querySelector('td[data-row="series"]').onclick = () => window.location.href = `/series/${series_id}#files`;
        row.querySelector('td[data-row="series"] [data-value="name"]').innerText = cards[0].series.name;
        row.querySelector('td[data-row="series"] img').src = `/assets/${series_id}/poster-750.jpg`;
        row.querySelector('td[data-row="count"]').innerText = cards.length;

        // Add expand/collapse functionality
        const expandButton = row.querySelector('[data-action="expand"]');
        expandButton.onclick = (event) => {
          event.stopPropagation();
          toggleUnloadedCards(series_id, cards, expandButton);
        };

        // Add load cards functionality
        const loadButton = row.querySelector('[data-action="load"]');
        loadButton.onclick = (event) => {
          event.stopPropagation();
          loadSeriesCards(series_id, loadButton);
        };

        tbody.appendChild(row);

        // Create detail row for cards
        const detailRow = detailTemplate.content.cloneNode(true);
        const detailTr = detailRow.querySelector('tr');
        detailTr.id = `unloaded-detail-${series_id}`;
        const cardsContainer = detailTr.querySelector('[data-row="cards-container"]');
        
        // Populate cards
        cards.forEach(card => {
          const cardElement = imageTemplate.content.cloneNode(true);
          cardElement.querySelector('.image img').src = card.file_url;
          cardElement.querySelector('[data-row="episode-info"]').innerText = 
            card.episode
            ? `Season ${card.episode.season_number} Episode ${card.episode.episode_number}`
            : 'No Episode Data'
          ;
          cardsContainer.appendChild(cardElement);
        });

        tbody.appendChild(detailTr);
      }

      // Update pagination
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
 * Toggle the display of unloaded cards for a specific series.
 * @param {number} seriesId - The series ID to toggle.
 * @param {ReturnUnloadedCardSchema[]} cards - The cards for this series.
 * @param {HTMLElement} button - The expand/collapse button.
 */
function toggleUnloadedCards(seriesId, cards, button) {
  const detailRow = document.getElementById(`unloaded-detail-${seriesId}`);
  const icon = button.querySelector('i');
  
  if (detailRow.style.display === 'none') {
    detailRow.style.display = '';
    icon.className = 'chevron up icon';
  } else {
    detailRow.style.display = 'none';
    icon.className = 'chevron down icon';
  }
}

/**
 * Load cards for a specific series.
 * @param {number} seriesId - The series ID to load cards for.
 * @param {HTMLElement} button - The load button element.
 */
function loadSeriesCards(seriesId, button) {
  // Show loading state using setLoadingIcon
  const $icon = setLoadingIcon($(button.querySelector('i')));

  $.ajax({
    type: 'PUT',
    url: `/api/v2/cards/series/${seriesId}/load`,
    success: () => {
      showInfoToast('Cards loaded successfully');
      // Re-query unloaded cards to refresh the data
      queryUnloadedCards();
      refreshTheme();
    },
    error: response => {
      showErrorToast({title: 'Error Loading Cards', response});
      // Reset button state
      icon.className = 'upload icon';
      button.disabled = false;
    },
    complete: () => removeLoadingIcon($icon),
  });
}


function initAll() {
  queryMissingCards();
  queryMissingLogos();
  queryUnloadedCards();
}
