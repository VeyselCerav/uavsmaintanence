# İHA Bakım Yönetim ve Planlama Sistemi — Mimari Paket

Bu klasör, tezin **Faz 1 (Architecture)** çıktısıdır. Kod yazılmadan önce domain, veri modeli, API, yetki ve i18n sınırları burada kilitlenir.

Kaynak: `İHA BAKIM YÖNETİM VE PLANLAMA SİSTEMİ.docx` (Nihai Cursor Master Development Prompt).

## Dokümanlar

| Dosya | İçerik |
|---|---|
| [01-sistem-mimarisi.md](./01-sistem-mimarisi.md) | Katmanlar, ilkeler, servis sınırları, akademik kapsam |
| [02-klasor-yapisi.md](./02-klasor-yapisi.md) | Frontend / backend / Docker klasör ağacı |
| [03-er-modeli.md](./03-er-modeli.md) | ER diyagramı ve ilişki kuralları |
| [04-veritabani-modelleri.md](./04-veritabani-modelleri.md) | Tablo alanları, enum’lar, indeksler |
| [05-api-mimarisi.md](./05-api-mimarisi.md) | REST sözleşmesi, kaynaklar, hata formatı |
| [06-frontend-rotalari.md](./06-frontend-rotalari.md) | Kullanıcı uygulaması sayfa haritası |
| [07-admin-rotalari.md](./07-admin-rotalari.md) | Admin Control Center sayfa haritası |
| [08-rbac.md](./08-rbac.md) | Roller, izin kataloğu, veri kapsamı |
| [09-i18n.md](./09-i18n.md) | TR / EN / AZ mimarisi |
| [10-fmea-domain.md](./10-fmea-domain.md) | FMEA domain modeli ve RPN |
| [11-rcm-domain.md](./11-rcm-domain.md) | RCM karar ağacı ve strateji seçimi |
| [12-bakim-sablonu-domain.md](./12-bakim-sablonu-domain.md) | Sınıf + platform + görev şablon motoru |

## Okuma sırası

1. Sistem mimarisi  
2. ER + veritabanı modelleri  
3. Bakım şablonu → FMEA → RCM  
4. API → RBAC → i18n  
5. Frontend / admin rotaları ve klasör yapısı  

## Sabitler (değişmez)

- Yapay zekâ, ML, LLM, chatbot, predictive maintenance **yok**.
- Bakım kararları kural tabanlıdır: RCM, FMEA, üretici kriteri, uçuş saati/çevrimi, takvim, komponent durumu.
- Django Admin son kullanıcı arayüzü değildir.
- Demo bakım periyotları resmi standart gibi sunulmaz.
- Öncelik: akademik doğruluk → veri modeli → bakım mantığı → güvenlik → kullanılabilirlik → UI.
