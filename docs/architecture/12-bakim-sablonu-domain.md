# 12 — Bakım Şablonu Domain Modeli

Bu, sistemin akademik çekirdeğidir. Tek tip bakım yoktur. Şablon **sınıf × platform × görev × yaklaşım** ile üretilir ve UAV’ye bağlanır.

## 1. Eşleşme kuralı (ADR-04)

```text
resolve(class, platform, mission, approach) → 0 veya 1 aktif şablon
```

- Kısmi eşleşme (yalnızca sınıf) yok. Sessiz fallback akademik sonucu bozar.
- Eşleşme yoksa UAV kaydı oluşturulabilir; `maintenance_template_id = NULL` ve durum uyarısı. `CLASS_SPECIFIC` + zorunlu şablon ayarı açıksa 409 `MAINTENANCE_TEMPLATE_NOT_FOUND`.
- `STANDARD` yaklaşımı ayrı şablon satırıdır; aynı üçlüde iki yaklaşım yan yana durabilir (tez karşılaştırması).

Benzersiz aktif kayıt:

```text
UNIQUE (uav_class_id, platform_type_id, mission_type_id, approach)
  WHERE is_active AND NOT is_deleted
```

Örnek:

```text
FIXED_WING  × MEDIUM × MAPPING      × CLASS_SPECIFIC → Template A
FIXED_WING  × MEDIUM × SURVEILLANCE × CLASS_SPECIFIC → Template B
MULTICOPTER × LIGHT  × MAPPING      × CLASS_SPECIFIC → Template C
FIXED_WING  × MEDIUM × MAPPING      × STANDARD       → Template S (taban)
```

A ve S aynı İHA üzerinde karşılaştırma için `UAV.maintenance_approach` ile seçilir. İHA bir anda tek şablona bağlıdır; yaklaşım değişince şablon yeniden resolve edilir ve audit yazılır.

## 2. Varlıklar

**MaintenanceTemplate**  
Kimlik, kapsam üçlüsü, `approach`, aktiflik, demo bayrağı, açıklama.

**MaintenanceTemplateItem**  
Komponent türüne bağlı görev:

| Alan | Rol |
|---|---|
| component_type | Hangi tür bakılır |
| task_code / task_name | Görev kimliği |
| interval_value + interval_unit | Saat, çevrim veya takvim |
| priority | LOW…CRITICAL |
| required_skill | Teknisyen yetkinliği |
| estimated_duration_minutes | Planlama |
| inspection_type | Görsel, işlevsel, … |
| rcm_strategy | RCM’den aktarılmış veya elle |

Bir tür için birden fazla görev olabilir (ör. motor 50 FH görsel + 200 FH overhaul).

**MaintenanceRule**  
Kullanım yüzdesine göre `DueStatus` üretir. Şablona değil sisteme aittir; tüm şablonlar aynı eşik dilimini paylaşır (karşılaştırılabilir ölçüm). Eşikler admin’den değişir.

## 3. Vade hesabı

`MaintenanceDueService.recalculate(uav)` her kurulu komponent × şablon kalemi için:

```text
kullanılan = unit’e göre:
  FLIGHT_HOURS      → component.operating_hours - baseline_hours
  FLIGHT_CYCLES     → uav.total_flight_cycles - baseline
  COMPONENT_CYCLES  → component.cycle_count - baseline
  CALENDAR_*        → now - last_maintenance_or_install

usage_percent = kullanılan / interval_value × 100

status:
  < approaching_percent → NORMAL
  < due_percent         → APPROACHING
  < overdue_percent     → DUE
  < critical_percent    → OVERDUE
  else                  → CRITICAL
```

`baseline`, son tamamlanmış ilgili `MaintenanceRecord` veya kurulum anıdır.

Tetikleyiciler: uçuş complete, komponent install/remove, bakım complete, şablon değişimi, kural eşiği değişimi (filo yeniden hesap).

## 4. UAV yaşam döngüsü

```text
1. Sınıf, platform, görev, approach seçilir
2. Template resolve
3. Fiziksel komponentler eklenir (şablon tür listesi önerilir, zorunlu kopya değil)
4. Uçuş → sayaç
5. Due satırları
6. Work Order (manuel veya auto_create_on_due)
7. Complete → record + next due + cost
```

Şablon, envanter yaratmaz. Envanter seri numaralı gerçek parçadır. Şablon “bu tür için ne zaman ne yapılır” der.

## 5. İş emri üretimi

Varsayılan: vade `DUE` olunca bildirim; WO’yu manager açar.  
Ayar `work_order.auto_create_on_due=true` ise motor taslak `OPEN` WO üretir (aynı due için ikinci WO yok).

WO önceliği: şablon priority ⊕ RPN bandı ⊕ due_status ([10-fmea-domain.md](./10-fmea-domain.md) kuralı).

## 6. Tez karşılaştırma verisi

Her `MaintenanceRecord.approach` ve `WorkOrder` dolaylı olarak UAV’nin o anki yaklaşımını taşır. Rapor boyutları:

```text
Maintenance Count
Unscheduled Maintenance
Cost
Downtime
MTBF
MTTR
Availability
```

kesit: `approach`, `uav_class`, `platform`, `mission`.

Demo interval’ler `is_demo=true`. UI ve PDF “DEMO DATA — resmi bakım standardı değildir” notu basar.

## 7. Servis listesi

| Servis | İş |
|---|---|
| `TemplateResolveService` | Üçlü + approach → şablon |
| `MaintenanceDueService` | Kalan kullanım ve status |
| `FlightCompletionService` | Saat/çevrim + due |
| `WorkOrderService` | Atama, durum makinesi |
| `WorkOrderCompletionService` | Record, maliyet, sayaç sıfırlama (baseline) |
| `MaintenancePriorityService` | RPN + gecikme |
| `NotificationService` | Eşik olayları |

Durum makinesi:

```text
OPEN → ASSIGNED → IN_PROGRESS → COMPLETED
                 ↘ WAITING_PARTS ↗
OPEN / ASSIGNED / IN_PROGRESS / WAITING_PARTS → CANCELLED
```

Geçersiz geçiş 409 `INVALID_STATUS_TRANSITION`.
