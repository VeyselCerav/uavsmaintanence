# 02 — Klasör Yapısı

Monorepo kökü. Frontend ve backend kardeş dizinlerdir.

```
uavsmaintence/
├── docs/
│   └── architecture/
├── frontend/
│   ├── app/
│   │   ├── (public)/
│   │   │   ├── login/
│   │   │   └── forgot-password/
│   │   ├── (app)/
│   │   │   ├── dashboard/
│   │   │   ├── uavs/
│   │   │   ├── components/
│   │   │   ├── flights/
│   │   │   ├── maintenance/
│   │   │   ├── work-orders/
│   │   │   ├── failures/
│   │   │   ├── fmea/
│   │   │   ├── rcm/
│   │   │   ├── parts/
│   │   │   ├── technicians/
│   │   │   ├── reliability/
│   │   │   ├── reports/
│   │   │   ├── documents/
│   │   │   ├── notifications/
│   │   │   └── profile/
│   │   ├── (admin)/
│   │   │   └── admin/
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                 # shadcn
│   │   └── system/             # DataTable, StatusBadge, MetricCard, …
│   ├── features/               # sayfa-özel bileşenler (uav, fmea, rcm, …)
│   ├── hooks/
│   ├── lib/
│   ├── services/               # API client (iş kuralı yok)
│   ├── types/
│   ├── i18n/
│   │   ├── tr.json
│   │   ├── en.json
│   │   ├── az.json
│   │   └── index.ts
│   ├── public/
│   ├── styles/
│   ├── playwright/
│   └── package.json
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── core/
│   │   ├── accounts/
│   │   ├── uavs/
│   │   ├── components/
│   │   ├── flights/
│   │   ├── maintenance/
│   │   ├── failures/
│   │   ├── fmea/
│   │   ├── rcm/
│   │   ├── reliability/
│   │   ├── parts/
│   │   ├── technicians/
│   │   ├── documents/
│   │   ├── reports/
│   │   ├── notifications/
│   │   └── audit/
│   ├── tests/                  # çapraz app senaryoları
│   ├── manage.py
│   └── pyproject.toml
├── nginx/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .github/workflows/
├── .env.example
└── README.md
```

## Django app iç yapısı

Her app aynı iskeleti izler:

```
apps/<name>/
├── __init__.py
├── apps.py
├── models.py
├── enums.py
├── selectors.py          # okuma sorguları
├── services.py           # yazma + iş kuralı
├── serializers.py
├── views.py
├── urls.py
├── permissions.py
├── admin.py              # yalnızca developer fallback
└── tests/
    ├── test_models.py
    ├── test_services.py
    └── test_api.py
```

`views.py` ince kalır. Örnek:

```text
WorkOrderViewSet.perform_create
    → WorkOrderService.create(...)
        → yetki zaten view permission’da
        → kural, atama, audit, bildirim
```

## Frontend katman kuralı

| Klasör | Ne olur | Ne olmaz |
|---|---|---|
| `app/` | Rota, layout, sayfa kompozisyonu | İş kuralı, ham fetch |
| `features/` | Ekran bölümleri (FMEA builder, şablon builder) | API URL dağınıklığı |
| `services/` | HTTP çağrıları, DTO eşleme | RPN/MTBF hesabı |
| `components/system/` | Paylaşılan UI (DataTable, RPNIndicator) | Domain kararı |
| `i18n/` | Çeviri | Hardcoded kullanıcı metni |

## Docker servisleri

```
frontend   → Next.js
backend    → Django / gunicorn
postgres   → PostgreSQL 18
nginx      → reverse proxy
```

Geliştirme: `docker-compose.yml`  
Üretim: `docker-compose.prod.yml`
