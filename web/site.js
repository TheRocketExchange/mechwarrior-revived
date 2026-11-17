"use strict";

const toc = document.querySelector(".toc-panel");
const navigation = document.querySelector(".navigation-menu");
const narrow = window.matchMedia("(max-width: 740px)");
if (narrow.matches) { toc.open = false; navigation.open = false; }
narrow.addEventListener("change", event => { toc.open = !event.matches; navigation.open = !event.matches; });
navigation.querySelector("nav").addEventListener("click", event => {
  if (narrow.matches && event.target.closest("a")) navigation.open = false;
});
document.addEventListener("click", event => {
  if (narrow.matches && !navigation.contains(event.target)) navigation.open = false;
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && narrow.matches && navigation.open) {
    navigation.open = false;
    navigation.querySelector("summary").focus();
  }
});
toc.addEventListener("click", event => {
  if (narrow.matches && event.target.closest(".contents a")) toc.open = false;
});

const printButton = document.querySelector("[data-print]");
printButton.hidden = false;
printButton.addEventListener("click", () => window.print());

const contentsLinks = [...document.querySelectorAll(".contents a")];
const headings = contentsLinks.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1))));
let pending = false;
function updateContents() {
  let current = headings[0];
  for (const heading of headings) {
    if (heading && heading.getBoundingClientRect().top <= 140) current = heading;
  }
  for (const link of contentsLinks) {
    const active = current && link.hash === "#" + current.id;
    link.classList.toggle("active", Boolean(active));
    if (active) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  }
  pending = false;
}
window.addEventListener("scroll", () => {
  if (!pending) { pending = true; requestAnimationFrame(updateContents); }
}, { passive: true });
updateContents();

const dialog = document.querySelector(".search-dialog");
const openSearch = document.querySelector("[data-search-open]");
const input = document.getElementById("rule-search");
const results = document.querySelector(".search-results");
const status = document.querySelector(".search-status");
const index = window.RULEBOOK_INDEX || [];
const clean = text => text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/[*_`#|]/g, "").replace(/\s+/g, " ").trim();
const records = index.map(record => ({ ...record, text: clean(record.text), haystack: (record.title + " " + record.page + " " + clean(record.text)).toLowerCase() }));

function search() {
  const query = input.value.trim().toLowerCase();
  const words = query.split(/\s+/).filter(Boolean);
  let matches = words.length ? records.filter(record => words.every(word => record.haystack.includes(word))) : records.filter(record => !record.url.includes("#"));
  if (words.length) matches.sort((a, b) => {
    const score = record => words.reduce((total, word) => total + (record.title.toLowerCase().includes(word) ? 3 : 0) + (record.page.toLowerCase().includes(word) ? 1 : 0), 0);
    return score(b) - score(a);
  });
  const total = matches.length;
  matches = matches.slice(0, 30);
  status.textContent = query ? (total ? `${total} matching section${total === 1 ? "" : "s"}${total > 30 ? " · showing the first 30" : ""}` : "No matches. Try a shorter term, such as heat or armor.") : "Browse a page or search across the whole packet.";
  results.replaceChildren();
  for (const record of matches) {
    const anchor = document.createElement("a");
    anchor.className = "search-result";
    anchor.href = record.url;
    const page = document.createElement("span");
    page.textContent = record.page;
    const title = document.createElement("strong");
    title.textContent = record.title;
    const snippet = document.createElement("p");
    const matchAt = words.length ? Math.max(0, record.text.toLowerCase().indexOf(words[0])) : 0;
    const start = Math.max(0, matchAt - 50);
    snippet.textContent = (start ? "…" : "") + record.text.slice(start, start + 175) + (record.text.length > start + 175 ? "…" : "");
    anchor.append(page, title, snippet);
    anchor.addEventListener("click", () => dialog.close());
    results.append(anchor);
  }
  results.scrollTop = 0;
}
function showSearch() {
  if (dialog.open) return;
  if (narrow.matches) navigation.open = false;
  search();
  dialog.showModal();
  input.focus();
}
openSearch.hidden = false;
openSearch.addEventListener("click", showSearch);
document.querySelector(".close-search").addEventListener("click", () => dialog.close());
input.addEventListener("input", search);
input.addEventListener("keydown", event => {
  if (event.key === "Enter") {
    const first = results.querySelector("a");
    if (first) first.click();
  }
});
dialog.addEventListener("click", event => {
  if (event.target !== dialog) return;
  const bounds = dialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
});
document.addEventListener("keydown", event => {
  if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey && !/INPUT|TEXTAREA|SELECT/.test(event.target.tagName) && !event.target.isContentEditable) {
    event.preventDefault();
    showSearch();
  }
});
