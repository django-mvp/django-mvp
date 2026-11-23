/*
 * The site search's keyboard: Ctrl K (or ⌘ K on a Mac) and "/" open the
 * dialog, the arrow keys move a highlight through the results while focus
 * stays in the field, Enter opens the highlighted result, and one Escape
 * closes.
 *
 * Every listener sits on the document and looks up #mvp-search when its event
 * fires, so the body a boosted navigation swaps in needs nothing rebound.
 */

const DIALOG = "mvp-search";
const RESULTS = "mvp-search-results";
const HIT = "[data-mvp-search-hit]";

const isMac = () => /mac/i.test(navigator.platform);

const dialog = () => document.getElementById(DIALOG);
const field = (d) => d.querySelector("input[name=q]");
const hits = (d) => [...d.querySelectorAll(HIT)];

function showModifier() {
  if (!isMac()) return;
  for (const key of document.querySelectorAll("[data-mvp-search-modifier]")) {
    key.textContent = "⌘";
  }
}

function openSearch() {
  const d = dialog();
  if (!d || d.open) return;
  d.showModal();
  const input = field(d);
  input.focus();
  input.select();
}

// Highlights one result, or none for -1, and tells the combobox which it is.
function setCurrent(d, index) {
  const all = hits(d);
  const input = field(d);
  all.forEach((hit, position) => {
    if (!hit.id) hit.id = `mvp-search-hit-${position}`;
    hit.classList.toggle("is-current", position === index);
    hit.setAttribute("aria-selected", position === index ? "true" : "false");
  });
  const current = all[index];
  if (current) {
    current.scrollIntoView({ block: "nearest" });
    input.setAttribute("aria-activedescendant", current.id);
  } else {
    input.removeAttribute("aria-activedescendant");
  }
  d.dataset.current = String(index);
}

function onOpenKey(event) {
  const modifier = isMac() ? event.metaKey : event.ctrlKey;
  if (modifier && event.key.toLowerCase() === "k") {
    event.preventDefault();
    openSearch();
    return;
  }
  const typing = event.target.closest?.("input, textarea, select, [contenteditable]");
  if (event.key === "/" && !typing && !modifier && !event.altKey) {
    event.preventDefault();
    openSearch();
  }
}

function onDialogKey(event) {
  const d = dialog();
  if (!d || !d.open || !d.contains(event.target)) return;
  // A search field eats the first Escape to clear itself; one closes here.
  if (event.key === "Escape") {
    event.preventDefault();
    d.close();
    return;
  }
  const all = hits(d);
  const current = Number(d.dataset.current ?? -1);
  if (event.key === "ArrowDown" && all.length) {
    event.preventDefault();
    setCurrent(d, Math.min(current + 1, all.length - 1));
  } else if (event.key === "ArrowUp" && all.length) {
    event.preventDefault();
    setCurrent(d, Math.max(current - 1, 0));
  } else if (event.key === "Enter" && event.target.name === "q" && all[current]) {
    event.preventDefault();
    window.location.href = all[current].href;
  }
}

// New results reset the highlight and say whether the list is open.
function onSwap(event) {
  if (event.detail.target.id !== RESULTS) return;
  const d = dialog();
  setCurrent(d, -1);
  field(d).setAttribute("aria-expanded", hits(d).length ? "true" : "false");
}

// A click on a result closes the dialog on the way to the page.
function onClick(event) {
  if (event.target.closest(`#${DIALOG} ${HIT}`)) dialog().close();
}

/** Starts the search's keyboard. Call it once, when the page loads. */
export function startSearch() {
  document.addEventListener("keydown", onOpenKey);
  document.addEventListener("keydown", onDialogKey);
  document.addEventListener("htmx:afterSwap", onSwap);
  document.addEventListener("click", onClick);
  // The ⌘ label is in markup a boosted navigation swaps in again.
  document.addEventListener("htmx:afterSettle", showModifier);
  showModifier();
}
