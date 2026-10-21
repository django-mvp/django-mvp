// Publishes the header's height as --mvp-header-height on :root (0 when it does not stick or is
// absent), so sticky panels and anchor scrolling can clear it. See docs/layout.md "Header height".
// mvp/tailwind/base.css holds the 4rem fallback used until this runs.

// Module scope so a body swap can drop the observer of the header it removed.
let observer = null;

export function startHeaderHeight() {
  const root = document.documentElement;
  const header = document.querySelector(".mvp-header");
  observer?.disconnect();
  observer = null;
  if (!header) {
    root.style.setProperty("--mvp-header-height", "0px");
    return;
  }
  const publish = () => {
    const sticky = getComputedStyle(header).position === "sticky";
    root.style.setProperty("--mvp-header-height", sticky ? `${header.offsetHeight}px` : "0px");
  };
  observer = new ResizeObserver(publish);
  observer.observe(header);
  publish();
}
