# Gestione patch e aggiornamenti Chromium

## Due livelli, una fonte di verità

1. **Overlay** (`umbrella/`): file nuovi, nessun conflitto con upstream.
2. **Integrazione** (`integration/specs.py`): modifiche puntuali a file
   Chromium, espresse come anchor esatti verificati sul commit pinnato.

`patches/` contiene il risultato generato dal checkout, non è la fonte di
verità. Il repository è riproducibile perché chiunque può rifare
overlay + integrazione sul commit fissato.

## Formato di una specifica

```python
InsertAfter(
    file="chrome/browser/chrome_browser_main.cc",
    anchor='main_parts->AddParts(\n      std::make_unique<ChromeBrowserMainExtraPartsViews>());',
    text='  main_parts->AddParts(\n      std::make_unique<umbrella::UmbrellaBrowserMainExtraParts>());\n',
    marker="UmbrellaBrowserMainExtraParts",
)
```

Regole:

- `anchor` deve comparire **esattamente una volta** nel file. Zero o più di una
  → errore bloccante con diagnostica.
- `marker` rende l'operazione idempotente: se è già presente, non viene
  applicata due volte.
- Nessuna regex "larga", nessun `sed` globale, nessuna patch che ignori il
  fallimento.
- Ogni operazione dichiara il motivo tecnico in un commento.

## Ciclo di lavoro

```bash
python scripts/link_overlay.py
python scripts/integrate.py --check
python scripts/integrate.py --apply
# build + test
python scripts/gen_patches.py
```

`gen_patches.py` produce:

- `patches/umbrella-<tag>.patch` — diff unificato applicabile con
  `git apply --check`;
- `patches/manifest.json` — file toccati, hash upstream, versione progetto,
  tag Chromium, data.

## Verifica prima di un commit

```bash
python scripts/integrate.py --check
python scripts/gen_patches.py --check
git -C chromium/src diff --stat
```

Se `--check` fallisce, non si committa: si aggiornano gli anchor.

## Aggiornamento a un nuovo Chromium

1. Scegliere un tag Stable e il suo commit:
   `gh api repos/chromium/chromium/git/ref/tags/<tag>`.
2. Aggiornare `versions.json` (tag, commit, milestone, data).
3. `python scripts/fetch_chromium.py --switch <tag>` (nuovo checkout o
   `gclient sync --revision`).
4. `python scripts/integrate.py --check`: elenca ogni anchor rotto.
5. Aggiornare `integration/specs.py` leggendo il nuovo codice: mai assumere
   che una funzione esista con la stessa firma.
6. Build + test + nuova patch.
7. Registrare l'esito in `docs/TESTING.md` e nel changelog.

Non si aggiorna mai l'upstream "a mano" dentro il checkout senza questo ciclo:
il prossimo `fetch_chromium.py` riporterebbe il commit al pin e le modifiche
non tracciate andrebbero perse.

## Cosa non è una patch

- Modifiche di stile o refactor non necessari al prodotto.
- Disattivazione di Site Isolation, sandbox, Safe Browsing o HTTPS-first.
- Cambi di user agent o informazioni di compatibilità dei siti.
- Feature flag nascoste che simulano funzionalità non implementate.

Queste richieste vanno rifiutate anche se riducono il lavoro di build.
