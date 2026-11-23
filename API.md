# Jamg'arma API hujjati

Jamg'arma - mobil ilova uchun backend: foydalanuvchi ro'yxatdan o'tadi, karta ochadi, kartani to'ldiradi, kartadan kartaga pul o'tkazadi, kommunal va mobil aloqa uchun to'lov qiladi, valyuta/kripto/aksiya kurslarini ko'radi.

| | |
|---|---|
| Framework | FastAPI (async), SQLAlchemy 2 + PostgreSQL (asyncpg) |
| Deploy | Vercel (`vercel.json`, funksiya limiti 30 s) |
| Base URL | `https://<sizning-domeningiz>` |
| Format | JSON (`Content-Type: application/json`) |
| Autentifikatsiya | `Authorization: Bearer <access_token>` (JWT, HS256) |
| CORS | Barcha originlarga ochiq |
| Til | Xato xabarlari o'zbek tilida |

Swagger UI: `GET /docs`, ReDoc: `GET /redoc`, OpenAPI sxema: `GET /openapi.json` (FastAPI standart).

---

## Mundarija

1. [Tezkor boshlash](#1-tezkor-boshlash)
2. [Autentifikatsiya va tokenlar](#2-autentifikatsiya-va-tokenlar)
3. [Xatoliklar](#3-xatoliklar)
4. [Endpointlar jadvali](#4-endpointlar-jadvali)
5. [Auth](#5-auth)
6. [Qurilmalar (push token)](#6-qurilmalar-push-token)
7. [Kartalar](#7-kartalar)
8. [P2P o'tkazma](#8-p2p-otkazma)
9. [Kommunal to'lovlar](#9-kommunal-tolovlar)
10. [Mobil aloqa / internet to'lovi](#10-mobil-aloqa--internet-tolovi)
11. [Tranzaksiyalar tarixi](#11-tranzaksiyalar-tarixi)
12. [Bozor ma'lumotlari (valyuta, kripto, aksiya)](#12-bozor-malumotlari-valyuta-kripto-aksiya)
13. [Enum qiymatlari](#13-enum-qiymatlari)
14. [Tashqi servislar va muhit o'zgaruvchilari](#14-tashqi-servislar-va-muhit-ozgaruvchilari)
15. [Ma'lum muammolar va eslatmalar](#15-malum-muammolar-va-eslatmalar)

---

## 1. Tezkor boshlash

Ro'yxatdan o'tish **ikki bosqichli**: avval ma'lumot yuboriladi, keyin SMS orqali kelgan kod bilan tasdiqlanadi.

```bash
BASE=https://<sizning-domeningiz>

# 1) Ro'yxatdan o'tish - OTP kodi telefonga yuboriladi (180 soniya amal qiladi)
curl -X POST $BASE/auth/register -H "Content-Type: application/json" -d '{
  "first_name": "Ali",
  "last_name": "Valiyev",
  "phone_number": "+998901234567",
  "password": "secret123"
}'

# 2) Kodni tasdiqlash - akkaunt yaratiladi va tokenlar qaytadi
curl -X POST $BASE/auth/confirm-otp -H "Content-Type: application/json" -d '{
  "phone_number": "+998901234567",
  "otp_code": 123456
}'

# 3) Tokenni o'zgaruvchiga olamiz va karta ochamiz
TOKEN=<access_token>
curl -X POST $BASE/cards/ -H "Authorization: Bearer $TOKEN"

# 4) Kartani to'ldirish (card_id - karta UUID si, qarang: 15-bo'lim, 2-band)
curl -X POST $BASE/cards/topup -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"card_id": "<karta-uuid>", "amount": 100000}'
```

Keyingi kirishlar uchun `POST /auth/login` ishlatiladi.

---

## 2. Autentifikatsiya va tokenlar

Himoyalangan endpointlarga har so'rovda header yuboriladi:

```
Authorization: Bearer <access_token>
```

| Token | Muddati | Vazifasi |
|---|---|---|
| `access_token` | 1 kun | Barcha himoyalangan endpointlar uchun |
| `refresh_token` | 30 kun | Faqat `POST /auth/refresh` uchun, yangi access token olish |

- Muddatlar `.env` dagi `ACCESS_TOKEN_EXPIRE_DAYS` va `REFRESH_TOKEN_EXPIRE_DAYS` orqali sozlanadi (hozirgi qiymat: 1 va 30 kun).
- Token ichida `sub` (user ID), `exp` va `type` (`access` yoki `refresh`) bo'ladi.
- Refresh token access token sifatida **qabul qilinmaydi** va aksincha.
- Token yo'q bo'lsa: `401 {"detail": "Not authenticated"}`.
- Token yaroqsiz yoki muddati o'tgan bo'lsa: `401 {"detail": "Token yaroqsiz yoki muddati o'tgan!"}`. Bunda client `/auth/refresh` orqali yangi token olib, so'rovni takrorlashi kerak.

---

## 3. Xatoliklar

Barcha xatolar FastAPI standart formatida qaytadi:

```json
{ "detail": "Xato matni" }
```

Validatsiya xatosi (`422`) - maydonlar bo'yicha ro'yxat:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "phone_number"],
      "msg": "Value error, Telefon raqam noto'g'ri formatda. Namuna: +998901234567",
      "input": "901234567"
    }
  ]
}
```

| Kod | Ma'nosi |
|---|---|
| `200` / `201` | Muvaffaqiyatli / yaratildi |
| `400` | Biznes qoidasi buzildi (mablag' yetarli emas, karta muzlatilgan, kod noto'g'ri va h.k.) |
| `401` | Token yo'q, yaroqsiz yoki login ma'lumotlari noto'g'ri |
| `403` | Huquq yetarli emas (admin dependency mavjud, hozircha endpointda ishlatilmagan) |
| `404` | Karta yoki token topilmadi |
| `422` | So'rov tanasi/parametrlari validatsiyadan o'tmadi |
| `502` / `503` | Tashqi servis (SMS, valyuta/kripto API) yoki ma'lumotlar bazasi bilan muammo |

> **Pul summalari:** `amount` va `balance` maydonlari `Decimal` (2 xonali). Javobda ular odatda **string** ko'rinishida keladi (masalan `"50000.00"`). So'rovda son yoki string yuborish mumkin. Valyuta har doim `UZS`.

> **ID turlari:** foydalanuvchi ID - butun son (`int`), karta va tranzaksiya ID - UUID.

---

## 4. Endpointlar jadvali

| Method | Path | Auth | Tavsif |
|---|---|:---:|---|
| GET | `/` | - | Xush kelibsiz xabari |
| POST | `/auth/register` | - | Ro'yxatdan o'tishni boshlash, OTP yuborish |
| POST | `/auth/confirm-otp` | - | OTP ni tasdiqlash, akkaunt yaratish |
| POST | `/auth/login` | - | Telefon va parol bilan kirish |
| POST | `/auth/refresh` | - | Yangi access token olish |
| GET | `/auth/me` | + | Joriy foydalanuvchi ma'lumoti |
| POST | `/devices/register` | + | Push token saqlash |
| DELETE | `/devices/unregister` | + | Push tokenni o'chirish |
| POST | `/cards/` | + | Yangi karta ochish |
| GET | `/cards/` | + | Mening kartalarim |
| PATCH | `/cards/freeze` | + | Kartani muzlatish |
| PATCH | `/cards/unfreeze` | + | Kartani muzdan chiqarish |
| GET | `/cards/search/{card_number}` | - | Karta raqami bo'yicha egasini topish |
| POST | `/cards/topup` | + | Kartani to'ldirish |
| POST | `/p2p/transfer` | + | Kartadan kartaga o'tkazma |
| POST | `/communal/pay` | + | Kommunal to'lov |
| GET | `/communal/history` | + | Kommunal to'lovlar tarixi |
| POST | `/telecom/pay` | + | Mobil aloqa / internet to'lovi |
| GET | `/transactions/` | + | Barcha tranzaksiyalar tarixi |
| GET | `/info/currencies` | - | USD, EUR, RUB kurslari |
| GET | `/info/crypto` | - | BTC va USDT bozor ma'lumotlari |
| GET | `/info/stocks` | - | Aksiyalar narxi (Finnhub) |
| GET | `/info/market` | - | Yuqoridagi uchalasi bitta javobda |

`/cards/` va `/transactions/` oxiridagi `/` bilan yoziladi (`/cards` yuborilsa 307 redirect bo'ladi).

---

## 5. Auth

### POST `/auth/register`

Ro'yxatdan o'tishni boshlaydi. Ma'lumotlar (parol hash qilingan holda) Redis'da **180 soniya** saqlanadi va telefonga 6 xonali OTP kod yuboriladi (Authenticator servisi orqali).

**Body**

| Maydon | Tur | Qoida |
|---|---|---|
| `first_name` | string | majburiy, max 350 |
| `last_name` | string | majburiy, max 350 |
| `phone_number` | string | majburiy, format `+998XXXXXXXXX` (jami 13 belgi) |
| `password` | string | majburiy, kamida 6 belgi |

**200 OK**

```json
{
  "message": "Tasdiqlash kodi Authenticator ilovasiga +998901234567 ga yuborildi!",
  "status": 200
}
```

**Xatolar**

| Kod | detail |
|---|---|
| 400 | `Bu telefon raqam avval ro'yxatdan o'tgan` |
| 422 | Telefon formati noto'g'ri, parol qisqa va h.k. |
| 502 | `SMS servisda xatolik: ...` |
| 503 | `SMS servisga ulanib bo'lmadi: ...` |

---

### POST `/auth/confirm-otp`

OTP kodni tekshiradi, foydalanuvchini bazaga yozadi va tokenlarni qaytaradi.

**Body**

| Maydon | Tur | Izoh |
|---|---|---|
| `phone_number` | string | `register` da yuborilgan raqam bilan bir xil |
| `otp_code` | integer | SMS dagi 6 xonali kod |

**200 OK**

```json
{
  "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz",
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi..."
}
```

**Xatolar (400)**

| detail | Sabab |
|---|---|
| `Kod muddati o'tgan yoki topilmadi` | 180 soniya o'tib ketgan yoki `register` chaqirilmagan |
| `Kod yaroqsiz yoki noto'g'ri` | Kod mos kelmadi |
| `Ro'yxatdan o'tish muddati tugagan, qaytadan ro'yxatdan o'ting` | Ro'yxatdan o'tish ma'lumoti Redis'dan o'chib ketgan |

---

### POST `/auth/login`

> Body **JSON** formatida yuboriladi (form-data emas).

**Body**

```json
{ "phone_number": "+998901234567", "password": "secret123" }
```

**200 OK**

```json
{
  "message": "Muvaffaqiyatli kirildi",
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi..."
}
```

**Xatolar**

| Kod | detail |
|---|---|
| 401 | `Telefon raqam yoki parol noto'g'ri` (raqam yo'q yoki parol xato - ikkalasida bir xil xabar) |

Ma'lumotlar bazasiga ulanishda xato bo'lsa, endpoint `200` bilan `{"message": "Xizmat vaqtinchalik ishlamayapti!"}` qaytaradi. Client `access_token` mavjudligini tekshirishi kerak.

---

### POST `/auth/refresh`

Refresh token orqali yangi access token beradi. Refresh token o'zgarmaydi (rotatsiya yo'q).

**Body**

```json
{ "refresh_token": "eyJhbGciOi..." }
```

**200 OK**

```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer" }
```

**Xato:** `401` - `Refresh token yaroqsiz yoki muddati o'tgan!`

---

### GET `/auth/me`

Joriy foydalanuvchi ma'lumotlari. Auth kerak.

**200 OK**

```json
{
  "id": 1,
  "first_name": "Ali",
  "last_name": "Valiyev",
  "phone_number": "+998901234567",
  "role": "client",
  "is_active": true
}
```

`role` qiymatlari: `client`, `admin`.

---

## 6. Qurilmalar (push token)

Expo push bildirishnomalari uchun qurilma tokenini saqlash. Ikkala endpoint ham auth talab qiladi.

### POST `/devices/register`

Login qilgandan keyin chaqiriladi. Token bazada bo'lsa, u joriy foydalanuvchiga **qayta biriktiriladi** va faollashtiriladi (qurilmada akkaunt almashsa shu holat yuz beradi).

**Body**

| Maydon | Tur | Izoh |
|---|---|---|
| `token` | string | Expo push token (`ExponentPushToken[...]`) |
| `device_type` | string | `ios`, `android` yoki `web` |

**200 OK**

```json
{ "message": "Qurilma tokeni muvaffaqiyatli saqlandi", "status": 200 }
```

> Push yuborishda faqat `ExponentPushToken[` yoki `ExpoPushToken[` bilan boshlanadigan tokenlarga xabar ketadi.

### DELETE `/devices/unregister`

Logout paytida chaqiriladi. **Body bilan** yuboriladi:

```json
{ "token": "ExponentPushToken[xxxxxxxx]" }
```

**200 OK**

```json
{ "message": "Qurilma tokeni o'chirildi", "status": 200 }
```

**Xato:** `404` - `Token topilmadi` (token yo'q yoki boshqa foydalanuvchiga tegishli).

---

## 7. Kartalar

Karta raqami: **16 xonali, `1008` bilan boshlanadi**, tizim o'zi generatsiya qiladi. Yangi karta balansi `0.00`.

### POST `/cards/`

Yangi karta ochadi. Body yo'q. Auth kerak.

**201 Created**

```json
{
  "card_number": 1008123456789012,
  "balance": "0.00",
  "is_frozen": false,
  "created_at": "2026-11-20T10:15:30.123456+00:00",
  "user_fullname": "Ali Valiyev"
}
```

**Xato:** `502` - `Servis vaqtinchalik ishlamayabdi! Xato: ...`

### GET `/cards/`

Foydalanuvchining barcha kartalari ro'yxati (karta yo'q bo'lsa bo'sh ro'yxat `[]`). Element formati yuqoridagi bilan bir xil.

### PATCH `/cards/freeze`  va  PATCH `/cards/unfreeze`

Kartani muzlatadi / muzdan chiqaradi. Muzlatilgan kartadan to'lov va o'tkazma qilib bo'lmaydi, unga pul ham o'tkazib bo'lmaydi.

**Body**

```json
{ "card_number": 1008123456789012 }
```

**200 OK** - yangilangan karta (`CardResponse`, yuqoridagi format).

**Xatolar**

| Kod | detail | Qachon |
|---|---|---|
| 404 | `Bunday karta topilmadi yoki sizga tegishli emas.` | Raqam xato yoki boshqa odamniki |
| 400 | `Bu karta allaqachon muzlatilgan !` | `freeze`, karta allaqachon muzlatilgan |
| 400 | `Bu karta muzlamagan !` | `unfreeze`, karta muzlatilmagan |
| 502 | `Servis vaqtincha ishlamayabdi!` | Kutilmagan xato |

### GET `/cards/search/{card_number}`

Karta raqami bo'yicha egasining ismini topadi. P2P o'tkazma oldidan "kimga yuboryapman?" ni ko'rsatish uchun. **Auth talab qilinmaydi.**

```bash
curl $BASE/cards/search/1008123456789012
```

**200 OK**

```json
{
  "card_number": 1008123456789012,
  "is_frozen": false,
  "user_fullname": "Ali Valiyev"
}
```

**Xatolar**

| Kod | detail |
|---|---|
| 404 | `Bunday raqamdagi karta topilmadi.` (harf kiritilsa ham shu xato) |
| 400 | `Bu karta muzlatilgan (bloklangan).` |

### POST `/cards/topup`

O'z kartangiz balansini to'ldiradi. Auth kerak. Karta qator bloklash (`SELECT ... FOR UPDATE`) bilan olinadi, shuning uchun parallel so'rovlarda balans buzilmaydi. Hozircha to'lov tizimi (Click/Payme va h.k.) ulanmagan: summa tekshiruvsiz to'g'ridan-to'g'ri balansga qo'shiladi.

**Body**

| Maydon | Tur | Qoida |
|---|---|---|
| `card_id` | UUID | O'zingizning kartangiz **ID** si (karta raqami emas) |
| `amount` | decimal | `> 0`, max 15 raqam, 2 xonali kasr |
| `description` | string, ixtiyoriy | max 255. Berilmasa `Kartani to'ldirish` yoziladi |

```json
{
  "card_id": "3f2b8c1e-5a47-4d0e-9b61-0c2a7e8d1f33",
  "amount": 100000,
  "description": "Balansni to'ldirish"
}
```

**200 OK** (eslatma: `201` emas)

```json
{
  "transaction_id": "c4a8e1d2-7b09-4f3a-9d52-1e6b8a0c5f77",
  "card_id": "3f2b8c1e-5a47-4d0e-9b61-0c2a7e8d1f33",
  "amount": "100000.00",
  "new_balance": "100000.00",
  "status": "success",
  "transaction_type": "replenishment",
  "created_at": "2026-11-23T09:30:00.000000+00:00"
}
```

**Xatolar**

| Kod | detail |
|---|---|
| 404 | `Karta topilmadi yoki sizga tegishli emas` |
| 400 | `Karta muzlatilgan, to'ldirib bo'lmaydi` |
| 422 | `amount` 0 dan katta emas yoki format noto'g'ri |

Tranzaksiya `GET /transactions/` da `transaction_type: "replenishment"`, `sender_card_id: null` va `receiver_card_id` = to'ldirilgan karta bilan ko'rinadi.

---

## 8. P2P o'tkazma

### POST `/p2p/transfer`

O'z kartangizdan boshqa kartaga pul o'tkazadi. Auth kerak.

**Body**

| Maydon | Tur | Qoida |
|---|---|---|
| `sender_card_id` | UUID | O'zingizning kartangizning **ID** si (karta raqami emas) |
| `receiver_card_number` | integer | Qabul qiluvchining 16 xonali karta raqami |
| `amount` | decimal | `> 0` |
| `description` | string, ixtiyoriy | max 255. Berilmasa `P2P o'tkazma` yoziladi |

```json
{
  "sender_card_id": "3f2b8c1e-5a47-4d0e-9b61-0c2a7e8d1f33",
  "receiver_card_number": 1008987654321098,
  "amount": 50000,
  "description": "Tushlik uchun"
}
```

**Kutilgan javob - 201 Created**

```json
{
  "message": "O'tkazma muvaffaqiyatli amalga oshirildi",
  "transaction_id": "a91d6f0a-2b4c-4e8f-8f6e-5d1b9c7e4a20",
  "amount": 50000.0
}
```

**Xatolar**

| Kod | detail |
|---|---|
| 404 | `Yuboruvchi kartasi topilmadi` |
| 400 | `Sizning kartangiz muzlatilgan` |
| 400 | `O'z kartangizga pul o'tkaza olmaysiz` |
| 400 | `Kartada mablag' yetarli emas` |
| 404 | `Qabul qiluvchi karta raqami topilmadi` |
| 400 | `Qabul qiluvchi karta muzlatilgan` |

> **Diqqat:** hozirgi kodda bu endpoint push-xabar yuborish qismida xato beradi (qarang: [15-bo'lim](#15-malum-muammolar-va-eslatmalar), 1-band). Pul o'tkazmasi bazaga yoziladi, lekin javob `500` bo'lib qolishi mumkin.

---

## 9. Kommunal to'lovlar

### POST `/communal/pay`

Karta balansidan kommunal xizmat uchun pul yechadi, tranzaksiya va to'lov tarixini yozadi. Auth kerak.

**Body**

| Maydon | Tur | Qoida |
|---|---|---|
| `card_id` | UUID | O'zingizning kartangiz ID si |
| `service_type` | enum | `electricity`, `gas`, `water`, `heating`, `trash`, `hoa` |
| `provider_name` | string | max 150, masalan `Hududgaz` |
| `account_number` | string | max 50, shaxsiy hisob raqami (LS) |
| `amount` | decimal | `> 0` |

```json
{
  "card_id": "3f2b8c1e-5a47-4d0e-9b61-0c2a7e8d1f33",
  "service_type": "gas",
  "provider_name": "Hududgaz",
  "account_number": "1234567890",
  "amount": 85000
}
```

**201 Created**

```json
{
  "id": "5c0e2a77-91b3-4a6d-8c15-7f3e0d9b2a41",
  "user_id": 1,
  "card_id": "3f2b8c1e-5a47-4d0e-9b61-0c2a7e8d1f33",
  "transaction_id": "a91d6f0a-2b4c-4e8f-8f6e-5d1b9c7e4a20",
  "service_type": "gas",
  "provider_name": "Hududgaz",
  "account_number": "1234567890",
  "amount": "85000.00",
  "status": "success",
  "created_at": "2026-11-20T10:20:00.000000+00:00"
}
```

**Xatolar**

| Kod | detail |
|---|---|
| 404 | `Karta topilmadi` (mavjud emas yoki sizniki emas) |
| 400 | `Karta muzlatilgan` |
| 400 | `Kartada mablag' yetarli emas` |

> To'lov tashqi provayderga yuborilmaydi: hozircha faqat ichki balans va tarix yangilanadi, status darhol `success` bo'ladi.

### GET `/communal/history`

Foydalanuvchining barcha kommunal to'lovlari, **eng yangisi birinchi**. Element formati yuqoridagi `201` javob bilan bir xil. To'lov yo'q bo'lsa `[]`.

---

## 10. Mobil aloqa / internet to'lovi

### POST `/telecom/pay`

Karta balansidan mobil aloqa yoki internet uchun to'laydi. Auth kerak.

**Body**

| Maydon | Tur | Qoida |
|---|---|---|
| `card_id` | UUID | O'zingizning kartangiz ID si |
| `provider` | enum | `beeline`, `uzmobile`, `ucell`, `mobiuz`, `uztelecom_internet` |
| `recipient_phone` | string | max 20, masalan `+998901234567` (format tekshirilmaydi) |
| `amount` | decimal | `> 0` |

```json
{
  "card_id": "3f2b8c1e-5a47-4d0e-9b61-0c2a7e8d1f33",
  "provider": "ucell",
  "recipient_phone": "+998931234567",
  "amount": 20000
}
```

**201 Created**

```json
{
  "message": "To'lov muvaffaqiyatli amalga oshirildi",
  "transaction_id": "b27e1c44-6d8a-4f10-a5b3-9e0c3d7a1f55"
}
```

**Xatolar:** `404 Karta topilmadi`, `400 Karta muzlatilgan`, `400 Kartada mablag' yetarli emas`.

---

## 11. Tranzaksiyalar tarixi

### GET `/transactions/`

Foydalanuvchining barcha kartalari qatnashgan tranzaksiyalar (yuborilgan **va** qabul qilingan), eng yangisi birinchi. Karta yo'q bo'lsa `[]`. Auth kerak.

**200 OK**

```json
[
  {
    "id": "a91d6f0a-2b4c-4e8f-8f6e-5d1b9c7e4a20",
    "sender_card_id": "3f2b8c1e-5a47-4d0e-9b61-0c2a7e8d1f33",
    "receiver_card_id": "7d4a9e12-0b36-4c58-b1f7-2e8c5a60d933",
    "amount": "50000.00",
    "currency": "UZS",
    "status": "success",
    "transaction_type": "p2p",
    "service_type": null,
    "provider": null,
    "recipient_phone": null,
    "description": "Tushlik uchun",
    "created_at": "2026-11-20T10:18:00.000000+00:00"
  }
]
```

Tranzaksiya turiga qarab maydonlar to'ladi:

| `transaction_type` | `receiver_card_id` | `service_type` | `provider` | `recipient_phone` |
|---|:---:|:---:|:---:|:---:|
| `p2p` | to'ladi | `null` | `null` | `null` |
| `communal` | `null` | to'ladi | `null` | `null` |
| `telecom` | `null` | `null` | to'ladi | to'ladi |
| `replenishment` | to'ladi | `null` | `null` | `null` |

`replenishment` tranzaksiyasida `sender_card_id` ham `null` bo'ladi.

`status` qiymatlari: `pending`, `success`, `failed` (hozirgi kodda faqat `success` yoziladi).

---

## 12. Bozor ma'lumotlari (valyuta, kripto, aksiya)

Barcha `/info/*` endpointlari **auth talab qilmaydi** va tashqi servislarga so'rov yuboradi (har biri 10 soniya timeout). Tashqi servis xato bersa `502` qaytadi.

### GET `/info/currencies`

USD, EUR va RUB kurslarini beradi (manba: `open.er-api.com`).

| Query | Tur | Default | Izoh |
|---|---|---|---|
| `base` | string (3 harf) | `USD` | Asosiy valyuta, masalan `USD` yoki `UZS`. Kichik harf ham qabul qilinadi |

```bash
curl "$BASE/info/currencies?base=UZS"
```

**200 OK**

```json
{
  "base": "UZS",
  "provider": "open.er-api.com",
  "rates": { "USD": 0.0000812, "EUR": 0.0000701, "RUB": 0.00652 }
}
```

`rates` da faqat manba qaytargan valyutalar bo'ladi. `base=USD` bo'lsa `USD: 1`.

**Xato:** `502` - `Valyuta API xatosi: ...`

### GET `/info/crypto`

BTC (Binance, `BTCUSDT` 24 soatlik ticker) va USDT (CoinGecko) bo'yicha ma'lumot beradi.

**200 OK**

```json
{
  "BTC": {
    "pair": "BTC/USDT",
    "price_usdt": 97000.5,
    "price_change_pct_24h": 1.25,
    "high_24h": 98000.0,
    "low_24h": 95500.0,
    "volume_24h_btc": 12345.67
  },
  "USDT": {
    "price_usd": 1.0,
    "price_change_pct_24h": 0.01,
    "volume_24h_usd": 50000000000.0
  }
}
```

`USDT` maydonlari CoinGecko javobida bo'lmasa `null` bo'lishi mumkin. BTC uchun Binance'ning `data-api.binance.vision` manzili ishlatiladi (`api.binance.com` ba'zi hududlarda `451` bilan bloklanishi mumkin, shuning uchun muqobil manzil ishlatilgan).

**Xato:** `502` - `Kripto API xatosi: ...` (CoinGecko bepul limiti oshib ketganda ham shu xato chiqishi mumkin).

### GET `/info/stocks`

Aksiyalar bo'yicha kunlik ma'lumot (manba: Finnhub).

| Query | Tur | Default | Izoh |
|---|---|---|---|
| `symbols` | string | `AAPL,MSFT,NVDA,GOOGL,TSLA` | Vergul bilan ajratilgan tikerlar |

**200 OK** (`FINNHUB_API_KEY` o'rnatilgan bo'lsa)

```json
{
  "provider": "finnhub.io",
  "stocks": {
    "AAPL": {
      "current_price": 230.1,
      "change": 1.2,
      "change_pct": 0.52,
      "high_of_day": 231.0,
      "low_of_day": 228.4,
      "prev_close": 228.9
    },
    "XXXX": { "error": "..." }
  }
}
```

Bitta tiker xato bersa, butun so'rov yiqilmaydi: o'sha tiker uchun `{"error": "..."}` qaytadi.

**`FINNHUB_API_KEY` o'rnatilmagan bo'lsa** ham `200` qaytadi, lekin ma'lumotsiz:

```json
{
  "note": "Real vaqt aksiyalar narxi uchun FINNHUB_API_KEY muhit o'zgaruvchisini o'rnating (bepul kalit finnhub.io dan olinadi).",
  "requested_symbols": ["AAPL", "MSFT"],
  "stocks": {}
}
```

Client `stocks` bo'sh ekanini tekshirishi kerak.

### GET `/info/market`

Uchala ma'lumotni bitta javobda beradi: `{"currencies": ..., "crypto": ..., "stocks": ...}`. Faqat `base` query parametrini qabul qiladi (default `USD`); `symbols` bu yerda berib bo'lmaydi, aksiyalar doim standart ro'yxat bilan olinadi. Uch so'rov parallel bajariladi, biri `502` bersa butun javob `502` bo'ladi.

---

## 13. Enum qiymatlari

| Enum | Qiymatlar |
|---|---|
| `UserRole` | `client`, `admin` |
| `CommunalTypes` | `electricity` (elektr), `gas` (gaz), `water` (suv), `heating` (isitish), `trash` (chiqindi), `hoa` (shirkat) |
| `TelecomProvider` | `beeline`, `uzmobile`, `ucell`, `mobiuz`, `uztelecom_internet` |
| `TransactionType` | `p2p`, `communal`, `telecom`, `replenishment` (hisobni to'ldirish, `POST /cards/topup`) |
| `device_type` | `ios`, `android`, `web` |

---

## 14. Tashqi servislar va muhit o'zgaruvchilari

| Servis | Nima uchun |
|---|---|
| Authenticator (`api.authenticator.devguard.uz`) | OTP SMS yuborish. Foydalanuvchi shu ilovani o'rnatgan bo'lishi kerak (`https://devguard.uz`) |
| Upstash Redis | Ro'yxatdan o'tish ma'lumoti va OTP ni 180 soniyaga saqlash |
| Expo Push (`exp.host`) | Push bildirishnomalar |
| open.er-api.com | Valyuta kurslari (`/info/currencies`) |
| Binance (`data-api.binance.vision`) | BTC/USDT ma'lumoti (`/info/crypto`) |
| CoinGecko | USDT ma'lumoti (`/info/crypto`) |
| Finnhub (`finnhub.io`) | Aksiyalar narxi (`/info/stocks`), kalit kerak |
| PostgreSQL | Asosiy ma'lumotlar bazasi (SSL majburiy) |

`.env` fayli kalitlari (qiymatlarni repoga qo'shmang; `.env.example` da hozircha faqat `SECRET_KEY`, `DATABASE_URL`, `ALGORITHM` va token muddatlari bor, qolganlarini qo'shib qo'yish kerak):

```
SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS, REFRESH_TOKEN_EXPIRE_DAYS
DATABASE_URL
UPSTASH_URL, UPSTASH_TOKEN
AUTHENTICATOR_SERVICE_ID, AUTHENTICATOR_SERVICE_TOKEN, AUTHENTICATOR_ACCESS_TOKEN
SMTP_APP_PASSWORD
FINNHUB_API_KEY   (ixtiyoriy; yo'q bo'lsa /info/stocks ma'lumotsiz javob beradi)
```

Ma'lumotlar bazasi migratsiyalari Alembic orqali: `alembic upgrade head`.

---

## 15. Ma'lum muammolar va eslatmalar

Hujjat kod asosida yozilgan. Quyidagilar kodni o'qish paytida topilgan, client yozayotganda yoki keyingi ishda e'tibor berish kerak:

1. **`POST /p2p/transfer` push-xabar qismida xato.** `api/p2p.py` da `BackgroundTasks` klassning o'zida chaqirilgan (`BackgroundTasks.add_task(...)`), endpoint parametri sifatida olinmagan. Bundan tashqari `user_id=transaction`, `P2PTransferCreate.amount` va `current_user.full_name` (modelda bunday maydon yo'q) noto'g'ri ishlatilgan. Natijada pul o'tkazmasi `commit` bo'ladi, lekin keyin xato chiqib, client `500` oladi. Tuzatish uchun: `background_tasks: BackgroundTasks` parametrini qo'shib, `user_id=receiver_card.user_id`, `transfer_in.amount` va `f"{current_user.first_name} {current_user.last_name}"` dan foydalanish kerak (qabul qiluvchi `user_id` ni `make_p2p_transfer` qaytarishi lozim).

2. **Karta `id` (UUID) hech bir endpointda qaytmaydi.** `CardResponse` faqat `card_number` ni beradi, lekin `/p2p/transfer`, `/communal/pay`, `/telecom/pay` esa `card_id` / `sender_card_id` (UUID) talab qiladi. `CardResponse` ga `id: uuid.UUID` qo'shish kerak.

3. **`POST /cards/topup` haqiqiy to'lov tizimiga ulanmagan.** Endpoint mavjud (qarang: 7-bo'lim), lekin istalgan foydalanuvchi o'z kartasiga istalgan summani to'g'ridan-to'g'ri qo'shishi mumkin, to'lov provayderi (Click/Payme/Uzcard) tekshiruvi yo'q. Production uchun to'lov tasdig'i (webhook) bilan almashtirish yoki endpointni yopish kerak.

4. **`GET /cards/search/{card_number}` ochiq (auth yo'q).** Istalgan kishi karta raqami bo'yicha egasining ism-familiyasini ko'ra oladi. Faqat shu ilova ichida kerak bo'lsa, `Depends(get_current_user)` qo'shish tavsiya etiladi.

5. **Ulanmagan router.** `api/notification.py` (`/notifications/register-token`, `/notifications/remove-token`) `main.py` ga `include_router` qilinmagan, shuning uchun **ishlamaydi**; u `/devices/*` ning eski nusxasi. Push token uchun faqat `/devices/*` ishlatiladi. (`api/currency.py` endi ulangan: `main.py` da `from api.currency import app as currency` va `include_router(currency)`; router o'zgaruvchisi `app` deb nomlangani qoldi, ishlashiga ta'sir qilmaydi.)

6. **Swagger UI da "Authorize" login uchun ishlamaydi.** `OAuth2PasswordBearer(tokenUrl="/auth/login")` form-data kutadi, lekin `/auth/login` JSON qabul qiladi. Himoyalangan endpointlarni `curl` yoki Postman bilan tekshiring.

7. **Xavfsizlik.** OTP urinishlari soni cheklanmagan (6 xonali kodni terib ko'rish mumkin). Qatorni bloklash (`SELECT ... FOR UPDATE`) faqat `POST /cards/topup` da bor; `/p2p/transfer`, `/communal/pay` va `/telecom/pay` da yo'q, shuning uchun bir vaqtdagi ikki so'rov balansdan ortiq yechishi mumkin.

8. **Karta ro'yxati.** `GET /cards/` har doim ro'yxat qaytaradi, kartasi yo'q foydalanuvchiga `404` emas, `[]` keladi.

9. **`/info/*` ochiq va keshlanmaydi.** Har so'rov tashqi API'larga boradi, shuning uchun CoinGecko/Finnhub bepul limitlariga tez yetib borish mumkin va Vercel'dagi 30 soniyalik limitga ta'sir qiladi. Kesh (masalan Redis'da 30-60 soniya) qo'shish tavsiya etiladi.