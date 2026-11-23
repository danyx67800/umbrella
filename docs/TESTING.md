# Test

## Regola

Nessuna funzionalità è "completata" perché il codice compila. Una funzione è
verificata solo quando esiste un esito registrato. I test non eseguiti sono
dichiarati come tali, mai come superati.

## Cosa è stato eseguito (23/11/2026)

Ambiente: Windows 11, Python 3.13.14, 31 GB RAM, 328 GB liberi, checkout
Chromium **non presente** (manca la toolchain C++).

| Verifica | Esito |
|---|---|
| `python -m unittest discover -s tests -v` | Eseguito: **38 test, 0 fallimenti** |
| `python scripts/verify_upstream_specs.py` | Eseguito: **21 operazioni, 0 errori** sul tag reale |
| `python scripts/integrate.py --apply` sulla fixture | Applicato; snippet verificati a mano |
| `npx tsc --noEmit --strict app.ts` | Eseguito: **0 errori** |
| GitHub Actions CI (windows-latest) | **Verde** (test, compileall, JSON, preflight) |
| `python scripts/gen_patches.py --check` | Non eseguito (serve il checkout git) |
| Workflow `Build Windows (self-hosted)` | Non eseguito: nessun runner registrato |
| Build Chromium / build Umbrella | **Non eseguita**: VS 2022, SDK e depot_tools assenti |
| Avvio del browser, navigazione, UI | **Non eseguiti** |

La fixture è composta dai file upstream reali scaricati dal tag pinnato
(`scripts/verify_upstream_specs.py` ricrea lo stesso controllo), non da
sorgenti inventati.

## Test automatici del repository

```bash
python -m unittest discover -s tests -v
```

Coprono:

- coerenza `VERSION` / `versions.json` / header C++ / changelog;
- motore di integrazione: anchor unico, idempotenza, check-only, GN list,
  regex con conteggio, hash guard dei file sostituiti;
- asset nuova scheda: token colore, CSP, assenza di rete/iframe, DuckDuckGo
  con `encodeURIComponent`, accessibilità, ID grit;
- specifiche: percorsi GN mappati su sorgenti esistenti, nessun marker
  duplicato;
- documentazione: link relativi, presenza dei documenti, dichiarazioni
  oneste sullo stato.

```bash
python scripts/verify_upstream_specs.py
```

Scarica dal tag pinnato solo i file toccati e verifica gli anchor senza
clonare Chromium. Da eseguire dopo ogni aggiornamento upstream.

## Test sul browser compilato

Da eseguire sulla macchina Windows con toolchain, con esito registrato in
questo file. Comandi di riferimento (target upstream):

```bash
autoninja -C out/Umbrella unit_tests browser_tests
out/Umbrella/unit_tests.exe --gtest_filter=Umbrella*
out/Umbrella/browser_tests.exe --gtest_filter=Umbrella*
```

I test C++ Umbrella saranno aggiunti insieme alla prima build; non esistono
ancora test che dichiarino di coprire codice non compilato.

## Matrice manuale (Fase 2+)

| Area | Caso | Esito |
|---|---|---|
| Avvio | profilo nuovo, primo avvio | da eseguire |
| Navigazione | HTTP, HTTPS, redirect, errore DNS | da eseguire |
| Navigazione | back / forward / reload / stop | da eseguire |
| Nuova scheda | `chrome://umbrella/`, ricerca DDG | da eseguire |
| Scorciatoie | add / edit / delete / drag / tastiera | da eseguire |
| Wallpaper | preset, upload, overlay, luminosità | da eseguire |
| Tema | dark, light, auto, reduced motion | da eseguire |
| Schede | multiple, verticali, bloccate, ripristino | da eseguire |
| Sessione | chiusura e ripristino | da eseguire |
| Preferiti | aggiunta, cartelle, persistenza | da eseguire |
| Cronologia | visita, ricerca, cancellazione | da eseguire |
| Download | avvio, pausa, ripresa, annulla, apri | da eseguire |
| Private mode | cookie/cache separati, chiusura | da eseguire |
| Permessi | camera, mic, notifiche, revoca | da eseguire |
| Sicurezza | Site Isolation attivo, sandbox | da eseguire |
| Media | video HTML5, audio, codec | da eseguire |
| Popup | blocco e gestione | da eseguire |
| Crash | ripristino dopo terminazione renderer | da eseguire |

## Criteri di regressione

- Nessun test esistente rimosso o indebolito per far passare una modifica.
- Un fallimento si corregge alla causa; niente `skip` senza motivazione
  documentata.
- Se un test richiede rete o credenziali, va marcato e non deve bloccare la CI
  di base.
