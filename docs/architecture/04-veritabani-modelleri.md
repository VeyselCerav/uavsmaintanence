# 04 — Veritabanı Modelleri

Alan adları İngilizce (kod), kullanıcı etiketleri i18n’dedir. Enum’lar PostgreSQL `TextChoices` olarak tutulur; kod içine iş kuralı gömülmez.

## Ortak soyut model

```text
BaseModel
  id                    UUID PK
  created_at            timestamptz
  updated_at            timestamptz
  created_by_id         UUID FK User NULL
  updated_by_id         UUID FK User NULL

SoftDeleteModel(BaseModel)
  is_deleted            bool default false
  deleted_at            timestamptz NULL
```

## Enum’lar

| Enum | Değerler |
|---|---|
| `UAVStatus` | READY, MAINTENANCE, GROUNDED, RETIRED |
| `MaintenanceApproach` | STANDARD, CLASS_SPECIFIC |
| `ComponentStatus` | INSTALLED, REMOVED, QUARANTINE, SCRAPPED |
| `FlightResult` | COMPLETED, ABORTED, TRAINING |
| `IntervalUnit` | FLIGHT_HOURS, FLIGHT_CYCLES, CALENDAR_DAYS, CALENDAR_MONTHS, CALENDAR_YEARS, COMPONENT_CYCLES |
| `DueStatus` | NORMAL, APPROACHING, DUE, OVERDUE, CRITICAL |
| `Priority` | LOW, MEDIUM, HIGH, CRITICAL |
| `MaintenanceType` | PREVENTIVE, CORRECTIVE, SCHEDULED, UNSCHEDULED, INSPECTION, FUNCTIONAL_CHECK |
| `WorkOrderStatus` | OPEN, ASSIGNED, IN_PROGRESS, WAITING_PARTS, COMPLETED, CANCELLED |
| `InspectionType` | VISUAL, FUNCTIONAL, MEASUREMENT, OVERHAUL, REPLACEMENT, LUBRICATION, SOFTWARE |
| `RCMStrategy` | SCHEDULED_INSPECTION, SCHEDULED_RESTORATION, SCHEDULED_DISCARD, CONDITION_INSPECTION, FUNCTIONAL_CHECK, CORRECTIVE |
| `AnalysisStatus` | DRAFT, IN_REVIEW, APPROVED, ARCHIVED |
| `PartStatus` | ACTIVE, INACTIVE, OBSOLETE |
| `TechnicianStatus` | ACTIVE, INACTIVE |
| `DocumentType` | MANUAL, PROCEDURE, CERTIFICATE, PHOTO, REPORT, OTHER |
| `NotificationType` | MAINTENANCE_APPROACHING, MAINTENANCE_DUE, MAINTENANCE_OVERDUE, CRITICAL_COMPONENT, LOW_STOCK, WORK_ORDER_ASSIGNED, WORK_ORDER_COMPLETED |
| `AuditAction` | CREATE, UPDATE, DELETE, LOGIN, LOGOUT, PERMISSION_CHANGE, MAINTENANCE_COMPLETION, WORK_ORDER_STATUS_CHANGE, FMEA_CHANGE, RCM_CHANGE, UAV_STATUS_CHANGE |

## accounts

**User**  
`email` UK, `password_hash`, `full_name`, `locale` (`tr|en|az`), `timezone`, `is_active`, `last_login_at`, `role_id`

**Role**  
`code` UK, `name`, `description`, `is_system`

**Permission**  
`code` UK (`uav.view`), `module`, `action`, `description`

**RolePermission**  
`(role_id, permission_id)` UK

## technicians

**Technician**  
`user_id` UK, `employee_number` UK, `status`, `notes`

**Skill**  
`code` UK, `name`

**TechnicianSkill**  
`(technician_id, skill_id)` UK, `certified_at`, `expires_at`

**TechnicianCertification**  
`technician_id`, `name`, `issuer`, `issued_at`, `expires_at`, `document_id` NULL

## uavs

**UAVClass**  
`code` UK, `name`, `description`, `mtow_min_kg`, `mtow_max_kg`, `sort_order`, `is_demo`, `is_active`  
Örnek kod: `VERY_LIGHT`, `LIGHT`, `MEDIUM`, `HEAVY` — kod sabit değildir, DB’den yönetilir.

**PlatformType**  
`code` UK, `name`, `description`, `is_active`  
Örnek: `MULTICOPTER`, `FIXED_WING`, `VTOL`, `HYBRID`, `ROTARY_WING`

**MissionType**  
`code` UK, `name`, `description`, `is_active`  
Örnek: `MAPPING`, `SURVEILLANCE`, `AGRICULTURE`, `SAR`, `INSPECTION`, `TRANSPORTATION`, `TRAINING`, `OTHER`

**UAV**  
`registration_number` UK, `serial_number` UK, `manufacturer`, `model`, `uav_class_id`, `platform_type_id`, `mission_type_id`, `maintenance_template_id` NULL, `maintenance_approach`, `mtow_kg`, `production_date`, `inventory_entry_date`, `total_flight_hours` numeric(12,2) default 0, `total_flight_count` int default 0, `total_flight_cycles` int default 0, `status`, `notes`, `is_demo`

İndeks: `(status)`, `(uav_class_id, platform_type_id, mission_type_id)`, `(maintenance_template_id)`

## components

**ComponentType**  
`code` UK, `name`, `description`, `tracks_hours` bool, `tracks_cycles` bool, `is_active`

**UAVComponent**  
`uav_id`, `component_type_id`, `parent_id` NULL, `name`, `serial_number`, `part_number`, `manufacturer`, `model`, `installed_at`, `removed_at` NULL, `operating_hours` numeric(12,2) default 0, `cycle_count` int default 0, `status`, `last_maintenance_at` NULL, `next_maintenance_at` NULL, `notes`

Kısmi UK: `(serial_number) WHERE removed_at IS NULL AND serial_number IS NOT NULL`  
İndeks: `(uav_id, status)`, `(component_type_id)`

## flights

**Flight**  
`flight_number` UK, `uav_id`, `operator_id` (User), `mission_type_id`, `flown_on` date, `start_at`, `end_at`, `duration_hours` (end-start’tan hesap, override yoksa), `distance_km` NULL, `max_altitude_m` NULL, `max_speed_kmh` NULL, `weather` NULL, `result`, `notes`, `counters_applied` bool default false

İndeks: `(uav_id, start_at DESC)`

## maintenance

**MaintenanceTemplate**  
`code` UK, `name`, `description`, `uav_class_id`, `platform_type_id`, `mission_type_id`, `approach`, `is_active`, `is_demo`, `notes`

Kısmi UK: aktif + silinmemiş üçlü + yaklaşım.

**MaintenanceTemplateItem**  
`template_id`, `component_type_id`, `sequence`, `task_code`, `task_name`, `interval_value` numeric(12,2), `interval_unit`, `priority`, `required_skill_id` NULL, `estimated_duration_minutes`, `inspection_type`, `rcm_strategy`, `notes`

UK: `(template_id, component_type_id, task_code)`

**MaintenanceRule**  
`code` UK, `name`, `due_status`, `threshold_percent` NULL, `threshold_hours` NULL, `threshold_days` NULL, `is_active`  
Varsayılan örnek (seed, `is_demo` veya ayardan): APPROACHING %80, DUE %100, OVERDUE %110, CRITICAL %130 — değerler DB’dedir.

**MaintenanceDue**  
`uav_id`, `component_id`, `template_item_id`, `status`, `remaining_value`, `remaining_unit`, `usage_percent`, `due_at` NULL, `calculated_at`, `priority`

UK: `(component_id, template_item_id)` — her kalem için güncel tek satır. Geçmiş hesaplar `MaintenanceDueHistory` ile tutulabilir (tez izi için önerilir).

**WorkOrder**  
`number` UK (ör. `WO-2026-000123`), `uav_id`, `component_id` NULL, `template_item_id` NULL, `maintenance_type`, `priority`, `status`, `planned_at` NULL, `started_at` NULL, `completed_at` NULL, `assigned_technician_id` NULL, `estimated_duration_minutes` NULL, `actual_duration_minutes` NULL, `findings`, `notes`

**WorkOrderPart**  
`work_order_id`, `part_id`, `quantity`, `unit_cost_snapshot`

**MaintenanceRecord**  
`work_order_id` UK, `uav_id`, `component_id` NULL, `maintenance_type`, `performed_at`, `technician_id`, `description`, `findings`, `action_taken`, `labor_hours`, `result`, `next_maintenance_at` NULL, `approach` (STANDARD | CLASS_SPECIFIC — karşılaştırma boyutu)

## failures

**FailureMode**  
`code` UK, `name`, `description` (katalog; FMEA ile paylaşılır)

**Failure**  
`uav_id`, `component_id` NULL, `failure_mode_id` NULL, `occurred_at`, `discovered_during` (FLIGHT | INSPECTION | MAINTENANCE | OTHER), `severity`, `description`, `downtime_hours` numeric(12,2) default 0, `resolved_at` NULL, `work_order_id` NULL

## fmea / rcm

Alanlar [10-fmea-domain.md](./10-fmea-domain.md) ve [11-rcm-domain.md](./11-rcm-domain.md) dosyalarındadır.

## parts

**Part**  
`part_number` UK, `name`, `manufacturer`, `model`, `stock_qty` numeric(12,2), `min_stock_qty`, `unit_cost`, `currency` (`TRY|USD|EUR|AZN`), `supplier`, `location`, `status`

**PartCompatibility**  
`part_id`, `uav_class_id` NULL, `platform_type_id` NULL, `component_type_id`  
NULL sınıf/platform = “tümüne uyumlu”.

## documents / costs / notifications / audit / core

**Document**  
`title`, `file_name`, `content_type`, `size_bytes`, `storage_key`, `document_type`, `uav_id` NULL, `component_id` NULL, `template_id` NULL, `work_order_id` NULL, `uploaded_by_id`

**CostRecord**  
`work_order_id` NULL, `uav_id`, `component_id` NULL, `maintenance_type` NULL, `part_cost`, `labor_cost`, `other_cost`, `total_cost` (generated veya service hesaplar), `currency`, `occurred_at`

**Notification**  
`user_id`, `type`, `title_key`, `body_key`, `payload` jsonb, `is_read`, `read_at` NULL

**AuditLog**  
`user_id` NULL, `timestamp`, `ip`, `action`, `entity_type`, `entity_id`, `old_value` jsonb, `new_value` jsonb, `message` (insan okur iz; örn. interval 50→40)

**SystemSetting**  
`key` UK, `value` jsonb, `description`  
Örnek anahtarlar:

```text
rpn.thresholds          { "low": [1,49], "medium": [50,99], "high": [100,199], "critical": [200,1000] }
maintenance.due_rules   { "approaching_percent": 80, "due_percent": 100, "overdue_percent": 110, "critical_percent": 130 }
notification.thresholds
work_order.auto_create_on_due   false
reliability.zero_failure_policy  "undefined"
```

**ReliabilitySnapshot** (isteğe bağlı önbellek)  
`scope` (FLEET | CLASS | UAV | COMPONENT), `scope_id` NULL, `period_start`, `period_end`, `mtbf_hours`, `mttr_hours`, `availability`, `failure_count`, `calculated_at`

## Güvenilirlik formülleri (kaynak)

```text
MTBF        = total_operating_time / number_of_failures
MTTR        = total_repair_time / number_of_repairs
Availability = MTBF / (MTBF + MTTR)
```

`number_of_failures = 0` ise MTBF tanımsızdır (`NULL`). Ayar `reliability.zero_failure_policy`: `undefined` (varsayılan, akademik olarak dürüst) | `operating_time_as_lower_bound` (rapor notu ile). Availability, MTBF NULL ise NULL’dır.

Kapsamlar: İHA, komponent, filo, sınıf. Hepsi aynı formül, farklı filtre.
