# Release

Le release si gestiscono con GitHub CLI. Una release non si pubblica se build,
test e pacchetto non sono stati verificati.

## Prerequisiti

- `gh auth status` autenticato con scope `repo`.
- Build Release completata e avviata su Windows 10 e 11 puliti.
- Matrice di `docs/TESTING.md` compilata.
- `CHANGELOG.md` aggiornato e versione allineata in `VERSION` e
  `versions.json`.

## 1. Verifica del repository

```bash
git status --short
python -m unittest discover -s tests -v
python scripts/verify_upstream_specs.py
python scripts/integrate.py --check
python scripts/gen_patches.py --check
```

Nessun file non tracciato o credenziale deve comparire in `git status`.

## 2. Build e pacchetto

```bash
python scripts/build.py --release
powershell -ExecutionPolicy Bypass -File scripts/package.ps1
```

Il pacchetto viene creato in `dist/Umbrella-<versione>-win64/` con
`SHA256SUMS`.

Validare su macchina pulita:

- avvio e navigazione;
- nuova scheda e scorciatoie;
- almeno un download e un video;
- chiusura e ripristino sessione;
- assenza di errori nel Visualizzatore eventi Windows.

## 3. Commit e tag

```bash
git add -A
git commit -m "release: Umbrella <versione>"
git tag -a v<versione> -m "Umbrella <versione>"
git push origin main
git push origin v<versione>
```

## 4. Release con gh

```bash
python scripts/release.py \
  --tag v<versione> \
  --artifacts dist/Umbrella-<versione>-win64.zip \
  --notes docs/releases/<versione>.md \
  --confirm
```

Lo script:

- verifica autenticazione e versione;
- rifiuta artefatti mancanti;
- calcola SHA-256 e scrive `dist/SHA256SUMS-<tag>.txt`;
- rifiuta un tag già pubblicato;
- chiama `gh release create` con note e checksum.

Per una prerelease usare `--draft` e pubblicare solo dopo la verifica.

## Criteri di blocco

Non pubblicare se:

- la build non è stata eseguita o fallisce;
- i test non sono stati eseguiti;
- il pacchetto non è stato avviato su una macchina pulita;
- manca la firma del codice per una distribuzione pubblica;
- le note contengono funzionalità non implementate;
- un artefatto non ha checksum.

## Aggiornamenti

Il sistema di auto-update firmato è previsto in Fase 7. Fino ad allora non
esiste alcun aggiornamento automatico: l'utente scarica manualmente una
release verificata. Non introdurre updater non firmati o canali non
controllati.
