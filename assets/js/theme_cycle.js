// The light, dark and automatic theme button (theme_cycle.html).
//
// Automatic is stored as an empty theme. theme-change reads an empty value
// as no theme at all and leaves the page alone, and the guard in base.html
// resolves it from the device before first paint. A visitor who never chose
// stores nothing, and keeps getting the configured default.

const AUTOMATIC = "";
const BUTTON_SELECTOR = "[data-theme-cycle]";
const device = window.matchMedia("(prefers-color-scheme: dark)");
const root = document.documentElement;

// The pair the button moves between, as "default,dark". Read off the button
// rather than kept here, so it follows the project's configuration.
function pairOnThePage() {
  const button = document.querySelector(BUTTON_SELECTOR);
  if (!button) {
    return null;
  }
  const [light, dark] = button.dataset.themeCycle.split(",");
  return { light, dark };
}

// Which step the button shows. Any theme but the dark one, set by the menu
// or a project's own script, shows the light step.
function markStep(pair) {
  if (localStorage.getItem("theme") === AUTOMATIC) {
    root.dataset.themeMode = "auto";
  } else if (root.dataset.theme === pair.dark) {
    root.dataset.themeMode = "dark";
  } else {
    delete root.dataset.themeMode;
  }
}

function choose(stored, pair) {
  localStorage.setItem("theme", stored);
  const automaticTheme = device.matches ? pair.dark : pair.light;
  root.setAttribute("data-theme", stored === AUTOMATIC ? automaticTheme : stored);
  markStep(pair);
}

export function startThemeCycle() {
  // Delegated, so a boosted navigation's fresh button needs no rebinding.
  document.addEventListener("click", (event) => {
    const button = event.target.closest(BUTTON_SELECTOR);
    if (!button) {
      return;
    }
    const pair = pairOnThePage();
    const next = {
      dark: AUTOMATIC,
      auto: pair.light,
    }[root.dataset.themeMode];
    choose(next ?? pair.dark, pair);
  });

  device.addEventListener("change", () => {
    const pair = pairOnThePage();
    if (pair && localStorage.getItem("theme") === AUTOMATIC) {
      choose(AUTOMATIC, pair);
    }
  });

  new MutationObserver(() => {
    const pair = pairOnThePage();
    if (pair) {
      markStep(pair);
    }
  }).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
}
