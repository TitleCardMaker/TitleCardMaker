/**
 * Available Card Types Modal - standalone component.
 * Displays all card types with filter; excluded types are shown in the same list with the card disabled.
 * @typedef {import('../.types.js').CardTypeDescription} CardTypeDescription
 */

/** @type {CardTypeDescription[]} */
let allCardTypesForModal = [];

/** @type {() => string[]} */
let getExcludedIdsCallback = () => [];

/**
 * Create HTML for a single card type entry.
 * @param {CardTypeDescription} cardType
 * @returns {string}
 */
function createCardTypeHTML(cardType) {
  const supportedHtml = '<i class="green check icon"></i> Supported';
  const notSupportedHtml = '<i class="red times icon"></i> Not Supported';
  const docsHref = cardType.source === 'builtin'
    ? `https://titlecardmaker.com/card_types/${cardType.identifier.replace(/ /g, '_')}`
    : '';

  return `
    <div class="ui horizontal raised fluid card">
      <div class="image" style="width: 400px; max-width: 300px;">
        <img src="${cardType.example}" alt="${cardType.name} example" style="object-fit: contain;">
      </div>
      <div class="content" style="flex: 1;">
        <div class="header">
          ${cardType.name}
          ${cardType.source === 'builtin' && docsHref
            ? `<a href="${docsHref}" target="_blank" class="ui blue tertiary icon button" style="float: right; margin-left: 0.5em;" title="View Documentation">
                Documentation <i class="external link icon"></i>
              </a>`
            : ''
          }
        </div>
        <div class="meta">
          <span class="date">by ${cardType.creators.join(', ')}</span>
          <br>
          <div class="ui divided horizontal list">
            <div class="item">
              <div class="content">
                <div class="header">Custom Fonts</div>
                <div class="description">
                  ${cardType.supports_custom_fonts ? supportedHtml : notSupportedHtml}
                </div>
              </div>
            </div>
            <div class="item">
              <div class="content">
                <div class="header">Custom Season Titles</div>
                <div class="description">
                  ${cardType.supports_custom_seasons ? supportedHtml : notSupportedHtml}
                </div>
              </div>
            </div>
            <div class="item">
              <div class="content">
                <div class="header">Extras</div>
                <div class="description">
                  <i class="options icon"></i>
                  <strong>${cardType.supported_extras ? cardType.supported_extras.length : 0}</strong> Available
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="description">
          ${cardType.description.map(desc => `<p>${desc}</p>`).join('')}
        </div>
      </div>
    </div>
  `;
}

/**
 * Render a section of card types (builtin, local, or remote). Excluded types are in the same list with disabled cards.
 * @param {CardTypeDescription[]} cards
 * @param {string} title
 * @param {string} icon
 * @param {Set<string>} excludedSet
 * @param {boolean} [isFirst] - If true, no top margin on the header.
 * @returns {string}
 */
function renderSourceSection(cards, title, icon, excludedSet, isFirst = false) {
  if (!cards || cards.length === 0) return '';
  return `
    <h3 class="ui dividing header" style="margin-top: ${isFirst ? '0' : '1'}em;">
      <i class="${icon} icon"></i>
      <div class="content">
        ${title}
        <div class="sub header">${cards.length} card type${cards.length !== 1 ? 's' : ''}</div>
      </div>
    </h3>
    <div class="ui segment">
      ${cards.filter(c => !excludedSet.has(c.identifier)).map(c => createCardTypeHTML(c)).join('')}
    </div>
  `;
}

/**
 * Populate the modal content. All card types in one list by source; excluded types show name with card disabled.
 * @param {CardTypeDescription[]} allCards
 * @param {string} filterText
 * @param {string[]} excludedIds
 */
function populate(allCards, filterText = '', excludedIds = []) {
  const contentDiv = document.getElementById('card-types-content');
  if (!contentDiv) return;

  if (!allCards || allCards.length === 0) {
    contentDiv.innerHTML = '<div class="ui message">No card types available.</div>';
    if (typeof refreshTheme === 'function') refreshTheme();
    return;
  }

  const excludedSet = new Set(excludedIds || []);

  // Filter by name/identifier/creators
  let filteredCards = allCards;
  if (filterText && filterText.trim() !== '') {
    const filterLower = filterText.toLowerCase().trim();
    filteredCards = allCards.filter(card =>
      card.name.toLowerCase().includes(filterLower) ||
      card.identifier.toLowerCase().includes(filterLower) ||
      card.creators.some(creator => creator.toLowerCase().includes(filterLower))
    );
  }

  if (filteredCards.length === 0) {
    contentDiv.innerHTML = `
      <div class="ui message">
        <i class="info circle icon"></i>
        No card types found matching "${filterText}"
      </div>
    `;
    if (typeof refreshTheme === 'function') refreshTheme();
    return;
  }

  const builtinCards = filteredCards.filter(c => c.source === 'builtin');
  const localCards = filteredCards.filter(c => c.source === 'local');
  const remoteCards = filteredCards.filter(c => c.source === 'remote');

  const html = `
    ${renderSourceSection(builtinCards, 'Built-in Card Types', 'building', excludedSet, true)}
    ${renderSourceSection(localCards, 'Local Card Types', 'folder', excludedSet)}
    ${renderSourceSection(remoteCards, 'Remote Card Types', 'cloud download', excludedSet)}
  `;

  contentDiv.innerHTML = html;
  if (typeof refreshTheme === 'function') refreshTheme();
}

/**
 * Initialize the Available Card Types modal.
 * @param {CardTypeDescription[]} allCards - All card type descriptions.
 * @param {() => string[]} getExcludedIds - Function that returns current excluded card type identifiers.
 * @param {string} [triggerSelector='#view-all-card-types'] - Selector for the element that opens the modal when clicked.
 */
function init(allCards, getExcludedIds, triggerSelector = '#view-all-card-types') {
  allCardTypesForModal = allCards || [];
  getExcludedIdsCallback = getExcludedIds || (() => []);

  const $modal = $('#all-card-types-modal');
  if (!$modal.length) return;

  $modal
    .modal('attach events', triggerSelector, 'show')
    .modal('setting', 'transition', 'fade up')
    .modal({
      blurring: true,
      onShow: () => {
        populate(allCardTypesForModal, $('#card-type-filter').val() || '', getExcludedIdsCallback());
      },
    });

  $('#card-type-filter').off('input.availableCardTypesModal').on('input.availableCardTypesModal', function() {
    const filterText = $(this).val();
    populate(allCardTypesForModal, filterText, getExcludedIdsCallback());
  });

  populate(allCardTypesForModal, '', getExcludedIdsCallback());
}

// Export for use by settings and other pages
window.AvailableCardTypesModal = {
  init,
  populate,
  get allCards() { return allCardTypesForModal; },
  set allCards(value) { allCardTypesForModal = value || []; },
};
