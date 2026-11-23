// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

export {};

type Theme = 'dark' | 'light' | 'auto';
type WallpaperPreset = 'midnight' | 'aurora' | 'graphite' | 'linen';

interface WallpaperState {
  kind: 'preset' | 'custom';
  value: string;
}

interface Settings {
  theme: Theme;
  wallpaper: WallpaperState;
  brightness: number;
  scrim: number;
}

interface Shortcut {
  id: string;
  name: string;
  url: string;
}

const SETTINGS_KEY = 'umbrella.ntp.settings.v1';
const SHORTCUTS_KEY = 'umbrella.ntp.shortcuts.v1';
const SEARCH_URL = 'https://duckduckgo.com/?q=';
const LOCALE = navigator.language || 'it-IT';

const PRESETS: WallpaperPreset[] = ['midnight', 'aurora', 'graphite', 'linen'];
const PRESET_LABELS: Record<WallpaperPreset, string> = {
  midnight: 'Mezzanotte',
  aurora: 'Aurora',
  graphite: 'Grafite',
  linen: 'Lino',
};

const DEFAULT_SETTINGS: Settings = {
  theme: 'dark',
  wallpaper: {kind: 'preset', value: 'midnight'},
  brightness: 100,
  scrim: 35,
};

const DEFAULT_SHORTCUTS: Shortcut[] = [
  {id: 'duckduckgo', name: 'DuckDuckGo', url: 'https://duckduckgo.com/'},
  {id: 'github', name: 'GitHub', url: 'https://github.com/'},
  {id: 'wikipedia', name: 'Wikipedia', url: 'https://it.wikipedia.org/'},
  {id: 'youtube', name: 'YouTube', url: 'https://www.youtube.com/'},
  {id: 'mdn', name: 'MDN', url: 'https://developer.mozilla.org/'},
  {id: 'reddit', name: 'Reddit', url: 'https://www.reddit.com/'},
];

function byId<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Elemento mancante: #${id}`);
  }
  return element as T;
}

const backdrop = byId<HTMLDivElement>('backdrop');
const clock = byId<HTMLHeadingElement>('clock');
const date = byId<HTMLParagraphElement>('date');
const searchForm = byId<HTMLFormElement>('search-form');
const searchInput = byId<HTMLInputElement>('search-input');
const shortcutGrid = byId<HTMLUListElement>('shortcut-grid');
const themeToggle = byId<HTMLButtonElement>('theme-toggle');
const customizeOpen = byId<HTMLButtonElement>('customize-open');
const customizeClose = byId<HTMLButtonElement>('customize-close');
const panel = byId<HTMLElement>('panel');
const panelScrim = byId<HTMLDivElement>('panel-scrim');
const themeChoices = byId<HTMLDivElement>('theme-choices');
const wallpaperGrid = byId<HTMLDivElement>('wallpaper-grid');
const wallpaperFile = byId<HTMLInputElement>('wallpaper-file');
const brightness = byId<HTMLInputElement>('brightness');
const brightnessValue = byId<HTMLOutputElement>('brightness-value');
const scrimOpacity = byId<HTMLInputElement>('scrim-opacity');
const scrimValue = byId<HTMLOutputElement>('scrim-value');
const resetButton = byId<HTMLButtonElement>('reset');
const dialog = byId<HTMLDialogElement>('shortcut-dialog');
const dialogTitle = byId<HTMLHeadingElement>('dialog-title');
const shortcutForm = byId<HTMLFormElement>('shortcut-form');
const shortcutName = byId<HTMLInputElement>('shortcut-name');
const shortcutUrl = byId<HTMLInputElement>('shortcut-url');
const shortcutError = byId<HTMLParagraphElement>('shortcut-error');
const shortcutDelete = byId<HTMLButtonElement>('shortcut-delete');
const shortcutCancel = byId<HTMLButtonElement>('shortcut-cancel');

let settings: Settings = loadSettings();
let shortcuts: Shortcut[] = loadShortcuts();
let editingId: string | null = null;
let draggedId: string | null = null;
let lastFocused: HTMLElement | null = null;

// ------------------------------------------------------------------ storage

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) {
      return {...DEFAULT_SETTINGS, wallpaper: {...DEFAULT_SETTINGS.wallpaper}};
    }
    const parsed: unknown = JSON.parse(raw);
    if (!isRecord(parsed)) {
      return {...DEFAULT_SETTINGS, wallpaper: {...DEFAULT_SETTINGS.wallpaper}};
    }

    const theme: Theme =
        parsed.theme === 'light' || parsed.theme === 'auto' ||
                parsed.theme === 'dark' ?
            parsed.theme :
            DEFAULT_SETTINGS.theme;

    let wallpaper: WallpaperState = {...DEFAULT_SETTINGS.wallpaper};
    if (isRecord(parsed.wallpaper) &&
        typeof parsed.wallpaper.value === 'string') {
      const kind = parsed.wallpaper.kind === 'custom' ? 'custom' : 'preset';
      if (kind === 'custom' ||
          PRESETS.includes(parsed.wallpaper.value as WallpaperPreset)) {
        wallpaper = {kind, value: parsed.wallpaper.value};
      }
    }

    const brightnessValue = clampNumber(
        parsed.brightness, 40, 120, DEFAULT_SETTINGS.brightness);
    const scrimValue =
        clampNumber(parsed.scrim, 0, 80, DEFAULT_SETTINGS.scrim);

    return {theme, wallpaper, brightness: brightnessValue, scrim: scrimValue};
  } catch {
    return {...DEFAULT_SETTINGS, wallpaper: {...DEFAULT_SETTINGS.wallpaper}};
  }
}

function loadShortcuts(): Shortcut[] {
  try {
    const raw = localStorage.getItem(SHORTCUTS_KEY);
    if (!raw) {
      return DEFAULT_SHORTCUTS.map((item) => ({...item}));
    }
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return DEFAULT_SHORTCUTS.map((item) => ({...item}));
    }
    const items: Shortcut[] = [];
    for (const entry of parsed) {
      if (!isRecord(entry) || typeof entry.id !== 'string' ||
          typeof entry.name !== 'string' || typeof entry.url !== 'string') {
        continue;
      }
      if (!isSafeHttpUrl(entry.url)) {
        continue;
      }
      items.push({
        id: entry.id,
        name: entry.name.slice(0, 40),
        url: entry.url,
      });
    }
    return items.length > 0 ?
        items :
        DEFAULT_SHORTCUTS.map((item) => ({...item}));
  } catch {
    return DEFAULT_SHORTCUTS.map((item) => ({...item}));
  }
}

function clampNumber(
    value: unknown, min: number, max: number, fallback: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fallback;
  }
  return Math.min(max, Math.max(min, Math.round(value)));
}

function persistSettings(): boolean {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    return true;
  } catch {
    window.alert(
        'Non c\'è spazio sufficiente per salvare questo sfondo. ' +
        'Prova un\'immagine più piccola.');
    return false;
  }
}

function persistShortcuts(): void {
  try {
    localStorage.setItem(SHORTCUTS_KEY, JSON.stringify(shortcuts));
  } catch {
    window.alert('Impossibile salvare le scorciatoie: spazio esaurito.');
  }
}

// -------------------------------------------------------------------- orologio

function renderClock(): void {
  const now = new Date();
  clock.textContent = new Intl.DateTimeFormat(LOCALE, {
    hour: '2-digit',
    minute: '2-digit',
  }).format(now);
  const formatted = new Intl.DateTimeFormat(LOCALE, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(now);
  date.textContent =
      formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

// ---------------------------------------------------------------------- tema

function resolvedTheme(): 'dark' | 'light' {
  if (settings.theme !== 'auto') {
    return settings.theme;
  }
  return window.matchMedia('(prefers-color-scheme: light)').matches ?
      'light' :
      'dark';
}

function applyTheme(): void {
  const theme = resolvedTheme();
  document.documentElement.dataset.theme = theme;
  themeToggle.setAttribute(
      'aria-label',
      theme === 'dark' ? 'Passa al tema chiaro' : 'Passa al tema scuro');
  for (const button of Array.from(
           themeChoices.querySelectorAll<HTMLButtonElement>(
               '[data-theme-choice]'))) {
    button.setAttribute(
        'aria-pressed',
        String(button.dataset.themeChoice === settings.theme));
  }
}

function cycleTheme(): void {
  settings.theme =
      settings.theme === 'dark' ? 'light' :
      settings.theme === 'light' ? 'auto' :
                                  'dark';
  persistSettings();
  applyTheme();
}

// ------------------------------------------------------------------- sfondo

function applyWallpaper(): void {
  backdrop.className = 'backdrop';
  backdrop.style.backgroundImage = '';

  if (settings.wallpaper.kind === 'custom' &&
      settings.wallpaper.value.length > 0) {
    backdrop.classList.add('wallpaper-custom');
    backdrop.style.backgroundImage = `url("${settings.wallpaper.value}")`;
  } else {
    backdrop.classList.add(`wallpaper-${settings.wallpaper.value}`);
  }

  brightness.value = String(settings.brightness);
  brightnessValue.textContent = `${settings.brightness}%`;
  scrimOpacity.value = String(settings.scrim);
  scrimValue.textContent = `${settings.scrim}%`;

  document.documentElement.style.setProperty(
      '--ntp-brightness', String(settings.brightness / 100));
  document.documentElement.style.setProperty(
      '--ntp-scrim-opacity', String(settings.scrim / 100));

  for (const button of Array.from(
           wallpaperGrid.querySelectorAll<HTMLButtonElement>(
               '.wallpaper-option'))) {
    const preset = button.dataset.wallpaper as WallpaperPreset | undefined;
    const selected = settings.wallpaper.kind === 'preset' &&
        preset === settings.wallpaper.value;
    button.setAttribute('aria-pressed', String(selected));
  }
}

function buildWallpaperGrid(): void {
  for (const preset of PRESETS) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className =
        `wallpaper-option thumb-${preset}`;
    button.dataset.wallpaper = preset;
    button.title = PRESET_LABELS[preset];
    button.setAttribute('aria-label', `Sfondo ${PRESET_LABELS[preset]}`);
    button.addEventListener('click', () => {
      settings.wallpaper = {kind: 'preset', value: preset};
      persistSettings();
      applyWallpaper();
    });
    wallpaperGrid.append(button);
  }
}

async function handleWallpaperFile(file: File): Promise<void> {
  if (!file.type.startsWith('image/')) {
    window.alert('Il file selezionato non è un\'immagine.');
    return;
  }
  if (file.size > 12 * 1024 * 1024) {
    window.alert('Immagine troppo grande: limite 12 MB.');
    return;
  }

  try {
    const dataUrl = await downscaleImage(file);
    const previous = settings.wallpaper;
    settings.wallpaper = {kind: 'custom', value: dataUrl};
    if (!persistSettings()) {
      settings.wallpaper = previous;
      applyWallpaper();
      return;
    }
    applyWallpaper();
  } catch {
    window.alert('Impossibile leggere questa immagine.');
  } finally {
    wallpaperFile.value = '';
  }
}

async function downscaleImage(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const maxEdge = 2560;
  const scale = Math.min(1, maxEdge / Math.max(bitmap.width, bitmap.height));
  const width = Math.max(1, Math.round(bitmap.width * scale));
  const height = Math.max(1, Math.round(bitmap.height * scale));

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (!context) {
    bitmap.close();
    throw new Error('Canvas non disponibile');
  }
  context.drawImage(bitmap, 0, 0, width, height);
  bitmap.close();

  const blob = await new Promise<Blob|null>((resolve) => {
    canvas.toBlob(resolve, 'image/jpeg', 0.86);
  });
  if (!blob) {
    throw new Error('Conversione immagine fallita');
  }
  return await blobToDataUrl(blob);
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result);
      } else {
        reject(new Error('Lettura immagine fallita'));
      }
    };
    reader.onerror = () => reject(new Error('Lettura immagine fallita'));
    reader.readAsDataURL(blob);
  });
}

// --------------------------------------------------------------- scorciatoie

function isSafeHttpUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

function normalizeUrl(raw: string): string | null {
  const value = raw.trim();
  if (value.length === 0) {
    return null;
  }
  const candidate = /^[a-z][a-z0-9+.-]*:/i.test(value) ?
      value :
      `https://${value}`;
  try {
    const url = new URL(candidate);
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      return null;
    }
    if (url.hostname !== 'localhost' && !url.hostname.includes('.')) {
      return null;
    }
    return url.toString();
  } catch {
    return null;
  }
}

function looksLikeUrl(value: string): boolean {
  if (/\s/.test(value)) {
    return false;
  }
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(value)) {
    return true;
  }
  if (/^localhost(:\d+)?(\/.*)?$/i.test(value)) {
    return true;
  }
  return /^[^\s/]+\.[^\s/]{2,}(?:[/:?#].*)?$/i.test(value);
}

function navigateFromInput(raw: string): void {
  const value = raw.trim();
  if (value.length === 0) {
    return;
  }
  if (looksLikeUrl(value)) {
    const url = normalizeUrl(value);
    if (url) {
      window.location.assign(url);
      return;
    }
  }
  window.location.assign(`${SEARCH_URL}${encodeURIComponent(value)}`);
}

function makeId(): string {
  if (typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function renderShortcuts(): void {
  shortcutGrid.textContent = '';

  shortcuts.forEach((shortcut, index) => {
    const item = document.createElement('li');
    item.className = 'shortcut';
    item.draggable = true;
    item.dataset.id = shortcut.id;
    item.classList.add(`hue-${index % 6}`);

    const link = document.createElement('a');
    link.className = 'shortcut-link';
    link.href = shortcut.url;
    link.title = shortcut.url;

    const letter = document.createElement('span');
    letter.className = 'shortcut-letter';
    letter.setAttribute('aria-hidden', 'true');
    letter.textContent =
        shortcut.name.trim().charAt(0).toUpperCase() || '·';

    const name = document.createElement('span');
    name.className = 'shortcut-name';
    name.textContent = shortcut.name;

    link.append(letter, name);

    const edit = document.createElement('button');
    edit.type = 'button';
    edit.className = 'shortcut-edit';
    edit.setAttribute('aria-label', `Modifica ${shortcut.name}`);
    edit.innerHTML =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="1.8" stroke-linecap="round" aria-hidden="true">' +
        '<path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3Z"/>' +
        '<path d="m13.5 6.5 4 4"/></svg>';
    edit.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      openShortcutDialog(shortcut.id);
    });

    link.addEventListener('keydown', (event) => {
      if (!event.altKey) {
        return;
      }
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        moveShortcut(shortcut.id, Math.max(0, index - 1));
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        moveShortcut(
            shortcut.id, Math.min(shortcuts.length - 1, index + 1));
      }
    });

    item.addEventListener('dragstart', (event) => {
      draggedId = shortcut.id;
      item.classList.add('is-dragging');
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', shortcut.id);
      }
    });
    item.addEventListener('dragend', () => {
      draggedId = null;
      item.classList.remove('is-dragging');
      clearDropTargets();
    });
    item.addEventListener('dragover', (event) => {
      if (draggedId && draggedId !== shortcut.id) {
        event.preventDefault();
        item.classList.add('drop-target');
      }
    });
    item.addEventListener('dragleave', () => {
      item.classList.remove('drop-target');
    });
    item.addEventListener('drop', (event) => {
      event.preventDefault();
      item.classList.remove('drop-target');
      if (draggedId) {
        moveShortcut(draggedId, index);
      }
    });

    item.append(link, edit);
    shortcutGrid.append(item);
  });

  const addItem = document.createElement('li');
  addItem.className = 'shortcut shortcut-add';
  const addButton = document.createElement('button');
  addButton.type = 'button';
  addButton.className = 'shortcut-add-button';
  addButton.setAttribute('aria-label', 'Aggiungi scorciatoia');
  addButton.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="1.8" stroke-linecap="round" aria-hidden="true">' +
      '<path d="M12 5v14M5 12h14"/></svg>' +
      '<span class="shortcut-add-label">Aggiungi</span>';
  addButton.addEventListener('click', () => openShortcutDialog(null));
  addItem.append(addButton);
  shortcutGrid.append(addItem);
}

function clearDropTargets(): void {
  for (const item of Array.from(
           shortcutGrid.querySelectorAll<HTMLElement>('.shortcut'))) {
    item.classList.remove('drop-target');
  }
}

function moveShortcut(id: string, targetIndex: number): void {
  const fromIndex = shortcuts.findIndex((item) => item.id === id);
  if (fromIndex < 0) {
    return;
  }
  const boundedTarget =
      Math.max(0, Math.min(shortcuts.length - 1, targetIndex));
  if (fromIndex === boundedTarget) {
    return;
  }
  const [moved] = shortcuts.splice(fromIndex, 1);
  if (!moved) {
    return;
  }
  shortcuts.splice(boundedTarget, 0, moved);
  persistShortcuts();
  renderShortcuts();
  requestAnimationFrame(() => {
    const anchor =
        shortcutGrid.querySelector<HTMLAnchorElement>(
            `.shortcut[data-id="${CSS.escape(id)}"] .shortcut-link`);
    anchor?.focus();
  });
}

function openShortcutDialog(id: string | null): void {
  editingId = id;
  shortcutError.hidden = true;
  shortcutError.textContent = '';

  const existing =
      id ? shortcuts.find((item) => item.id === id) : undefined;
  dialogTitle.textContent =
      existing ? 'Modifica scorciatoia' : 'Nuova scorciatoia';
  shortcutName.value = existing ? existing.name : '';
  shortcutUrl.value = existing ? existing.url : '';
  shortcutDelete.hidden = !existing;

  dialog.showModal();
  shortcutName.focus();
  shortcutName.select();
}

function closeShortcutDialog(): void {
  editingId = null;
  dialog.close();
}

function handleShortcutSubmit(event: SubmitEvent): void {
  event.preventDefault();
  const name = shortcutName.value.trim();
  const url = normalizeUrl(shortcutUrl.value);

  if (name.length === 0) {
    showFormError('Inserisci un nome.');
    return;
  }
  if (!url) {
    showFormError('Inserisci un indirizzo http o https valido.');
    return;
  }

  if (editingId) {
    const target = shortcuts.find((item) => item.id === editingId);
    if (target) {
      target.name = name.slice(0, 40);
      target.url = url;
    }
  } else {
    shortcuts.push({id: makeId(), name: name.slice(0, 40), url});
  }

  persistShortcuts();
  renderShortcuts();
  closeShortcutDialog();
}

function showFormError(message: string): void {
  shortcutError.textContent = message;
  shortcutError.hidden = false;
  shortcutUrl.focus();
}

function deleteEditingShortcut(): void {
  if (!editingId) {
    return;
  }
  shortcuts = shortcuts.filter((item) => item.id !== editingId);
  persistShortcuts();
  renderShortcuts();
  closeShortcutDialog();
}

// ------------------------------------------------------------------ pannello

function openPanel(): void {
  lastFocused = document.activeElement instanceof HTMLElement ?
      document.activeElement :
      null;
  panelScrim.hidden = false;
  requestAnimationFrame(() => panelScrim.classList.add('is-visible'));
  panel.classList.add('is-open');
  panel.setAttribute('aria-hidden', 'false');
  customizeOpen.setAttribute('aria-expanded', 'true');
  customizeClose.focus();
}

function closePanel(): void {
  panel.classList.remove('is-open');
  panel.setAttribute('aria-hidden', 'true');
  customizeOpen.setAttribute('aria-expanded', 'false');
  panelScrim.classList.remove('is-visible');
  window.setTimeout(() => {
    if (!panel.classList.contains('is-open')) {
      panelScrim.hidden = true;
    }
  }, 220);
  lastFocused?.focus();
}

// ---------------------------------------------------------------------- init

function wireEvents(): void {
  searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    navigateFromInput(searchInput.value);
  });

  themeToggle.addEventListener('click', cycleTheme);
  customizeOpen.addEventListener('click', openPanel);
  customizeClose.addEventListener('click', closePanel);
  panelScrim.addEventListener('click', closePanel);

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && panel.classList.contains('is-open')) {
      closePanel();
    }
  });

  for (const button of Array.from(
           themeChoices.querySelectorAll<HTMLButtonElement>(
               '[data-theme-choice]'))) {
    button.addEventListener('click', () => {
      const choice = button.dataset.themeChoice;
      if (choice === 'dark' || choice === 'light' || choice === 'auto') {
        settings.theme = choice;
        persistSettings();
        applyTheme();
      }
    });
  }

  brightness.addEventListener('input', () => {
    settings.brightness = Number(brightness.value);
    brightnessValue.textContent = `${settings.brightness}%`;
    document.documentElement.style.setProperty(
        '--ntp-brightness', String(settings.brightness / 100));
    persistSettings();
  });

  scrimOpacity.addEventListener('input', () => {
    settings.scrim = Number(scrimOpacity.value);
    scrimValue.textContent = `${settings.scrim}%`;
    document.documentElement.style.setProperty(
        '--ntp-scrim-opacity', String(settings.scrim / 100));
    persistSettings();
  });

  wallpaperFile.addEventListener('change', () => {
    const file = wallpaperFile.files?.[0];
    if (file) {
      void handleWallpaperFile(file);
    }
  });

  resetButton.addEventListener('click', () => {
    const confirmed = window.confirm(
        'Ripristinare la nuova scheda? Scorciatoie e sfondo personalizzati ' +
        'verranno rimossi da questo dispositivo.');
    if (!confirmed) {
      return;
    }
    localStorage.removeItem(SETTINGS_KEY);
    localStorage.removeItem(SHORTCUTS_KEY);
    settings = loadSettings();
    shortcuts = loadShortcuts();
    applyTheme();
    applyWallpaper();
    renderShortcuts();
  });

  window.matchMedia('(prefers-color-scheme: light)')
      .addEventListener('change', () => {
        if (settings.theme === 'auto') {
          applyTheme();
        }
      });

  shortcutForm.addEventListener('submit', (event) => {
    handleShortcutSubmit(event);
  });
  shortcutCancel.addEventListener('click', closeShortcutDialog);
  shortcutDelete.addEventListener('click', deleteEditingShortcut);
  dialog.addEventListener('close', () => {
    editingId = null;
  });
}

function init(): void {
  renderClock();
  window.setInterval(renderClock, 10_000);
  buildWallpaperGrid();
  wireEvents();
  applyTheme();
  applyWallpaper();
  renderShortcuts();
}

init();
