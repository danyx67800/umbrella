# Build su Windows

## Requisiti reali

Il pin Chromium 158.0.8127.37 richiede **Visual Studio 2026 (>=18.0)** e
**Windows SDK 10.0.28000.2270 o successivo**. Visual Studio 2022 e l'SDK 26100
non sono più sufficienti: `build/vs_toolchain.py` al commit pinnato dichiara
`SDK_VERSION = '10.0.28000.0'`.

| Requisito | Minimo | Note |
|---|---|---|
| Windows | 10 22H2 / 11 x64 | long paths abilitati |
| Visual Studio | 2026 18.0+ | workload Desktop C++ + ATL/MFC |
| Windows SDK | 10.0.28000.2270+ | installare l'SDK completo |
| RAM | 16 GB | 32 GB consigliati |
| Disco | ~120–150 GB liberi | checkout ~45 GB + build ~60–90 GB |
| Python | 3.11+ | lo script verifica |
| Git | 2.40+ | core.longpaths |
| depot_tools | ultimo | `gclient`, `gn`, `autoninja` nel PATH |

La macchina di sviluppo ha 6 core/12 thread, 31 GB di RAM e 327 GB liberi:
sufficiente, ma la prima build richiede ore.

## 1. Toolchain

Lo script di supporto installa VS 2026 Build Tools e l'SDK completo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_toolchain.ps1
```

Richiede privilegi amministratore. Esegue:

- VS 2026 Build Tools 18.x con `Microsoft.VisualStudio.Workload.NativeDesktop`
  e `Microsoft.VisualStudio.Component.VC.ATLMFC`;
- Windows SDK 10.0.28000 con tutte le feature;
- `LongPathsEnabled=1`, `git core.longpaths=true`;
- `DEPOT_TOOLS_WIN_TOOLCHAIN=0` e `vs2026_install` a livello macchina.

Installazione manuale equivalente:

```powershell
vs_BuildTools.exe --quiet --wait --norestart `
  --add Microsoft.VisualStudio.Workload.NativeDesktop `
  --add Microsoft.VisualStudio.Component.VC.ATLMFC `
  --includeRecommended
winsdksetup.exe /features + /q /norestart
```

Se il percorso di VS non viene rilevato, impostare
`vs2026_install=C:\Program Files\Microsoft Visual Studio\2026\BuildTools`.

`depot_tools` non richiede privilegi e vive nel repository:

```bash
git clone --depth 1 https://chromium.googlesource.com/chromium/tools/depot_tools.git .depot_tools
export PATH="$PWD/.depot_tools:$PATH"
```

## 2. Preflight

```bash
python scripts/preflight.py
```

Controlla spazio, RAM, Python, **VS 2026**, **SDK 28000**, depot_tools e
coerenza del pin. Con VS 2022 o SDK 26100 fallisce prima di scaricare nulla.
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

Prima build: 3–5 ore su 6 core/12 thread. Build incrementali: minuti.

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
| `gclient: command not found` | `.depot_tools` fuori dal PATH | `export PATH="$PWD/.depot_tools:$PATH"` |
| `vswhere not found` | VS non installato | eseguire `install_toolchain.ps1` |
| `No supported Visual Studio` | VS 2022 o versione <18 | installare VS 2026 |
| `Windows SDK ... 10.0.28000` | SDK 26100/22621 | installare SDK 28000 |
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
| Durata job | 6 h | 3–5 h su 6 core |

Il disco da 14 GB rende la build impossibile prima ancora del tempo. I
[larger runner](https://docs.github.com/en/actions/reference/runners/larger-runners)
con 150–600 GB esistono, ma **solo per organizzazioni Team/Enterprise**; non
sono disponibili su un account personale.

### Workflow self-hosted

`.github/workflows/build-windows.yml` è avviabile manualmente e richiede un
runner con label `self-hosted`, `windows`, `x64`, `umbrella-build`.

Preparazione:

1. Eseguire `scripts/install_toolchain.ps1` e verificare
   `python scripts/preflight.py`.
2. Nella pagina **Settings → Actions → Runners → New self-hosted runner**
   scaricare il runner Windows x64 e configurarlo:

```powershell
.\config.cmd --url https://github.com/danyx67800/umbrella `
  --token <TOKEN> --labels umbrella-build `
  --work C:\umbrella-runner\_work --name umbrella-desktop
.\run.cmd
```

3. Avviare **Actions → Build Windows (self-hosted) → Run workflow**.

Il workflow clona `depot_tools` nel workspace (`.depot_tools`), ripristina
l'integrazione precedente, sincronizza il commit pinnato, reinstalla l'overlay,
verifica gli anchor, compila con GN/Ninja e carica
`dist/Umbrella-<versione>-win64.zip` come artefatto non firmato.

`actions/checkout` usa `clean: false` per conservare `chromium/` e `.cache/`
tra una build e l'altra. Il runner va trattato come macchina dedicata: il
workflow esegue codice del repository con i privilegi dell'utente che lancia
`run.cmd`.

**Sicurezza:** il workflow parte solo con `workflow_dispatch` (richiede
permessi di scrittura). Non aggiungere trigger `pull_request` o
`pull_request_target` a un workflow self-hosted: eseguirebbe codice di terzi
sulla macchina.

La build hosted resta intenzionalmente assente: un workflow che tenta di
compilare Chromium su 14 GB sprecherebbe solo tempo e minuti.
