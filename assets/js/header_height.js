/*
 * Publishes the app header's height as --mvp-header-height on :root.
 *
 * The header's height is not a constant: a tray, a wrapped breadcrumb trail
 * or a project's own `above`/`below` content all change it. Anything that has
 * to clear the header (a sticky page side panel, the browser's scroll to an
 * anchor through scroll-padding-top) reads this one value instead of
 * guessing. A header that does not stick clears nothing, and a page with no
 * header has nothing to clear, so both publish 0.
 *
 * mvp/tailwind/base.css holds the 4rem fallback used until this runs.
 */

export function startHeaderHeight() {
  const root = document.documentElement;
  const header = document.querySelector(".mvp-header");
  if (!header) {
    root.style.setProperty("--mvp-header-height", "0px");
    return;
  }
  const publish = () => {
    const sticky = getComputedStyle(header).position === "sticky";
    root.style.setProperty("--mvp-header-height", sticky ? `${header.offsetHeight}px` : "0px");
  };
  new ResizeObserver(publish).observe(header);
  publish();
}
