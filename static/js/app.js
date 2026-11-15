"use strict";

// Keep all navigation links available without JavaScript; enhance to a drawer on small screens.
const navigation = document.querySelector("#app-navigation");
const menuToggle = document.querySelector(".nav-toggle");
if (navigation && menuToggle) {
  const narrowScreen = window.matchMedia("(max-width: 960px)");
  const backdrop = document.querySelector(".nav-backdrop");
  const mainShell = document.querySelector(".main-shell");
  document.documentElement.classList.add("js-nav");
  menuToggle.hidden = false;
  function setNavigation(open, returnFocus = false) {
    const expanded = open && narrowScreen.matches;
    document.body.classList.toggle("nav-open", expanded);
    menuToggle.setAttribute("aria-expanded", String(expanded));
    navigation.inert = narrowScreen.matches && !expanded;
    mainShell.inert = expanded;
    backdrop.hidden = !expanded;
    if (expanded) {
      navigation.setAttribute("role", "dialog");
      navigation.setAttribute("aria-modal", "true");
      navigation.querySelector("[data-nav-close]").focus();
    } else {
      navigation.removeAttribute("role");
      navigation.removeAttribute("aria-modal");
      if (returnFocus && narrowScreen.matches) menuToggle.focus();
    }
  }
  menuToggle.addEventListener("click", () => setNavigation(true));
  document.querySelectorAll("[data-nav-close]").forEach(button => {
    button.addEventListener("click", () => setNavigation(false, true));
  });
  document.addEventListener("keydown", event => {
    if (!document.body.classList.contains("nav-open")) return;
    if (event.key === "Escape") {
      event.preventDefault();
      setNavigation(false, true);
    }
    if (event.key === "Tab") {
      const controls = [...navigation.querySelectorAll("a, button")].filter(el => el.getClientRects().length);
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  narrowScreen.addEventListener("change", () => setNavigation(false));
  setNavigation(false);
}

// Native dialog preserves keyboard focus and submits the original CSRF-protected form.
const confirmation = document.querySelector("#confirmation-dialog");
let pendingSubmission = null;
let approvedForm = null;
document.addEventListener("submit", event => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement) || !form.dataset.confirm || form === approvedForm) return;
  if (!confirmation || typeof confirmation.showModal !== "function") {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    return;
  }
  event.preventDefault();
  pendingSubmission = {form, submitter: event.submitter};
  confirmation.querySelector("[data-confirm-message]").textContent = form.dataset.confirm;
  confirmation.querySelector("[value=confirm]").textContent = event.submitter?.textContent.trim() || "Confirm";
  confirmation.returnValue = "cancel";
  confirmation.showModal();
});
if (confirmation) {
  confirmation.addEventListener("close", () => {
    const pending = pendingSubmission;
    pendingSubmission = null;
    if (confirmation.returnValue !== "confirm" || !pending) return;
    approvedForm = pending.form;
    try { pending.form.requestSubmit(pending.submitter || undefined); }
    finally { approvedForm = null; }
  });
}

// Search documentation already present in the page; no data is sent to a server.
const guideSearch = document.querySelector("#guide-search");
if (guideSearch) {
  document.querySelectorAll("[data-guide-enhancement]").forEach(el => { el.hidden = false; });
  const sections = [...document.querySelectorAll(".guide-section")];
  const index = sections.map(section => ({section, text: section.textContent.toLowerCase()}));
  const status = document.querySelector("#guide-result-count");
  function filterGuide() {
    const words = guideSearch.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    let matches = 0;
    index.forEach(({section, text}) => {
      const visible = words.every(word => text.includes(word));
      section.hidden = !visible;
      document.querySelector('[data-guide-target="' + section.id + '"]').hidden = !visible;
      if (visible) matches += 1;
    });
    status.textContent = matches + " of " + sections.length + " sections";
    document.querySelector(".guide-no-results").hidden = matches !== 0;
  }
  guideSearch.addEventListener("input", filterGuide);
  document.querySelector("[data-guide-clear]").addEventListener("click", () => {
    guideSearch.value = ""; filterGuide(); guideSearch.focus();
  });
  document.querySelector("[data-guide-print]").addEventListener("click", () => window.print());
  filterGuide();
}
