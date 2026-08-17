# Kullanım Rehberi

**İHA Bakım Yönetim ve Planlama Sistemi** — teknisyen ve yönetici (admin) kullanıcıları için kısa el kitabı.

Ana adres: **http://localhost:8080** (Nginx üzerinden; önerilen giriş noktası)

---

## 1. Giriş

| Rol | E-posta | Parola | Açıklama |
|---|---|---|---|
| **Yönetici (ADMIN)** | `admin@local.test` | `admin12345` | Tam yetki; kullanıcı, ayar ve denetim kaydı |
| **Teknisyen (TECHNICIAN)** | `tech@local.test` | `tech12345` | İş emri yürütme, arıza kaydı, görüntüleme |

Giriş ekranında sağ alttan **TR / EN / AZ** dili seçilebilir.

**Parolamı unuttum:** Geliştirme ortamında e-posta gönderilmez; istek sonrası ekranda sıfırlama bağlantısı görünür (yalnızca `DEBUG` modunda).

---

## 2. Rol özeti

### Yönetici (ADMIN)

- Tüm modüllere erişir.
- **Kontrol merkezi** (`/admin`): sınıf, platform, görev, komponent türü, bakım şablonu/kuralı, teknisyen, yetenek, **kullanıcı**, **sistem ayarları**, **denetim kaydı**.
- İHA ekleme/düzenleme, komponent tak/sök, doküman yükleme/silme, FMEA/RCM onayı, rapor dışa aktarma.
- Son aktif yönetici hesabı devre dışı bırakılamaz.

### Teknisyen (TECHNICIAN)

- **Özet**, **Filo**, **Bakım**, **İş emirleri**, **Arızalar**, **FMEA/RCM** (görüntüleme), **Parçalar**, **Dokümanlar** (görüntüleme/indirme).
- İş emrinde **başlat** ve **tamamla**; arıza oluşturma/güncelleme.
- İHA ekleme, şablon düzenleme, kullanıcı yönetimi, kontrol merkezi ve rapor dışa aktarma **yoktur**.

> **Not:** Bakım müdürü (`MAINTENANCE_MANAGER`) rolü tez demosunda ayrı kullanıcı olarak seed edilmemiştir; operasyonel yönetim için `admin@local.test` kullanın.

---

## 3. Ana ekranlar

Sol menüden erişilir:

| Menü | Ne için? |
|---|---|
| **Özet** | Filo durumu, bakım vadeleri grafikleri, açık iş emirleri, güvenilirlik özeti |
| **Filo** | İHA listesi ve detay (komponentler, vadeler, uçuş, olay geçmişi) |
| **Uçuşlar** | Uçuş kaydı; sayaçlar işlendiğinde bakım vadeleri güncellenir |
| **Bakım** | Vade listesi, takvim, bakım kayıtları |
| **İş emirleri** | Açık/tamamlanan iş emirleri, atama, durum geçişi |
| **Arızalar** | Arıza kaydı, MTBF/MTTR girdisi |
| **FMEA / RCM** | Analiz kayıtları (RPN sunucuda hesaplanır) |
| **Parçalar** | Stok ve iş emrine parça çıkışı |
| **Dokümanlar** | Dosya yükleme (PDF, görüntü, ofis; en fazla 10 MB) ve indirme |
| **Güvenilirlik** | MTBF, MTTR, kullanılabilirlik |
| **Karşılaştırma** | STANDARD vs CLASS_SPECIFIC yaklaşım karşılaştırması |
| **Raporlar** | PDF/Excel dışa aktarma |

Üst çubuk: **global arama** (en az 2 karakter), bildirimler, profil, çıkış.

---

## 4. Tipik iş akışları

### 4.1 Yönetici — demo filoyu inceleme

1. **Özet** → filo pasta grafiği ve vade çubuk grafiğini kontrol edin.
2. **Filo** → örn. `TR-UAV-001` detayına girin.
3. **Takılı komponentler**, **Bakım vadeleri**, **Olay geçmişi** bölümlerini inceleyin.
4. **Karşılaştırma** → `TR-UAV-006` (STANDARD) ile sınıfa özgü filonun metriklerini yan yana görün.

### 4.2 Yönetici — yeni İHA ve bakım şablonu

1. **Kontrol merkezi** → Sınıf / Platform / Görev kataloglarını doğrulayın.
2. **Bakım şablonları** → sınıf × platform × görev için şablon oluşturun; görev kalemlerini ekleyin.
3. **Filo** → **Yeni İHA** → şablon otomatik bağlanır (CLASS_SPECIFIC).
4. İHA detayında komponent **tak** → ilgili tür için vadeler yeniden hesaplanır.

### 4.3 Teknisyen — iş emrini tamamlama

1. **İş emirleri** → açık emri seçin (ör. demo `TR-UAV-001` pervane vadesi).
2. **Başlat** → işe alın.
3. Bulguları/notları girin; gerekirse **Parçalar** üzerinden iş emrine parça ekleyin.
4. **Tamamla** → bakım kaydı oluşur; ilgili vade sıfırlanır/güncellenir.

### 4.4 Teknisyen — arıza kaydı

1. **Arızalar** → **Yeni arıza**.
2. İHA ve (varsa) komponent seçin; oluşum zamanı ve şiddeti girin.
3. Kayıt güvenilirlik metriklerine yansır.

### 4.5 Yönetici — doküman yükleme

1. **Dokümanlar** → **Yeni doküman** veya İHA detayındaki doküman bölümü.
2. Başlık, tür ve **dosya** seçin; İHA / iş emri / şablon bağlayın.
3. Listede **İndir** ile dosyayı alın. Eski demo kayıtlarında yalnızca metadata olabilir (dosya yok).

### 4.6 Yönetici — komponent sökme

1. **Filo** → İHA detayı → **Takılı komponentler**.
2. Açık iş emri **yoksa** hedef durumu (Söküldü / Karantina / Hurda) seçip **Sök**.
3. Komponente bağlı bakım vadeleri kaldırılır.

### 4.7 Rapor alma (yönetici)

1. **Raporlar** → rapor tipi seçin (filo, vade, iş emri, güvenilirlik, karşılaştırma vb.).
2. Gerekirse İHA veya tarih aralığı filtreleyin.
3. **PDF** veya **Excel** indirin.

---

## 5. Kontrol merkezi (yalnızca yetkili roller)

`/admin` — sol menüde **Kontrol merkezi** ( `admin.access` yetkisi gerekir).

| Bölüm | ADMIN | Teknisyen |
|---|---|---|
| Sınıf / Platform / Görev / Komponent türü | Evet | Hayır |
| Bakım şablonu ve kuralları | Evet | Hayır |
| Teknisyen / Yetenek | Evet | Hayır |
| **Kullanıcılar** | Evet (ADMIN) | Hayır |
| **Sistem ayarları** (vade eşikleri, RPN) | Evet (ADMIN) | Hayır |
| **Denetim kaydı** | Evet (ADMIN) | Hayır |

Vade eşikleri ve RPN bantları burada değiştirilir; değişiklikler sunucuda saklanır ve tüm kullanıcılar aynı kuralları görür.

---

## 6. Global arama

Üst çubukta en az **2 karakter** yazın. Sonuçlar yetkiye göre filtrelenir:

İHA, komponent, iş emri, bakım, arıza, parça.

Örnek: `TR-UAV-001`

---

## 7. Demo verisi

İlk kurulumdan sonra demo filo için (PowerShell):

```powershell
docker compose exec backend python manage.py seed_fleet
```

Demo İHA’lar `TR-UAV-001` … `TR-UAV-006` aralığındadır. `TR-UAV-006`, `TR-UAV-001` ile aynı sınıf/platform/görevde **STANDARD** bakım yaklaşımı içindir (karşılaştırma demosu).

Demo kayıtları **DEMO** rozeti ile işaretlidir; resmi bakım standardı değildir.

---

## 8. Sık karşılaşılan durumlar

| Durum | Ne yapmalı? |
|---|---|
| Oturum süresi doldu | Yeniden giriş yapın |
| İş emri tamamlanmıyor | Durum geçişi kurallarına uygun adımı izleyin (Açık → Atandı → Devam → Tamamlandı) |
| Komponent sökülemiyor | İlgili komponente açık iş emri varsa önce kapatın |
| Doküman indirilemiyor | Kayıt eski metadata-only demo olabilir; yeni dosya yükleyin |
| Vade yüzdesi beklenenden farklı | Uçuş sayaçları işlendi mi, komponent takılı mı kontrol edin; eşikler Kontrol merkezi → Ayarlar’da |

---

## 9. Bilinçli sınırlar (tez kapsamı)

- **SMTP / e-posta** yok; parola sıfırlama demo bağlantısı ile sınırlıdır.
- **Yapay zekâ / ML / LLM** kullanılmaz; RPN, vade yüzdesi, MTBF vb. sunucuda kural tabanlı hesaplanır.
- Frontend hesaplama yapmaz; tüm metrikler API’den gelir.

---

## 10. Destek ve teknik not

- API dokümantasyonu: http://localhost:8000/api/docs/
- Mimari: [docs/architecture/README.md](docs/architecture/README.md)
- Kurulum: [README.md](README.md)
