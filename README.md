# UMBRELLA

Browser desktop nativo basato direttamente sul sorgente ufficiale Chromium.
Nessun Electron, nessun CEF, nessun WebContentsView, nessun iframe: il browser
è un fork di Chromium con UI nativa Views e pagine servite dall'architettura
WebUI di Chromium.

- **Versione progetto:** 0.1.0 (`VERSION`)
- **Chromium:** 158.0.8127.37 — commit `b8c2be851f62f6a394ec57955d7f31335d7cb6d4`
- **Canale upstream:** Stable (17 novembre 2026)
- **Piattaforma:** Windows 10/11 x64
- **Repository:** https://github.com/danyx67800/umbrella

Stato upstream e pin sono in [`versions.json`](versions.json).

---

## Stato reale del progetto

Questa non è una demo e non contiene una UI web che imita un browser. È
l'impalcatura di fork riproducibile di Chromium, con il primo strato
proprietario già scritto e con hook di integrazione verificati sul sorgente
upstream del tag pinnato.

| Area | Stato |
|---|---|
| Pin upstream verificato (tag + commit) | Fatto |
| Repo GitHub + workflow Git/gh | Fatto |
| Tooling fetch/sync/build/package | Fatto, non eseguito in questo ambiente |
| Overlay C++ (prefs, features, versione, default search, extra parts) | Scritto, **non compilato** |
| Nuova scheda WebUI `chrome://umbrella/` | Scritta, **non compilata né eseguita** |
| Motore di integrazione con anchor verificati | Fatto e testato |
| CI Windows (test, JSON, preflight) | Verde |
| Workflow build self-hosted | Pronto, in attesa di un runner registrato |
| Build Chromium su Windows | **Bloccata**: toolchain C++ assente |
| Toolbar/sidebar native Views, temi nativi, installer | **Non ancora implementati** (Fase 3+) |

### Blocker misurati su questa macchina

- Visual Studio 2022 / MSVC / Windows SDK: **non installati**.
- `depot_tools`: **non presenti**.
- Spazio libero su `C:`: **328 GB** — sufficiente per checkout + build.
- RAM: **31 GB** — sufficiente.

Il repository è progettato per essere clonato su una macchina Windows con
toolchain completa: `scripts/preflight.py` blocca la build se i requisiti non
sono soddisfatti, invece di fallire a metà.

---

## Architettura in breve

```
Chromium upstream (pinnato, mai modificato a mano)
        │
        ├── overlay  chrome/browser/umbrella/            ← codice C++ Umbrella
        ├── overlay  chrome/browser/resources/umbrella/  ← WebUI nuova scheda
        └── patch    ~6 punti di aggancio verificati      ← integrazione
```

Punti di integrazione già verificati sul tag `158.0.8127.37`:

| File upstream | Hook |
|---|---|
| `chrome/browser/BUILD.gn` (`source_set("core")`) | sorgenti Umbrella |
| `chrome/browser/chrome_browser_main.cc` | `AddParts(...)` per il primo avvio |
| `chrome/browser/prefs/browser_prefs.cc` | default pref Umbrella |
| `chrome/browser/search/search.cc` | `GetNewTabPageURL()` → `chrome://umbrella/` |
| `chrome/browser/ui/webui/chrome_web_ui_configs.cc` | registrazione `UmbrellaUIConfig` |
| `chrome/browser/resources/BUILD.gn` | pak risorse della nuova scheda |
| `chrome/app/theme/chromium/BRANDING` + `chromium_strings.grd` | branding |

Tutto il resto — navigazione, tab, profili, cronologia, preferiti, download,
permessi, sandbox, Site Isolation, Safe Browsing, rete, rendering — resta il
codice Chromium nativo, non replicato.

Dettagli: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Avvio rapido (su macchina con toolchain)

```bash
python scripts/preflight.py
python scripts/fetch_chromium.py          # checkout + sync al commit pinnato
python scripts/link_overlay.py            # copia l'overlay nel checkout
python scripts/integrate.py --check       # verifica gli anchor upstream
python scripts/integrate.py --apply       # applica i punti di aggancio
python scripts/build.py --release         # gn gen + autoninja
```

Per riallineare il repository dopo una build:

```bash
python scripts/gen_patches.py             # esporta patches/ + manifest
python -m unittest discover -s tests -v
```

Guida completa: [`docs/BUILD.md`](docs/BUILD.md).

---

## Struttura del repository

```
umbrella/
├── umbrella/            # codice proprietario (overlay, non compilato da solo)
│   ├── browser/         # C++ browser process: prefs, search, WebUI, extra parts
│   ├── common/          # versione, feature, costanti
│   └── resources/       # nuova scheda: HTML/CSS/TS + build_webui
├── integration/         # specifiche di integrazione + motore con anchor
├── scripts/             # preflight, fetch, overlay, integrazione, build, patch
├── gn/args/             # configurazioni GN release/debug
├── design/              # design token (fonte unica) e branding
├── patches/             # patch generate dal checkout (fonte: integration/)
├── tests/               # test eseguibili senza Chromium
├── docs/                # architettura, build, sicurezza, roadmap, release
└── .github/workflows/   # CI leggera (niente build Chromium su runner GitHub)
```

Il checkout Chromium vive in `chromium/` ed è ignorato da Git: il repository
Umbrella non duplica ~100 GB di upstream. La riproducibilità è garantita da
commit pinnato + overlay versionato + specifiche di integrazione + patch
generate.

---

## Privacy e telemetria

Umbrella non aggiunge analytics, telemetria proprietaria, pubblicità o
tracking. Eredita le connessioni native di Chromium (Safe Browsing, component
updater, variations, DNS/HTTPS probing, suggerimenti del motore di ricerca):
sono documentate in [`docs/SECURITY.md`](docs/SECURITY.md) e non vengono
disattivate per "semplificare" lo sviluppo. Nessuna protezione viene dichiarata
superiore a quella effettivamente implementata.

Motore predefinito: **DuckDuckGo** (`https://duckduckgo.com/`), applicato al
primo avvio solo se l'utente non ha già scelto un motore diverso.

---

## Licenza e marchi

Il codice Umbrella in questo repository è distribuito con licenza BSD 3-Clause
([`LICENSE`](LICENSE)), compatibile con Chromium. Chromium è © The Chromium
Authors, BSD 3-Clause. Umbrella non è affiliato a Google, Brave, Vivaldi o
Microsoft e non usa i loro marchi, loghi o interfacce.
