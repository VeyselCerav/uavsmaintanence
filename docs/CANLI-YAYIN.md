# Ücretsiz canlı yayın rehberi

Repo: [github.com/VeyselCerav/uavsmaintanence](https://github.com/VeyselCerav/uavsmaintanence)

**Önerilen ücretsiz mimari**

| Katman | Servis | Ücretsiz plan |
|---|---|---|
| Frontend (Next.js) | [Vercel](https://vercel.com) | Hobby |
| Backend (Django) | [Render](https://render.com) | Free (keep-alive ile uyanık tutulur) |
| PostgreSQL | [Neon](https://neon.tech) | Free |

> Doküman dosyaları Render ücretsiz diskte **kalıcı değildir** (yeniden deploy sonrası silinebilir). Tez demosu için metadata + yeni yüklemeler yeterlidir.

---

## 0. Kodu GitHub’a gönderin

PowerShell (proje kökünde):

```powershell
git init
git add .
git commit -m "İHA bakım sistemi — tez demosu"
git branch -M main
git remote add origin https://github.com/VeyselCerav/uavsmaintanence.git
git push -u origin main
```

---

## 1. Neon — PostgreSQL

1. [neon.tech](https://neon.tech) → hesap açın → **New Project**.
2. **Connection string** → **Pooled** → `postgresql://...?sslmode=require` kopyalayın.
3. Bu değer `DATABASE_URL` olacak.

---

## 2. Render — Backend

1. [render.com](https://render.com) → **New** → **Blueprint**.
2. GitHub repo: `VeyselCerav/uavsmaintanence` bağlayın.
3. `render.yaml` otomatik okunur → **Apply**.
4. Servis oluşunca **Environment** → şu değişkenleri girin:

| Değişken | Örnek |
|---|---|
| `DATABASE_URL` | Neon connection string |
| `DJANGO_ALLOWED_HOSTS` | `uavs-backend.onrender.com` (Render size verdiği host) |
| `CORS_ALLOWED_ORIGINS` | `https://SIZIN-VERCEL-ADRESINIZ.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | Aynı Vercel URL |
| `SEED_DEMO` | `true` (yalnızca boş veritabanında çalışır; her uyanışta tekrar etmez) |

5. **Manual Deploy** veya otomatik deploy bekleyin.
6. Sağlık: `https://uavs-backend.onrender.com/health/` → `{"success":true,...}`

API tabanı: `https://uavs-backend.onrender.com/api/v1/`

---

## 3. Vercel — Frontend

1. [vercel.com](https://vercel.com) → **Add New Project** → GitHub repo seçin.
2. **Root Directory:** `frontend`
3. **Environment Variables:**

| Ad | Değer |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://uavs-backend.onrender.com/api/v1` |

4. **Deploy**.
5. Vercel URL’nizi (ör. `https://uavsmaintanence.vercel.app`) Render’daki `CORS_ALLOWED_ORIGINS` ve `CSRF_TRUSTED_ORIGINS` içine ekleyip backend’i **yeniden deploy** edin.

---

## 4. Demo giriş

| Rol | E-posta | Parola |
|---|---|---|
| Yönetici | `admin@local.test` | `admin12345` |
| Teknisyen | `tech@local.test` | `tech12345` |

Canlı ortamda demo parolaları **hemen değiştirmeniz** önerilir (Kontrol merkezi → Kullanıcılar).

---

## 5. Ücretsiz keep-alive (uyku modunu azaltır)

Render Free ~15 dakikada uykuya yatar; ilk istek 30–60 sn sürebilir. Repodaki `.github/workflows/keep-alive.yml` her 5 dakikada `/health/?db=1` adresini yoklar (Render + Neon). Giriş sayfası açılınca da aynı adres önceden çağrılır.

- Workflow `main` dalına gittikten sonra **Actions** sekmesinde **Keep-alive** görünür.
- İlk kez **Run workflow** ile elle çalıştırın; zamanlayıcı GitHub’da birkaç dakika gecikebilir.
- Backend adresi farklıysa repo **Settings → Secrets and variables → Actions → Variables** içine `BACKEND_HEALTH_URL` ekleyin (`https://SIZIN-HOST.onrender.com/health/?db=1`).
- GitHub Actions kapalıysa ücretsiz [cron-job.org](https://cron-job.org) ile aynı URL’ye 5 dakikada bir GET atın.

## 6. Sorun giderme

| Belirti | Çözüm |
|---|---|
| Frontend “network” hatası | `NEXT_PUBLIC_API_URL` doğru mu; Render uyanık mı |
| CORS hatası | Vercel URL `CORS_ALLOWED_ORIGINS` içinde mi |
| 502 / timeout | Keep-alive çalışıyor mu bakın; yine uykudaysa sayfayı yenileyin, 30–60 sn bekleyin |
| Boş veritabanı | `SEED_DEMO=true` ile redeploy (yalnızca boş DB’de seed eder) veya shell: `python manage.py seed_fleet` |

Render shell (PowerShell’den değil, Render pano → Shell):

```bash
python manage.py migrate
python manage.py seed_rbac
python manage.py seed_dev_user
python manage.py seed_fleet
```

---

## Alternatif (tek VPS)

Oracle / Hetzner / başka VPS + `docker compose -f docker-compose.prod.yml up` — ücretsiz değil veya kurulum daha uzun; tez demosu için Vercel+Render+Neon yeterlidir.
