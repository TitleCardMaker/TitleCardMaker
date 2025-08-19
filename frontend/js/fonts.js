{% if False %}
import {
  FontAnalysis, NamedFont, PreviewTitleCard
} from './.types.js';
{% endif %}

/**
 * "Change" the given icon to a loading indication. This is done by inserting an
 * adjacent spinner icon and hiding the given icon.
 * @param {JQuery} icon Element of the icon to set as loading,
 */
function setLoadingIcon($icon) {
  $icon.css('display', 'none');
  $('<i class="spinner loading icon"></i>').insertAfter($icon);
}

/**
 * Remove the loading indication from the given icon. This removes the
 * previously inserted adjacent spinner icon and unhides the given icon.
 * @param {JQuery} $icon Element of the icon to unset as loading.
 */
function removeLoadingIcon($icon) {
  const $spinnerIcon = $icon.next();
  if ($spinnerIcon.hasClass('spinner') && $spinnerIcon.hasClass('icon')) {
    $spinnerIcon.remove();
  }
  $icon.css('display', '');
}

/**
 * Submit an API request to create a new Font. If successful, then all Fonts
 * are reloaded.
 */
function addFont() {
  const $icon = $('#create-font .icon');
  setLoadingIcon($icon);

  const data = {name: ' Blank Custom Font'};
  $.ajax({
    type: 'POST',
    url: '/api/v2/fonts/font/new',
    data: JSON.stringify(data),
    contentType: 'application/json',
    /**
     * Font created; show toast and re-query all Fonts.
     * @param {NamedFont} font - Newly created Font.
     */
    success: font => {
      showInfoToast(`Created Font #${font.id}`);
      window.location.hash = `font-id${font.id}`;
      getAllFonts();
    },
    error: response => showErrorToast({title: 'Error Creating Font', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Submit an API request to delete the given Font from the database. If
 * successful, the HTML element for this Font is removed from the page.
 * @param {NamedFont} font Font to delete.
 */
function deleteFont(font) {
  const $icon = $(`font-id${font.id} .button[data-action="delete"] .icon`);
  setLoadingIcon($icon);

  // Submit API request
  $.ajax({
    type: 'DELETE',
    url: `/api/v2/fonts/font/${font.id}`,
    /** Font deleted, show toast and remove this Font's element from the DOM. */
    success: () => {
      showInfoToast(`Deleted Font "${font.name}"`);
      document.getElementById(`font-id${font.id}`).remove();
      // $(`#font-id${font.id}`).remove();
    },
    error: response => showErrorToast({title: 'Error Deleting Font', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Submit an API request to reload the preview image for the Font with the given
 * data.
 * @param {number} fontId - ID of the Font whose preview is being reloaded.
 * @param {HTMLFormElement} fontForm - Form whose data is being previewed.
 * @param {HTMLFormElement} previewForm - Form containing preview images.
 * @param {HTMLElement} cardElement - Element to mark as loading while the
 * preview is being generated.
 * @param {HTMLImageElement} imageElement - Element whose `src` to update.
 */
function reloadPreview(fontId, fontForm, previewForm, cardElement, imageElement) {
  const fontFormObj = new FormData(fontForm);
  const previewFormObj = new FormData(previewForm);
  /** @type {PreviewTitleCard} */
  const previewCardObj = {
    card_type: previewFormObj.get('card_type') || '{{preferences.default_card_type}}',
    title_text: previewFormObj.get('title_text'),
    font_id: fontId,
    font_title_case: fontFormObj.get('title_case'),
    font_color: fontFormObj.get('color'),
    font_interline_spacing: fontFormObj.get('interline_spacing'),
    font_interword_spacing: fontFormObj.get('interword_spacing'),
    font_kerning: fontFormObj.get('kerning') / 100.0,
    font_size: fontFormObj.get('size') / 100.0,
    font_stroke_width: fontFormObj.get('stroke_width') / 100.0,
    font_vertical_shift: fontFormObj.get('vertical_shift'),
  };

  // Submit API request
  cardElement.classList.add('loading');
  $.ajax({
    type: 'POST',
    url: '/api/v2/cards/preview',
    data: JSON.stringify(previewCardObj),
    contentType: 'application/json',
    /**
     * Preview created; update `imageElement.src`.
     * @param {string} imageUrl - New URI to the generated preview image.
     */
    success: imageUrl => imageElement.src = `${imageUrl}?${new Date().getTime()}`,
    error: response => showErrorToast({title: 'Error Creating Preview Card', response}),
    complete: () => cardElement.classList.remove('loading'),
  });
}

/**
 * Submit an API request to update the Font with the given ID (if the Font Form
 * is valid). This also uploads the uploaded Font file (if present).
 * @param {number} fontId - ID of the Font whose form is being parsed and
 * updated.
 * @param {EventTarget} eventTarget - Target of the event initializing the save
 * (the Font Form).
 */
function saveFontForm(fontId, eventTarget) {
  // Validate form, exit if invalid
  if (!$(`#font-id${fontId}`).form('is valid')) { return; }

  // Mark as loading
  const $icon = $(`#font-id${fontId} .button[data-action="save"] .icon`);
  setLoadingIcon($icon);

  // Construct form
  let form = new FormData(eventTarget);
  let listData = {replacements_in: [], replacements_out: []};
  for (let [key, value] of [...form.entries()]) {
    if (key === 'size' || key === 'kerning' || key === 'stroke_width') {
      form.set(key, value/100.0);
    }
    if (key === 'replacements_in') { listData.replacements_in.push(value); }
    if (key === 'replacements_out') { listData.replacements_out.push(value); }
  }
  // Add boolean toggle(s)
  $.each($(`#font-id${fontId}`).find('input[type=checkbox]'), (key, val) => {
    form.append($(val).attr('name'), $(val).is(':checked'));
  });

  // Submit API request
  $.ajax({
    type: 'PATCH',
    url: `/api/v2/fonts/font/${fontId}`,
    data: JSON.stringify({...Object.fromEntries(form.entries()), ...listData}),
    contentType: 'application/json',
    /**
     * Font updated, display toast.
     * @param {NamedFont} font - Updated Font.
     */
    success: font => showInfoToast(`Updated Font "${font.name}"`),
    error: response => showErrorToast({title: 'Error Updating Font', response}),
  });

  // No Font file to upload
  if (form.get('font_file').size === 0) {
    removeLoadingIcon($icon);
    return;
  }

  // Submit separate API request to upload font file
  let fileForm = new FormData();
  fileForm.append('file', form.get('font_file'));
  $.ajax({
    type: 'PUT',
    url: `/api/v2/fonts/font/${fontId}/file`,
    data: fileForm,
    processData: false,
    contentType: false,
    success: () => showInfoToast('Uploaded Font File'),
    error: response => showErrorToast({title: 'Error Uploading Font File', response}),
    complete: () => {
      removeLoadingIcon($icon);
      $(`#font-id${fontId} .button[data-action="populateReplacements"]`).toggleClass('disabled', false);
    },
  });
}

/**
 * Perform an analysis of this Font, adding any suggested Font replacements to
 * the DOM.
 * @param {number} fontId - ID of the Font being analyzed.
 * @param {string} elementId - ID of the form associated with this Font.
 */
function querySuggestedFontReplacements(fontId, elementId) {
  $.ajax({
    type: 'GET',
    url: `/api/v2/fonts/font/${fontId}/analysis`,
    /**
     * Font analyzed, update DOM with suggested replacements.
     * @param {FontAnalysis} analysis - Analysis to display.
     */
    success: analysis => {
      // Disable button now that Font has been analyzed
      $(`#${elementId} .button[data-action="populateReplacements"]`).toggleClass('disabled', true);
      // Show toast for irreplaceable characters
      if (analysis.missing.length > 0) {
        showErrorToast({
          title: 'Irreplaceable Characters Identified',
          message: 'No Suitable replacements found for: ' + analysis.missing.join(' '),
          displayTime: 10000,
        });
      }
      // No replacements, show toast and exit
      if (Object.keys(analysis.replacements).length === 0) {
        showInfoToast('No Suggested Replacements');
        return;
      }
      // There are replacements, add to page
      const inElement = document.querySelector(`#${elementId} .field[data-value="in-replacements"]`);
      const outElement = document.querySelector(`#${elementId} .field[data-value="out-replacements"]`);
      for (const [repl_in, repl_out] of Object.entries(analysis.replacements)) {
        // Skip if this replacement already exists
        let found = false;
        $(`#${elementId} input[name="replacements_in"]`).each(function() {
          if ($(this).val() === repl_in) { found = true; return; }
        });
        if (!found) {
          const newInput = document.createElement('input');
          newInput.value = repl_in; newInput.name = 'replacements_in'; newInput.type='text';
          inElement.appendChild(newInput);
          const newOutput = document.createElement('input');
          newOutput.value = repl_out; newOutput.name = 'replacements_out'; newOutput.type='text';
          newOutput.placeholder = 'Delete Character';
          outElement.appendChild(newOutput);
        }
      }
      showInfoToast({title: 'Added Suggested Replacements', message: 'Blank replacements indicate a deleted character'});
    },
    error: response => showErrorToast({title: 'Error Analyzing Font', response}),
  });
}

/**
 * Submit an API request to transfer the Font references.
 * @param {number} fromId ID of the Font whose assignments are being transferred
 * from.
 * @param {number} toId ID of the Font whose assignments are being transferred
 * to.
 * @param {boolean} deleteFrom Whether to delete the "from" Font after
 * transferring.
 */
function transferFontReferences(fromId, toId, deleteFrom) {
  const $icon = $(`font-id${fromId} .button[data-action="transfer"] .icon`);
  setLoadingIcon($icon);

  // Get args
  const args = new URLSearchParams({
    from: fromId,
    to: toId,
    delete_from: deleteFrom,
  });

  // Submit API request
  $.ajax({
    type: 'PUT',
    url: `/api/v2/fonts/transfer?${args.toString()}`,
    /**
     * Font transferred, display a toast and delete the Font from the page if
     * indicated.
     * @param {NamedFont} font "To" Font after re-assignment.
     */
    success: font => {
      showInfoToast(`Font references transferred to "${font.name}"`);
      if (deleteFrom) {
        showInfoToast('Font deleted');
        // Remove deleted Font
        document.getElementById(`font-id${fromId}`).remove();
        $(`.dropdown[data-action="transfer"] .item[data-value="${fromId}"]`).remove();
      }
    },
    error: response => showErrorToast({title: 'Error transferring Font', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * 
 * @param {number} fromId ID of the Font whose assignments are being transferred
 * from.
 * @param {number} toId ID of the Font whose assignments are being transferred
 * to.
 */
function showTransferFontDialog(fromId, toId) {
  document.querySelector('#transfer-font-modal [data-action="transfer-only"]').onclick = () => transferFontReferences(fromId, toId, false);
  document.querySelector('#transfer-font-modal [data-action="transfer-with-delete"]').onclick = () => transferFontReferences(fromId, toId, true);
  $('#transfer-font-modal').modal('show');
}

/**
 * Populate the given font element with the given font object.
 * @param {HTMLElement} fontElement Element being populated.
 * @param {NamedFont} font Font object whose details are used to populate the
 * element.
 */
function populateFontOverview(fontElement, font) {
  fontElement.querySelector('.accordion').id = `font-id${font.id}`;
  fontElement.querySelector('.accordion').dataset.id = font.id;
  fontElement.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${font.name}`;
  return fontElement;
}

/**
 * Populate the given font element with the given font object.
 * @param {HTMLElement} template Element being populated.
 * @param {NamedFont} font Font object whose details are used to populate the
 * element.
 * @returns {Node} Modified `template`.
 */
function populateFontElement(fontElement, font) {
  fontElement.querySelector('.title').innerHTML = `<i class="dropdown icon"></i>${font.name}`;
  fontElement.querySelector('input[name="name"]').value = font.name;

  fontElement.querySelector('label[data-value="file"]').innerHTML =
    font.file_name === null ? 'File' : `File (<span class="prefix">config/assets/fonts/${font.id}/</span>${font.file_name})`;
  
  if (font.color !== null) {
    fontElement.querySelector('input[name="color"]').value = font.color;
    // Update inline circle
    fontElement.querySelector('.field[data-value="color"] .color.circle').style.setProperty('--color', font.color);
  }
  // Add onchange listener to recolor circle
  fontElement.querySelector('input[name="color"]').oninput = function () {
    document.querySelector(`#font-id${font.id} .field[data-value="color"] .color.circle`).style.setProperty('--color', $(this).val());
  }

  if (font.title_case !== null) {
    fontElement.querySelector('input[name="title_case"]').value = font.title_case;
  }
  fontElement.querySelector('input[name="line_split_modifier"]').value = font.line_split_modifier;
  fontElement.querySelector('input[name="size"]').value = Math.round(font.size*100);
  fontElement.querySelector('input[name="kerning"]').value = Math.round(font.kerning*100);
  fontElement.querySelector('input[name="stroke_width"]').value = Math.round(font.stroke_width*100);
  fontElement.querySelector('input[name="interline_spacing"]').value = font.interline_spacing;
  fontElement.querySelector('input[name="interword_spacing"]').value = font.interword_spacing;
  fontElement.querySelector('input[name="vertical_shift"]').value = font.vertical_shift;

  // Set font replacements
  const inElement = fontElement.querySelector('.field[data-value="in-replacements"]');
  const outElement = fontElement.querySelector('.field[data-value="out-replacements"]');
  for (let i = 0; i < font.replacements_in.length; i++) {
    const newInput = document.createElement('input');
    newInput.name = 'replacements_in'; newInput.type = 'text';
    newInput.value = font.replacements_in[i];
    inElement.appendChild(newInput);
    
    const newOutput = document.createElement('input');
    newOutput.name = 'replacements_out'; newOutput.type='text'; newOutput.placeholder = 'Delete Character';
    newOutput.value = font.replacements_out[i];
    outElement.appendChild(newOutput);
  }

  // Query suggested font replacements on button click
  fontElement.querySelector('.button[data-action="populateReplacements"]').onclick = () => querySuggestedFontReplacements(font.id, `font-id${font.id}`);
  
  // Set submit form event to submit PATCH API request
  fontElement.querySelector('form[data-label="font-form"]').id = `font-id${font.id}`;
  fontElement.querySelector('form[data-label="font-form"]').onsubmit = event => {
    event.preventDefault();
    saveFontForm(font.id, event.target);
  };

  // Disable transfer item to this Font (cannot transfer to itself)
  fontElement.querySelector('.button[data-action="transfer"]').onclick = event => event.preventDefault();
  fontElement.querySelector(`.dropdown[data-value="font_ids"] .item[data-value="${font.id}"]`).classList.add('disabled');

  // Set delete button to submit DELETE API request
  fontElement.querySelector('.negative.button').onclick = event => {
    event.preventDefault();
    deleteFont(font);
  };

  // Reload preview when button is pressed
  const previewCard = fontElement.querySelector('.ui.card');
  const previewImage = fontElement.querySelector('img');
  const fontForm = fontElement.querySelector('form[data-label="font-form"]');
  const previewForm =  fontElement.querySelector('form[data-value="preview-form"]');
  fontElement.querySelector('.card').onclick = () => reloadPreview(font.id, fontForm, previewForm, previewCard, previewImage);
  fontElement.querySelector('.button[data-action="refresh"]').onclick = () => reloadPreview(font.id, fontForm, previewForm, previewCard, previewImage);

  // Update title text + preview when a-z icon is clicked
  const titleInput = fontElement.querySelector('form[data-value="preview-form"] input[name="title_text"]');
  fontElement.querySelector('form[data-value="preview-form"] .field label a').onclick = () => {
    titleInput.value = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ\\nabcdefghijklmnopqrstuvwxyz';
    reloadPreview(font.id, fontForm, previewForm, previewCard, previewImage);
  }

  return fontElement;
}

/**
 * Add blank character replacement input fields for the field closest to the
 * pressing button.
 * @param {HTMLButtonElement} buttonElement Button which was pressed.
 */
function addBlankReplacement(buttonElement) {
  const $form = $(buttonElement).closest('form')
  $form.find('.field[data-value="in-replacements"]').append(
    $('<input name="replacements_in" type="text" placeholder="Text">')
  );
  $form.find('.field[data-value="out-replacements"]').append(
    $('<input name="replacements_out" type="text" placeholder="Delete Character">')
  );
}

/**
 * Groups an array of Fonts by the `sort_name` attribute, starting with the
 * first `n` letters. If a group has at least `maxgroupSize` elements, it
 * further groups by an additional letter recursively. Fonts with names starting
 * with a number are grouped under "#".
 * @param {NamedFont[]} fonts - The array of objects to be grouped. Each object
 * must have a `name` attribute.
 * @param {number} n - The number of initial letters to group by.
 * @param {number} maxgroupSize - The maximum number of elements in a group
 * before subgrouping.
 * @returns {Object.<string, NamedFont[]>} - An object where keys are prefixes
 * and values are arrays of grouped objects.
 */
function groupObjectsByPrefix(fonts, n, maxgroupSize=19) {
  const result = {};

  /**
   * Groups objects by a prefix of their `sort_name` attribute.
   * @param {NamedFont[]} fonts - The array of objects to be grouped.
   * @param {number} prefixLength - The length of the prefix to group by.
   * @returns {Object} - An object where keys are prefixes and values are arrays
   * of grouped objects.
   */
  function groupByPrefix(fonts, prefixLength) {
    const tempGroup = {};
    fonts.forEach(font => {
      let prefix;
      if (/^\d/.test(font.sort_name)) {
        prefix = "#";
      } else {
        prefix = font.sort_name.slice(0, prefixLength);
      }
      if (!tempGroup[prefix]) {
        tempGroup[prefix] = [];
      }
      tempGroup[prefix].push(font);
    });
    return tempGroup;
  }

  /**
   * Processes groups of objects and recursively refines groups that have at
   * least `maxgroupSize` elements.
   * @param {NamedFont[]} objects - The array of objects to be processed.
   * @param {number} prefixLength - The current length of the prefix used for
   * grouping.
   */
  function processGroup(objects, prefixLength) {
    const groups = groupByPrefix(objects, prefixLength);
    for (const prefix in groups) {
      if (groups[prefix].length >= maxgroupSize) {
        const subGroups = groupByPrefix(groups[prefix], prefixLength + 1);
        for (const subPrefix in subGroups) {
          result[subPrefix] = subGroups[subPrefix];
        }
      } else {
        result[prefix] = groups[prefix];
      }
    }
  }

  processGroup(fonts, n);
  return result;
}

/**
 * Submit an API request to query all defined Fonts and add their populated
 * forms to the DOM.
 */
function getAllFonts() {
  $.ajax({
    type: 'GET',
    url: '/api/v2/available/fonts',
    /**
     * Fonts queried, add all Font forms to the DOM.
     * @param {NamedFont[]} fonts 
     */
    success: fonts => {
      // Get the currently active Font from the URL
      const activeFontId = window.location.hash.substring(1);

      // Populate font transfer dropdown in the template
      const transferItems = fonts.map(font => {
        const item = document.createElement('div');
        item.className = 'item';
        item.innerText = font.name;
        item.dataset.value = font.id;
        return item;
      });
      document.getElementById('font-template').content.querySelector('.dropdown[data-value="font_ids"] .menu .menu').replaceChildren(...transferItems);

      const fontElements = [];
      // If there are lots of fonts, group elements under letter sections
      if (fonts.length > 20) {
        let groupedFonts = groupObjectsByPrefix(fonts, 1);
        for (const [letter, fonts] of Object.entries(groupedFonts)) {
          const header = document.createElement('h3');
          header.className = 'ui dividing header';
          header.innerText = (letter === ' ') ? 'Blank Fonts' : (letter[0].toUpperCase() + letter.slice(1));
          fontElements.push(header);

          fonts.forEach(font => {
            // Add accordion for this Font with minimal info
            const template = document.getElementById('font-template').content.cloneNode(true);
            const populatedTemplate = populateFontOverview(template, font);
            fontElements.push(populatedTemplate);
          });
        }
      } else {
        fonts.forEach(font => {
          // Add accordion for this Font with minimal info
          const template = document.getElementById('font-template').content.cloneNode(true);
          const populatedTemplate = populateFontOverview(template, font);
          fontElements.push(populatedTemplate);
        });
      }

      // Put new font elements on the page
      document.getElementById('loader')?.remove();
      document.getElementById('fonts').replaceChildren(...fontElements);
      $('.dropdown[data-value="title_case"]').dropdown();

      // Scroll to active Font if indicated
      if (activeFontId) {
        document.getElementById(activeFontId)?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      }

      // Enable transfer functionality
      $('.dropdown[data-action="transfer"]').dropdown({
          action: 'hide',
          onChange: function(value, text, $selectedItem) {
            showTransferFontDialog(
              $selectedItem.closest('.accordion').data('id'),
              value,
            )
          }
        });

      // Enable accordion/dropdown/checkbox elements
      $('.ui.accordion').accordion({
        onOpen: function () {
          const $accordion = $(this);
          const $form = $accordion.find('form[data-label="font-form"]');
          const id = $accordion.closest('.accordion').data('id');

          // Only populate if not already populated
          if (!$form.find('input[name="name"]').val()) {
            const fontElement = $accordion[0].parentElement;
            const $content = $(fontElement).find('.content.segment');

            $content.addClass('loading');
            $.ajax({
              type: 'GET',
              url: `/api/v2/fonts/font/${id}`,
              /**
               * Font queried, populate the font element with the font object.
               * @param {NamedFont} font 
               */
              success: font => {
                populateFontElement(fontElement, font);

                // Enable form elements
                $form.find('.ui.dropdown').dropdown();
                $form.find('.ui.checkbox').checkbox();

                // Fill in card type dropdowns
                loadCardTypes({
                  element: '.ui.card-type.dropdown',
                  isSelected: (identifier) => identifier === '{{preferences.default_card_type}}',
                  showExcluded: false,
                  dropdownArgs: {},
                });

                // Enable transfer functionality
                $('.dropdown[data-action="transfer"]').dropdown({
                  action: 'hide',
                  onChange: function(value, text, $selectedItem) {
                    showTransferFontDialog(
                      $selectedItem.closest('.accordion').data('id'),
                      value,
                    )
                  }
                });

                // Refresh theme for newly added HTML
                refreshTheme();
              },
              error: response => showErrorToast({title: 'Error Loading Font Details', response}),
              complete: () => $content.removeClass('loading'),
            });
          }
        }
      });
      $('.ui.checkbox').checkbox();

      // Fill in card type dropdowns
      loadCardTypes({
        element: '.ui.card-type.dropdown',
        isSelected: (identifier) => identifier === '{{preferences.default_card_type}}',
        showExcluded: false,
        dropdownArgs: {},
      });

      // Refresh theme for any newly added HTML
      refreshTheme();
    },
    error: response => showErrorToast({title: 'Error Loading Fonts', response}),
  });
}

function initAll() {
  getAllFonts();
}
