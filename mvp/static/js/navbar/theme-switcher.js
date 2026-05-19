/**
 * Theme Switcher — vanilla JS IIFE
 *
 * Mirrors AdminLTE's color-mode toggle (issue #6010).
 * Loaded synchronously in <head> so it prevents FOUC by applying the
 * resolved theme to <html data-bs-theme> before the first paint.
 *
 * HTML contract:
 *   - Trigger icons:  data-lte-theme-icon="light|dark|auto"
 *   - Dropdown items: data-bs-theme-value="light|dark|auto"
 *   - Active check:   <i class="bi bi-check-lg"> inside each button
 *
 * Storage key: "lte-theme"
 */
; (() => {
  "use strict"

  const STORAGE_KEY = "lte-theme"

  const getStoredTheme = () => {
    try { return localStorage.getItem(STORAGE_KEY) } catch { return null }
  }
  const setStoredTheme = (theme) => {
    try { localStorage.setItem(STORAGE_KEY, theme) } catch { }
  }

  const prefersDark = () =>
    globalThis.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false

  const getPreferredTheme = () => {
    const stored = getStoredTheme()
    if (stored) return stored
    return prefersDark() ? "dark" : "light"
  }

  const setTheme = (theme) => {
    const resolved =
      theme === "auto" ? (prefersDark() ? "dark" : "light") : theme
    document.documentElement.setAttribute("data-bs-theme", resolved)
  }

  // Apply immediately to prevent FOUC
  setTheme(getPreferredTheme())

  const showActiveTheme = (theme) => {
    // Highlight the active dropdown option
    document.querySelectorAll("[data-bs-theme-value]").forEach((el) => {
      el.classList.remove("active")
      el.setAttribute("aria-pressed", "false")
      const check = el.querySelector(".bi-check-lg")
      if (check) check.classList.add("d-none")
    })
    const active = document.querySelector(`[data-bs-theme-value="${theme}"]`)
    if (active) {
      active.classList.add("active")
      active.setAttribute("aria-pressed", "true")
      const check = active.querySelector(".bi-check-lg")
      if (check) check.classList.remove("d-none")
    }
    // Sync the trigger icon
    document.querySelectorAll("[data-lte-theme-icon]").forEach((icon) => {
      icon.classList.toggle("d-none", icon.dataset.lteThemeIcon !== theme)
    })
  }

  globalThis.matchMedia?.("(prefers-color-scheme: dark)")
    ?.addEventListener("change", () => {
      const stored = getStoredTheme()
      if (!stored || stored === "auto") setTheme(getPreferredTheme())
    })

  document.addEventListener("DOMContentLoaded", () => {
    showActiveTheme(getPreferredTheme())
    document.querySelectorAll("[data-bs-theme-value]").forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const theme = toggle.getAttribute("data-bs-theme-value")
        setStoredTheme(theme)
        setTheme(theme)
        showActiveTheme(theme)
      })
    })
  })
})()
