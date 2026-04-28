/**
 * Theme Switcher Widget JavaScript
 *
 * Handles theme detection, application, and persistence for the AdminLTE theme switcher.
 *
 * Features:
 * - Detects initial theme from localStorage or system preference
 * - Applies theme to <html data-bs-theme> attribute
 * - Persists theme to localStorage
 * - Handles localStorage unavailable (session-only mode)
 * - Detects and responds to system preference changes
 * - Completes theme changes in < 100ms
 */

(function () {
  "use strict"

  // Constants
  const STORAGE_KEY = "theme"
  const THEMES = {
    LIGHT: "light",
    DARK: "dark",
    AUTO: "auto",
  }

  /**
   * Get system color scheme preference
   * @returns {string} 'dark' or 'light'
   */
  function getSystemPreference() {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      return THEMES.DARK
    }
    return THEMES.LIGHT
  }

  /**
   * Get initial theme from localStorage or system preference
   * @returns {string} Theme name ('light', 'dark', or 'auto')
   */
  function getInitialTheme() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored && Object.values(THEMES).includes(stored)) {
        return stored
      }
    } catch (e) {
      // localStorage not available - continue with system preference
      console.warn("localStorage not available, using system preference")
    }

    // Default to 'light' if no stored preference
    return THEMES.LIGHT
  }

  /**
   * Persist theme preference to localStorage
   * @param {string} theme - Theme name to persist
   */
  function persistTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch (e) {
      // localStorage not available (session-only mode)
      console.warn("Could not persist theme to localStorage:", e.message)
    }
  }

  /**
   * Apply theme to document
   * @param {string} theme - Theme name ('light', 'dark', or 'auto')
   */
  function applyTheme(theme) {
    const startTime = performance.now()

    let actualTheme = theme
    if (theme === THEMES.AUTO) {
      actualTheme = getSystemPreference()
    }

    // Check if theme was already applied by inline script
    const preApplied = document.documentElement.hasAttribute(
      "data-theme-preapplied",
    )
    const currentTheme = document.documentElement.getAttribute("data-bs-theme")

    // Only apply if not already set or if changing
    if (!preApplied || currentTheme !== actualTheme) {
      // Apply to <html> element
      document.documentElement.setAttribute("data-bs-theme", actualTheme)
    }

    // Remove pre-applied marker after first check
    if (preApplied) {
      document.documentElement.removeAttribute("data-theme-preapplied")
    }

    // Update active indicators in dropdown
    updateActiveIndicators(theme)

    // Update navbar icon to match current theme
    updateNavbarIcon(theme, actualTheme)

    const duration = performance.now() - startTime
    if (duration > 100) {
      console.warn(
        `Theme application took ${duration.toFixed(2)}ms (> 100ms target)`,
      )
    }
  }

  /**
   * Update navbar icon to reflect current theme
   * @param {string} theme - Selected theme preference ('light', 'dark', or 'auto')
   * @param {string} actualTheme - Actual theme being applied ('light' or 'dark')
   */
  function updateNavbarIcon(theme, actualTheme) {
    const dropdown = document.querySelector('[data-theme-switcher="true"]')
    if (!dropdown) return

    const navbarIcon = dropdown.querySelector(".nav-link i, .nav-link svg")
    if (!navbarIcon) return

    // Remove all theme icon classes
    navbarIcon.classList.remove(
      "bi-sun",
      "bi-moon-stars-fill",
      "bi-circle-half",
    )

    // Add appropriate icon based on theme preference
    if (theme === THEMES.AUTO) {
      navbarIcon.classList.add("bi-circle-half")
    } else if (actualTheme === THEMES.DARK) {
      navbarIcon.classList.add("bi-moon-stars-fill")
    } else {
      navbarIcon.classList.add("bi-sun")
    }
  }

  /**
   * Update active state indicators in theme switcher dropdown
   * @param {string} theme - Currently active theme
   */
  function updateActiveIndicators(theme) {
    const dropdown = document.querySelector('[data-theme-switcher="true"]')
    if (!dropdown) return

    const options = dropdown.querySelectorAll("[data-theme]")
    options.forEach((option) => {
      const optionTheme = option.getAttribute("data-theme")
      const isActive = optionTheme === theme

      // Update active class
      option.classList.toggle("active", isActive)

      // Find the checkmark icon specifically (second icon in each item)
      // The first icon is the theme icon (sun/moon/circle-half) which should always be visible
      const icons = option.querySelectorAll("i, svg")
      if (icons.length >= 2) {
        // The last icon is the checkmark
        const checkmark = icons[icons.length - 1]
        checkmark.style.display = isActive ? "inline" : "none"
      }
    })
  }

  /**
   * Handle theme option click
   * @param {Event} event - Click event
   */
  function handleThemeClick(event) {
    event.preventDefault()

    const theme = event.currentTarget.getAttribute("data-theme")
    if (!theme || !Object.values(THEMES).includes(theme)) {
      console.error("Invalid theme:", theme)
      return
    }

    // Apply and persist theme
    applyTheme(theme)
    persistTheme(theme)
  }

  /**
   * Initialize theme switcher
   */
  function init() {
    // Apply initial theme immediately
    const initialTheme = getInitialTheme()
    applyTheme(initialTheme)

    // Set up click handlers for theme options
    const dropdown = document.querySelector('[data-theme-switcher="true"]')
    if (!dropdown) {
      console.warn("Theme switcher not found on page")
      return
    }

    const options = dropdown.querySelectorAll("[data-theme]")
    options.forEach((option) => {
      option.addEventListener("click", handleThemeClick)
    })

    // Listen for system preference changes (when in auto mode)
    if (window.matchMedia) {
      const darkModeQuery = window.matchMedia("(prefers-color-scheme: dark)")

      // Modern API
      if (darkModeQuery.addEventListener) {
        darkModeQuery.addEventListener("change", (e) => {
          const currentTheme = getInitialTheme()
          if (currentTheme === THEMES.AUTO) {
            applyTheme(THEMES.AUTO)
          }
        })
      }
      // Legacy API (for older browsers)
      else if (darkModeQuery.addListener) {
        darkModeQuery.addListener((e) => {
          const currentTheme = getInitialTheme()
          if (currentTheme === THEMES.AUTO) {
            applyTheme(THEMES.AUTO)
          }
        })
      }
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init)
  } else {
    init()
  }

  // Export functions for testing (if needed)
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      getSystemPreference,
      getInitialTheme,
      persistTheme,
      applyTheme,
      updateActiveIndicators,
    }
  }
})()
