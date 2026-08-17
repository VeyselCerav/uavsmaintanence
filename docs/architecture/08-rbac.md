# 08 — RBAC Mimarisi

Yetki iki katmanlıdır: **permission** (ne yapabilir) + **object scope** (hangi kayıt).

## 1. Sistem rolleri

| Rol | Amaç |
|---|---|
| `ADMIN` | Tam erişim, Control Center, ayarlar, kullanıcı |
| `MAINTENANCE_MANAGER` | Bakım planı, WO onay/atama, FMEA/RCM yazma, rapor |
| `TECHNICIAN` | Atandığı WO’yu yürütme, bakım kaydı, arıza girişi |
| `OPERATOR` | Uçuş oluşturma, kendi uçuşlarını görme, filo salt okunur |
| `VIEWER` | Salt okunur (export yok varsayılan) |

Rol `is_system=true` ile silinemez. Yeni özel roller admin’den permission atayarak üretilebilir.

## 2. İzin kataloğu

Biçim: `<module>.<action>`

```text
dashboard.view
admin.access

uav.view | create | update | delete
uav_class.view | create | update | delete
platform.view | create | update | delete
mission.view | create | update | delete

component.view | create | update | delete
flight.view | create | update | delete | complete
maintenance.view | create | update | approve
maintenance_template.view | create | update | delete
maintenance_rule.view | create | update | delete

work_order.view | create | update | assign | start | complete | cancel
failure.view | create | update | delete
fmea.view | create | update | approve
rcm.view | create | update | approve
part.view | create | update | delete
technician.view | create | update
document.view | create | delete
reliability.view
reports.view | export
cost.view
notification.view
user.view | create | update | delete
role.view | update
permission.view
settings.view | update
audit.view
```

## 3. Varsayılan rol × izin

| İzin grubu | ADMIN | MANAGER | TECH | OPERATOR | VIEWER |
|---|---|---|---|---|---|
| dashboard.view | ● | ● | ● | ● | ● |
| admin.access | ● | ● | | | |
| uav.view | ● | ● | ● | ● | ● |
| uav.create/update | ● | ● | | | |
| uav.delete | ● | | | | |
| katalog yazma (class/platform/mission/template/rule) | ● | ○ | | | |
| flight.create / complete | ● | ● | | ● | |
| work_order.view | ● | ● | ▲ | ● | ● |
| work_order.assign / create | ● | ● | | | |
| work_order.start / complete | ● | ● | ▲ | | |
| maintenance.approve | ● | ● | | | |
| failure.create | ● | ● | ● | ○ | |
| fmea/rcm.view | ● | ● | ● | | ● |
| fmea/rcm.create/update | ● | ● | | | |
| fmea/rcm.approve | ● | ● | | | |
| reports.export | ● | ● | | | |
| settings / user / audit | ● | | | | |

● tam ▲ yalnızca atandığı kayıt ○ isteğe bağlı (ayar) boş yok

**ADR-12 (kilitli):** Manager `admin.access` ile Control Center’a girer. `/admin/users`, `/admin/roles`, `/admin/permissions`, `/admin/settings`, `/admin/audit-logs`, `/admin/system` yalnızca `ADMIN` (ve `user.*` / `settings.*` / `audit.view`) görür. Manager şablon, kural, FMEA, RCM ve katalog yazma sayfalarını kullanır.

## 4. Nesne kapsamı

```text
TECHNICIAN
  GET/PATCH work-order  → assigned_technician.user_id == request.user.id
  GET uav               → atandığı açık WO’nun UAV’si (veya filo view izni varsa tümü)
  START/COMPLETE        → yalnızca ASSIGNED veya IN_PROGRESS ve kendisine ait

OPERATOR
  POST flight           → operator_id = request.user.id (başkası adına ancak manager/admin)
  PATCH flight          → kendi kaydı ve counters_applied=false

VIEWER
  tüm yazma 403
  export 403 (reports.export yok)

ADMIN
  object scope yok
```

DRF: `HasPermission` + `HasObjectPermission`. Service katmanı aynı kontrolü tekrar etmez; view zorunludur. Tehlikeli işlemler (interval değişimi, RPN eşiği) service içinde actor’ü audit’e yazar.

## 5. JWT claims (minimal)

```text
sub, role, locale, permissions[]   # permissions listesi uzunsa role + server-side lookup
```

Yetki kaynağı her istekte DB’dir (rol değişince token yenilenene kadar eski claim yanıltmasın). Token’daki `permissions` yalnızca UI gizleme içindir; API kararı DB’dendir.
