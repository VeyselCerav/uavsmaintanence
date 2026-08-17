# 07 — Admin Rota Mimarisi (Control Center)

Layout: `(admin)/admin` — “Aviation Maintenance Control Center”. Django Admin klonu değildir.

Erişim: `ADMIN` veya `admin.access` izni (`MAINTENANCE_MANAGER` dahil). Users / Roles / Permissions / Settings / Audit / System sayfaları yalnızca `ADMIN`. Django Admin (`/django-admin/`) Nginx’de dışarı kapalıdır.

## Rotalar

| Rota | Amaç |
|---|---|
| `/admin` | Admin dashboard |
| `/admin/uavs` | Filo yönetimi (tam yazma) |
| `/admin/classes` | İHA sınıfları |
| `/admin/platforms` | Platform tipleri |
| `/admin/missions` | Görev tipleri |
| `/admin/components` | Komponent türleri |
| `/admin/maintenance-templates` | Şablon listesi |
| `/admin/maintenance-templates/new` | Template Builder |
| `/admin/maintenance-templates/[id]` | Template Builder (düzenle) |
| `/admin/maintenance-rules` | Vade / eşik kuralları |
| `/admin/fmea` | FMEA katalog / analiz |
| `/admin/fmea/[id]` | FMEA builder |
| `/admin/rcm` | RCM katalog / analiz |
| `/admin/rcm/[id]` | RCM karar ağacı |
| `/admin/users` | Kullanıcılar |
| `/admin/roles` | Roller |
| `/admin/permissions` | İzinler (sistem izinleri salt okunur) |
| `/admin/settings` | SystemSetting, RPN bantları, vade eşikleri |
| `/admin/audit-logs` | Denetim kaydı |
| `/admin/system` | Sistem sağlığı, seed/demo bayrakları |

## Admin dashboard panelleri

- Filo özeti (READY / MAINTENANCE / GROUNDED / RETIRED)
- İş emri durum dağılımı
- Gecikmiş görevler
- Kritik FMEA (RPN bandı)
- RCM analiz durumu (DRAFT / APPROVED)
- Minimum stok altı parçalar
- Teknisyen iş yükü
- Aylık bakım maliyeti
- Filo availability, MTBF, MTTR

## Template Builder

Sıra:

1. UAV Class + Platform + Mission + Approach seç  
2. Komponent türü + görev + interval + öncelik + skill + süre + inspection + RCM strategy ekle  
3. Kaydet → ilgili yeni İHA’larda `resolve` ile kullanılabilir  

Ekran teknik konfigürasyon aracıdır; sihirbaz/AI görünümü yoktur.

## Ayar ekranı (hard-code yasağı)

Buradan değişir: bakım interval varsayılanı değil (interval şablon kalemindedir), vade eşikleri, RPN bantları, bildirim eşikleri, `work_order.auto_create_on_due`, para birimi varsayılanı, sıfır arıza MTBF politikası.

Sınıf, platform, görev tipi, komponent türü ayrı admin sayfalarındadır.
