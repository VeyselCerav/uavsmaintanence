# 11 — RCM Domain Modeli

RCM (Reliability Centered Maintenance) karar ağacı kural tabanlıdır. Çıktı bir `RCMStrategy` değeridir; LLM yorumu yoktur.

## 1. Kapsam

FMEA ile aynı ayrıştırma:

```text
RCM kapsamı = UAVClass × PlatformType × ComponentType [× MissionType]
```

Fixed Wing motor ≠ Multicopter motor ≠ VTOL lift motor.

## 2. Varlıklar

**RCMAnalysis**

| Alan | Açıklama |
|---|---|
| code | UK |
| title | |
| uav_class_id, platform_type_id, component_type_id | zorunlu |
| mission_type_id | opsiyonel |
| status / revision / is_demo | FMEA ile aynı yaşam döngüsü |
| approved_at / approved_by | |

**RCMItem**

| Alan | Açıklama |
|---|---|
| function | |
| functional_failure | |
| failure_mode | |
| failure_effect | |
| safety_effect | bool |
| operational_effect | bool |
| detectability | LOW / MEDIUM / HIGH (veya 1–10; **öneri:** LOW/MEDIUM/HIGH, FMEA Detection ile karışmasın) |
| preventive_feasible | bool |
| strategy | RCMStrategy enum |
| rationale | İnsan gerekçesi (zorunlu onayda) |
| fmea_item_id | opsiyonel bağ |
| sequence | |

## 3. Karar ağacı (varsayılan kural tablosu)

`RCMEvaluationService.evaluate(item)` — deterministik:

```text
1. safety_effect == true
      AND preventive_feasible == true
        AND detectability == HIGH     → CONDITION_INSPECTION
        ELSE                          → SCHEDULED_RESTORATION
      AND preventive_feasible == false → CORRECTIVE
         (güvenlik + önlem yok: UAV GROUNDED politikası ayar ile; strateji yine CORRECTIVE + uyarı)

2. safety_effect == false AND operational_effect == true
      AND preventive_feasible == true
        AND detectability == HIGH     → CONDITION_INSPECTION
        ELSE                          → SCHEDULED_INSPECTION
      AND preventive_feasible == false → CORRECTIVE

3. safety_effect == false AND operational_effect == false
      AND preventive_feasible == true → FUNCTIONAL_CHECK
      ELSE                            → CORRECTIVE
```

`SCHEDULED_DISCARD` ağaçtan otomatik çıkmaz; analist, ömür sonu parçalar için manuel seçer (pil, propeller lifetime). UI bunu açık seçenek olarak sunar; kural “otomatik discard önerme”.

Analist stratejiyi override edebilir. Override’da `rationale` zorunlu, audit’e yazılır.

## 4. Şablon ile ilişki

`MaintenanceTemplateItem.rcm_strategy` RCM çıktısından kopyalanabilir; şablon kaynağıdır. RCM analizi değişince şablon otomatik sessiz güncellenmez. Manager “stratejiyi şablona aktar” eylemi ile bilinçli kopyalar (tez izi).

## 5. Ekran

```text
Function → Functional Failure → Failure Mode
  → Safety Effect? YES/NO
  → Operational Effect? YES/NO
  → Preventive Maintenance Feasible? YES/NO
  → (Detectability)
  → Maintenance Strategy
```

Sonuç kayıt altına alınır. Onaylı RCM olmadan da şablon stratejisi elle girilebilir; raporlarda “RCM’e bağlı değil” bayrağı gösterilir.
