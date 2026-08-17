# 10 — FMEA Domain Modeli

FMEA (Failure Modes and Effects Analysis) kural tabanlıdır. Model eğitilmez, öneri motoru yoktur. Amaç: sınıf + platform (+ görev) + komponent türü için arıza etkisini sayısallaştırmak ve bakım önceliğine girdi vermek.

## 1. Neden İHA sınıfına özel?

Aynı “motor” Fixed Wing, Multicopter ve VTOL lift motorunda farklı fonksiyon, farklı etki, farklı RPN üretebilir. Bu yüzden FMEA komponent seri numarasına değil **komponent türü + platform + sınıf** kapsamına bağlanır. İsteğe bağlı `mission_type` ile daha da ayrışır.

```text
FMEA kapsamı = UAVClass × PlatformType × ComponentType [× MissionType]
```

## 2. Varlıklar

**FMEA** (analiz başlığı)

| Alan | Açıklama |
|---|---|
| code | UK, ör. `FMEA-FW-MED-MOTOR-001` |
| title | Analiz adı |
| uav_class_id | zorunlu |
| platform_type_id | zorunlu |
| component_type_id | zorunlu |
| mission_type_id | NULL = tüm görevler |
| status | DRAFT / IN_REVIEW / APPROVED / ARCHIVED |
| revision | int, onayda artar |
| is_demo | demo etiketi |
| approved_at / approved_by | |

**FMEAItem**

| Alan | Açıklama |
|---|---|
| function | Komponentin işlevi |
| functional_failure | İşlevin yerine getirilememesi |
| failure_mode | Nasıl bozulur |
| failure_cause | Neden |
| failure_effect | Sonuç |
| severity | 1–10 |
| occurrence | 1–10 |
| detection | 1–10 |
| rpn | `S × O × D` (server) |
| existing_control | Mevcut kontrol |
| recommended_action | Önerilen eylem |
| failure_mode_id | katalog FK, opsiyonel |
| sequence | |

## 3. RPN

```text
RPN = Severity × Occurrence × Detection
```

Bantlar `SystemSetting.rpn.thresholds` (varsayılan seed, değiştirilebilir):

| Bant | Aralık |
|---|---|
| LOW | 1–49 |
| MEDIUM | 50–99 |
| HIGH | 100–199 |
| CRITICAL | 200+ |

UI: `RPNIndicator` sayı + bant. Gradient/glow yok.

## 4. Önceliğe etki (kural)

`MaintenancePriorityService` (kural, AI değil):

```text
base = template_item.priority
if rpn_band == CRITICAL → en az HIGH, overdue ise CRITICAL
if rpn_band == HIGH and due_status in (DUE, OVERDUE) → HIGH
if due_status == CRITICAL → CRITICAL
if due_status == OVERDUE and base < HIGH → HIGH
```

Formül ayardan okunur; kodda sihirli sayı bırakılmaz.

## 5. Builder akışı (UI)

```text
Function → Functional Failure → Failure Mode → Cause → Effect
        → Severity, Occurrence, Detection → RPN
```

Teknik ve sade. Onaylanmamış FMEA bakım motoruna girmez. `APPROVED` revizyonu motorun okuduğu tek sürümdür.

## 6. İz

Her kalem değişimi `AuditAction.FMEA_CHANGE`. Eski/yeni S, O, D, RPN jsonb’de tutulur.
