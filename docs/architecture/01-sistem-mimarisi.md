# 01 — Sistem Mimarisi

## 1. Sistem tanımı

**İHA Sınıfı, Platform Tipi ve Operasyon Tipine Özgü Bakım Yönetim ve Planlama Sistemi.**

Yüksek lisans tezi kapsamında geliştirilecek profesyonel web uygulaması. Amaç tek tip bakım uygulamak değil; sınıf, platform ve görev farklarını bakım şablonuna, iş emrine, FMEA/RCM analizine ve güvenilirlik metriklerine aktarmaktır.

Araştırma problemi:

> Farklı İHA sınıflarının, platform tiplerinin ve operasyon türlerinin bakım gereksinimleri farklı olduğundan, bu farklılıkların sınıf ve görev tabanlı bir bakım yönetim sistemine aktarılması.

Tez karşılaştırması için sistem iki yaklaşımı yan yana ölçebilir:

- `STANDARD` — sınıf/görev farkı gözetmeyen taban bakım
- `CLASS_SPECIFIC` — sınıf + platform + görev şablonuna bağlı bakım

## 2. Mimari stil

Modüler monolith.

```
Next.js Frontend  →  Django REST Framework  →  Django Service Layer  →  Django ORM  →  PostgreSQL
```

- Microservice yok.
- Frontend ve backend ayrı süreçlerdir.
- İş kuralı React bileşeninde olmaz.
- İş kuralı DRF view’da şişmez; `services.py` katmanındadır.
- View: HTTP, yetki, serileştirme.
- Service: bakım vadesi, uçuş sonrası sayaç, RPN, RCM stratejisi, MTBF/MTTR/Availability.
- ORM: kalıcılık.

## 3. Teknoloji yığını

| Katman | Seçim |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Lucide, TanStack Query/Table, RHF, Zod, Apache ECharts |
| Backend | Python 3.13, Django 5.2 LTS, DRF, Django ORM, JWT |
| Yardımcı doğrulama | Pydantic (API yardımcı katmanı; asıl sözleşme DRF serializer) |
| Veritabanı | PostgreSQL 18 |
| Çalıştırma | Docker, Compose, Nginx |
| Test | Pytest + pytest-django, Playwright |
| Lint | Ruff, MyPy, ESLint, Prettier |

## 4. İki arayüz, tek frontend uygulaması

Spec “iki ayrı Next.js arayüzü” ister. Docker Compose’ta tek `frontend` servisi vardır.

**Kilitlenen karar (ADR-01):** Tek Next.js uygulaması, iki route group:

- `(app)` — teknisyen / operatör / bakım yöneticisi / izleyici
- `(admin)` — Admin Control Center

Gerekçe: ortak tasarım sistemi, i18n, auth client ve API katmanı tekrar etmez; Nginx tek origin üzerinden `/` ve `/admin` ayırır. Django Admin yalnızca geliştirici/acil durum fallback’idir ve dışarı açılmaz.

## 5. Domain sınırları (Django app)

| App | Sorumluluk |
|---|---|
| `accounts` | Kullanıcı, rol, izin, JWT, profil |
| `uavs` | Filo, sınıf, platform, görev tipi |
| `components` | Komponent türü, kurulu komponent, hiyerarşi |
| `flights` | Uçuş kaydı, sayaç güncelleme tetikleyicisi |
| `maintenance` | Şablon, kural, kayıt, iş emri, takvim, vade motoru |
| `failures` | Arıza olayı |
| `fmea` | FMEA analizi ve RPN |
| `rcm` | RCM analizi ve strateji |
| `reliability` | MTBF, MTTR, Availability (hesaplanan; kaynak veri diğer app’lerde) |
| `parts` | Stok, uyumluluk |
| `technicians` | Teknisyen profili, yetkinlik, sertifika |
| `documents` | Dosya bağlama |
| `reports` | PDF / Excel |
| `notifications` | Kural tabanlı bildirim |
| `audit` | Değişiklik günlüğü |
| `core` | SystemSetting, paylaşılan enum, exception, pagination |

`reliability` kendi olay tablosunu tutmaz; uçuş, arıza ve iş emri verisinden hesaplar. İsteğe bağlı `ReliabilitySnapshot` rapor hızı için tutulabilir; kaynak gerçeklik snapshot değildir.

## 6. Çalışma zamanı akışı

```
Uçuş tamamlanır
    → FlightCompletionService
        → UAV.total_flight_hours / count / cycles
        → Kurulu komponent operating_hours / cycle_count
        → MaintenanceDueService
            → status: NORMAL | APPROACHING | DUE | OVERDUE | CRITICAL
            → bildirim (eşik aşımı)
            → (kural açıksa) Work Order taslağı

Bakım tamamlanır
    → WorkOrderCompletionService
        → MaintenanceRecord
        → komponent last/next maintenance
        → maliyet satırı
        → güvenilirlik girdileri (onarım süresi)
        → audit log
```

## 7. Bakım karar motoru (AI yok)

Karar üreten tek kaynak kuraldır:

1. UAV’nin sınıfı, platformu, görev tipi  
2. Eşleşen `MaintenanceTemplate`  
3. Komponent türüne bağlı şablon kalemleri  
4. Interval birimi (saat / çevrim / takvim)  
5. `MaintenanceRule` eşikleri  
6. FMEA RPN bandı (öncelik etkisi)  
7. RCM stratejisi (görev tipi: inspection, restoration, discard, …)

Motor girdi–çıktısı denetlenebilir olmalıdır. Aynı girdide aynı çıktı üretilir (deterministik).

## 8. Güvenlik ilkeleri

- JWT access + refresh.
- RBAC: rol + granüler permission.
- Object-level: teknisyen yalnızca atandığı iş emrini günceller.
- Secret kaynak kodda yok.
- Dosya tipi/boyut doğrulama.
- Rate limit, güvenli header, CORS allowlist.
- Tüm kritik yazmalar audit’e düşer.

## 9. Tasarım ilkeleri (frontend)

Havacılık bakım kontrol merkezi. Neon, gradient, glassmorphism, AI ikonu yok.

Renkler: `#F5F6F7` zemin, `#263746` primary, fonksiyonel success/warning/danger/info.

Desktop-first, tablet ve mobil ayrı düzen (küçültülmüş masaüstü değil).

## 10. Açık bırakılan, burada kilitlenen kararlar

| ID | Karar |
|---|---|
| ADR-01 | Tek Next.js, `(app)` + `(admin)` route group |
| ADR-02 | Birincil anahtar: UUID |
| ADR-03 | Kritik varlıklar soft-delete (`is_deleted`, `deleted_at`) |
| ADR-04 | Şablon eşleşmesi tam üçlü: class + platform + mission. Eşleşme yoksa otomatik bağlama yok |
| ADR-05 | `Technician` bir `User` profilidir (1:1); User olmadan teknisyen kaydı yok |
| ADR-06 | Güvenilirlik anlık hesaplanır; snapshot yalnızca rapor önbelleğidir |
| ADR-07 | Backend kullanıcıya ham hata metni değil `error.code` döner; çeviri frontend’dedir |
| ADR-08 | Demo seed kayıtları `is_demo=true` ve UI’da “DEMO” rozeti taşır |
| ADR-09 | Standart vs sınıf-özel karşılaştırma `MaintenanceApproach` alanı ile tutulur |
| ADR-10 | Django Admin yalnızca `DEBUG` veya iç ağ; Nginx’de dışarı kapatılır |
| ADR-11 | Katalog `name` TR saklanır; sistem etiketleri i18n JSON’dadır |
| ADR-12 | `MAINTENANCE_MANAGER` Control Center’a girer (`admin.access`); Users / Settings / Audit menüleri yalnızca `ADMIN` |
