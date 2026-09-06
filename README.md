# İHA Bakım Yönetim ve Planlama Sistemi

Sınıf, platform ve görev tipine özgü İHA bakım yönetim sistemi. Yüksek lisans tezi. **Yapay zekâ / ML / LLM kullanılmaz.**

- Mimari: [docs/architecture/README.md](docs/architecture/README.md)
- **Kullanım rehberi:** [Yönetici](docs/kullanim-kilavuzu-yonetici.md) · [Teknisyen](docs/kullanim-kilavuzu-teknisyen.md) · [özet](Kullanım%20Rehberi.md)
- **Ücretsiz canlı yayın:** [docs/CANLI-YAYIN.md](docs/CANLI-YAYIN.md) — repo: [github.com/VeyselCerav/uavsmaintanence](https://github.com/VeyselCerav/uavsmaintanence)

## Akademik amaç

Farklı İHA sınıfları, platform tipleri ve operasyon türlerinin bakım gereksinimlerini sınıf ve görev tabanlı bir sisteme aktarmak. Karşılaştırma boyutları: `STANDARD` ve `CLASS_SPECIFIC`.

## Özellikler

| Alan | Durum |
|---|---|
| Filo, uçuş, bakım vadeleri, iş emri yaşam döngüsü | Tamamlandı |
| Arıza, FMEA (RPN), RCM, güvenilirlik (MTBF/MTTR) | Tamamlandı |
| Parça/stok, maliyet, doküman **dosya yükleme/indirme** | Tamamlandı |
| Komponent **tak/sök**, global arama, bildirimler | Tamamlandı |
| STANDARD vs CLASS_SPECIFIC **karşılaştırma** + grafikler | Tamamlandı |
| Raporlar (PDF/Excel), RBAC, çoklu dil (TR/EN/AZ) | Tamamlandı |
| Parola sıfırlama (demo token; SMTP yok) | Tamamlandı |
| Pytest (94) + Playwright E2E (giriş, arama) | Tamamlandı |

Hesaplamalar (vade yüzdesi, RPN, MTBF vb.) **sunucuda** yapılır; frontend yalnızca gösterir.

## Mimari

```
Next.js 16  →  Nginx :8080  →  Django REST Framework  →  Service layer  →  ORM  →  PostgreSQL 18
```

Tek Next.js uygulaması, iki arayüz:

- `(app)` kullanıcı uygulaması
- `(admin)` Kontrol merkezi

Django Admin son kullanıcıya kapalıdır (`/django-admin/` Nginx’te 404).

## Teknoloji

| Katman | Sürüm |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind 4, ECharts |
| Backend | Python 3.13, Django 5.2 LTS, DRF, JWT |
| Veritabanı | PostgreSQL 18 |
| Proxy | Nginx |
| Test | Pytest, Playwright |

## Kurulum (Docker)

PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

İlk kurulumdan sonra, başka bir terminalde:

```powershell
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_rbac
docker compose exec backend python manage.py seed_dev_user
docker compose exec backend python manage.py seed_fleet
```

**Önerilen giriş adresi:** http://localhost:8080

Diğer uçlar:

| Adres | Açıklama |
|---|---|
| http://localhost:8080 | Nginx → uygulama (önerilen) |
| http://localhost:3000 | Frontend (doğrudan) |
| http://localhost:8000/api/v1/ | API |
| http://localhost:8000/api/docs/ | OpenAPI |
| http://localhost:8000/django-admin/ | Geliştirici Django Admin |

**Demo kullanıcılar**

| Rol | E-posta | Parola |
|---|---|---|
| Yönetici | `admin@local.test` | `admin12345` |
| Teknisyen | `tech@local.test` | `tech12345` |

## Ortam değişkenleri

`.env.example` dosyasını kopyalayın. Secret değerleri kaynak koda koymayın.

İsteğe bağlı: `DOCUMENT_MAX_BYTES` (varsayılan 10 MB), `PASSWORD_RESET_HOURS` (varsayılan 2).

## Veritabanı / migration / seed

```powershell
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_rbac
docker compose exec backend python manage.py seed_dev_user
docker compose exec backend python manage.py seed_fleet
```

## Geliştirme (Docker olmadan, PowerShell)

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example ..\.env
$env:DJANGO_SETTINGS_MODULE = "config.settings.development"
python manage.py migrate
python manage.py seed_rbac
python manage.py seed_dev_user
python manage.py seed_fleet
python manage.py runserver
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

PostgreSQL 18’in ayakta olması gerekir. Python sürümü 3.13 olmalıdır (3.14 desteklenmez).

Frontend paketleri Docker’da named volume kullanır; `echarts` veya `@playwright/test` ekledikten sonra:

```powershell
docker compose exec frontend npm install
```

## Test

Backend (Docker; test ayarları ile):

```powershell
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test backend pytest -q
```

Frontend lint:

```powershell
cd frontend
npm run lint
```

E2E (uygulama http://localhost:8080’de ayaktayken):

```powershell
cd frontend
npx playwright install chromium
npm run test:e2e
```

## API

Taban: `/api/v1/`  
Auth: `POST /api/v1/auth/login/`  
Hata gövdesi `error.code` + `error.message_key` döner; çeviri frontend’dedir.

Örnek uçlar: `/documents/` (multipart yükleme), `/documents/{id}/download/`, `/components/`, `/search/?q=`, `/reports/comparison/`.

## Çoklu dil

`frontend/i18n/tr.json`, `en.json`, `az.json`. Varsayılan: TR.

## Roller

| Rol | Özet |
|---|---|
| **ADMIN** | Tam yetki; kullanıcı, ayar, denetim |
| **MAINTENANCE_MANAGER** | Operasyon + kontrol merkezi (kullanıcı/ayar hariç) |
| **TECHNICIAN** | İş emri yürütme, arıza; yönetim yok |
| **OPERATOR** | Uçuş kaydı |
| **VIEWER** | Salt okunur |

Ayrıntılı ekran ve iş akışları: [Kullanım Rehberi.md](Kullanım%20Rehberi.md).

## Bilinçli kapsam dışı

- SMTP / gerçek e-posta (parola sıfırlama demo token ile)
- Yapay zekâ öneri motoru
- Eski demo doküman kayıtlarında binary dosya olmayabilir (metadata-only seed)

Demo bakım periyotları resmi standart değildir.
