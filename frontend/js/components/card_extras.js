/**
 * Card extras UI: card type in settings-panel header + stacked field panels, native selects.
 * Depends on helper.js: toTitleCase, queryAvailableExtras, allExtras, filteredExtras,
 * updateLinkedFields, updateColorBubble.
 */

/**
 * @param {string|null|undefined} tooltip
 * @returns {string}
 */
function formatExtraTooltipHtml(tooltip) {
  if (!tooltip) {
    return '';
  }
  return tooltip
    .replaceAll('<v>', '<span class="ui blue text inverted">')
    .replaceAll('</v>', '</span>')
    .replaceAll(
      /<c>(.*?)<\/c>/g,
      '<code class="color">$1<span style="--color: $1" class="color circle"></span></code>',
    );
}

function sortedCardTypeKeys(types) {
  return Object.keys(types).sort((a, b) => {
    if (a === 'Variable Overrides') {
      return -1;
    }
    if (b === 'Variable Overrides') {
      return 1;
    }
    return toTitleCase(a).localeCompare(toTitleCase(b));
  });
}

/**
 * @param {HTMLElement} section
 * @returns {string[]}
 */
function getExtrasCardTypeKeysFromRoot(section) {
  const root = section.querySelector('.card-extras-root');
  if (!root) {
    return [];
  }
  const raw = root.getAttribute('data-extras-card-type-keys');
  if (!raw) {
    const sel = section.querySelector('.card-extras-type-select');
    return sel ? [...sel.options].map((o) => o.value) : [];
  }
  try {
    return JSON.parse(raw);
  } catch (_e) {
    return [];
  }
}

/**
 * Show the panel for the selected card type (all extras rows visible).
 * @param {HTMLElement} section
 */
function syncCardExtrasPanels(section) {
  const typeSelect = section.querySelector('.card-extras-type-select');
  if (!typeSelect) {
    return;
  }
  const val = typeSelect.value;
  section.querySelectorAll('.card-extra-type-panel').forEach((panel) => {
    const ct = panel.getAttribute('data-card-type');
    panel.hidden = ct !== val;
  });
}

/**
 * @param {Object} extra
 * @param {HTMLTemplateElement} inputTemplateElement
 * @param {Object} opts
 * @param {boolean} opts.templateMode
 * @param {string} [opts.activeValue]
 * @returns {DocumentFragment|HTMLElement}
 */
function buildCardExtraField(extra, inputTemplateElement, opts) {
  const defaultText = extra.default === null || extra.default === undefined
    ? 'Default'
    : extra.default;
  const allowed = extra.allowed_values && extra.allowed_values.length
    ? extra.allowed_values
    : null;

  if (allowed) {
    const field = document.createElement('div');
    field.className = 'field card-extra-field';
    field.dataset.label = extra.name;

    const label = document.createElement('label');
    label.textContent = extra.name;

    const select = document.createElement('select');
    select.className = 'card-extra-native-select';
    select.name = extra.identifier;
    select.setAttribute('onchange', 'updateLinkedFields(this);');

    const optDefault = document.createElement('option');
    optDefault.value = '';
    optDefault.textContent = `Default (${defaultText})`;
    select.appendChild(optDefault);

    allowed.forEach((v) => {
      const o = document.createElement('option');
      o.value = String(v);
      o.textContent = String(v);
      select.appendChild(o);
    });

    if (opts.activeValue !== undefined && opts.activeValue !== null && opts.activeValue !== '') {
      const s = String(opts.activeValue);
      if ([...select.options].some((o) => o.value === s)) {
        select.value = s;
      }
    }

    const help = document.createElement('p');
    help.className = 'help';
    help.innerHTML = `<b>${extra.description}</b><br>${formatExtraTooltipHtml(extra.tooltip)}`;

    field.appendChild(label);
    field.appendChild(select);
    field.appendChild(help);
    return field;
  }

  const frag = inputTemplateElement.content.cloneNode(true);
  if (extra.name.endsWith('Color')) {
    frag.querySelector('label').innerHTML = `${extra.name}<span data-name="${extra.name}" class="inline color circle" style="--default-color: ${defaultText}"></span>`;
  } else {
    frag.querySelector('label').innerText = extra.name;
    if (opts.templateMode) {
      frag.querySelector('input').removeAttribute('oninput');
    }
  }

  const fieldEl = frag.querySelector('.field');
  fieldEl.classList.add('card-extra-field');
  fieldEl.dataset.label = extra.name;

  const textInput = frag.querySelector('input');
  textInput.name = extra.identifier;
  textInput.placeholder = String(defaultText);
  textInput.setAttribute('onchange', 'updateLinkedFields(this);');
  frag.querySelector('.help').innerHTML = `<b>${extra.description}</b><br>${formatExtraTooltipHtml(extra.tooltip)}`;

  const unitRegex = /Unit is (\S+)\./;
  if (extra.tooltip && extra.tooltip.match(unitRegex)) {
    const unit = extra.tooltip.match(unitRegex)[1];
    frag.querySelector('.basic.label').innerText = unit === 'pixels' ? 'px' : unit;
  } else {
    frag.querySelector('.right.labeled').classList.remove('right', 'labeled');
    frag.querySelector('.basic.label').remove();
  }

  if (opts.activeValue !== undefined && opts.activeValue !== null && opts.activeValue !== '') {
    const thisValue = opts.activeValue;
    textInput.value = thisValue;
    if (extra.name.endsWith('Color')) {
      frag.querySelector('.field label > .color.circle')?.style.setProperty('--color', thisValue);
    }
  }

  return frag;
}

/**
 * @param {HTMLElement} section
 * @param {Object.<string, Object[]>} types
 * @param {HTMLTemplateElement} inputTemplateElement
 * @param {Object} opts
 * @param {?string} opts.activeTab
 * @param {boolean} opts.isGlobal
 * @param {number} opts.groupAmount
 * @param {?Object} opts.activeExtras
 * @param {boolean} opts.templateMode
 */
function mountCardExtras(section, types, inputTemplateElement, opts) {
  const {
    activeTab,
    isGlobal,
    groupAmount,
    activeExtras,
    templateMode,
  } = opts;

  section.replaceChildren();
  section._tcmExtrasTypes = types;

  const root = document.createElement('div');
  root.className = 'settings-panel card-extras-root';

  const header = document.createElement('div');
  header.className = 'settings-panel-header card-extras-type-header';

  const icon = document.createElement('i');
  icon.className = 'sliders horizontal icon';

  const title = document.createElement('span');
  title.className = 'card-extras-header-title';
  title.textContent = 'Extras';

  const typeSelect = document.createElement('select');
  typeSelect.className = 'card-extras-type-select';
  typeSelect.setAttribute('aria-label', 'Card type for extras');

  header.appendChild(icon);
  header.appendChild(title);
  header.appendChild(typeSelect);

  const bodySection = document.createElement('section');
  bodySection.className = 'card-extras-body';

  const panelHost = document.createElement('div');
  panelHost.className = 'card-extras-panel-host';

  bodySection.appendChild(panelHost);
  root.appendChild(header);
  root.appendChild(bodySection);
  section.appendChild(root);

  const keys = sortedCardTypeKeys(types);
  root.setAttribute('data-extras-card-type-keys', JSON.stringify(keys));

  keys.forEach((card_type) => {
    const extras = types[card_type];

    const panel = document.createElement('div');
    panel.className = 'card-extra-type-panel';
    panel.setAttribute('data-card-type', card_type);

    const body = document.createElement('div');
    body.className = 'card-extra-panel-fields';

    panel.appendChild(body);
    panelHost.appendChild(panel);

    extras.forEach((extra, index) => {
      let activeValue;
      if (activeExtras && typeof activeExtras === 'object' && !Array.isArray(activeExtras)) {
        if (isGlobal && activeExtras[card_type]
            && Object.prototype.hasOwnProperty.call(activeExtras[card_type], extra.identifier)) {
          activeValue = activeExtras[card_type][extra.identifier];
        } else if (!isGlobal
            && Object.prototype.hasOwnProperty.call(activeExtras, extra.identifier)) {
          activeValue = activeExtras[extra.identifier];
        }
      }

      const node = buildCardExtraField(extra, inputTemplateElement, {
        templateMode,
        activeValue,
      });

      if (index % groupAmount === 0) {
        const newFields = document.createElement('div');
        newFields.className = 'ui equal width fields';
        body.appendChild(newFields);
      }
      body.lastChild.appendChild(node);
    });
  });

  keys.forEach((k) => {
    const opt = document.createElement('option');
    opt.value = k;
    opt.textContent = toTitleCase(k);
    typeSelect.appendChild(opt);
  });

  const initial = activeTab && keys.includes(activeTab) ? activeTab : (keys[0] || '');
  typeSelect.value = initial;

  syncCardExtrasPanels(section);
}

/**
 * Populate the extras section of an HTML Template (no live values).
 * @param {Object} args
 * @param {HTMLElement} args.extraTemplateSection
 * @param {HTMLTemplateElement} args.inputTemplateElement
 * @param {number} [args.groupAmount]
 */
async function populateExtraTemplate({
  extraTemplateSection,
  inputTemplateElement,
  groupAmount = 3,
}) {
  if (allExtras === undefined) {
    await queryAvailableExtras();
  }

  /** @type {Object.<string, Object[]>} */
  const types = {};
  allExtras.forEach((extra) => {
    const ex = { ...extra };
    ex.card_type = ex.card_type || 'Variable Overrides';
    if (types[ex.card_type] === undefined) {
      types[ex.card_type] = [];
    }
    types[ex.card_type].push(ex);
  });

  mountCardExtras(extraTemplateSection, types, inputTemplateElement, {
    activeTab: null,
    isGlobal: false,
    groupAmount,
    activeExtras: null,
    templateMode: true,
  });
}

/**
 * @param {?Object} activeExtras
 * @param {string} activeTab
 * @param {string} sectionQuerySelector
 * @param {HTMLTemplateElement} inputTemplateElement
 * @param {boolean} [isGlobal]
 * @param {number} [groupAmount]
 * @param {boolean} [_initializeTabs] ignored
 * @param {string[]|null} [restrictToCardTypes] when set, only mount these card type keys (e.g. episode editor)
 * @param {boolean} [useAllCardTypeExtras] when true, include extras for every card type (uses allExtras, not filteredExtras)
 */
async function initializeExtras(
  activeExtras,
  activeTab,
  sectionQuerySelector,
  inputTemplateElement,
  isGlobal = false,
  groupAmount = 3,
  _initializeTabs = true,
  restrictToCardTypes = null,
  useAllCardTypeExtras = false,
) {
  if (filteredExtras === undefined) {
    await queryAvailableExtras();
  }

  const extrasSource = useAllCardTypeExtras && typeof allExtras !== 'undefined' && allExtras
    ? allExtras
    : filteredExtras;

  /** @type {Object.<string, Object[]>} */
  const types = {};
  extrasSource.forEach((extra) => {
    if (isGlobal && !extra.card_type) {
      return;
    }
    const ex = { ...extra };
    ex.card_type = ex.card_type || 'Variable Overrides';
    if (restrictToCardTypes && restrictToCardTypes.length) {
      if (!restrictToCardTypes.includes(ex.card_type)) {
        return;
      }
    }
    if (types[ex.card_type] === undefined) {
      types[ex.card_type] = [];
    }
    types[ex.card_type].push(ex);
  });

  const section = document.querySelector(sectionQuerySelector);
  if (!section) {
    return;
  }

  mountCardExtras(section, types, inputTemplateElement, {
    activeTab,
    isGlobal,
    groupAmount,
    activeExtras,
    templateMode: false,
  });
}

/**
 * Sync extras card-type selector after template card type changes (accordion open).
 * @param {ParentNode} accordionOrRoot
 */
function syncCardExtrasTypeSelectFromTemplate(accordionOrRoot) {
  const root = accordionOrRoot.querySelector
    ? accordionOrRoot
    : document.querySelector(accordionOrRoot);
  if (!root) {
    return;
  }
  const section = root.querySelector('section[aria-label="extras"]');
  if (!section) {
    return;
  }
  const hiddenCardType = root.querySelector('input[name="card_type"]');
  const sel = section.querySelector('.card-extras-type-select');
  if (!hiddenCardType || !sel) {
    return;
  }
  const raw = hiddenCardType.value || '';
  const keys = section._tcmExtrasTypes
    ? sortedCardTypeKeys(section._tcmExtrasTypes)
    : getExtrasCardTypeKeysFromRoot(section);
  if (!keys.length) {
    return;
  }
  const pick = keys.includes(raw) ? raw : keys[0];
  sel.value = pick;
  syncCardExtrasPanels(section);
}

if (typeof window !== 'undefined' && !window._tcmCardExtrasDelegationBound) {
  window._tcmCardExtrasDelegationBound = true;
  document.addEventListener('change', (e) => {
    const el = e.target;
    if (!el || !el.classList || !el.classList.contains('card-extras-type-select')) {
      return;
    }
    const section = el.closest('section[aria-label="extras"]');
    if (!section) {
      return;
    }
    syncCardExtrasPanels(section);
  });
}
