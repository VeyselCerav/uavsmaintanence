# Yönetici kullanım kılavuzu

**İHA Bakım Yönetim ve Planlama Sistemi** — `ADMIN` rolü

| | |
|---|---|
| Canlı site | https://uavsmaintanence.vercel.app |
| Giriş | https://uavsmaintanence.vercel.app/login |
| Demo hesap | `admin@local.test` / `admin12345` |
| Dil | Giriş ve profilde TR / EN / AZ |

Demo parolayı canlı ortamda değiştirin. İlk açılışta sunucu uyanıyorsa 30–60 saniye sürebilir; giriş sayfasını açıp birkaç saniye bekleyin.

---

## 1. Bu rol ne yapar?

Yönetici **tüm modüllere** ve **Kontrol merkezi**ne (`/admin`) erişir. Katalog (sınıf, platform, görev, komponent türü), bakım şablonu, kullanıcı, sistem ayarları ve denetim kaydı yalnızca bu roldedir.

Sistem kural tabanlıdır: vade yüzdesi, RPN, MTBF/MTTR sunucuda hesaplanır. Yapay zekâ yoktur.

---

## 2. Giriş ve kabuk

1. Giriş sayfasında e-posta ve parola.
2. Üst çubuk: global arama (en az 2 karakter), bildirimler, profil, **Kontrol merkezi**, çıkış.
3. Sol menü: Özet, Filo, Uçuşlar, Bakım, İş emirleri, Arızalar, FMEA, RCM, Parçalar, Dokümanlar, Güvenilirlik, Karşılaştırma, Raporlar.

**DEMO** rozeti resmi bakım standardı değildir.

---

## 3. Özet (dashboard)

Filo pasta grafiği, vade çubuk grafiği, İHA durum kartları, açık iş emri sayısı, MTBF/MTTR/kullanılabilirlik ve dikkat gerektiren vade / iş emri listeleri.

- Kartlara tıklayarak ilgili listeye gidin.
- Tablodaki satır İHA veya iş emri detayına gider.

---

## 4. Filo

### Liste

Kayıt no, model, sınıf, platform, görev, şablon, durum. Arama kayıt no / seri no / modele bakar.

### Yeni İHA

**Filo → Yeni İHA.** Zorunlu alanlar:

- Kayıt numarası, seri numarası (benzersiz)
- Üretici, model
- Sınıf, platform, görev tipi
- Bakım yaklaşımı: `CLASS_SPECIFIC` veya `STANDARD`
- Durum (READY, MAINTENANCE, GROUNDED, RETIRED)

`CLASS_SPECIFIC` seçilince sınıf × platform × görev şablonu otomatik bağlanır. Şablon yoksa önce Kontrol merkezinde oluşturun.

MTOW ve üretim / envanter tarihi isteğe bağlıdır. Sınıf bantları:

| Kod | MTOW (kg) |
|---|---|
| VERY_LIGHT | 0 – 2 |
| LIGHT | 2 – 25 |
| MEDIUM | 25 – 150 |
| HEAVY | 150 – 600 |

### İHA detayı

Takılı komponentler, bakım vadeleri, uçuşlar, arızalar, dokümanlar, olay geçmişi.

**Komponent tak:** tür, ad, seri no. Takılınca ilgili şablon kalemleri için vadeler yeniden hesaplanır.

**Komponent sök:** açık iş emri yoksa Söküldü / Karantina / Hurda. Bağlı vadeler kalkar.

---

## 5. Uçuşlar

Uçuş kaydı İHA sayaçlarını (saat, uçuş adedi, çevrim) günceller; vadeler buna göre değişir.

1. **Uçuşlar → Yeni uçuş** (veya İHA detayı).
2. İHA, tarih, başlangıç/bitiş, sonuç (`COMPLETED` / `ABORTED` / `TRAINING`).
3. Kayıt tamamlanınca sayaçlar işlenir (`counters_applied`).

Aynı uçuşu iki kez işlemeyin.

---

## 6. Bakım

- **Vade listesi:** NORMAL / APPROACHING / DUE / OVERDUE / CRITICAL. Varsayılan eşikler: %80 yaklaşan, %100 vade, %110 gecikmiş, %130 kritik (Ayarlar’dan değişir).
- **Takvim:** gün / hafta / ay.
- **Bakım kayıtları:** tamamlanan iş emirlerinden oluşan geçmiş.

Vade satırından İHA detayına veya iş emri oluşturmaya geçilir.

---

## 7. İş emirleri

Akış: **Açık → Atandı → Devam ediyor → (Parça bekliyor) → Tamamlandı** veya **İptal**.

1. Vadeden veya **İş emirleri → Yeni**.
2. Teknisyen atayın.
3. Teknisyen başlatır / tamamlar; siz de atama, iptal, parça çıkışı yapabilirsiniz.
4. Tamamlanınca bakım kaydı oluşur; vade sıfırlanır veya yeniden hesaplanır.

Açık iş emri varken o komponent sökülemez.

---

## 8. Arıza, FMEA, RCM

**Arıza:** İHA, komponent, oluşum zamanı, şiddet, keşif yeri (uçuş / muayene / bakım). Güvenilirlik metriklerine girer.

**FMEA:** analiz oluşturun, kalemlerde S / O / D girin. **RPN sunucuda** hesaplanır. Onaylayın.

**RCM:** FMEA kaleminden strateji (periyodik muayene, restorasyon, hurda, durum izleme, fonksiyonel kontrol, düzeltici). Onaylayın.

---

## 9. Parçalar, dokümanlar, güvenilirlik, karşılaştırma, raporlar

| Modül | Yönetici işi |
|---|---|
| Parçalar | Stok, uyumluluk, iş emrine çıkış, maliyet |
| Dokümanlar | PDF / görüntü / ofis, en fazla 10 MB; İHA veya iş emrine bağlama |
| Güvenilirlik | Filo / sınıf / İHA MTBF, MTTR, kullanılabilirlik |
| Karşılaştırma | STANDARD vs CLASS_SPECIFIC (Puma `TR-PUB-004` vs Mini `TR-PUB-003`) |
| Raporlar | PDF veya Excel; İHA / tarih filtresi |

Canlı ücretsiz diskte eski dosyalar silinebilir; yeni yükleme yapın.

---

## 10. Kontrol merkezi (`/admin`)

Sol üstten veya `/admin`.

| Bölüm | Ne için? |
|---|---|
| Özet | Filo / iş emri / gecikmiş görev panelleri |
| Sınıflar, platformlar, görevler | Katalog |
| Komponent türleri | AIRFRAME, PROPULSION, AVIONICS, BATTERY, PAYLOAD… |
| Bakım şablonları | Sınıf × platform × görev × yaklaşım; kalem: interval, birim, öncelik, muayene tipi |
| Bakım kuralları | Vade eşikleri |
| Teknisyenler / yetenekler | Personel ve sertifika |
| Kullanıcılar | Rol atama, aktif/pasif. Son yönetici kapatılamaz |
| Ayarlar | Vade %, RPN bantları, sıfır arıza MTBF politikası, vade aşımında otomatik iş emri |
| Denetim kaydı | Kim neyi değiştirdi |

### Şablon oluşturma sırası

1. Sınıf, platform, görev, yaklaşım.
2. Komponent türü + görev kodu + interval (`FLIGHT_HOURS`, `FLIGHT_CYCLES`, `COMPONENT_CYCLES`, `CALENDAR_DAYS` …).
3. Kaydet. Yeni `CLASS_SPECIFIC` İHA’lar bu şablonu alır.

---

## 11. Kullanıcı ve bildirim

**Profil:** ad, dil, parola.

Bildirimler: yaklaşan/gecikmiş vade, atanan iş emri. Zil 20 sn’de bir yenilenir.

---

## 12. Tipik senaryolar

**Yeni platform tipi filoya alma**

1. Kontrol merkezi → sınıf/platform/görev doğrula veya ekle.
2. Şablon + kalemler.
3. Filo → Yeni İHA.
4. Komponent tak → vadeler oluşsun.
5. Gerekirse FMEA/RCM taslağı.

**Vade eşiğini sıkılaştırma**

Kontrol merkezi → Ayarlar → `maintenance.due_rules`. Değişiklik tüm kullanıcılar için geçerlidir.

**Karşılaştırma demosu**

`TR-PUB-003` (CLASS_SPECIFIC, Bayraktar Mini) ve `TR-PUB-004` (STANDARD, Puma AE) aynı sınıf/platform/görevdedir. **Karşılaştırma** ekranı iki kolu yan yana gösterir.

---

## 13. Sık sorunlar

| Durum | Çözüm |
|---|---|
| Şablon bağlanmadı | Sınıf/platform/görev/yaklaşım üçlüsü için aktif şablon var mı? |
| Vade yok | Komponent takılı mı, şablon kalemi o türe ait mi? |
| Komponent sökülemiyor | Açık iş emrini kapatın |
| Giriş çok yavaş | Eski Render uykusu; canlı yayın Northflank ise sayfayı yenileyin, API adresini kontrol edin |
| Doküman inmiyor | Metadata-only demo olabilir; yeni dosya yükleyin |
| Oturum bitti | Yeniden giriş |

---

## 14. Yetki özeti (ADMIN)

Tüm `*.view / create / update / delete` ve `admin.access`, `user.*`, `settings.*`, `audit.view`, `reports.export`. Nesne kapsamı yok (tüm filoyu görür).

Teknisyen kılavuzu: [kullanim-kilavuzu-teknisyen.md](./kullanim-kilavuzu-teknisyen.md)

Açık kaynak İHA JSON (henüz yüklenmedi): [../data/import/iha-katalog-acik-kaynak.json](../data/import/iha-katalog-acik-kaynak.json)
