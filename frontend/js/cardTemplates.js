{% if False %}
import {
  AvailableFont,
  EpisodeDataSourceToggle,
  ImageSourceToggle,
  Page,
  PreviewTitleCard,
  Series,
  Style,
  Template,
  TemplateFilter,
  Translation
} from './.types.js';
{% endif %}

/**
 * Parse some list value, converting empty lists to the fallback
 * @param {Array} value - List being parsed.
 * @param {*} fallback - Fallback object to return in case `value` is empty.
 * @returns 
 */
const parseList = (value, fallback=[]) => value.length ? value : fallback;

/**
 * Submit an API request to create a new Template. If successful, then all 
 * Templates are reloaded.
 */
function addTemplate() {
  $.ajax({
    type: 'POST',
    url: '/api/v2/templates/template/new',
    data: JSON.stringify({name: ' Blank Template'}),
    contentType: 'application/json',
    /**
     * Template successfully created, show a Toast and re-query all Templates.
     * @param {Template} template - Newly created Template.
     */
    success: template => {
      showInfoToast(`Created Template #${template.id}`);
      getAllTemplates();
    },
    error: response => showErrorToast({title: 'Error Creating Template', response}),
  });
}

/**
 * Reload the preview image.
 * @param {string} templateElementId - Element ID of the template whose preview
 * is being generated.
 * @param {HTMLElement} cardElement - The preview card element
 * @param {HTMLElement} imgElement - The preview image element
 * @param {HTMLElement} previewForm - Preview form element containing episode selection
 */
function reloadPreview(templateElementId, cardElement, imgElement, previewForm) {
  // Check if an episode is selected to determine watched status
  const previewFormObj = previewForm ? new FormData(previewForm) : null;
  const episodeId = previewFormObj ? previewFormObj.get('episode_id') : null;
  
  // Default to unwatched if no episode is selected
  // If episode is selected, we'll determine watched status from the episode data
  let isWatched = false;
  
  /** @type {Style} Effective style - default to unwatched style */
  let style = $(`#${templateElementId} input[name="unwatched_style"]`).val() || '{{preferences.default_unwatched_style}}';
  
  // If episode is selected, we'll use the episode's actual watched status
  // For now, default to unwatched style for preview

  const extras = {};
  $(`#${templateElementId} section[aria-label="extras"] input`).each(function() {
    if ($(this).val() !== '') {
      extras[$(this).attr('name')] = $(this).val();
    }
  });

  if (!episodeId) {
    showErrorToast({title: 'Select Episode to display preview of'});
    return;
  }
  // Extract template ID from templateElementId (format: "template-id{id}")
  const templateId = parseInt(templateElementId.replace('template-id', ''));

  // Helper function to convert string booleans to actual booleans
  const toBool = (val) => {
    if (val === 'True') return true;
    if (val === 'False') return false;
    return val || null;
  };

  // Build UpdateTemplate object - include both watched and unwatched styles
  const updateTemplate = {
    card_type: $(`#${templateElementId} input[name="card_type"]`).val() || null,
    font_id: $(`#${templateElementId} input[name="font_id"]`).val() || null,
    watched_style: $(`#${templateElementId} input[name="watched_style"]`).val() || null,
    unwatched_style: $(`#${templateElementId} input[name="unwatched_style"]`).val() || null,
    hide_season_text: toBool($(`#${templateElementId} input[name="hide_season_text"]`).val()),
    hide_episode_text: toBool($(`#${templateElementId} input[name="hide_episode_text"]`).val()),
    episode_text_format: $(`#${templateElementId} input[name="episode_text_format"]`).val() || null,
    data_source_id: $(`#${templateElementId} input[name="data_source_id"]`).val() || null,
    image_source_priority: $(`#${templateElementId} input[name="image_source_priority"]`).val() ? 
      $(`#${templateElementId} input[name="image_source_priority"]`).val().split(',').filter(id => id !== '') : null,
    sync_specials: toBool($(`#${templateElementId} input[name="sync_specials"]`).val()),
    skip_localized_images: toBool($(`#${templateElementId} input[name="skip_localized_images"]`).val()),
  };

  // Add extras to update_template
  if (Object.keys(extras).length > 0) {
    updateTemplate.extras = extras;
  }

  // Build filters array
  const filters = [];
  $(`#${templateElementId} input[name="argument"]`).each(function(index) {
    const argument = $(this).val();
    const operation = $(`#${templateElementId} input[name="operation"]`).eq(index).val();
    const reference = $(`#${templateElementId} input[name="reference"]`).eq(index).val();
    if (argument && operation) {
      filters.push({
        argument: argument,
        operation: operation,
        reference: reference || null,
      });
    }
  });
  if (filters.length > 0) {
    updateTemplate.filters = filters;
  }

  // Build translations array
  const translations = [];
  $(`#${templateElementId} input[name="language_code"]`).each(function(index) {
    const languageCode = $(this).val();
    const dataKey = $(`#${templateElementId} input[name="data_key"]`).eq(index).val();
    if (languageCode && dataKey) {
      translations.push({
        language_code: languageCode,
        data_key: dataKey,
      });
    }
  });
  if (translations.length > 0) {
    updateTemplate.translations = translations;
  }

  // Build season_titles dict
  const seasonTitles = {};
  $(`#${templateElementId} input[name="season_title_ranges"]`).each(function(index) {
    const range = $(this).val();
    const value = $(`#${templateElementId} input[name="season_title_values"]`).eq(index).val();
    if (range && value) {
      seasonTitles[range] = value;
    }
  });
  if (Object.keys(seasonTitles).length > 0) {
    updateTemplate.season_titles = seasonTitles;
  }

  // Remove undefined values
  Object.keys(updateTemplate).forEach(key => {
    if (updateTemplate[key] === undefined || updateTemplate[key] === '') {
      delete updateTemplate[key];
    }
  });

  // const previewData = { update_template: updateTemplate };

  // Submit API request
  cardElement.classList.add('loading');
  $.ajax({
    type: 'POST',
    url: `/api/v2/cards/preview/episode/${episodeId}/template/${templateId}`,
    data: JSON.stringify(updateTemplate),
    contentType: 'application/json',
    /**
     * Preview created - update the image src.
     * @param {string} imageUrl URL to the image to display.
     */
    success: imageUrl => imgElement.src = `${imageUrl}?${new Date().getTime()}`,
    error: response =>  showErrorToast({title: 'Error Creating Preview Card', response}),
    complete: () => cardElement.classList.remove('loading'),
  });
}

/**
 * Submit the API requests to delete the Template with the given ID. This also
 * queries and displays a list of the Series associated with this Template.
 * A confirmation modal is shown.
 * @param {number} templateId - ID of the Template being deleted.
 */
function showDeleteModal(templateId) {
  /** @type {string[]} */
  let seriesElements = ['<li><span class="ui text">No associated Series</span></li>'];

  // Get list of Series associated with this Template
  $.ajax({
    type: 'GET',
    url: `/api/v2/series/search?template_id=${templateId}&size=25`,
    /**
     * Series queried successfully, populate list to display in modal.
     * @param {Page<Series>} allSeries - Page of Series associated with the
     * Template being deleted.
     */
    success: allSeries => {
      seriesElements = allSeries.items.map(({name, year}) => `<li>${name} (${year})</li>`);
      if (allSeries.total > 25) {
        seriesElements.push(`<li><span class="ui red text">${allSeries.total-25} more Series...</span></li>`);
      }
    },
    error: response => showErrorToast({title: 'Error Querying Associated Series', response}),
    /** Fill out and display modal to confirm deletion */
    complete: () => {
      // Populate modal with list of Series (or nothing)
      document.querySelector('#delete-template-modal [data-value="series-list"]').innerHTML = seriesElements.join('');

      // Assign delete API request to button press
      $('#delete-template-modal .button[data-action="delete-template"]').off('click').on('click', () => {
        $.ajax({
          type: 'DELETE',
          url: `/api/v2/templates/template/${templateId}`,
          success: () => {
            showInfoToast('Deleted Template');
            document.getElementById(`template-id${templateId}`).remove();
          },
          error: response => showErrorToast({title: 'Error Deleting Template', response}),
        });
      });
    
      $('#delete-template-modal').modal('show');
    },
  });
}

/**
 * Parse the given Form and submit an API request to patch this Template.
 * @param {number} templateId - ID of the Template being updated.
 */
function updateTemplate(templateId) {

  const extras = {};
  $(`#template-id${templateId} section[aria-label="extras"] input`).each(function() {
    if ($(this).val() !== '') {
      extras[$(this).attr('name')] = $(this).val();
    }
  });

  const data = {
    name: $(`#template-id${templateId} input[name="name"]`).val(),
    filters: parseList(
        Array.from(document.querySelectorAll(`#template-id${templateId} input[name="operation"]`)).map((input, index) => {
          return {
            argument: document.querySelectorAll(`#template-id${templateId} input[name="argument"]`)[index].value,
            operation: input.value,
            reference: document.querySelectorAll(`#template-id${templateId} input[name="reference"]`)[index].value,
          };
        }).filter(({operation}) => operation !== '')
      ),
    card_type: $(`#template-id${templateId} input[name="card_type"]`).val() || null,
    font_id: $(`#template-id${templateId} input[name="font_id"]`).val() || null,
    watched_style: $(`#template-id${templateId} input[name="watched_style"]`).val() || null,
    unwatched_style: $(`#template-id${templateId} input[name="unwatched_style"]`).val() || null,
    hide_season_text: $(`#template-id${templateId} input[name="hide_season_text"]`).val() || null,
    season_title_ranges: parseList(
        Array.from(document.querySelectorAll(`#template-id${templateId} input[name="season_title_ranges"]`)).map(input => input.value),
      ),
    season_title_values: parseList(
        Array.from(document.querySelectorAll(`#template-id${templateId} input[name="season_title_values"]`)).map(input => input.value),
      ),
    hide_episode_text: $(`#template-id${templateId} input[name="hide_episode_text"]`).val() || null,
    episode_text_format: $(`#template-id${templateId} input[name="episode_text_format"]`).val() || null,
    skip_localized_images: $(`#template-id${templateId} input[name="skip_localized_images"]`).val() || null,
    data_source_id: $(`#template-id${templateId} input[name="data_source_id"]`).val() || null,
    image_source_priority: parseList(
        document.querySelector(`#template-id${templateId} input[name="image_source_priority"]`).value.split(',').filter(id => id != '')
      ),
    sync_specials: $(`#template-id${templateId} input[name="sync_specials"]`).val() || null,
    translations: parseList(
        Array.from(document.querySelectorAll(`#template-id${templateId} input[name="language_code"]`)).map((input, index) => {
          return {
            language_code: input.value,
            data_key: document.querySelectorAll(`#template-id${templateId} input[name="data_key"]`)[index].value,
          };
        }).filter(({data_key}) => data_key !== '')
      ),
    extras: extras,
  }

  $.ajax({
    type: 'PATCH',
    url: `/api/v2/templates/template/${templateId}`,
    data: JSON.stringify(data),
    contentType: 'application/json',
    /**
     * Template updated, display toast.
     * @param {Template} updatedTemplate - New Template
     */
    success: updatedTemplate => showInfoToast(`Updated Template "${updatedTemplate.name}"`),
    error: response => showErrorToast({title: 'Error Updating Template', response}),
  });
}

let htmlTemplatesInitialized = false;

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
 * Query all templates, adding their content to the page.
 */
async function getAllTemplates() {
  // Start querying templates, but do not wait for results
  /** @type {Promise<Template[]>} */
  const templatePromise = fetch('/api/v2/templates/all').then(resp => resp.json());

  // Query all "available" data used to populate dropdowns in the HTML template
  if (!htmlTemplatesInitialized) {
    /** @type {[AvailableFont[], EpisodeDataSourceToggle[], ImageSourceToggle[], TemplateFilter[], Translation[]]} */
    const [
      allFonts,
      allEpisodeDataSources,
      allImageSources,
      // allFilterOptions,
      allTranslations,
    ] = await Promise.all([
      fetch('/api/v2/available/fonts').then(resp => resp.json()),
      fetch('/api/v2/settings/episode-data-source').then(resp => resp.json()),
      fetch('/api/v2/settings/image-source-priority').then(resp => resp.json()),
      // fetch('/api/v2/available/template-filters').then(resp => resp.json()),
      fetch('/api/v2/available/translations').then(resp => resp.json()),
    ]);
  
    // ----------------------- Add selectable items to the HTML template dropdowns
    const htmlTemplate = document.getElementById('template').content;
    const translationTemplate = document.getElementById('translation-template').content;
    // Fonts
    const fontMenu = htmlTemplate.querySelector('.dropdown[data-value="font_id"] .menu');
    allFonts.forEach(font => {
      addDropdownItem(fontMenu, {innerText: font.name, value: font.id});
    });
    // Data source IDs
    const dataSourceIdMenu = htmlTemplate.querySelector('.dropdown[data-value="data_source_id"] .menu');
    allEpisodeDataSources.forEach(source => {
      addDropdownItem(dataSourceIdMenu, {innerText: source.name, value: source.interface_id});
    });
    // Image Source Priorities
    const ispMenu = htmlTemplate.querySelector('.dropdown[data-value="image_source_priority"] .menu');
    allImageSources.forEach(source => addDropdownItem(ispMenu, {innerText: source.name, value: source.interface_id}));
    // Translation languages
    const translationMenu = translationTemplate.querySelector('.dropdown[data-value="language_code"] .menu');
    allTranslations.forEach(translation => {
      addDropdownItem(translationMenu, {innerText: translation.language, value: translation.language_code});
    });
    // ---------------------------------------------------------------------------
    // Populate extras
    await populateExtraTemplate({
      extraTemplateSection: htmlTemplate.querySelector('section[aria-label="extras"]'),
      inputTemplateElement: document.getElementById('extra-template'),
      groupAmount: 3,
    });
    htmlTemplatesInitialized = true;
  }

  /** @type {Template[]} Finish Template data query */
  const allTemplates = await templatePromise;

  // Create elements to add to the page
  const elements = [],
    hasManyTemplates = allTemplates.length > 10;
  let currentHeader = '';
  allTemplates.forEach(templateObj => {
    // Add letter header for this Template if necessary
    const letter = templateObj.sort_name[0].toUpperCase();
    if (hasManyTemplates && letter !== currentHeader) {
      const header = document.createElement('h3');
      header.className = 'ui dividing header';
      header.innerText = letter === ' ' ? 'Blank Templates' : letter;
      elements.push(header);
      currentHeader = letter;
    }

    // Clone template
    const base = document.querySelector('#template').content.cloneNode(true);
    const templateElementId = `template-id${templateObj.id}`;
    base.querySelector('.accordion').id = templateElementId;
    base.querySelector('.accordion').dataset.name = templateObj.name;
    // Set accordion title and title input
    base.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${templateObj.name}`;
    const nameElem = base.querySelector('input[name="name"]');
    nameElem.placeholder = templateObj.name;
    nameElem.value = templateObj.name;
    // Filters added later
    if (templateObj.filters.length > 0) {
      const conditionsDiv = base.querySelector('[data-value="conditions"]');
      for (const condition of templateObj.filters) {
        // Clone filter template
        const newCondition = document.getElementById('filter-template').content.cloneNode(true);
        // Populate filter
        newCondition.querySelector('input[name="argument"]').value = condition.argument;
        newCondition.querySelector('input[name="operation"]').value = condition.operation;
        if (condition.reference !== null) {
          newCondition.querySelector('input[name="reference"]').value = condition.reference;
        }
        // Add to page
        conditionsDiv.appendChild(newCondition);
      }
    }
    // Card type set later
    // Font ID
    if (templateObj.font_id === null) {
      base.querySelector('a[data-value="font-link"]').remove();
    } else {
      base.querySelector('a[data-value="font-link"]').href = `/fonts#font-id${templateObj.font_id}`;
      base.querySelector('.dropdown[data-value="font_id"] > input').value = templateObj.font_id;
    }
    // Unwatched and Watched style
    if (templateObj.watched_style) {
      base.querySelector('.dropdown[data-value="watched_style"] > input').value = templateObj.watched_style;
    }
    if (templateObj.unwatched_style) {
      base.querySelector('.dropdown[data-value="unwatched_style"] > input').value = templateObj.unwatched_style;
    }
    // Hide season text
    if (templateObj.hide_season_text !== null) {
      const value = templateObj.hide_season_text ? 'True' : 'False';
      base.querySelector('.dropdown[data-value="hide_season_text"] > input').value = value;
    }
    // Season titles
    if (templateObj.season_titles && Object.entries(templateObj.season_titles).length > 0) {
      const rangeDiv = base.querySelector('.field[data-value="season-title-range"]');
      const valueDiv = base.querySelector('.field[data-value="season-title-value"]');
      for (const [range, value] of Object.entries(templateObj.season_titles)) {
        const rangeElem = document.createElement('input');
        rangeElem.name = 'season_title_ranges'; rangeElem.setAttribute('data-value', 'season-titles');
        rangeElem.type = 'text'; rangeElem.value = range;
        rangeDiv.appendChild(rangeElem);
        const valueElem = document.createElement('input');
        valueElem.name = 'season_title_values'; valueElem.type = 'text'; valueElem.value = value;
        valueDiv.appendChild(valueElem);
      }
    }
    // Hide episode text
    if (templateObj.hide_episode_text !== null) {
      const value = templateObj.hide_episode_text ? 'True' : 'False';
      base.querySelector('.dropdown[data-value="hide_episode_text"] > input').value = value;
    }
    // Episode text format
    base.querySelector('input[name="episode_text_format"]').value = templateObj.episode_text_format;
    // Ignored Localized Images
    if (templateObj.skip_localized_images !== null) {
      const value = templateObj.skip_localized_images ? 'True' : 'False';
      base.querySelector('.dropdown[data-value="skip_localized_images"] > input').value = value;
    }
    // Episode data source
    if (templateObj.data_source_id !== null) {
      base.querySelector('.dropdown[data-value="data_source_id"] > input').value = templateObj.data_source_id;
    }
    // Sync specials
    if (templateObj.sync_specials !== null) {
      const value = templateObj.sync_specials ? 'True' : 'False';
      base.querySelector('.dropdown[data-value="sync_specials"] > input').value = value;
    }
    // Image source priority
    if (templateObj.image_source_priority !== null) {
      base.querySelector('.dropdown[data-value="image_source_priority"] > input').value = templateObj.image_source_priority;
    }
    // Translations
    if (templateObj.translations !== null && templateObj.translations.length > 0) {
      const translationSegment = base.querySelector('[data-value="translations"]');
      for (const translation of templateObj.translations) {
        const newTranslation = document.getElementById('translation-template').content.cloneNode(true);
        newTranslation.querySelector('input[name="language_code"]').value = translation.language_code;
        newTranslation.querySelector('input[name="data_key"]').value = translation.data_key;
        translationSegment.append(newTranslation);
      }
    }
    // Extras
    if (templateObj.extras && Object.entries(templateObj.extras).length > 0) {
      for (const [identifier, value] of Object.entries(templateObj.extras)) {
        base.querySelectorAll(`section[aria-label="extras"] input[name="${identifier}"]`).forEach(input => input.value = value);
      }
    }
    // Update card preview
    const previewCard = base.querySelector('.preview.card');
    const previewImg = base.querySelector('.preview.card img');
    const previewForm = base.querySelector('form[data-value="preview-form"]');
    base.querySelector('.button[data-action="refresh"]').onclick = () => {
      reloadPreview(templateElementId, previewCard, previewImg, previewForm);
    };
    previewCard.onclick = () => reloadPreview(templateElementId, previewCard, previewImg, previewForm);


    // Update Templates
    base.querySelector('button[button-type="submit"]').onclick = (event) => {
      event.preventDefault();
      updateTemplate(templateObj.id);
    };
    // Delete Template
    base.querySelector('button[button-type="delete"]').onclick = (event) => {
      event.preventDefault();
      showDeleteModal(templateObj.id)
    };

    elements.push(base);
  });

  // Add elements to the page, refresh theme, and then initialize accordions
  document.getElementById('templates').replaceChildren(...elements);
  refreshTheme();
  $('.ui.accordion').accordion({
    duration: 750,
    /**
     * Callback when a template accordion is opened. When the template is
     * viewed, initialize the extra tabs. This is not done ahead of time
     * because it can be very slow.
     */
    onOpen: function () {
      // Get the card type of this template (or global) to determine which tab to open to
      const cardIdentifier = $(this).find('input[name="card_type"]').val() || '{{ preferences.default_card_type }}';
      $(this).find('section[aria-label="extras"] .item').tab('change tab', cardIdentifier);
    },
  });

  // Fill in fancy values
  await getAllCardTypes();
  const cardTypeLoads = allTemplates.map(templateObj =>
    loadCardTypes({
      element: `#template-id${templateObj.id} .dropdown[data-value="card_type"]`,
      isSelected: (identifier) => identifier === templateObj.card_type,
      dropdownArgs: {
        placeholder: 'Global Default',
      }
    })
  );
  const cardTypeResults = await Promise.all(cardTypeLoads);
  if (window.AvailableCardTypesModal && cardTypeResults[0]) {
    window.AvailableCardTypesModal.init(cardTypeResults[0], () => [], '.card-type-help');
  }

  // Enable accordion/dropdown/checkbox elements
  document.getElementById('loader')?.remove();
  $('.ui.checkbox').checkbox();
  $('.ui.dropdown').dropdown();
  $('.ui.clearable.dropdown').dropdown({clearable: true});
  $('.field[data-value="season-titles"] label i').popup({
    popup: '#season-title-popup',
    position: 'right center',
  });

  // Initialize episode search dropdowns after general dropdown initialization
  // This must be done after elements are in the DOM and after general dropdown init
  allTemplates.forEach(templateObj => {
    const templateElementId = `template-id${templateObj.id}`;
    const episodeDropdown = document.querySelector(`#${templateElementId} .dropdown.episode-search`);
    if (episodeDropdown) {
      const previewCard = document.querySelector(`#${templateElementId} .preview.card`);
      const previewImg = document.querySelector(`#${templateElementId} .preview.card img`);
      const previewForm = document.querySelector(`#${templateElementId} form[data-value="preview-form"]`);
      
      $(episodeDropdown).dropdown({
        clearable: true,
        placeholder: 'Search for episode...',
        fullTextSearch: true,
        forceSelection: false,
        apiSettings: {
          url: '/api/v2/episodes/search?search={query}&page=1&limit=20',
          onResponse: function(response) {
            const items = response.items.map(episode => ({
              name: `${episode.series.name} - ${episode.title} (S${episode.season_number.toString().padStart(2, '0')}E${episode.episode_number.toString().padStart(2, '0')})`,
              value: episode.id,
            }));
            return {
              success: true,
              results: items,
            };
          },
        },
        minCharacters: 2,
        onChange: function(value) {
          // Refresh preview when episode is selected or cleared
          reloadPreview(templateElementId, previewCard, previewImg, previewForm);
        },
      });
    }
  });

  // Refresh theme for any newly added HTML
  refreshTheme();
}

function initAll() {
  getAllTemplates();
}

/**
 * Remove a filter condition row from the template.
 * @param {HTMLButtonElement} button The remove button that was clicked.
 */
function removeFilterCondition(button) {
  button.closest('.filter-condition-row').remove();
  refreshTheme();
}

/**
 * Add a new blank filter set to the template containing the initiating button.
 * @param {HTMLDivElement} addButton Initiating add button which was clicked.
 */
function addBlankFilter(addButton) {
  // Get blank filter template
  const newCondition = document.getElementById('filter-template').content.cloneNode(true);
  // Add to condition list
  addButton.closest('div[data-label="filters"]')
    .querySelector('div[data-value="conditions"]')
    .appendChild(newCondition);
  // Initialize newly added dropdowns, refresh theme
  $(addButton).parent('div[data-label="filters"]').find('.ui.dropdown').dropdown();
  refreshTheme();
}

/**
 * Add a new blank season title set to the template containing the initiating
 * button.
 * @param {HTMLDivElement} addButton Initiating add button which was clicked.
 */
function addBlankTitle(addButton) {
  // Create range input
  const newRange = document.createElement('input');
  newRange.name = 'season_title_ranges'; newRange.type = 'text';
  newRange.setAttribute('data-value', 'season-titles');
  // Create title input
  const newTitle = document.createElement('input');
  newTitle.name = 'season_title_values'; newTitle.type = 'text';
  // Add to page
  addButton.closest('div.field')
    .querySelector('.field[data-value="season-title-range"]')
    .appendChild(newRange);
    addButton.closest('div.field')
    .querySelector('.field[data-value="season-title-value"]')
    .appendChild(newTitle);

  refreshTheme();
}

/**
 * Add a new blank translation set to the template containing the initiating
 * button.
 * @param {HTMLDivElement} addButton Initiating add button which was clicked.
 */
function addBlankTranslation(addButton) {
  // Get blank translation template
  const newTranslation = document.getElementById('translation-template').content.cloneNode(true);
  // Add to section
  addButton.closest('div.field')
    .querySelector('div[data-value="translations"]')
    .appendChild(newTranslation);
  // Initialize newly added dropdowns, refresh theme
  $(addButton).parent('div.field').find('.ui.dropdown').dropdown({
    allowAdditions: true,
  });
  refreshTheme();
}
