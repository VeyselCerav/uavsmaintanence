# 03 — ER Modeli

Tüm iş varlıkları UUID PK kullanır. `created_at`, `updated_at`, `created_by`, `updated_by` ortak iz alanlarıdır. Kritik tablolarda `is_deleted` / `deleted_at` vardır.

## 1. Çekirdek ilişki (özet)

```text
UAVClass ──┐
PlatformType ──┼── MaintenanceTemplate ── MaintenanceTemplateItem ── ComponentType
MissionType ──┘                                      │
                                                     │
User ── Technician                                   │
  │                                                  ▼
  └── Role ── RolePermission ── Permission     UAV ── UAVComponent
                                                     │
Flight ──────────────────────────────────────────────┤
Failure ─────────────────────────────────────────────┤
MaintenanceRecord / WorkOrder ───────────────────────┤
Document / CostRecord ───────────────────────────────┘

FMEA ── FMEAItem     (kapsam: class + platform + component_type [+ mission])
RCMAnalysis ── RCMItem
```

## 2. Kimlik ve yetki

```mermaid
erDiagram
    User ||--o| Technician : "1:1 profil"
    User }o--|| Role : has
    Role ||--o{ RolePermission : grants
    Permission ||--o{ RolePermission : in
    User ||--o{ AuditLog : produces
    User ||--o{ Notification : receives

    User {
        uuid id PK
        string email UK
        string full_name
        string locale
        string timezone
        bool is_active
    }

    Role {
        uuid id PK
        string code UK
        string name
        bool is_system
    }

    Permission {
        uuid id PK
        string code UK
        string module
        string action
    }

    Technician {
        uuid id PK
        uuid user_id UK
        string employee_number UK
        string status
    }
```

Sistem rolleri silinmez: `ADMIN`, `MAINTENANCE_MANAGER`, `TECHNICIAN`, `OPERATOR`, `VIEWER`.

## 3. Taksonomi ve filo

```mermaid
erDiagram
    UAVClass ||--o{ UAV : classifies
    PlatformType ||--o{ UAV : types
    MissionType ||--o{ UAV : primary-mission
    UAVClass ||--o{ MaintenanceTemplate : scoped
    PlatformType ||--o{ MaintenanceTemplate : scoped
    MissionType ||--o{ MaintenanceTemplate : scoped
    MaintenanceTemplate ||--o{ UAV : bound
    UAV ||--o{ UAVComponent : has
    ComponentType ||--o{ UAVComponent : of-type
    UAVComponent ||--o{ UAVComponent : parent

    UAVClass {
        uuid id PK
        string code UK
        string name
        numeric mtow_min_kg
        numeric mtow_max_kg
        bool is_demo
    }

    PlatformType {
        uuid id PK
        string code UK
        string name
    }

    MissionType {
        uuid id PK
        string code UK
        string name
    }

    UAV {
        uuid id PK
        string registration_number UK
        string serial_number UK
        string status
        string maintenance_approach
        numeric total_flight_hours
        int total_flight_count
        int total_flight_cycles
        uuid class_id FK
        uuid platform_id FK
        uuid mission_type_id FK
        uuid maintenance_template_id FK
    }

    UAVComponent {
        uuid id PK
        string serial_number
        string status
        numeric operating_hours
        int cycle_count
        timestamptz installed_at
        timestamptz removed_at
    }
```

`UAV.status`: `READY | MAINTENANCE | GROUNDED | RETIRED`  
`UAV.maintenance_approach`: `STANDARD | CLASS_SPECIFIC`

Kurulu komponent ağacı UAV köküne bağlıdır. Aynı anda `removed_at IS NULL` olan seri numarası tekildir.

## 4. Bakım şablonu, kural, uçuş, iş emri

```mermaid
erDiagram
    MaintenanceTemplate ||--o{ MaintenanceTemplateItem : contains
    ComponentType ||--o{ MaintenanceTemplateItem : targets
    MaintenanceTemplate ||--o{ MaintenanceRule : optional-scope
    UAV ||--o{ Flight : flies
    UAV ||--o{ MaintenanceDue : current
    UAVComponent ||--o{ MaintenanceDue : tracked
    MaintenanceTemplateItem ||--o{ MaintenanceDue : from-item
    UAV ||--o{ WorkOrder : assigned-to-uav
    UAVComponent ||--o{ WorkOrder : optional-target
    WorkOrder ||--o| MaintenanceRecord : produces
    Technician ||--o{ WorkOrder : assigned
    WorkOrder ||--o{ WorkOrderPart : uses
    Part ||--o{ WorkOrderPart : consumed

    MaintenanceTemplate {
        uuid id PK
        string code UK
        uuid uav_class_id FK
        uuid platform_type_id FK
        uuid mission_type_id FK
        string approach
        bool is_active
        bool is_demo
    }

    MaintenanceTemplateItem {
        uuid id PK
        int sequence
        numeric interval_value
        string interval_unit
        string priority
        string inspection_type
        string rcm_strategy
        int estimated_duration_minutes
    }

    Flight {
        uuid id PK
        numeric duration_hours
        string result
        bool counters_applied
    }

    MaintenanceDue {
        uuid id PK
        string status
        numeric remaining_value
        string remaining_unit
        timestamptz due_at
    }

    WorkOrder {
        uuid id PK
        string number UK
        string status
        string priority
        string maintenance_type
    }
```

`MaintenanceTemplate` için benzersiz aktif üçlü:

```text
UNIQUE (uav_class_id, platform_type_id, mission_type_id, approach) WHERE is_deleted = false AND is_active = true
```

## 5. Arıza, FMEA, RCM, güvenilirlik

```mermaid
erDiagram
    UAV ||--o{ Failure : suffers
    UAVComponent ||--o{ Failure : source
    FailureMode ||--o{ Failure : classified
    UAVClass ||--o{ FMEA : scoped
    PlatformType ||--o{ FMEA : scoped
    ComponentType ||--o{ FMEA : scoped
    FMEA ||--o{ FMEAItem : contains
    FailureMode ||--o{ FMEAItem : mode
    UAVClass ||--o{ RCMAnalysis : scoped
    PlatformType ||--o{ RCMAnalysis : scoped
    ComponentType ||--o{ RCMAnalysis : scoped
    RCMAnalysis ||--o{ RCMItem : contains
    UAV ||--o{ ReliabilitySnapshot : optional-cache

    Failure {
        uuid id PK
        timestamptz occurred_at
        string severity
        numeric downtime_hours
    }

    FMEA {
        uuid id PK
        string code UK
        string status
        int revision
    }

    FMEAItem {
        uuid id PK
        int severity
        int occurrence
        int detection
        int rpn
    }

    RCMAnalysis {
        uuid id PK
        string code UK
        string status
        int revision
    }

    RCMItem {
        uuid id PK
        bool safety_effect
        bool operational_effect
        bool preventive_feasible
        string strategy
    }
```

Aynı komponent türü farklı platformda ayrı FMEA/RCM kaydı olabilir. Kimlik: `(class, platform, component_type, [mission], revision)`.

## 6. Parça, doküman, maliyet, ayar

```mermaid
erDiagram
    Part ||--o{ PartCompatibility : applies
    UAVClass ||--o{ PartCompatibility : class
    PlatformType ||--o{ PartCompatibility : platform
    ComponentType ||--o{ PartCompatibility : component
    UAV ||--o{ Document : attached
    UAVComponent ||--o{ Document : attached
    WorkOrder ||--o{ Document : attached
    MaintenanceTemplate ||--o{ Document : attached
    WorkOrder ||--o{ CostRecord : costs
    SystemSetting {
        uuid id PK
        string key UK
        jsonb value
    }
```

## 7. Bütünlük kuralları

1. UAV oluşturulunca `CLASS_SPECIFIC` ise tam üçlü şablon aranır; yoksa kayıt reddedilir veya şablonsuz bırakılır (uyarı). `STANDARD` ise `approach=STANDARD` şablonu bağlanır.
2. Uçuş `result=COMPLETED` ve `counters_applied=false` iken sayaçlar bir transaction içinde artar; `counters_applied=true` olur. İkinci kez artmaz.
3. Sökülen komponent (`removed_at` dolu) yeni uçuştan saat almaz.
4. İş emri `COMPLETED` olunca `MaintenanceRecord` zorunludur.
5. FMEA kaleminde RPN uygulama katmanında `S × O × D` ile hesaplanır; istemci değeri kaynak değildir.
6. Silinen sınıf/platform/görev, bağlı UAV veya şablon varken hard-delete edilemez.
