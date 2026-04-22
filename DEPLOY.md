# Deploy — romanize-ar

Prod target: `romanize.abddemir.com.tr` via Cloudflare Tunnel → Dokploy Traefik.

## 1. Sunucuda servis

```bash
ssh sunucu
cd /opt
git clone git@github.com:drademir/romanize-ar.git
cd romanize-ar
docker compose build    # ~10 dk (ilk sefer camel-tools model indirir ~500MB)
docker compose up -d
docker logs -f romanize-ar    # "Uvicorn running on 0.0.0.0:8100"
```

Healthcheck:

```bash
docker exec romanize-ar python -c "import urllib.request as u; print(u.urlopen('http://localhost:8100/health').read())"
# {"status":"ok","disambiguator_loaded":true}
```

## 2. Shared docker network (DAVET + ODİD erişimi)

Her iki projenin docker-compose'u `romanize-ar` network'üne eklenir, **veya** (tercih edilen) Traefik üzerinden HTTPS routing kullanılır:

### Seçenek A — Traefik HTTPS (tavsiye)

`docker-compose.yml`'deki Traefik labels zaten doğru. Yalnızca Cloudflare DNS ekle:

```bash
# Cloudflare: Add CNAME romanize → <tunnel-id>.cfargotunnel.com (proxied)
# veya Tunnel config'e ingress rule:
ssh sunucu "cat /etc/cloudflared/config.yml"
# romanize.abddemir.com.tr → http://localhost:8100 satırı ekle, sonra:
ssh sunucu "systemctl restart cloudflared"
```

Sonra her iki projede:
- **DAVET v2** (`davet-monorepo/apps/web/.env`): `ROMANIZE_AR_URL=https://romanize.abddemir.com.tr`
- **ODİD** (`otoritediziniorg/.env`): `ROMANIZE_AR_URL=https://romanize.abddemir.com.tr`

### Seçenek B — Internal docker network

```yaml
# romanize-ar/docker-compose.yml networks bloğunu external: true yerine:
networks:
  shared:
    name: romanize-shared
    driver: bridge
```

Her iki projenin compose'una:

```yaml
services:
  web:
    networks:
      - default
      - romanize-shared
networks:
  romanize-shared:
    external: true
```

Env: `ROMANIZE_AR_URL=http://romanize-ar:8100`

## 3. ODİD DB migration

Schema'ya `translit_suggestions` tablosu eklendi. Bir sonraki db-migrate çalıştırıldığında otomatik oluşur (IF NOT EXISTS):

```bash
ssh sunucu "cd /opt/otoritediziniorg && docker compose exec app node scripts/db-migrate.mjs"
```

## 4. Haftalık öneri cron'u

```bash
# Sunucuda root crontab:
# 0 3 * * 0  cd /opt/otoritediziniorg && docker compose exec -T app node scripts/suggest-translits.mjs >> /var/log/translit-suggest.log 2>&1
```

İlk run (dry) manuel:

```bash
ssh sunucu "cd /opt/otoritediziniorg && docker compose exec app node scripts/suggest-translits.mjs --dry-run --limit 10"
```

## 5. Smoke test — canlı

```bash
curl 'https://romanize.abddemir.com.tr/api/romanize?text=%D9%83%D8%AA%D8%A7%D8%A8&scheme=ijmes'
# {"input":"كتاب","output":"Kitāb","scheme":"ijmes","disambiguated":true,...}
```

DAVET:
```
https://davet.org.tr/tr/en-ar-transliterasyon
```

ODİD:
```
https://otoritedizini.org/tr/rehber   (AR-EN bölümü üstte)
https://otoritedizini.org/tr/admin/translit-onerileri   (admin-only)
```
