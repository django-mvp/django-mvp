/**
 * Theme Switcher — Alpine.js component
 *
 * Registered as Alpine.data('themeSwitcher') and used via x-data="themeSwitcher"
 * in the theme_switcher.html Cotton component.
 *
 * Responsibilities:
 * - Load persisted theme from localStorage on init
 * - Apply the resolved theme to <html data-bs-theme>
 * - React to system preference changes when theme is "auto"
 * - Persist the chosen theme to localStorage
 */
document.addEventListener("alpine:init", () => {
  Alpine.data("themeSwitcher", () => ({
    /** Currently selected theme preference: 'light' | 'dark' | 'auto' */
    theme: "light",

    init() {
      this.theme = this._getStored()
      this._apply(this.theme)

      // Re-apply when the OS preference changes (only matters in auto mode)
      window
        .matchMedia?.("(prefers-color-scheme: dark)")
        ?.addEventListener("change", () => {
          if (this.theme === "auto") this._apply("auto")
        })
    },

    /** Bootstrap Icon class object for x-bind:class on the toggle button icon */
    get iconClass() {
      return {
        "bi-sun": this.theme === "light",
        "bi-moon-stars-fill": this.theme === "dark",
        "bi-circle-half": this.theme === "auto",
      }
    },

    /** Called from x-on:click.prevent on each dropdown item */
    setTheme(theme) {
      this.theme = theme
      this._apply(theme)
      try {
        localStorage.setItem("theme", theme)
      } catch (e) {
        console.warn("Could not persist theme:", e.message)
      }
    },

    /** Resolve and apply theme to the <html> element */
    _apply(theme) {
      const actual =
        theme === "auto"
          ? window.matchMedia?.("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light"
          : theme
      document.documentElement.setAttribute("data-bs-theme", actual)
    },

    /** Read persisted theme, falling back to 'light' */
    _getStored() {
      try {
        const stored = localStorage.getItem("theme")
        if (["light", "dark", "auto"].includes(stored)) return stored
      } catch (e) {
        console.warn("localStorage not available:", e.message)
      }
      return "light"
    },
  }))
})
