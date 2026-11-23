# Patch generate

Questa directory contiene l'output di `scripts/gen_patches.py`, non la fonte
di verità.

- **Fonte:** `integration/specs.py` + overlay in `umbrella/`.
- **Base:** Chromium `158.0.8127.37`
  (`b8c2be851f62f6a394ec57955d7f31335d7cb6d4`).
- **File:** `umbrella-<tag>.patch` e `manifest.json` con hash e file toccati.

## Applicazione

```bash
git -C chromium/src apply --check ../../patches/umbrella-158.0.8127.37.patch
git -C chromium/src apply ../../patches/umbrella-158.0.8127.37.patch
```

## Rigenerazione

```bash
python scripts/link_overlay.py
python scripts/integrate.py --apply
python scripts/gen_patches.py
python scripts/gen_patches.py --check
```

Se `--check` fallisce, la patch su disco non corrisponde al checkout: non
committare e non distribuire quella patch.

Non modificare i file `.patch` a mano: al prossimo aggiornamento upstream le
modifiche andrebbero perse. Ogni cambiamento va fatto nelle specifiche e
rigenerato.
