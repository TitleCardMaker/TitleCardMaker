/**
 * Episode Styles Modal - standalone component.
 * Informational gallery explaining Art vs Unique episode styles.
 */

/**
 * Initialize the Episode Styles modal.
 * @param {string} [triggerSelector='.button[data-value="style-button"]'] - Selector for elements that open the modal.
 */
function init(triggerSelector = '.button[data-value="style-button"]') {
  const $modal = $('#style-modal');
  if (!$modal.length) return;

  $modal
    .modal('attach events', triggerSelector, 'show')
    .modal('setting', 'transition', 'fade up')
    .modal({ blurring: true });
}

// Export for use by settings, series, and templates pages
window.StyleModal = {
  init,
};
