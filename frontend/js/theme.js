/*
 * Refresh the theme of all HTML elements on the page. This sets the inverted
 * CSS class of all elements under the main-content ID; as well as modals.
 * Uninvertible conntent is excluded.
 */
function refreshTheme() {
  const siteTheme = window.localStorage.getItem('site-theme') || 'dark';
  const inverted = (siteTheme === 'dark');
  $('#main-content .ui:not(.uninvertible)').toggleClass('inverted', inverted);
  $('.modal:not(.basic):not(.uninvertible), .modal:not(.basic):not(.uninvertible) >* .ui:not(.uninvertible), .accordion:not(.uninvertible), .accordion:not(.uninvertible) >* .ui:not(.uninvertible)').toggleClass('inverted', inverted);

  // Update theme-color meta tag for mobile browsers
  let themeColorMeta = document.querySelector('meta[name="theme-color"]');
  if (!themeColorMeta) {
    themeColorMeta = document.createElement('meta');
    themeColorMeta.name = 'theme-color';
    document.head.appendChild(themeColorMeta);
  }

  if (inverted) {
    // Set <html> background image
    document.documentElement.style.setProperty('--background', 'linear-gradient(to bottom right, rgb(29,29,29), rgb(40,40,40))')
    document.documentElement.classList.add('dark');
    document.querySelector('#theme-toggle i').className = 'moon outline icon';
    themeColorMeta.content = '#1b1c1d';
  } else {
    document.documentElement.style.setProperty('--background', 'linear-gradient(to bottom right, var(--background-color-light), #d9d9d9)');
    document.documentElement.classList.remove('dark');
    document.querySelector('#theme-toggle i').className = 'sun outline icon';
    themeColorMeta.content = '#f5f7fa';
  }
}

/*
 * Toggle the current theme from light -> dark or dark -> light. This changes 
 * the theme icon, updates the theme local storage variable, and refreshes all
 * HTML.
 */
function toggleTheme() {
  const currentTheme = window.localStorage.getItem('site-theme') || 'dark';
  const themeIcon = document.querySelector('#theme-toggle i');
  // Light -> Dark
  if (currentTheme === 'light') {
    themeIcon.className = 'moon outline icon';
    window.localStorage.setItem('site-theme', 'dark');
  // Dark -> light
  } else {
    themeIcon.className = 'sun outline icon';
    window.localStorage.setItem('site-theme', 'light');
  }
  refreshTheme();
}

$(document).ready(() => {
  // Refresh theme
  refreshTheme();
  // Highlight side bar icon of current page
  $(`#nav-menu a[href="${location.pathname}"]`).toggleClass('highlighted', true);
});
