// Alpine.data("mvpReorder"), registered in index.js (docs/adr/0035-behaviour-lives-in-registered-alpine-components.md).
import Sortable from "sortablejs";

export function registerReorder(Alpine) {
  Alpine.data("mvpReorder", () => ({
    engine: Sortable,
  }));
}
