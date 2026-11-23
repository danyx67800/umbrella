# Changelog

Formato basato su Keep a Changelog. Il progetto segue SemVer.

## [0.1.0] — 2026-11-23

### Added

- Pin upstream verificato: Chromium 158.0.8127.37,
  commit `b8c2be851f62f6a394ec57955d7f31335d7cb6d4` (Stable, 17/11/2026).
- Struttura fork riproducibile: overlay proprietario, specifiche di
  integrazione con anchor verificati, generazione patch, configurazioni GN.
- Layer C++ Umbrella: versione, feature, pref di profilo, default search
  DuckDuckGo al primo avvio, `ChromeBrowserMainExtraParts`.
- Nuova scheda WebUI `chrome://umbrella/`: ricerca DuckDuckGo, scorciatoie
  CRUD con drag & drop, wallpaper, overlay/luminosità, temi, persistenza locale.
- Tooling: preflight ambiente, fetch Chromium pinnato, overlay sync,
  integrazione/check/revert, build GN+Ninja, packaging, release.
- Test eseguibili senza Chromium e CI Windows leggera.
- Workflow `Build Windows (self-hosted)` per compilare su hardware adeguato,
  con verifica anchor, packaging e artefatto non firmato.
- `scripts/install_toolchain.ps1`: installazione di VS 2026 Build Tools e
  Windows SDK 10.0.28000, requisiti reali del pin Chromium 158.
- Preflight che rifiuta VS 2022 e SDK 26100 invece di fallire a metà build.

### Known limitations

- Nessuna build Chromium eseguita: VS 2026 e Windows SDK 10.0.28000 non sono
  installati. L'installer è pronto e il runner self-hosted è online, ma il
  prompt UAC non è stato approvato. Disco e RAM sono sufficienti.
- Toolbar, sidebar verticale nativa, impostazioni complete, installer e
  aggiornamenti firmati sono pianificati nelle fasi successive (vedi
  `docs/ROADMAP.md`).
- Il pacchetto Windows mantiene il nome eseguibile upstream finché non viene
  completata la personalizzazione `install_static`/branding.
