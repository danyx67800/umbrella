# Architettura

## Principio

Umbrella è un fork di Chromium, non un browser costruito sopra Chromium.
Il codice upstream resta la sorgente di verità per navigazione, processi,
rete, rendering, profili, permessi e sicurezza. Umbrella aggiunge un layer
proprietario sottile e verificabile, più un numero minimo di punti di
aggancio tracciati in `integration/specs.py` e trasformati in patch.

Il repository non contiene il checkout Chromium: `scripts/fetch_chromium.py`
lo crea al commit pinnato in `versions.json`.

## Modello di processo

Nessuna modifica al modello di sicurezza:

- processo browser: UI nativa, profili, rete, coordinamento;
- processi renderer separati con Site Isolation attiva;
- processo GPU separato;
- Network Service nel processo browser;
- sandbox Win32 (job object, token ristretti) invariata;
- Blink e V8 invariati.

Umbrella non crea un secondo motore di navigazione e non disabilita nessuna
protezione per ottenere prestazioni.

## Livelli

```
┌──────────────────────────────────────────────────────────────┐
│ UI nativa Views (toolbar, tab strip, frame)  → Fase 3        │
│ UI WebUI trusted `chrome://umbrella/`        → Fase 2 (qui)  │
├──────────────────────────────────────────────────────────────┤
│ Servizi Chromium riusati senza duplicazione                  │
│ Browser, TabStripModel, Omnibox, Profiles, History,          │
│ Bookmarks, Downloads, Permissions, ContentSettings,          │
│ Safe Browsing, TemplateURLService                            │
├──────────────────────────────────────────────────────────────┤
│ Layer proprietario `chrome/browser/umbrella/`                │
│ prefs · features · version · default search · extra parts     │
│ WebUI controller/config                                      │
├──────────────────────────────────────────────────────────────┤
│ Chromium upstream @ 158.0.8127.37                            │
└──────────────────────────────────────────────────────────────┘
```

## Punti di integrazione

Tutti verificati sul tag `158.0.8127.37` (file e funzioni esistono davvero in
quella revisione). Il motore `integration/` fallisce se un anchor cambia: non
applica patch "alla cieca".

### 1. Sorgenti nel target GN

`chrome/browser/BUILD.gn`, target `source_set("core")` (contiene
`chrome_browser_main.cc`). Vengono aggiunti i file dell'overlay. Il codice
proprietario è collocato in `chrome/browser/umbrella/` così non serve un
nuovo target GN né un grafo di dipendenze separato.

### 2. Startup

`chrome/browser/chrome_browser_main.cc` registra un
`ChromeBrowserMainExtraParts` con `AddParts(...)`, accanto a
`ChromeBrowserMainExtraPartsViews`. L'extra part implementa `PostProfileInit`
e applica le impostazioni di primo avvio: DuckDuckGo se il motore corrente è
ancora quello predefinito upstream, senza mai sovrascrivere una scelta utente.

### 3. Default delle preferenze

`chrome/browser/prefs/browser_prefs.cc`, funzione `RegisterProfilePrefs`:
registra le preferenze proprietarie. Il default delle schede verticali viene
applicato una sola volta dall'extra part, dopo la creazione del profilo, così
una scelta successiva dell'utente non viene mai sovrascritta.

### 4. Nuova scheda

`chrome/browser/search/search.cc`, `GetNewTabPageURL(Profile*)`:
restituisce `chrome://umbrella/` quando la nuova scheda Umbrella è attiva.
La funzione è l'unico punto usato da omnibox, confronto URL e navigazione NTP,
quindi il comportamento resta coerente in tutto il browser.

### 5. WebUI

`chrome/browser/ui/webui/chrome_web_ui_configs.cc`: registrazione di
`umbrella::UmbrellaUIConfig`, basata su `content::DefaultWebUIConfig<UmbrellaUI>`
(stesso pattern di `about_ui.h` upstream). `chrome://umbrella/` è un nuovo host
sullo schema `chrome://` già esistente: nessuna modifica al content layer e
nessun nuovo schema URL.

### 6. Risorse

`chrome/browser/resources/BUILD.gn`, `group("resources")`: aggiunta di
`"umbrella:resources"`. La pagina è costruita con `build_webui` (lo stesso
strumento delle pagine Chrome), con `grd_prefix = "umbrella"`, quindi i file
finiscono nei pak firmati insieme alle altre risorse del browser.

### 7. Branding

`chrome/app/theme/chromium/BRANDING` e `chrome/app/chromium_strings.grd`:
nome prodotto, short name, copyright. Il branding Google non viene usato e
`is_chrome_branded` resta `false`; nessuna informazione di compatibilità dei
siti viene alterata.

## Perché la nuova scheda è WebUI

La nuova scheda è una pagina interna trusted, non un sito remoto e non un
iframe. WebUI offre:

- isolamento dal contenuto web (origine `chrome://`);
- CSP e bindings nativi;
- nessuna richiesta di rete per il layout;
- possibilità di passare in futuro a Mojo per preferenze native.

La personalizzazione (scorciatoie, wallpaper, overlay) usa `localStorage`
dell'origine `chrome://umbrella/` in questa fase. La migrazione a pref di
profilo versionate è in roadmap (Fase 4) e non cambia l'architettura della
pagina.

Toolbar, tab strip e sidebar restano nativi Views: la UI principale non è
una pagina web. `chrome://umbrella/` è solo il contenuto della nuova scheda,
come `chrome://newtab` in Chromium.

## Cosa non viene duplicato

| Funzione | Implementazione |
|---|---|
| Navigazione, redirect, popup | `content/`, `chrome/browser/ui` |
| Tab, gruppi, session restore | `TabStripModel`, `SessionService` |
| Omnibox e suggerimenti | `OmniboxController`, `AutocompleteController` |
| Preferiti | `BookmarkModel` |
| Cronologia | `HistoryService` |
| Download | `DownloadManager` |
| Profili e dati | `Profile`, `ProfileManager` |
| Permessi | `PermissionManager`, `ContentSettings` |
| Private mode | profili off-the-record |
| Sicurezza | Site Isolation, sandbox, Safe Browsing |

## Persistenza

- Dati browser: formati nativi Chromium nel profilo.
- Preferenze Umbrella: `PrefService` del profilo, registrate in
  `umbrella_prefs.cc`.
- Personalizzazione NTP: `localStorage` dell'origine interna, con export/
  import previsto in Fase 4.
- Versionamento e migrazioni: `umbrella_prefs` espone una versione schema,
  incrementata solo con migrazione esplicita.

## Aggiornamenti di Chromium

Procedura in `docs/PATCHES.md`. Ogni upgrade produce:

1. nuovo tag/commit in `versions.json`;
2. nuovi anchor verificati;
3. patch rigenerate;
4. build e test registrati in `docs/TESTING.md`.

Mai `git pull` sul checkout senza passare dal processo di verifica.
