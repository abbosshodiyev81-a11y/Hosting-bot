# Telegram Bot Hosting Bot

Ushbu bot boshqa Telegram botlarni ishga tushirish va boshqarish uchun mo'ljallangan.

## Funksiyalar
- **Bot qo'shish**: Bot nomi, API tokeni va `.py` faylini yuklash orqali yangi bot qo'shish.
- **Boshqaruv**: Botlarni ishga tushirish (Start), to'xtatish (Stop) va o'chirish (Delete).
- **Loglar**: Botning terminaldagi chiqishlarini ko'rish.
- **Env Vars**: Bot uchun muhit o'zgaruvchilarini (Environment Variables) JSON formatida sozlash.
- **Requirements**: Agar bot papkasida `requirements.txt` bo'lsa, u avtomatik ravishda o'rnatiladi.

## O'rnatish va Ishga Tushirish

1. Kutubxonalarni o'rnating:
   ```bash
   pip install aiogram
   ```

2. Bot tokenini sozlang:
   `main.py` faylidagi `API_TOKEN` o'zgaruvchisiga o'z bot tokeningizni qo'ying yoki muhit o'zgaruvchisi sifatida eksport qiling:
   ```bash
   export HOSTING_BOT_TOKEN="Sizning_Tokeningiz"
   ```

3. Botni ishga tushiring:
   ```bash
   python main.py
   ```

## Loyiha Strukturasi
- `main.py`: Asosiy bot kodi va interfeysi.
- `manager.py`: Bot jarayonlarini (subprocesses) boshqarish.
- `database.py`: SQLite ma'lumotlar bazasi bilan ishlash.
- `hosted_bots/`: Yuklangan botlar saqlanadigan papka.

## Eslatma
Xavfsizlik nuqtai nazaridan, ushbu tizimni faqat ishonchli foydalanuvchilar uchun ishlating, chunki u ixtiyoriy Python kodlarini bajarish imkonini beradi.
