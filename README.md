# romanize-ar

Arabic → English transliteration microservice (ALA-LC / IJMES / EI3).

Pipeline:
1. **camel-tools MLEDisambiguator** — morphological disambiguation + diacritization
2. **CAMeL ar2phon rule engine** — greedy longest-match char-translit → ALA-LC output
3. **Scheme post-process** — LOC→IJMES/EI3 (final `á`→`ā`, drop word-initial hamza)

Rule tables (`data/*.tsv`) sourced from [CAMeL-Lab/Arabic-ALA-LC-Romanization](https://github.com/CAMeL-Lab/Arabic-ALA-LC-Romanization) under Apache-2.0 (see `LICENSE.camel`).

## Endpoints

- `GET  /api/romanize?text=...&scheme=ijmes|ala-lc&use_disambig=true`
- `POST /api/romanize`  `{text, scheme, use_disambig}`
- `POST /api/romanize/batch`  `{items: [...], scheme, use_disambig}`
- `GET  /health`
- `GET  /docs` (OpenAPI)

## Consumers

- **DAVET** (davet-monorepo): `/tr/en-ar-transliterasyon` — interaktif sayfa
- **ODİD** (otoritedizini.org): `/tr/rehber` — AR-EN bölümü + Work/Author öneri cron'u

## Local dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
camel_data -i disambig-mle-calima-msa-r13   # ~500MB, one-time
uvicorn app.main:app --reload --port 8100
pytest -v
```

## Prod deploy

```bash
docker compose up -d --build
# → https://romanize.abddemir.com.tr (Traefik + Let's Encrypt)
```

## Scheme reference

| Feature | ALA-LC | IJMES / EI3 |
|---|---|---|
| Final alif maqṣūra (ى) | `á` | `ā` |
| Word-initial hamza | `ʾamīr` | `amīr` |
| ʿayn | `ʿ` (U+02BF) | `ʿ` |
| Hamza | `ʾ` (U+02BE) | `ʾ` |
| Sun letter assim. | no | no |
| `al-` | always | always |
