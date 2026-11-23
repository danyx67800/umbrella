# Build su Windows

## Requisiti reali

| Requisito | Minimo | Note |
|---|---|---|
| Windows | 10 22H2 / 11 x64 | |
| Visual Studio | 2022 17.9+ con Desktop C++ | toolset MSVC x64/x86 |
| Windows SDK | versione richiesta da `build/vs_toolchain.py` | installare l'SDK completo |
| RAM | 16 GB | 32 GB consigliati |
| Disco | ~120–150 GB liberi | checkout ~45 GB + build ~60–90 GB |
| Python | 3.11+ | lo script verifica |
| Git | 2.40+ | |
| depot_tools | ultimo | `gclient`, `gn`, `autoninja` nel PATH |

Su questa macchina di sviluppo **mancano Visual Studio, Windows SDK e
depot_tools**: la build non è stata eseguita. Lo spazio disco (328 GB) e la
RAM (31 GB) sono invece sufficienti. `preflight.py` riporta esattamente
questo e termina con errore prima di scaricare nulla.

## 1. Toolchain

Installare Visual Studio 2022 Build Tools (o Community) con:

- Desktop development with C++;
- MSVC v143 x64/x86 build tools;
- Windows 10/11 SDK;
- C++ ATL e C++ CMake tools (richiesti da alcuni target).

Poi `depot_tools`:

```powershell
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git C:\depot_tools
$env:PATH = "C:\depot_tools;$env:PATH"
```

Impostare `DEPOT_TOOLS_WIN_TOOLCHAIN=0` se si usa l'installazione locale di
Visual Studio invece del toolchain interno di Chromium, come documentato da
upstream.

## 2. Preflight

```bash
python scripts/preflight.py
```

Controlla OS, spazio, RAM, Python, VS/SDK, depot_tools, coerenza del pin.
`--skip-toolchain` è pensato solo per la CI.

## 3. Checkout pinnato

```bash
python scripts/fetch_chromium.py
```

Lo script:

1. crea `chromium/.gclient` con `target_os = ["win"]`;
2. esegue `gclient sync --revision src@<commit> --with_branch_heads --with_tags`;
3. verifica che `git rev-parse HEAD` corrisponda al commit in `versions.json`;
4. esegue `gclient runhooks`;
5. scrive `chromium/.umbrella-checkout.json`.

Non usa `fetch chromium` alla cieca: il commit è fissato e verificato.

## 4. Overlay

```bash
python scripts/link_overlay.py
```

Copia (non symlink: su Windows richiedono privilegi) l'overlay in:

- `chromium/src/chrome/browser/umbrella/`
- `chromium/src/chrome/browser/resources/umbrella/`

Registra hash dei file in `chromium/.umbrella-overlay.json`, così `--check`
rileva drift e `--clean` rimuove solo ciò che ha installato.

## 5. Integrazione

```bash
python scripts/integrate.py --check
python scripts/integrate.py --apply
```

`--check` verifica che ogni anchor esista una sola volta. Se Chromium cambia,
lo script si ferma e indica file, anchor e numero di occorrenze: nessuna patch
applicata a caso.

Dopo l'applicazione, `git -C chromium/src diff` mostra esattamente le modifiche
upstream.

## 6. Configurazione GN e compilazione

```bash
python scripts/build.py --release
```

Lo script scrive `out/Umbrella/args.gn` dal template `gn/args/umbrella.gn`,
poi esegue:

```
gn gen out/Umbrella
autoninja -C out/Umbrella chrome
```

Il file args è in `gn/args/umbrella.gn`. Target predefinito `chrome`
(l'eseguibile Windows è `chrome.exe` finché il rebranding di
`install_static` non sarà completato).

Prima build: 1–3 ore su 16 core. Build incrementali: minuti.

### Debug

```bash
python scripts/build.py --debug --target chrome
```

`is_debug = true`, `is_component_build = true`, simboli completi. Debug e
Release usano directory separate (`out/UmbrellaDebug`, `out/Umbrella`).

## 7. Test

```bash
python -m unittest discover -s tests -v
```

I test del repository non richiedono Chromium. I test del browser compilato
usano i target upstream (`browser_tests`, `unit_tests`) e vanno eseguiti sulla
macchina di build; la matrice manuale è in `docs/TESTING.md`.

## 8. Packaging

```bash
powershell -ExecutionPolicy Bypass -File scripts/package.ps1 -OutDir out/Umbrella
```

Crea `dist/Umbrella-<versione>-win64.zip` e `SHA256SUMS`. La validazione del
pacchetto su macchina pulita è obbligatoria prima di qualunque release.

## Problemi comuni

| Sintomo | Causa | Azione |
|---|---|---|
| `gclient: command not found` | depot_tools fuori dal PATH | aggiungere `C:\depot_tools` |
| `vswhere not found` | VS non installato | installare Build Tools |
| `The Windows SDK ... was not found` | SDK assente | installare SDK completo |
| `No space left on device` | < 100 GB | spostare checkout su disco dedicato |
| `gn: not found` | hook non eseguiti | `gclient runhooks` |
| anchor non trovato | upstream cambiato | aggiornare `integration/specs.py` |

## CI

La CI standard esegue test Python, validazione JSON, coerenza pin e controllo
degli asset.

### Perché i runner GitHub-hosted non possono compilare Chromium

| Risorsa | Runner standard | Requisito Chromium |
|---|---|---|
| vCPU | 4 | 8–16 consigliati |
| RAM | 16 GB | 16–32 GB |
| Disco | **14 GB** | **120–150 GB** |
| Durata job | 6 h | 1–3 h su 8–16 core |

Il disco da 14 GB rende la build impossibile prima ancora del tempo. I
[larger runner](https://docs.github.com/en/actions/reference/runners/larger-runners)
con 150–600 GB esistono, ma **solo per organizzazioni Team/Enterprise**; non
sono disponibili su un account personale. Questa macchina ha 6 core/12 thread,
31 GB di RAM e 328 GB liberi: è adatta come runner self-hosted.

### Workflow self-hosted

`.github/workflows/build-windows.yml` è avviabile manualmente e richiede un
runner con label `self-hosted`, `windows`, `x64`, `umbrella-build`.

Preparazione del runner:

1. Installare Visual Studio 2022 Build Tools + Windows SDK e `depot_tools`
   come descritto sopra, assicurandosi che `gclient`, `gn` e `autoninja` siano
   nel PATH (il workflow aggiunge `C:\depot_tools` se esiste).
2. Nelle impostazioni del repository: **Settings → Actions → Runners → New
   self-hosted runner**, scaricare il runner Windows x64 e configurare:

```powershell
.\config.cmd --url https://github.com/danyx67800/umbrella `
  --token <TOKEN> --labels umbrella-build --work C:\umbrella-runner
.\run.cmd
```

3. Avviare **Actions → Build Windows (self-hosted) → Run workflow** e
   scegliere `release` o `debug`.

Il workflow ripristina l'integrazione precedente, sincronizza il commit
pinnato, reinstalla l'overlay, verifica gli anchor, compila con GN/Ninja e
carica `dist/Umbrella-<versione>-win64.zip` come artefatto non firmato.

**Sicurezza:** il workflow parte solo con `workflow_dispatch` (richiede
permessi di scrittura). Non aggiungere trigger `pull_request` o
`pull_request_target` a un workflow self-hosted: eseguirebbe codice di terzi
sulla macchina.

La build hosted resta intenzionalmente assente: un workflow che tenta di
compilare Chromium su 14 GB sprecherebbe solo tempo e minuti.
