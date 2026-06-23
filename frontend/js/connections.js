{% if False %}
import {
  AnyConnection,
  EmbyConnection,
  InterfaceType,
  JellyfinConnection,
  PlexConnection,
  ReturnUserSchema,
  SonarrConnection,
  TMDbConnection,
  TVDbConnection,
} from './.types.js';
{% endif %}

/** @type {number[]} ID's of all invalid Connections. */
const invalidConnectionIDs = {{ preferences.invalid_connections | safe }};
/** @type {boolean} Whether authentication is required */
const requireAuth = {{ preferences.require_auth | lower }};
/** @type {Object.<number, string[]>} Mapping of Connection IDs to library names */
const libraryMap = {
  {% for connection_id, libraries in preferences.libraries.items() %}
  {{ connection_id }}: {{libraries[1] | tojson}},
  {% endfor %}
};

// TVDb ordering types
const tvdbOrderingTypes = [
  {name: 'Absolute', value: 'absolute'},
  {name: 'Alternate (Story)', value: 'alternate'},
  {name: 'Default', value: 'default'},
  {name: 'DVD', value: 'dvd'},
  {name: 'Official', value: 'official'},
  {name: 'Regional', value: 'regional'}
];

const availableTVDbLanguages = [
  { value: "ara", name: "Arabic" },
  { value: "ces", name: "Czech" },
  { value: "dan", name: "Danish" },
  { value: "deu", name: "German" },
  { value: "ell", name: "Greek" },
  { value: "eng", name: "English" },
  { value: "fra", name: "French" },
  { value: "ita", name: "Italian" },
  { value: "kor", name: "Korean" },
  { value: "nld", name: "Dutch" },
  { value: "pol", name: "Polish" },
  { value: "por", name: "Portuguese" },
  { value: "pt", name: "Portuguese (Portugal)" },
  { value: "rus", name: "Russian" },
  { value: "spa", name: "Spanish" },
  { value: "swe", name: "Swedish" },
  { value: "tur", name: "Turkish" },
  { value: "zho", name: "Chinese" },
  { value: "zhtw", name: "Chinese (Traditional)" }
];

/** @type {EmbyConnection | JellyfinConnection | PlexConnection} */
const mediaServerConnections = [
  {% for connection in connections %}
    {% if connection.interface_type in ('Emby', 'Jellyfin', 'Plex')  %}
      {{ connection | tojson }},
    {% endif %}
  {% endfor %}
];

/** @type {AnyConnection[]} List of all defined connections. */
let allConnections = {{ connections | tojson }};

/**
 * Get the global logo language priority, and initialize the dropdown
 * with those values.
 */
let availableLanguages = [];
async function getAvailableLanguages() {
  availableLanguages = await fetch('/api/v2/available/logo-languages').then(resp => resp.json());
}

/**
 * Format the given FastAPI response object into a single string.
 * @param {Object} errorResponse - AJAX response from to format.
 * @param {string | Object} errorResponse.detail - Details of the FastAPI error
 * to add to the return.
 * @returns {string} Formatted HTML string representation of the given response.
 * @example
 * describeErrorsHTML({detail: [{loc: ['body', 'name'], msg: 'Name is required'}]})
 * // returns '<ul class="list"><li><strong>Name</strong>: Name is required</li></ul>'
 */
function describeErrorsHTML(errorObj) {
  if (!errorObj || !Array.isArray(errorObj.detail)) {
    return 'No errors found.';
  }

  const toTitleCase = str =>
    str.replace(/_/g, " ")
       .replace(/\w\S*/g, word => word.charAt(0).toUpperCase() + word.slice(1));

  const items = errorObj.detail.map(err => {
    let loc = [...err.loc];

    // Strip "body" prefix if present
    if (loc.length > 0 && loc[0] === "body") {
      loc = loc.slice(1);
    }

    const field =toTitleCase(loc.join(" "));

    return `<li><strong>${field}</strong>: ${err.msg}</li>`;
  }).join("");

  return `<ul class="list">${items}</ul>`;
}   

/**
 * Populate the title row of a cloned connection card template.
 * @param {DocumentFragment} cardFragment - Cloned connection template.
 * @param { id: number, name: string } connection - Connection metadata.
 */
function setConnectionCardTitle(cardFragment, connection) {
  if (invalidConnectionIDs.includes(connection.id)) {
    cardFragment.querySelector('.connection-title').classList.add('invalid');
  }
  cardFragment.querySelector('.connection-name').textContent = connection.name;
  cardFragment.querySelector('.connection-id-badge').textContent = String(connection.id);
  cardFragment.querySelector('.content').id = `connection${connection.id}`;
}

/**
 * Set a connection form toggle to the given state.
 * @param {number} connectionId - ID of the Connection whose form to update.
 * @param {string} name - Checkbox input name.
 * @param {boolean} checked - Whether the toggle should be on.
 */
function setConnectionToggle(connectionId, name, checked) {
  $(`#connection${connectionId} input[name="${name}"]`).prop('checked', checked);
}

/**
 * Submit the API request to enable authentication. If successful the page is
 * redirected to the login page with a callback to redirect back here if the
 * subsequent login is successful.
 */
function enableAuthentication() {
  $.ajax({
    type: 'POST',
    url: '/api/v2/auth/enable',
    /**
     * Authentication enabled.
     * @param {ReturnUserSchema} returnUser 
     */
    success: (returnUser) => {
      // Show toast, redirect to login page
      $.toast({
        class: 'blue info',
        title: 'Enabled Authentication',
        message: 'You will be redirected to the login page..'
      });

      // If the user is temporary, add parameter to redirect URL
      let redirectURL = '/login?redirect=/connections';
      if (returnUser.temporary) {
        redirectURL += '&temporary=true';
      }

      // After 2.5s, redirect to login with redirect back here
      setTimeout(() => {
        window.location.href = redirectURL;
      }, 2500);
    },
    error: response => showErrorToast({title: 'Error Enabling Authentication', response}),
  });
}

/**
 * Submit the API request to disable authentication. If successful the
 * authentication section is disabled.
 */
function disableAuthentication() {
  $.ajax({
    type: 'POST',
    url: '/api/v2/auth/disable',
    success: () => {
      // Uncheck toggle, disable fields
      $('#require-auth-toggle').prop('checked', false);
      $('#auth-settings .field').toggleClass('disabled', true);

      // Clear username input
      $('#auth-settings input[name="username"]')[0].value = '';

      // Show toast
      $.toast({class: 'warning', title: 'Disabled Authentication'});
    },
    error: response => showErrorToast({title: 'Error Disabling Authentication', response}),
  });
}

/**
 * Submit the API request to edit the current active User's credentials. If
 * successful, the TCM token cookie is cleared, and the page is redirected to
 * the login page with a callback to redirect back here.
 */
function editUserAuth() {
  $.ajax({
    type: 'POST',
    url: '/api/v2/auth/edit',
    data: JSON.stringify({
      username: $('#auth-settings input[name="username"]')[0].value,
      password: $('#auth-settings input[name="password"]')[0].value,
    }), contentType: 'application/json',
    success: () => {
      $.toast({
        class: 'blue info',
        title: 'Credentials Updated',
        message: 'You will be redirected to the login page..',
      });

      // Clear cookie
      document.cookie = `tcm_token=;Max-Age=0;path=/;SameSite=Lax`;

      // Redirect back here
      setTimeout(() => {
        window.location.href = '/login?redirect=/connections';
      }, 1000);
    },
    error: response => showErrorToast({title: 'Unable to Update Credentials', response}),
  });
}

/**
 * Initialize the Authorization form/section. This enabled/disables fields, and
 * assigns functions to all events/presses.
 */
function initializeAuthForm() {
  const $toggle = $('#require-auth-toggle');

  // Enable/disable auth fields based on initial state
  if (requireAuth) {
    $toggle.prop('checked', true);
    $('#auth-settings .field').toggleClass('disabled', false);
  } else {
    $toggle.prop('checked', false);
    $('#auth-settings .field').toggleClass('disabled', true);
  }

  $toggle.on('change', function() {
    if (this.checked) {
      enableAuthentication();
    } else {
      disableAuthentication();
    }
  });

  // Assign edit API request to button press
  $('#auth-settings button').on('click', event => {
    event.preventDefault();
    editUserAuth();
  });
}

/** Add form validation for all the non-Auth and Tautulli connection forms. */
function addFormValidation() {
  // Add form validation
  $('form[form-type="emby"]').form({
    on: 'blur',
    inline: true,
    fields: {
      name: ['empty'],
      url: ['empty'],
      api_key: ['empty'],
      filesize_limit: {
        rules: [
          {
            type: 'regExp',
            value: /^\d+\s+(Bytes|Kilobytes|Megabytes)$/,
            prompt: 'Filesize limits can be in "Bytes", "Kilobytes", or "Megabytes"',
          }
        ]
      }
    },
  });
  $('form[form-type="plex"]').form({
    on: 'blur',
    inline: true,
    fields: {
      name: ['empty'],
      url: ['empty'],
      api_key: ['empty'],
      filesize_limit: {
        rules: [
          {
            type: 'regExp',
            value: /^\d+\s+(Bytes|Kilobytes|Megabytes)$/,
            prompt: 'Filesize limits can be in "Bytes", "Kilobytes", or "Megabytes"',
          }
        ]
      }
    },
  });
  $('form[form-type="sonarr"]').form({
    on: 'blur',
    inline: true,
    fields: {
      name: ['empty'],
      url: ['empty'],
      api_key: ['empty'],
    },
  });
  $('form[form-type="tmdb"],form[form-type="tvdb"]').form({
    on: 'blur',
    inline: true,
    fields: {
      name: ['empty'],
      api_key: ['empty', 'regExp[/^[a-f0-9]+$/gi]'],
      minimum_dimensions: ['empty', 'regExp[/^\d+x\d+$/gi]'],
      language_priority: ['empty', 'minLength[1]'],
    },
  });
}

/**
 * Add form validation to the Tautulli integration form, and assign the API
 * request to the form submission.
 * @param {number} plexInterfaceId - ID of the Plex interface associated with the
 * Tautulli instance.
 */
function initializeTautulliForm(plexInterfaceId) {
  // Add form validation
  $('#tautulli-agent-form').form({
    on: 'blur',
    inline: true,
    fields: {
      url: ['empty'],
      api_key: ['empty'],
      agent_name: {
        optional: true,
        value: ['minLength[1]'],
      },
    },
  }).on('submit', event => {
    // Prevent default event form handler
    event.preventDefault();

    // If the form is not valid, exit
    if (!$('#tautulli-agent-form').form('is valid')) { return; }

    // Add tcm_url if not provided
    const data = Object.fromEntries(new FormData(event.target));
    data.tcm_url = data.tcm_url || window.location.origin;

    // Submit API request
    $('#tautulli-agent-modal button').toggleClass('loading', true);
    $.ajax({
      type: 'POST',
      url: `/api/v2/connection/tautulli/integrate?plex_interface_id=${plexInterfaceId}`,
      data: JSON.stringify(data),
      contentType: 'application/json',
      success: () => {
        // Show toast, disable 
        $.toast({
          class: 'blue info',
          title: `Created "${data.agent_name}" Notification Agent`,
          displayTime: 5000,
        });
        $('#tautulli-agent-modal button').toggleClass('disabled', true);
        $(`#connection${plexInterfaceId} .button[data-action="tautulli"]`).toggleClass('disabled', true);
      },
      error: response => showErrorToast({title: 'Error Creating Notification Agent', response}),
      complete: () => $('#tautulli-agent-modal button').toggleClass('loading', false),
    });
  });
}

/**
 * Add the required HTML elements for a new Sonarr library field to the Form
 * of the Connection with the given ID.
 * @param {number} connectionId - ID of the Connection whose form to add fields
 * to.
 */
function addSonarrLibraryField(connectionId) {
  // Add interface_id dropdown
  const interfaceDropdownTemplate = document.getElementById('interface-dropdown-template');
  const dropdown = interfaceDropdownTemplate.content.cloneNode(true);
  $(`#connection${connectionId} .field[data-value="media_server"]`).append(dropdown);
  $(`#connection${connectionId} .dropdown[data-value="interface_id"]`).last().dropdown({
    placeholder: 'Media Server',
    values: mediaServerConnections.map(({id, name}) => {
      return {value: id, name: name, selected: false};
    }),
  });
  // Add library name and path inputs
  const name = document.createElement('input');
  $(`#connection${connectionId} .field[data-value="library_name"]`).append(name);
  const path = document.createElement('input');
  $(`#connection${connectionId} .field[data-value="library_path"]`).append(path);
  refreshTheme();
}

/**
 * Submit an API request to update the given Connection. This parses the given
 * form, and adds any checkboxes or given jsonData to the submitted JSON object.
 * @param {HTMLFormElement} form - Form with Connection details to parse.
 * @param {number} connectionId - ID of the Connection being updated.
 * @param {InterfaceType} connectionType - Type of Connection being modified.
 * @param {Object} jsonData - Extra JSON data to include in the API request
 * payload.
 */
function updateConnection(form, connectionId, connectionType, jsonData) {
  $(`#connection${connectionId} .button[data-action="save"]`).toggleClass('loading', true);
  // Add checkbox status as true/false
  $.each($(`#connection${connectionId}`).find('input[type=checkbox]'), (key, val) => {
    form.append($(val).attr('name'), $(val).is(':checked'))
  });

  $.ajax({
    type: 'PATCH',
    url: `/api/v2/connection/${connectionType.toLowerCase()}/${connectionId}`,
    data: JSON.stringify({
      ...Object.fromEntries(form.entries()),
      ...jsonData,
    }),
    contentType: 'application/json',
    success: updatedConnection => showInfoToast(`Updated Connection "${updatedConnection.name}"`),
    error: response => showErrorToast({title: 'Error Updating Connection', response}),
    complete: () => $(`#connection${connectionId} .button[data-action="save"]`).toggleClass('loading', false),
  });
}

/**
 * Submit an API request to delete the Connection object with the given ID.
 * @param {number} connectionId - ID of the Connection being deleted.
 * @param {boolean} deleteCards - Whether to delete Cards associated with the
 * Connection.
 */
function _deleteConnectionRequest(connectionId, deleteCards=false) {
  $.ajax({
    type: 'DELETE',
    url: `/api/v2/connection/${connectionId}?delete_title_cards=${deleteCards}`,
    success: () => {
      showInfoToast('Deleted Connection');
      if (deleteCards) { showInfoToast('Deleted Title Cards'); }
      showInfoToast('Reloading page..');
      setTimeout(window.location.reload, 2500);
    },
    error: response => showErrorToast({title: 'Error Deleting Connection', response}),
  });
}

/**
 * Submit an API request to query the latest libraries from the Connection with
 * the given ID.
 * @param {number} connectionId ID of the Connection whose list to refresh.
 */
function _refreshLibraryList(connectionId) {
  // Clear existing list
  $(`#connection${connectionId} .labels[data-value="libraries"]`).empty()

  // Query for new list
  $.ajax({
    type: 'POST',
    url: `/api/v2/connection/${connectionId}/libraries`,
    /**
     * Libraries queried - update labels.
     * @param {string[]} libraries List of libraries for the Connection.
     */
    success: libraries => {
      showInfoToast('Libraries Updated');
      $(`#connection${connectionId} .labels[data-value="libraries"]`)
        .empty()
        .append(libraries.map(library => $(`<div class="ui label">${library}</div>`)));
    },
    /** Error querying libraries, show toast  */
    error: response => showErrorToast({title: 'Error Querying Libraries', response}),
  })
}

/**
 * Submit an API request to delete any unlinked libraries which are assigned to
 * a Series but not a part of the given Connection's latest list.
 * @param {number} connectionId ID of the Connection whose unlinked libraries to
 * delete.
 */
function _deleteUnlinkedLibraries(connectionId) {
  // Mark icon as loading
  const $icon = $(`#connection${connectionId} [data-action="delete-libraries"] .icon`);
  setLoadingIcon($icon);

  // Submit API request
  $.ajax({
    type: 'DELETE',
    url: `/api/v2/connection/${connectionId}/libraries?unlinked=true`,
    success: changedCount => showInfoToast(`Modified ${changedCount} Series`),
    /** Error deleting libraries, show toast  */
    error: response => showErrorToast({title: 'Error Deleting Libraries', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Submit an API request to delete all reference to the given library for the
 * given Connection.
 * @param {number} connectionId ID of the Connection whose library reference is
 * being deleted.
 * @param {string} libraryName Name of the library reference to delete from all
 * Series.
 */
function deleteLibrary(connectionId, libraryName) {
  // Mark icon as loading
  const $icon = $(`#connection${connectionId} .label[data-library-name="${libraryName}"] .icon`);
  setLoadingIcon($icon);

  // Submit API request
  const args = new URLSearchParams({library_name: libraryName})
  $.ajax({
    type: 'DELETE',
    url: `/api/v2/connection/${connectionId}/libraries?${args.toString()}`,
    success: changedCount => showInfoToast(`Modified ${changedCount} Series`),
    /** Error deleting libraries, show toast  */
    error: response => showErrorToast({title: 'Error Deleting Libraries', response}),
    complete: () => removeLoadingIcon($icon),
  });
}

/**
 * Display a temporary modal which asks the user to confirm the Connection
 * deletion. If confirmed, then submit an API request to delete the Connection
 * with the given ID. If that is successful, then the HTML element(s) for this
 * Connection are removed from the page and the Sonarr connections are
 * re-initialized (so they may display the correct library dropdowns).
 * @param {number} connectionId - ID of the Connection being deleted.
 * @param {boolean} [isMediaServer] - Whether the Connection is a media server.
 * If true, then the indicated warning text is slightly modified.
 */
function deleteConnection(connectionId, isMediaServer=false) {
  // Internal modal content
  let content = `
  <span class="ui large red text"><b>This action cannot be undone.</b></span><br><br>
  <span class="ui text">This <span class="ui red text">will</span> delete any linked Syncs, and remove assigned Libraries.</span><br>
  <span>It <span class="ui red text">may</span> modify your global Episode Data Source and Image Source Priority.</span><br>`;
  if (isMediaServer) {
    content += `<span>It <span class="ui red text">can</span> delete Title Cards.</span>`;
  }

  // Actions within the modal
  const actions = [
    // Do not delete - no action
    {text: 'No', icon: 'remove', class: 'green ok basic inverted'},
    // Delete Connection only
    {
      text: 'Yes, delete this Connection',
      icon: 'trash alternate outline',
      class: 'red inverted',
      click: () => _deleteConnectionRequest(connectionId, false),
    },
  ];
  if (isMediaServer) {
    actions.push({
      text: 'Yes, delete this Connection and any associated Title Cards',
      icon: 'dumpster',
      class: 'red inverted',
      click: () => _deleteConnectionRequest(connectionId, true),
    });
  }

  // Create and display modal
  $.modal({
    classTitle: 'ui icon header',
    title: '<i class="trash icon"></i>Delete Connection?',
    class: 'basic',
    content: content,
    classContent: 'center aligned',
    actions: actions,
    classActions: 'center aligned',
  }).modal('show');
}

/**
 * Initialize the Emby portion of the page with all Emby Connections.
 */
function initializeEmby() {
  /** @type {EmbyConnection[]} */
  const connections = allConnections.filter(connection => connection.interface_type === 'Emby');

  const embyTemplate = document.getElementById('emby-connection-template');

  // Add accordions for each Connection
  const embyForms = connections.map(connection => {
    const embyForm = embyTemplate.content.cloneNode(true);
    setConnectionCardTitle(embyForm, connection);
    embyForm.querySelector('input[name="name"]').value = connection.name;
    embyForm.querySelector('input[name="url"]').value = connection.url;
    embyForm.querySelector('input[name="api_key"]').value = connection.api_key;
    // Username later
    // SSL later
    embyForm.querySelector('input[name="filesize_limit"]').value = connection.filesize_limit;
    embyForm.querySelector('[data-action="delete-libraries"]').onclick = () => _deleteUnlinkedLibraries(connection.id);

    return embyForm;
  });
  document.getElementById('emby-connections').replaceChildren(...embyForms);

  // Initialize elements of Form
  connections.forEach(connection => {
    // Enabled
    setConnectionToggle(connection.id, 'enabled', connection.enabled);
    // Query for usernames to initialize Dropdown if Connection is enabled
    if (connection.enabled) {
      $.ajax({
        type: 'GET',
        url: `/api/v2/available/usernames/emby?interface_id=${connection.id}`,
        success: usernames => {
          $(`#connection${connection.id} .dropdown[data-value="username"]`).dropdown({
            values: usernames.map(username => {
              return {
                name: username,
                value: username,
                selected: username === connection.username
              };
            }),
          });
        },
        error: response => showErrorToast({title: `Error Querying ${connection.name} Usernames`, response}),
      });
    } else if (connection.username) {
      const dropdown = $(`#connection${connection.id} .dropdown[data-value="username"]`);
      dropdown.toggleClass('disabled', true);
      dropdown.dropdown({
        values: [{name: connection.username, value: connection.username, selected: true}],
      });
    }
    // SSL
    setConnectionToggle(connection.id, 'use_ssl', connection.use_ssl);
    // Libraries
    const libraries = libraryMap[connection.id]?.map(library => $(`<div class="ui right icon label" data-library-name="${library}">${library}<i class="trash alternate outline link icon" onclick="deleteLibrary(${connection.id}, '${library}')"></i></div>`));
    $(`#connection${connection.id} .labels[data-value="libraries"]`).append(libraries);
    document.querySelector(`#connection${connection.id} [data-action="refresh-libraries"]`).onclick = () => _refreshLibraryList(connection.id);

    // Assign save function to button
    $(`#connection${connection.id} form`).on('submit', (event) => {
      event.preventDefault();
      if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
      updateConnection(new FormData(event.target), connection.id, 'Emby');
    });

    // Assign delete function to button
    $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
      event.preventDefault();
      deleteConnection(connection.id, true);
    });
  });

  addFormValidation();
  refreshTheme();
}

/**
 * Initialize the Jellyfin portion of the page with all Jellyfin Connections.
 */
function initializeJellyfin() {
  /** @type {JellyfinConnection[]} */
  const connections = allConnections.filter(connection => connection.interface_type === 'Jellyfin');

  const jellyfinTemplate = document.getElementById('emby-connection-template');

  // Add accordions for each Connection
  const jellyfinForms = connections.map(connection => {
    const jellyfinForm = jellyfinTemplate.content.cloneNode(true);
    setConnectionCardTitle(jellyfinForm, connection);
    jellyfinForm.querySelector('input[name="name"]').value = connection.name;
    jellyfinForm.querySelector('input[name="url"]').value = connection.url;
    jellyfinForm.querySelector('input[name="api_key"]').value = connection.api_key;
    // Username later
    // SSL later
    jellyfinForm.querySelector('input[name="filesize_limit"]').value = connection.filesize_limit;
    jellyfinForm.querySelector('[data-action="delete-libraries"]').onclick = () => _deleteUnlinkedLibraries(connection.id);

    return jellyfinForm;
  });
  document.getElementById('jellyfin-connections').replaceChildren(...jellyfinForms);

  // Initialize elements of Form
  connections.forEach(connection => {
    // Enabled
    setConnectionToggle(connection.id, 'enabled', connection.enabled);
    // Query for usernames to initialize Dropdown if Connection is enabled
    if (connection.enabled) {
      $.ajax({
        type: 'GET',
        url: `/api/v2/available/usernames/jellyfin?interface_id=${connection.id}`,
        success: usernames => {
          $(`#connection${connection.id} .dropdown[data-value="username"]`).dropdown({
            values: usernames.map(username => {
              return {
                name: username,
                value: username,
                selected: username === connection.username
              };
            }),
          });
        }, error: response => showErrorToast({title: `Error Querying ${connection.name} Usernames`, response}),
      });
    } else if (connection.username) {
      const dropdown = $(`#connection${connection.id} .dropdown[data-value="username"]`);
      dropdown.toggleClass('disabled', true);
      dropdown.dropdown({
        values: [{name: connection.username, value: connection.username, selected: true}],
      });
    }

    // SSL
    setConnectionToggle(connection.id, 'use_ssl', connection.use_ssl);

    // Libraries
    const libraries = libraryMap[connection.id]?.map(library => $(`<div class="ui right icon label" data-library-name="${library}">${library}<i class="trash alternate outline link icon" onclick="deleteLibrary(${connection.id}, '${library}')"></i></div>`));
    $(`#connection${connection.id} .labels[data-value="libraries"]`).append(libraries);
    document.querySelector(`#connection${connection.id} [data-action="refresh-libraries"]`).onclick = () => _refreshLibraryList(connection.id);

    // Assign save function to button
    $(`#connection${connection.id} form`).on('submit', (event) => {
      event.preventDefault();
      if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
      updateConnection(new FormData(event.target), connection.id, 'Jellyfin');
    });
    // Assign delete function to button
    $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
      event.preventDefault();
      deleteConnection(connection.id, true);
    });
  });
  
  addFormValidation();
  refreshTheme();
}

/*
 * Initialize the Plex portion of the page with all Plex Connections.
 */
function initializePlex() {
  /** @type {PlexConnection[]} */
  const connections = allConnections.filter(connection => connection.interface_type === 'Plex');

  const plexTemplate = document.getElementById('plex-connection-template');
  const plexSection = document.getElementById('plex-connections');

  // Add accordions for each Connection
  const plexForms = connections.map(connection => {
    const plexForm = plexTemplate.content.cloneNode(true);
    setConnectionCardTitle(plexForm, connection);
    plexForm.querySelector('input[name="name"]').value = connection.name;
    plexForm.querySelector('input[name="url"]').value = connection.url;
    plexForm.querySelector('input[name="api_key"]').value = connection.api_key;
    // SSL later
    // Kometa integration later
    plexForm.querySelector('input[name="filesize_limit"]').value = connection.filesize_limit;
    plexForm.querySelector('[data-action="delete-libraries"]').onclick = () => _deleteUnlinkedLibraries(connection.id);

    return plexForm;
  });
  plexSection.replaceChildren(...plexForms);

  // Initialize elements of Form
  connections.forEach(connection => {
    // Enabled
    setConnectionToggle(connection.id, 'enabled', connection.enabled);
    // SSL
    setConnectionToggle(connection.id, 'use_ssl', connection.use_ssl);
    // Integrate with Kometa
    setConnectionToggle(connection.id, 'integrate_with_kometa', connection.integrate_with_kometa);

    // Assign appropriate Tautulli modal form launch to button
    $(`#connection${connection.id} .button[data-action="tautulli"]`).on('click', () => {
      initializeTautulliForm(connection.id);
      $('#tautulli-agent-modal')
        .modal({blurring: true})
        .modal('show');
    });

    // Libraries
    const libraries = libraryMap[connection.id]?.map(library => $(`<div class="ui right icon label" data-library-name="${library}">${library}<i class="trash alternate outline link icon" onclick="deleteLibrary(${connection.id}, '${library}')"></i></div>`));
    $(`#connection${connection.id} .labels[data-value="libraries"]`).append(libraries);
    document.querySelector(`#connection${connection.id} [data-action="refresh-libraries"]`).onclick = () => _refreshLibraryList(connection.id);

    // Assign save function to button
    $(`#connection${connection.id} form`).on('submit', (event) => {
      event.preventDefault();
      if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
      updateConnection(new FormData(event.target), connection.id, 'Plex');
    });

    // Assign delete function to button
    $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
      event.preventDefault();
      deleteConnection(connection.id, true);
    });
  });

  addFormValidation();
  refreshTheme();
}

/*
 * Initialize the Sonarr portion of the page with all Sonarr Connections.
 */
function initializeSonarr() {
  /** @type {SonarrConnection[]} */
  const connections = allConnections.filter(connection => connection.interface_type === 'Sonarr');

  const sonarrTemplate = document.getElementById('sonarr-connection-template');
  const sonarrSection = document.getElementById('sonarr-connections');
  const interfaceDropdownTemplate = document.getElementById('interface-dropdown-template');

  // Add accordions for each Connection
  const sonarrForms = connections.map(connection => {
    const sonarrForm = sonarrTemplate.content.cloneNode(true);
    setConnectionCardTitle(sonarrForm, connection);
    // Remove warning for existing connections
    sonarrForm.querySelector('.warning.message').remove();
    sonarrForm.querySelector('input[name="name"]').value = connection.name;
    sonarrForm.querySelector('input[name="url"]').value = connection.url;
    sonarrForm.querySelector('input[name="api_key"]').value = connection.api_key;
    // SSL later
    // Downloaded only later
    // Libraries
    connection.libraries.forEach(({name, path}) => {
      // media_server later
      const dropdown = interfaceDropdownTemplate.content.cloneNode(true);
      sonarrForm.querySelector('.field[data-value="libraries"] .field[data-value="media_server"]').appendChild(dropdown);
      const nameInput = document.createElement('input'); nameInput.name = 'library_name'; nameInput.value = name;
      sonarrForm.querySelector('.field[data-value="libraries"] .field[data-value="library_name"]').appendChild(nameInput);
      const pathInput = document.createElement('input'); pathInput.name = 'library_path'; pathInput.value = path;
      sonarrForm.querySelector('.field[data-value="libraries"] .field[data-value="library_path"]').appendChild(pathInput);
    });
    // Add/query library buttons later

    return sonarrForm;
  });
  sonarrSection.replaceChildren(...sonarrForms);

  // Initialize elements of Form
  connections.forEach(connection => {
    // Enabled
    setConnectionToggle(connection.id, 'enabled', connection.enabled);
    // SSL
    setConnectionToggle(connection.id, 'use_ssl', connection.use_ssl);
    // Downloaded only
    setConnectionToggle(connection.id, 'downloaded_only', connection.downloaded_only);
    // Library interface dropdowns
    connection.libraries.forEach(({interface_id}, index) => {
      $(`#connection${connection.id} .dropdown[data-value="interface_id"]`).eq(index).dropdown({
        placeholder: 'Media Server',
        values: mediaServerConnections.map(({id, name}) => {
          return {value: id, name: name, selected: id === interface_id};
        }),
      })
    });
    // Add new library field on click
    $(`#connection${connection.id} .button[data-action="add-library"]`).on('click', () => addSonarrLibraryField(connection.id));
    // Query libraries on click
    $(`#connection${connection.id} .button[data-action="query-libraries"]`).on('click', () => {
      $.ajax({
        type: 'GET',
        url: `/api/v2/connection/sonarr/${connection.id}/libraries`,
        success: libraries => {
          // Add new library fields if needed
          const inputCount = $(`#connection${connection.id} .field[data-value="library_name"] input`).length;
          if (inputCount < libraries.length) {
            [...Array(libraries.length - inputCount)].map(() => addSonarrLibraryField(connection.id));
          }
          libraries.forEach(({name, path}, index) => {
            $(`#connection${connection.id} .field[data-value="library_name"] input`).eq(index).val(name);
            $(`#connection${connection.id} .field[data-value="library_path"] input`).eq(index).val(path);
          });
        }, error: response => showErrorToast({title: 'Error Querying Libraries', response}),
      });
    });
    // Assign save function to button
    $(`#connection${connection.id} form`).on('submit', (event) => {
      event.preventDefault();
      if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
      const form = new FormData(event.target);
      // Add library list data
      const libraryData = [];
      $(`#connection${connection.id} .field[data-value="library_name"] input`).each((index, element) => {
        const path = $(`#connection${connection.id} .field[data-value="library_path"] input`).eq(index).val();
        if (path !== "") {
          libraryData.push({
            name: element.value,
            path: path,
            interface_id: $(`#connection${connection.id} .dropdown[data-value="interface_id"] input`).eq(index).val(),
          });
        }
      });
      updateConnection(form, connection.id, 'Sonarr', {libraries: libraryData});
    });
    // Assign delete function to button
    $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
      event.preventDefault();
      deleteConnection(connection.id);
    });
  });

  addFormValidation();
  refreshTheme();
}

/*
 * Initialize the TMDb portion of the page with all TMDb Connections.
 */
function initializeTMDb() {
  /** @type {TMDbConnection[]} */
  const connections = allConnections.filter(connection => connection.interface_type === 'TMDb');

  const tmdbTemplate = document.getElementById('tmdb-connection-template');
  const tmdbSection = document.getElementById('tmdb-connections');

  // Add accordions for each Connection
  const tmdbForms = connections.map(connection => {
    const tmdbForm = tmdbTemplate.content.cloneNode(true);
    setConnectionCardTitle(tmdbForm, connection);
    tmdbForm.querySelector('input[name="name"]').value = connection.name;
    tmdbForm.querySelector('input[name="api_key"]').value = connection.api_key;
    tmdbForm.querySelector('input[name="minimum_dimensions"]').value = connection.minimum_dimensions;
    // Language priority later
    return tmdbForm;
  });
  tmdbSection.replaceChildren(...tmdbForms);

  // Initialize elements of Form
  connections.forEach(connection => {
    // Enabled
    setConnectionToggle(connection.id, 'enabled', connection.enabled);
    // Ignore localized images
    setConnectionToggle(connection.id, 'skip_localized', connection.skip_localized);
    // Initialize logo language priority dropdown
    $(`#connection${connection.id} .dropdown[data-value="language_priority"]`).dropdown({
      values: availableLanguages.map(language => {
        return {
          name: language.name,
          value: language.value,
          selected: connection.language_priority.includes(language.value),
        };
      }),
    });
    // Assign save function to button
    $(`#connection${connection.id} form`).on('submit', (event) => {
      event.preventDefault();
      if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
      updateConnection(new FormData(event.target), connection.id, 'TMDb');
    });
    // Assign delete function to button
    $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
      event.preventDefault();
      deleteConnection(connection.id);
    });
  });

  addFormValidation();
  refreshTheme();
}

/*
 * Initialize the TVDb portion of the page with all TMDb Connections.
 */
function initializeTVDb() {
  /** @type {TVDbConnection[]} */
  const connections = allConnections.filter(connection => connection.interface_type === 'TVDb');

  const tvdbTemplate = document.getElementById('tvdb-connection-template');
  const tvdbSection = document.getElementById('tvdb-connections');

  // Add accordions for each Connection
  const tvdbForms = connections.map(connection => {
    const tvdbForm = tvdbTemplate.content.cloneNode(true);
    setConnectionCardTitle(tvdbForm, connection);
    tvdbForm.querySelector('input[name="name"]').value = connection.name;
    tvdbForm.querySelector('input[name="api_key"]').value = connection.api_key;
    tvdbForm.querySelector('input[name="minimum_dimensions"]').value = connection.minimum_dimensions;
    // Language priority later
    // Ordering later
    // Include movies later
    return tvdbForm;
  });
  tvdbSection.replaceChildren(...tvdbForms);

  // Initialize elements of Form
  connections.forEach(connection => {
    // Enabled
    setConnectionToggle(connection.id, 'enabled', connection.enabled);
    // Ignore movies
    setConnectionToggle(connection.id, 'include_movies', connection.include_movies);
    // Initialize language priority dropdown
    $(`#connection${connection.id} .dropdown[data-value="language_priority"]`).dropdown({
      values: availableTVDbLanguages.map(language => {
        return {
          name: language.name,
          value: language.value,
          selected: connection.language_priority.includes(language.value),
        };
      }),
    });
    // Initialize episode ordering dropdown
    $(`#connection${connection.id} .dropdown[data-value="episode_ordering"]`).dropdown({
      values: tvdbOrderingTypes.map(ordering => {
        return {
          name: ordering.name,
          value: ordering.value,
          selected: connection.episode_ordering === ordering.value,
        };
      }),
    });
    // Assign save function to button
    $(`#connection${connection.id} form`).on('submit', (event) => {
      event.preventDefault();
      if (!$(`#connection${connection.id} form`).form('is valid')) { return; }
      updateConnection(new FormData(event.target), connection.id, 'TVDb');
    });
    // Assign delete function to button
    $(`#connection${connection.id} button[data-action="delete"]`).on('click', (event) => {
      event.preventDefault();
      deleteConnection(connection.id);
    });
  });

  addFormValidation();
  refreshTheme();
}

let tempFormId = 0;
/**
 * Add a new (blank) Connection of the given type to the UI. This adjusts the
 * save button to submit a POST request instead of PATCH. 
 * @param {"emby" | "jellyfin" | "plex" | "sonarr" | "tmdb" | "tvdb"} connectionType
 */
function addConnection(connectionType) {
  // Get the template for this Connection - Jellyfin uses Emby template
  let template;
  if (connectionType === 'jellyfin' || connectionType == 'emby') {
    template = document.getElementById('emby-connection-template').content.cloneNode(true);
  } else {
    template = document.getElementById(`${connectionType}-connection-template`).content.cloneNode(true);
  }

  // Disable other add Connection buttons
  $('.add-connection.button').toggleClass('disabled', true);

  // Add ID to form
  let formId = `new-connection${tempFormId}`
  template.querySelector('form').id = formId;
  tempFormId++;

  // Update element
  if (connectionType === 'sonarr') {
    // Disable library fields
    template.querySelector('.button[data-action="add-library"]').classList.add('disabled');
    template.querySelector('.button[data-action="query-libraries"]').classList.add('disabled');
  } else if (connectionType === 'plex') {
    // Disable Tautulli button
    template.querySelector('.button[data-action="tautulli"]').classList.add('disabled');
  } else if (connectionType === 'tmdb') {
    // Disable language dropdowns until added
    template.querySelector('.field[data-value="language_priority"]').classList.add('disabled');
  } else if (connectionType === 'tvdb') {
    // Remove dropdowns until Connection is added
    template.querySelector('.field[data-value="language_priority"]').remove();
    template.querySelector('.field[data-value="episode_ordering"]').remove();
  } else if (connectionType === 'emby' || connectionType === 'jellyfin') {
    // Remove username dropdown until added
    template.querySelector('.field[data-value="username"]').remove();
  }

  // Set accordion as active
  template.querySelector('.connection-title').classList.add('active');
  template.querySelector('.connection-content').classList.add('active');

  // Turn save button into create
  template.querySelector('button[data-action="save"]').innerHTML = '<i class="add icon"></i> Create';
  
  // Assign post API request to form submission
  template.querySelector('form').onsubmit = (event) => {
    event.preventDefault();
    // Parse form and submit API request
    let form = new FormData(event.target);
    $.each($(`#${formId}`).find('input[type=checkbox]'), (key, val) => {
      form.append($(val).attr('name'), $(val).is(':checked'));
    });

    $.ajax({
      type: 'POST',
      url: `/api/v2/connection/${connectionType}/new`,
      data: JSON.stringify({...Object.fromEntries(form.entries())}),
      contentType: 'application/json',
      /**
       * Connection created, display a toast and reload the page.
       * @param {AnyConnection} newConnection Newly created connection.
       */
      success: newConnection => {
        showInfoToast({title:`Created Connection "${newConnection.name}"`, message: 'Reloading page..'});
        document.getElementById(formId).classList.remove('error');
        setTimeout(() => window.location.reload(), 2000);
      },
      error: response => {
        showErrorToast({title: 'Error Creating Connection', response});
        // Update error message in the Form
        document.querySelector(`#${formId} .error.message p`).innerHTML = describeErrorsHTML(response.responseJSON);
        document.getElementById(formId).classList.add('error');
      },
    });
  };

  // Delete delete button
  template.querySelector('button[data-action="delete"]').remove();

  // Add Connection to relevant section, open accordion
  const connectionsList = document.getElementById(`${connectionType.toLowerCase()}-connections`);
  connectionsList.appendChild(template);
  const newCard = connectionsList.lastElementChild;
  $(newCard).accordion();
  $(newCard).accordion('open', 0);

  // Refresh theme
  refreshTheme();
  addFormValidation();
}

async function initAll() {
  initializeEmby();
  initializeJellyfin();
  initializePlex();
  initializeSonarr();
  await getAvailableLanguages();
  initializeTMDb();
  initializeTVDb();

  // Enable elements
  $('.ui.dropdown').dropdown();
  $('.connection-card.ui.accordion').accordion();

  initializeAuthForm();
}
