{% if False %}
import {
  TitleCardExtendedPage,
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
 * Query the given page of recently created Title Cards.
 * @param {number} page Page number of recent Cards to display.
 */
function queryLatestCards(page=1) {
  // Submit API request
  const args = new URLSearchParams({
    after: $('#after').calendar('get date').toISOString(),
    page: page,
    size: 8,
  });

  $.ajax({
    type: 'GET',
    url: `/api/v2/cards/recent?${args.toString()}`,
    /**
     * Recent cards queried, populate card elements on the page.
     * @param {TitleCardExtendedPage} cardPage Page of recent Title Cards.
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

function initAll() {
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
      queryLatestCards();
    },
  });

  // Query recent cards on page load
  queryLatestCards();

  // Store the most recent login time
  storeLastLoginTime();
}
