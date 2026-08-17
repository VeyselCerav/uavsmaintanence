# 06 — Frontend Rota Mimarisi (Kullanıcı Uygulaması)

Layout: `(app)` — üst header, sol navigasyon, içerik. Roller menüyü permission’a göre görür; gizli rota yine 403 döner.

## Public

| Rota | Sayfa |
|---|---|
| `/login` | Giriş |
| `/forgot-password` | Parola sıfırlama |

## Uygulama

| Rota | Amaç | Birincil izin |
|---|---|---|
| `/dashboard` | Filo özeti, vade, WO, availability | `dashboard.view` |
| `/uavs` | Filo tablosu | `uav.view` |
| `/uavs/new` | Yeni İHA | `uav.create` |
| `/uavs/[id]` | İHA detay (sekmeler) | `uav.view` |
| `/uavs/[id]/edit` | Düzenle | `uav.update` |
| `/uav-classes` | Sınıf listesi (okuma) | `uav_class.view` |
| `/platforms` | Platform listesi | `platform.view` |
| `/missions` | Görev tipleri | `mission.view` |
| `/components` | Kurulu komponentler | `component.view` |
| `/flights` | Uçuş listesi | `flight.view` |
| `/flights/new` | Uçuş kaydı | `flight.create` |
| `/flights/[id]` | Uçuş detay | `flight.view` |
| `/maintenance` | Bakım kayıtları / vadeler | `maintenance.view` |
| `/maintenance/calendar` | Gün / hafta / ay takvimi | `maintenance.view` |
| `/work-orders` | İş emirleri | `work_order.view` |
| `/work-orders/[id]` | İş emri paneli | `work_order.view` |
| `/failures` | Arızalar | `failure.view` |
| `/failures/[id]` | Arıza detay | `failure.view` |
| `/fmea` | FMEA listesi | `fmea.view` |
| `/fmea/[id]` | FMEA builder (sade teknik akış) | `fmea.view` |
| `/rcm` | RCM listesi | `rcm.view` |
| `/rcm/[id]` | RCM karar ağacı | `rcm.view` |
| `/parts` | Stok | `part.view` |
| `/technicians` | Teknisyenler | `technician.view` |
| `/reliability` | MTBF / MTTR / Availability | `reliability.view` |
| `/reports` | PDF / Excel | `reports.view` |
| `/documents` | Dokümanlar | `document.view` |
| `/notifications` | Bildirimler | authenticated |
| `/profile` | Profil, dil, parola | authenticated |

Katalog sayfaları (`/uav-classes`, `/platforms`, `/missions`) kullanıcıda salt okunurdur. Yazma Admin Control Center’dadır.

## İHA detay sekmeleri

`/uavs/[id]` içinde:

```text
overview | technical | components | flights | maintenance
failures | fmea | rcm | documents | cost | reliability | timeline
```

Timeline olayları: UAV created, component installed/removed, flight, maintenance, failure, inspection.

## Kabuk davranışları

- Global arama: UAV, seri no, komponent, WO, bakım, arıza, parça.
- Dil: `tr | en | az` (profil + `Accept-Language`).
- Mobil: sidebar collapse, responsive tablo, gerektiğinde alt navigasyon.
- Bulk action yalnızca ilgili permission varken görünür.

## İş kuralı yasağı

Frontend RPN, vade yüzdesi veya MTBF hesaplamaz. Gösterir. Form doğrulama (Zod) yalnızca şekil kontrolüdür; asıl kural backend’dedir.
