# 05 — API Mimarisi

Taban: `/api/v1/`  
Kimlik: `Authorization: Bearer <access_jwt>`  
Dokümantasyon: OpenAPI / Swagger / ReDoc (`/api/schema/`, `/api/docs/`, `/api/redoc/`)

## 1. Sözleşme

Başarı (liste):

```json
{
  "success": true,
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 0
  }
}
```

Başarı (tekil):

```json
{
  "success": true,
  "data": {}
}
```

Hata:

```json
{
  "success": false,
  "error": {
    "code": "MAINTENANCE_TEMPLATE_NOT_FOUND",
    "message_key": "errors.maintenance.template_not_found",
    "details": {}
  }
}
```

- `message_key` frontend çevirisine gider. Backend kullanıcı dilinde cümle üretmez (ADR-07).
- `details` alan hataları: `{ "field": "registration_number", "code": "unique" }`.
- HTTP: 400 doğrulama, 401 kimlik, 403 yetki, 404 yok, 409 çakışma, 429 limit, 500 beklenmeyen.

## 2. Liste parametreleri

```text
page, page_size
search
ordering
filter[<field>]=
locale   (isteğe bağlı; varsayılan kullanıcı locale)
```

Export: `Accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` veya `?export=xlsx`.

## 3. Kaynak haritası

### Auth

| Method | Path | İzin |
|---|---|---|
| POST | `/auth/login/` | public |
| POST | `/auth/refresh/` | public |
| POST | `/auth/logout/` | authenticated |
| POST | `/auth/forgot-password/` | public |
| GET | `/auth/me/` | authenticated |
| PATCH | `/auth/me/` | authenticated |

### Katalog (okuma app, yazma admin)

`/uav-classes/`, `/platforms/`, `/missions/`, `/component-types/`, `/skills/`  
Admin yazma: aynı kaynaklar + `IsAdminOrMaintenanceManager` create/update/delete.

### Filo ve operasyon

```text
/uavs/
/uavs/{id}/
/uavs/{id}/components/
/uavs/{id}/flights/
/uavs/{id}/maintenance/
/uavs/{id}/failures/
/uavs/{id}/timeline/
/uavs/{id}/reliability/
/uavs/{id}/costs/
/uavs/{id}/documents/

/flights/
/flights/{id}/complete/          # sayaç + vade motoru

/components/
/components/{id}/install/
/components/{id}/remove/
```

### Bakım

```text
/maintenance-templates/
/maintenance-templates/{id}/
/maintenance-templates/{id}/items/
/maintenance-templates/resolve/?uav_class=&platform=&mission=&approach=

/maintenance-rules/
/maintenance-dues/
/maintenance-dues/recalculate/   # UAV veya filo

/work-orders/
/work-orders/{id}/
/work-orders/{id}/assign/
/work-orders/{id}/start/
/work-orders/{id}/complete/
/work-orders/{id}/cancel/

/maintenance-records/
```

### FMEA / RCM / arıza / güvenilirlik

```text
/failures/
/failure-modes/

/fmea/
/fmea/{id}/
/fmea/{id}/items/
/fmea/{id}/approve/

/rcm/
/rcm/{id}/
/rcm/{id}/items/
/rcm/{id}/evaluate/             # kural tabanlı strateji önerisi
/rcm/{id}/approve/

/reliability/?scope=fleet|class|uav|component&scope_id=&from=&to=
```

### Parça, teknisyen, rapor, sistem

```text
/parts/
/parts/{id}/compatibility/

/technicians/
/technicians/{id}/skills/
/technicians/{id}/workload/

/documents/
/reports/pdf/{type}/
/reports/xlsx/{type}/

/notifications/
/notifications/{id}/read/
/notifications/read-all/

/search/?q=                     # UAV, serial, component, WO, maintenance, failure, part

/admin/users/
/admin/roles/
/admin/permissions/
/admin/settings/
/admin/audit-logs/
```

PDF tipleri: `uav-history`, `maintenance`, `work-order`, `failure`, `fmea`, `rcm`, `fleet`, `reliability`, `cost`  
Excel: `uavs`, `components`, `flights`, `maintenance`, `failures`, `fmea`, `rcm`, `costs`

## 4. View vs service

```text
POST /flights/{id}/complete/
  FlightViewSet.complete
    → FlightCompletionService.complete(flight, actor)
        → UAV sayaçları
        → komponent sayaçları
        → MaintenanceDueService.recalculate(uav)
        → NotificationService.emit_due_changes
        → AuditService.log
```

RPN ve RCM stratejisi her zaman service’de hesaplanır. Client `rpn` gönderirse yok sayılır.

## 5. Idempotency

- `flights/{id}/complete/` ikinci çağrıda 409 `FLIGHT_COUNTERS_ALREADY_APPLIED`
- `work-orders/{id}/complete/` ikinci çağrıda 409 `WORK_ORDER_ALREADY_COMPLETED`

## 6. Versiyonlama

Kırıcı değişiklik yeni prefix: `/api/v2/`. v1 tez süresi boyunca kararlı kalır.
