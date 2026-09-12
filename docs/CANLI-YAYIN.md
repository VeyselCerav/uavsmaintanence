# Ücretsiz canlı yayın

Frontend: Vercel (`https://uavsmaintanence.vercel.app`)  
Backend + Postgres: Northflank (uyku yok)

JSON ile addon kurmanıza gerek yok. Hazır şablon: [northflank-template.json](../northflank-template.json)

## Sizin yapmanız gereken (3 adım)

1. [app.northflank.com](https://app.northflank.com) → hesap (GitHub ile giriş).
2. Sol menü **Templates → Create template → Code**.
3. `northflank-template.json` içeriğini yapıştırın → **Create** → **Run template**.

GitHub bağlantısı isterse **Allow** deyin. 5–10 dakika sonra **Services → uavs-backend** içindeki `*.code.run` adresini kopyalayın.

Sağlık: `https://O-ADRES.code.run/health/?db=1`

## Vercel (tek değişken)

`NEXT_PUBLIC_API_URL` = `https://O-ADRES.code.run/api/v1`  
sonra **Redeploy**.

## Demo

| Rol | E-posta | Parola |
|---|---|---|
| Yönetici | `admin@local.test` | `admin12345` |
| Teknisyen | `tech@local.test` | `tech12345` |

## Benim yerinize çalıştırmam için

Northflank → Account → API tokens → yeni token. Token’ı sohbete yapıştırın; şablonu CLI ile ben çalıştırırım. Token’ı repoya koymayın.
