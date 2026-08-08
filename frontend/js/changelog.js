/**
 * Single-version changelog viewer.
 * Expects a global CHANGELOG array from changelogData.js (newest first).
 */

/** @type {string|null} */
let activeVersion = null;

/**
 * Find a changelog entry by version string.
 * @param {string} version
 * @returns {object|undefined}
 */
function findRelease(version) {
  return CHANGELOG.find((entry) => entry.version === version);
}

/**
 * Resolve the initial version from the URL hash or fall back to newest.
 * @returns {string}
 */
function resolveInitialVersion() {
  const hash = (location.hash || '').replace(/^#/, '').trim();
  if (hash && findRelease(hash)) {
    return hash;
  }
  return CHANGELOG[0]?.version;
}

/**
 * Update prev/next button disabled state for the active version.
 * @param {number} index
 */
function updateNavButtons(index) {
  const prev = document.getElementById('changelog-prev');
  const next = document.getElementById('changelog-next');
  if (prev) prev.disabled = index <= 0;
  if (next) next.disabled = index < 0 || index >= CHANGELOG.length - 1;
}

/**
 * Sync the version <select> to the given version without firing change handlers.
 * @param {string} version
 */
function syncSelect(version) {
  const select = document.getElementById('changelog-version-select');
  if (select && select.value !== version) {
    select.value = version;
  }
}

/**
 * Update the URL hash without scrolling or adding history entries.
 * @param {string} version
 */
function syncHash(version) {
  const url = `${location.pathname}${location.search}#${version}`;
  history.replaceState(null, '', url);
}

/**
 * Build a nested ordered/unordered list for changelog items.
 * @param {Array} items
 * @param {boolean} ordered
 * @returns {HTMLOListElement|HTMLUListElement}
 */
function buildItemList(items, ordered = true) {
  const list = document.createElement(ordered ? 'ol' : 'ul');
  list.className = 'changelog-list';

  for (const item of items) {
    // Image-only nodes render as list items containing the figure
    if (item.image && !item.html && !item.children) {
      const li = document.createElement('li');
      li.className = 'changelog-image-item';
      li.appendChild(buildImage(item));
      list.appendChild(li);
      continue;
    }

    const li = document.createElement('li');
    if (item.html) {
      const text = document.createElement('span');
      text.className = 'changelog-item-text';
      text.innerHTML = item.html;
      li.appendChild(text);
    }

    if (item.image) {
      li.appendChild(buildImage(item));
    }

    if (item.children?.length) {
      // Nested children use unordered lists for visual hierarchy
      const hasOnlyImages = item.children.every((c) => c.image && !c.html && !c.children);
      if (hasOnlyImages) {
        const wrap = document.createElement('div');
        wrap.className = 'changelog-images';
        for (const child of item.children) {
          wrap.appendChild(buildImage(child));
        }
        li.appendChild(wrap);
      } else {
        li.appendChild(buildItemList(item.children, false));
      }
    }

    list.appendChild(li);
  }

  return list;
}

/**
 * Create an image element for a changelog screenshot.
 * @param {object} item - Changelog image node with image URL and optional width
 * @returns {HTMLImageElement}
 */
function buildImage(item) {
  const img = document.createElement('img');
  img.className = 'changelog-image';
  img.src = item.image;
  img.loading = 'lazy';
  img.alt = '';
  if (item.width) {
    img.style.width = item.width.includes('%') || item.width.includes('px')
      ? item.width
      : `${item.width}%`;
  }
  return img;
}

/**
 * Render a single release into #changelog-release.
 * @param {string} version
 */
function renderRelease(version) {
  const release = findRelease(version);
  const mount = document.getElementById('changelog-release');
  if (!mount || !release) return;

  activeVersion = version;
  const index = CHANGELOG.findIndex((entry) => entry.version === version);

  syncSelect(version);
  syncHash(version);
  updateNavButtons(index);

  // Build release header
  const fragment = document.createDocumentFragment();

  const header = document.createElement('header');
  header.className = 'changelog-release-header';

  const title = document.createElement('h2');
  title.className = 'changelog-version-title';
  title.id = version;
  title.textContent = release.version;
  header.appendChild(title);

  if (release.date) {
    const date = document.createElement('p');
    date.className = 'changelog-version-date';
    date.textContent = `Released ${release.date}`;
    header.appendChild(date);
  }

  fragment.appendChild(header);

  // Build each section
  for (const section of release.sections || []) {
    const block = document.createElement('section');
    block.className = 'changelog-section';

    const heading = document.createElement('h3');
    heading.className = 'changelog-section-title';
    heading.textContent = section.title;
    block.appendChild(heading);

    if (section.items?.length) {
      block.appendChild(buildItemList(section.items, true));
    }

    fragment.appendChild(block);
  }

  mount.replaceChildren(fragment);
  mount.scrollTop = 0;
}

/**
 * Populate the version select and wire up navigation.
 */
function initializePage() {
  if (!Array.isArray(CHANGELOG) || CHANGELOG.length === 0) {
    const mount = document.getElementById('changelog-release');
    if (mount) {
      mount.textContent = 'No changelog entries available.';
    }
    return;
  }

  const select = document.getElementById('changelog-version-select');
  if (select) {
    select.replaceChildren();
    for (const entry of CHANGELOG) {
      const option = document.createElement('option');
      option.value = entry.version;
      option.textContent = entry.version;
      select.appendChild(option);
    }

    select.addEventListener('change', () => {
      renderRelease(select.value);
    });
  }

  document.getElementById('changelog-prev')?.addEventListener('click', () => {
    const index = CHANGELOG.findIndex((entry) => entry.version === activeVersion);
    if (index > 0) {
      renderRelease(CHANGELOG[index - 1].version);
    }
  });

  document.getElementById('changelog-next')?.addEventListener('click', () => {
    const index = CHANGELOG.findIndex((entry) => entry.version === activeVersion);
    if (index >= 0 && index < CHANGELOG.length - 1) {
      renderRelease(CHANGELOG[index + 1].version);
    }
  });

  // Respond to in-page hash changes (e.g. browser back/forward to hash)
  window.addEventListener('hashchange', () => {
    const hash = (location.hash || '').replace(/^#/, '').trim();
    if (hash && findRelease(hash) && hash !== activeVersion) {
      renderRelease(hash);
    }
  });

  renderRelease(resolveInitialVersion());
}
