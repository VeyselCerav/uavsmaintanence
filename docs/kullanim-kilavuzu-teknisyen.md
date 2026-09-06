# Teknisyen kullanım kılavuzu

**İHA Bakım Yönetim ve Planlama Sistemi** — `TECHNICIAN` rolü

| | |
|---|---|
| Canlı site | https://uavsmaintanence.vercel.app |
| Giriş | https://uavsmaintanence.vercel.app/login |
| Demo hesap | `tech@local.test` / `tech12345` |
| Dil | Giriş ve profilde TR / EN / AZ |

İlk açılışta sunucu uyanıyorsa 30–60 saniye sürebilir; giriş sayfasını açıp birkaç saniye bekleyin.

---

## 1. Bu rol ne yapar?

Teknisyen **atanmış iş emirlerini yürütür**, bakım kaydı üretir ve **arıza girer**. Filoyu, vadeleri, parçaları ve dokümanları görüntüler.

**Yapamaz:** İHA ekleme/silme, şablon, kullanıcı, ayar, kontrol merkezi, rapor dışa aktarma, iş emri oluşturma/atama.

Menüde görünüp açılamayan sayfalar yetki dışıdır; hata alırsanız yöneticiye sorun.

---

## 2. Giriş

1. E-posta / parola.
2. Üst çubuk: arama (en az 2 karakter), bildirimler, adınız, çıkış.
3. Sol menüden günlük iş: **Özet → İş emirleri → Bakım → Arızalar**.

Size atanan iş emri bildirimi zil ikonunda görünür.

---

## 3. Özet

Filo ve vade özeti ile **size açık iş emirleri** (başkasının emri listede olmaz).

Kartlar ve tablolar ilgili sayfaya götürür.

---

## 4. İş emri — asıl işiniz

### Liste

Numara, İHA kayıt no, görev, atanan, durum. Arama kutusunu kullanın.

Sizin kapsamınız: **atanmış** kayıtlar. Durumlar:

| Durum | Sizin adımınız |
|---|---|
| Atandı (`ASSIGNED`) | **Başlat** |
| Devam (`IN_PROGRESS`) | İşleyin, not/parça, sonra **Tamamla** |
| Parça bekliyor | Parça gelince devam / tamamla |
| Tamamlandı / İptal | Salt okunur |

Açık (`OPEN`) emri size atanmadan başlatamazsınız; yönetici atamalıdır.

### Tamamlama adımları

1. **İş emirleri** → size ait satır.
2. İHA, komponent, görev kodu, önceliği okuyun.
3. **Başlat** — durum Devam olur.
4. Görsel/fonksiyonel kontrolü yapın; **bulgular** ve notları yazın.
5. Parça değiştiyse yönetici veya yetkili stoktan iş emrine parça bağlar; siz `part.view` ile görürsünüz.
6. **Tamamla** — bakım kaydı oluşur, ilgili vade güncellenir.

Yarıda bırakmayın: başlattıysanız tamamlayın veya yöneticiye iptal/parça bekleme için haber verin.

---

## 5. Bakım vadeleri

**Bakım** menüsü: hangi İHA’da hangi görev, kullanım yüzdesi, kalan süre, durum.

- `APPROACHING` / `DUE` / `OVERDUE` / `CRITICAL` iş emrine dönüşmüş olabilir.
- Takvim görünümü planlama içindir; iş emri oluşturmazsınız.
- Satıra tıklayınca İHA detayına gidersiniz (görüntüleme).

Vade yüzdesini siz hesaplamazsınız; uçuş sayaçları ve şablon interval’i sunucuda işler.

---

## 6. Filo ve komponent (görüntüleme)

**Filo:** liste ve İHA detayı. Kayıt no, takılı komponentler, vadeler, geçmiş.

Komponent **tak/sök yapamazsınız**. Seri no ve durumu okuyup iş emrine not düşersiniz.

---

## 7. Arıza kaydı

Uçuşta, muayenede veya bakımda gördüğünüz arızayı girin; güvenilirlik (MTBF/MTTR) buna dayanır.

1. **Arızalar → Yeni arıza**.
2. İHA zorunlu; komponent varsa seçin.
3. Oluşum zamanı, şiddet, keşif yeri (uçuş / muayene / bakım / diğer), açıklama.
4. Kaydet. Sonra güncelleyebilirsiniz (çözüm zamanı vb.).

İş emrine bağlama yönetici/süreç tarafındadır; sizin kaydınız iz bırakır.

---

## 8. FMEA / RCM / parçalar / dokümanlar

| Ekran | Teknisyen |
|---|---|
| FMEA, RCM | Okuma; onay/yazma yok |
| Parçalar | Stok görüntüleme |
| Dokümanlar | Görüntüleme ve indirme (yükleme yok) |
| Uçuşlar | Liste/detay; yeni uçuş yok |

İndirilemeyen doküman çoğu zaman dosyasız demo kaydıdır.

---

## 9. Arama, bildirim, profil

- Arama: İHA, komponent, iş emri, arıza, parça (yetkinizin gördüğü kayıtlar).
- Bildirim: size atanan iş, vade uyarısı.
- Profil: ad, dil, parola.

---

## 10. Günlük kontrol listesi

1. Bildirim zili.
2. Özet → açık iş emri var mı?
3. Atandıysa başlat → uygula → not → tamamla.
4. Anormal bulgu varsa **Arıza** açın.
5. Kritik vade (`CRITICAL` / `OVERDUE`) görürseniz yöneticiye iş emri/atama için haber verin (siz oluşturamazsınız).

---

## 11. Sık sorunlar

| Durum | Ne yapmalı? |
|---|---|
| İş emri listesi boş | Size atama yok demektir; yöneticiye sorun |
| Başlat butonu yok | Durum Atandı değil veya size ait değil |
| Tamamlanmıyor | Önce Başlat; zorunlu alanları doldurun |
| İHA ekleyemiyorum | Teknisyen yetkisi yoktur |
| Kontrol merkezi 403 | Yalnızca yönetici |
| Sayfa boş / yükleniyor | Sunucu uyanıyor olabilir; bekleyin veya yenileyin |

---

## 12. Yetki özeti (TECHNICIAN)

`dashboard.view`, `uav.view`, `component.view`, `flight.view`, `maintenance.view`, `work_order.view`, `work_order.start`, `work_order.complete`, `failure.view/create/update`, `fmea.view`, `rcm.view`, `part.view`, `document.view`, `notification.view`.

İş emri **nesne kapsamı:** yalnızca `assigned_technician` siz olan kayıtlar.

Yönetici kılavuzu: [kullanim-kilavuzu-yonetici.md](./kullanim-kilavuzu-yonetici.md)
