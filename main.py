import asyncio
import logging
import os
import shutil
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from manager import BotManager

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("HOSTING_BOT_TOKEN", "your_bot_token")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
db = Database()
manager = BotManager()

class AddBot(StatesGroup):
    waiting_for_name = State()
    waiting_for_token = State()
    waiting_for_python_file = State()
    waiting_for_extra_files_choice = State()
    waiting_for_extra_file = State()
    waiting_for_requirements_file = State()

class ManageEnv(StatesGroup):
    waiting_for_env_key = State()
    waiting_for_env_value = State()

class EditBot(StatesGroup):
    waiting_for_code = State()
    waiting_for_requirements = State()
    waiting_for_file_edit = State() # Fayl menejeri uchun yangi state

class AdminPanel(StatesGroup):
    waiting_for_password = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.username)
    await show_main_menu(message)

@dp.message(F.text == "enteradmin.panel")
async def admin_login_start(message: types.Message, state: FSMContext):
    await state.set_state(AdminPanel.waiting_for_password)
    await message.answer("Admin panel parolini kiriting:")

@dp.message(AdminPanel.waiting_for_password)
async def admin_login_process(message: types.Message, state: FSMContext):
    # Parolni bu yerda o'zgartirishingiz mumkin
    ADMIN_PASSWORD = "admin" 
    if message.text == ADMIN_PASSWORD:
        await state.clear()
        await show_admin_menu(message)
    else:
        await message.answer("❌ Parol noto'g'ri! Qayta urinib ko'ring yoki bekor qiling.")

async def show_admin_menu(message_or_callback):
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 Foydalanuvchilar", callback_data="admin_users")
    kb.button(text="🤖 Barcha Botlar", callback_data="admin_all_bots")
    kb.button(text="⬅️ Chiqish", callback_data="start_menu")
    kb.adjust(1)
    
    text = "🔐 Admin Panelga xush kelibsiz!"
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=kb.as_markup())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: types.CallbackQuery):
    # Database'dan barcha foydalanuvchilarni olish (Database klassiga yangi metod kerak)
    users = db.get_all_users()
    if not users:
        await callback.answer("Foydalanuvchilar yo'q.")
        return
    
    text = "👥 Foydalanuvchilar ro'yxati:\n\n"
    for u in users:
        username = u[2] if u[2] else "Noma'lum"
        text += f"ID: {u[1]} | User: @{username}\n"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Orqaga", callback_data="admin_menu")
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "admin_menu")
async def cb_admin_menu(callback: types.CallbackQuery):
    await show_admin_menu(callback)

@dp.callback_query(F.data == "admin_all_bots")
async def cb_admin_all_bots(callback: types.CallbackQuery):
    # Barcha botlarni olish (Database klassiga yangi metod kerak)
    bots = db.get_all_bots()
    if not bots:
        await callback.answer("Botlar yo'q.")
        return
    
    kb = InlineKeyboardBuilder()
    for b in bots:
        kb.button(text=f"🤖 {b[2]} (User: {b[1]})", callback_data=f"admin_manage_{b[0]}")
    kb.button(text="⬅️ Orqaga", callback_data="admin_menu")
    kb.adjust(1)
    
    await callback.message.edit_text("Barcha botlar:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("admin_manage_"))
async def cb_admin_manage_bot(callback: types.CallbackQuery):
    bot_id = int(callback.data.split("_")[2])
    bot_data = db.get_bot(bot_id)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📂 Fayllarni ko'rish", callback_data=f"files_{bot_id}") # Mavjud fayl menejerini ishlatamiz
    kb.button(text="⬅️ Orqaga", callback_data="admin_all_bots")
    kb.adjust(1)
    
    await callback.message.edit_text(
        f"🤖 Bot: {bot_data[2]}\n👤 Egasi ID: {bot_data[1]}\n📊 Status: {bot_data[4]}",
        reply_markup=kb.as_markup()
    )

async def show_main_menu(message_or_callback):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Bot qo'shish", callback_data="add_bot")
    kb.button(text="🤖 Mening botlarim", callback_data="my_bots")
    kb.adjust(1)
    
    text = "Salom! Bu Telegram bot hosting tizimi.\nBu yerda siz o'z botlaringizni ishga tushirishingiz va boshqarishingiz mumkin."
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=kb.as_markup())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "start_menu")
async def cb_start_menu(callback: types.CallbackQuery):
    await show_main_menu(callback)

@dp.callback_query(F.data == "add_bot")
async def cb_add_bot(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddBot.waiting_for_name)
    await callback.message.edit_text("Bot nomini kiriting:")

@dp.message(AddBot.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddBot.waiting_for_token)
    await message.answer("Bot API tokenini kiriting:")

@dp.message(AddBot.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    await state.update_data(token=message.text)
    await state.set_state(AddBot.waiting_for_python_file)
    await message.answer("Bot kodini (.py fayl) yuboring:")

@dp.message(AddBot.waiting_for_python_file, F.document)
async def process_python_file(message: types.Message, state: FSMContext):
    if not message.document.file_name.endswith('.py'):
        await message.answer("Iltimos, asosiy fayl sifatida faqat .py fayl yuboring!")
        return
    
    data = await state.get_data()
    safe_name = "".join([c for c in data['name'] if c.isalnum()]).lower()
    bot_dir = f"{message.from_user.id}_{safe_name}"
    full_path = os.path.join("hosted_bots", bot_dir)
    os.makedirs(full_path, exist_ok=True)
    
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, os.path.join(full_path, "main.py"))
    
    db.add_bot(message.from_user.id, data['name'], data['token'], bot_dir)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha", callback_data="extra_files_yes")
    kb.button(text="❌ Yo'q", callback_data="extra_files_no")
    kb.adjust(2)
    
    await state.set_state(AddBot.waiting_for_extra_files_choice)
    await message.answer(
        "Asosiy fayl yuklandi. Sizda qo'shimcha fayllar bormi? (.json, .db, .py va h.k.)",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(AddBot.waiting_for_extra_files_choice, F.data == "extra_files_yes")
async def cb_extra_files_yes(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddBot.waiting_for_extra_file)
    await callback.message.edit_text("Qo'shimcha faylni yuboring:")

@dp.callback_query(AddBot.waiting_for_extra_files_choice, F.data == "extra_files_no")
async def cb_extra_files_no(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddBot.waiting_for_requirements_file)
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭ O'tkazib yuborish", callback_data="skip_requirements")
    await callback.message.edit_text(
        "Endi kutubxonalar ro'yxatini (requirements.txt) yuborishingiz mumkin yoki o'tkazib yuboring:",
        reply_markup=kb.as_markup()
    )

@dp.message(AddBot.waiting_for_extra_file, F.document)
async def process_extra_file(message: types.Message, state: FSMContext):
    data = await state.get_data()
    safe_name = "".join([c for c in data['name'] if c.isalnum()]).lower()
    bot_dir = f"{message.from_user.id}_{safe_name}"
    full_path = os.path.join("hosted_bots", bot_dir)
    
    file_name = message.document.file_name
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, os.path.join(full_path, file_name))
    
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha", callback_data="extra_files_yes")
    kb.button(text="❌ Yo'q", callback_data="extra_files_no")
    kb.adjust(2)
    
    await state.set_state(AddBot.waiting_for_extra_files_choice)
    await message.answer(f"'{file_name}' yuklandi. Yana fayl bormi?", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "skip_requirements")
async def cb_skip_requirements(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("✅ Bot muvaffaqiyatli qo'shildi! Endi uni 'Mening botlarim' bo'limidan boshqarishingiz mumkin.")
    await show_main_menu(callback)

@dp.message(AddBot.waiting_for_requirements_file, F.document)
async def process_requirements_file(message: types.Message, state: FSMContext):
    data = await state.get_data()
    safe_name = "".join([c for c in data['name'] if c.isalnum()]).lower()
    bot_dir = f"{message.from_user.id}_{safe_name}"
    full_path = os.path.join("hosted_bots", bot_dir)
    
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, os.path.join(full_path, "requirements.txt"))
    
    await state.clear()
    await message.answer("✅ requirements.txt yuklandi va bot muvaffaqiyatli qo'shildi!")
    await show_main_menu(message)

@dp.callback_query(F.data == "my_bots")
async def cb_my_bots(callback: types.CallbackQuery):
    bots = db.get_user_bots(callback.from_user.id)
    if not bots:
        await callback.answer("Sizda hali botlar yo'q.", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    for b in bots:
        status_emoji = "🟢" if b[4] == "running" else "🔴"
        kb.button(text=f"{status_emoji} {b[2]}", callback_data=f"manage_{b[0]}")
    kb.button(text="⬅️ Orqaga", callback_data="start_menu")
    kb.adjust(1)
    
    await callback.message.edit_text("Sizning botlaringiz:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("manage_"))
async def cb_manage_bot(callback: types.CallbackQuery):
    bot_id = int(callback.data.split("_")[1])
    bot_data = db.get_bot(bot_id)
    
    if not bot_data:
        await callback.answer("Bot topilmadi")
        return

    kb = InlineKeyboardBuilder()
    if bot_data[4] == "running":
        kb.button(text="🛑 To'xtatish", callback_data=f"stop_{bot_id}")
    else:
        kb.button(text="▶️ Ishga tushirish", callback_data=f"start_{bot_id}")
    
    kb.button(text="📜 Loglar", callback_data=f"logs_{bot_id}")
    kb.button(text="⚙️ Env Vars", callback_data=f"env_list_{bot_id}")
    kb.button(text="📂 Fayl Menejeri", callback_data=f"files_{bot_id}")
    kb.button(text="⚙️ Env Vars", callback_data=f"env_list_{bot_id}")
    kb.button(text="🗑 O'chirish", callback_data=f"delete_{bot_id}")
    kb.button(text="⬅️ Orqaga", callback_data="my_bots")
    kb.adjust(2)
    
    status_text = "🟢 Ishlamoqda" if bot_data[4] == "running" else "🔴 To'xtatilgan"
    
    await callback.message.edit_text(
        f"🤖 Bot: {bot_data[2]}\n"
        f"📊 Status: {status_text}\n"
        f"🔑 Token: {bot_data[3][:10]}...\n"
        f"📁 Path: {bot_data[5]}",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data.startswith("start_"))
async def cb_start_bot(callback: types.CallbackQuery):
    bot_id = int(callback.data.split("_")[1])
    bot_data = db.get_bot(bot_id)
    
    env_vars = json.loads(bot_data[6]) if bot_data[6] else {}
    success, msg = manager.start_bot(bot_id, bot_data[5], bot_data[3], env_vars)
    
    if success:
        db.update_bot_status(bot_id, "running")
        await callback.answer(msg, show_alert=False)
        await cb_manage_bot(callback)
    else:
        await callback.answer(f"❌ {msg}", show_alert=True)

@dp.callback_query(F.data.startswith("stop_"))
async def cb_stop_bot(callback: types.CallbackQuery):
    bot_id = int(callback.data.split("_")[1])
    success, msg = manager.stop_bot(bot_id)
    if success:
        db.update_bot_status(bot_id, "stopped")
        await callback.answer(msg, show_alert=False)
        await cb_manage_bot(callback)
    else:
        await callback.answer(f"❌ {msg}", show_alert=True)

@dp.callback_query(F.data.startswith("logs_"))
async def cb_view_logs(callback: types.CallbackQuery):
    bot_id = int(callback.data.split("_")[1])
    bot_data = db.get_bot(bot_id)
    logs = manager.get_logs(bot_data[5])
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Yangilash", callback_data=f"logs_{bot_id}")
    kb.button(text="⬅️ Orqaga", callback_data=f"manage_{bot_id}")
    kb.adjust(2)
    
    # Loglarni formatlash
    if len(logs) > 4000:
        logs = logs[-4000:]
    
    # Backticks larni almashtirish
    logs = logs.replace('`', "'")
    
    await callback.message.edit_text(
        f"📜 Bot: {bot_data[2]}\n\n"
        f"Loglar:\n"
        f"{logs}",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data.startswith("env_list_"))
async def cb_env_list(callback: types.CallbackQuery):
    bot_id = int(callback.data.split("_")[2])
    bot_data = db.get_bot(bot_id)
    env_vars = json.loads(bot_data[6]) if bot_data[6] else {}
    
    kb = InlineKeyboardBuilder()
    for key, value in env_vars.items():
        kb.button(text=f"❌ {key}", callback_data=f"env_del_{bot_id}_{key}")
    
    if len(env_vars) < 5:
        kb.button(text="➕ Yangi qo'shish", callback_data=f"env_add_{bot_id}")
    
    kb.button(text="⬅️ Orqaga", callback_data=f"manage_{bot_id}")
    kb.adjust(1)
    
    env_text = "\n".join([f"<code>{k}</code> = <code>{v}</code>" for k, v in env_vars.items()]) or "Hali o'zgaruvchilar yo'q."
    
    await callback.message.edit_text(
        f"⚙️ Bot: {bot_data[2]}\n\n"
        f"Environment Variables (maks 5 ta):\n\n{env_text}",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("env_add_"))
async def cb_env_add(callback: types.CallbackQuery, state: FSMContext):
    bot_id = int(callback.data.split("_")[2])
    await state.update_data(bot_id=bot_id)
    await state.set_state(ManageEnv.waiting_for_env_key)
    await callback.message.edit_text("O'zgaruvchi nomini (KEY) kiriting:")

@dp.message(ManageEnv.waiting_for_env_key)
async def process_env_key(message: types.Message, state: FSMContext):
    await state.update_data(env_key=message.text)
    await state.set_state(ManageEnv.waiting_for_env_value)
    await message.answer(f"'{message.text}' uchun qiymatni (VALUE) kiriting:")

@dp.message(ManageEnv.waiting_for_env_value)
async def process_env_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data['bot_id']
    key = data['env_key']
    value = message.text
    
    bot_data = db.get_bot(bot_id)
    env_vars = json.loads(bot_data[6]) if bot_data[6] else {}
    
    if len(env_vars) >= 5:
        await message.answer("❌ Maksimal 5 ta o'zgaruvchi qo'shish mumkin!")
    else:
        env_vars[key] = value
        db.update_env_vars(bot_id, env_vars)
        await message.answer(f"✅ '{key}'='{value}' qo'shildi!")
    
    await state.clear()
    # Qayta ro'yxatni ko'rsatish uchun fake callback yaratamiz
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.data = f"env_list_{bot_id}"
    await cb_env_list(FakeCallback(message))

@dp.callback_query(F.data.startswith("env_del_"))
async def cb_env_del(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    bot_id = int(parts[2])
    key_to_del = parts[3]
    
    bot_data = db.get_bot(bot_id)
    env_vars = json.loads(bot_data[6]) if bot_data[6] else {}
    
    if key_to_del in env_vars:
        del env_vars[key_to_del]
        db.update_env_vars(bot_id, env_vars)
        await callback.answer(f"'{key_to_del}' o'chirildi")
    
    await cb_env_list(callback)

@dp.callback_query(F.data.startswith("files_"))
async def cb_file_manager(callback: types.CallbackQuery):
    bot_id = int(callback.data.split("_")[1])
    bot_data = db.get_bot(bot_id)
    bot_path = os.path.join("hosted_bots", bot_data[5])
    
    files = [f for f in os.listdir(bot_path) if os.path.isfile(os.path.join(bot_path, f))]
    
    kb = InlineKeyboardBuilder()
    for f in files:
        # Log faylini tahrirlash shart emas
        if f == "bot.log": continue
        kb.button(text=f"📄 {f}", callback_data=f"fedit_{bot_id}_{f}")
    
    kb.button(text="➕ Fayl qo'shish", callback_data=f"fadd_{bot_id}")
    kb.button(text="⬅️ Orqaga", callback_data=f"manage_{bot_id}")
    kb.adjust(1)
    
    await callback.message.edit_text(
        f"📂 Bot: {bot_data[2]}\nFayllar ro'yxati (tahrirlash uchun tanlang):",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data.startswith("fedit_"))
async def cb_file_edit_start(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    bot_id = int(parts[1])
    filename = parts[2]
    bot_data = db.get_bot(bot_id)
    file_path = os.path.join("hosted_bots", bot_data[5], filename)
    
    # Matnli fayllarni tekshirish
    text_exts = ['.py', '.txt', '.json', '.html', '.css', '.js', '.md']
    is_text = any(filename.endswith(ext) for ext in text_exts)
    
    if not is_text:
        await callback.answer("Bu fayl turini tahrirlab bo'lmaydi (faqat matnli fayllar).", show_alert=True)
        return

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    await state.update_data(bot_id=bot_id, filename=filename)
    await state.set_state(EditBot.waiting_for_file_edit)
    
    preview = content[:3000] + ("\n..." if len(content) > 3000 else "")
    
    await callback.message.edit_text(
        f"📝 Fayl: {filename}\n\n<pre>{preview}</pre>\n\nYangi tarkibni yuboring:",
        parse_mode="HTML"
    )

@dp.message(EditBot.waiting_for_file_edit)
async def process_file_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data['bot_id']
    filename = data['filename']
    bot_data = db.get_bot(bot_id)
    file_path = os.path.join("hosted_bots", bot_data[5], filename)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(message.text)
        await message.answer(f"✅ '{filename}' muvaffaqiyatli yangilandi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
    
    await state.clear()
    await show_main_menu(message)

@dp.callback_query(F.data.startswith("fadd_"))
async def cb_file_add_start(callback: types.CallbackQuery, state: FSMContext):
    bot_id = int(callback.data.split("_")[1])
    await state.update_data(bot_id=bot_id)
    await state.set_state(AddBot.waiting_for_extra_file) # Reusing state
    await callback.message.edit_text("Yangi faylni yuboring:")

@dp.message(EditBot.waiting_for_code)
async def process_edit_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data['bot_id']
    bot_data = db.get_bot(bot_id)
    
    main_file = os.path.join("hosted_bots", bot_data[5], "main.py")
    
    try:
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(message.text)
        
        await message.answer("✅ Kod muvaffaqiyatli yangilandi! Botni qayta ishga tushirishni unutmang.")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
    
    await state.clear()
    await show_main_menu(message)

@dp.callback_query(F.data.startswith("edit_req_"))
async def cb_edit_req(callback: types.CallbackQuery, state: FSMContext):
    bot_id = int(callback.data.split("_")[2])
    bot_data = db.get_bot(bot_id)
    
    req_file = os.path.join("hosted_bots", bot_data[5], "requirements.txt")
    content = ""
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            content = f.read()
    
    await state.update_data(bot_id=bot_id)
    await state.set_state(EditBot.waiting_for_requirements)
    
    req_preview = content if content else "Bo'sh"
    await callback.message.edit_text(
        f"📦 Bot: {bot_data[2]}\n\n"
        f"Hozirgi requirements.txt:\n<pre>{req_preview}</pre>\n\n"
        "Yangi kutubxonalar ro'yxatini yuboring (har bir qatorda bittadan):",
        parse_mode="HTML"
    )

@dp.message(EditBot.waiting_for_requirements)
async def process_edit_req(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data['bot_id']
    bot_data = db.get_bot(bot_id)
    
    req_file = os.path.join("hosted_bots", bot_data[5], "requirements.txt")
    
    try:
        with open(req_file, 'w', encoding='utf-8') as f:
            f.write(message.text)
        
        await message.answer("✅ requirements.txt muvaffaqiyatli yangilandi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
    
    await state.clear()
    await show_main_menu(message)

@dp.callback_query(F.data.startswith("delete_"))
async def cb_delete_bot(callback: types.CallbackQuery):
    bot_id = int(callback.data.split("_")[1])
    bot_data = db.get_bot(bot_id)
    
    # Avval to'xtatamiz
    manager.stop_bot(bot_id)
    
    # Fayllarni o'chiramiz
    full_path = os.path.join("hosted_bots", bot_data[5])
    if os.path.exists(full_path):
        shutil.rmtree(full_path)
    
    # DB dan o'chiramiz
    db.delete_bot(bot_id)
    
    await callback.answer("✅ Bot o'chirildi")
    await cb_my_bots(callback)

async def main():
    print("--- Hosting Bot ishga tushmoqda... ---")
    
    # hosted_bots papkasini yaratish
    if not os.path.exists("hosted_bots"):
        os.makedirs("hosted_bots")
        print("📁 hosted_bots papkasi yaratildi")
    
    # Ma'lumotlar bazasini tekshirish
    print("📊 Ma'lumotlar bazasi yuklandi")
    
    bot_info = await bot.get_me()
    print(f"--- Bot muvaffaqiyatli ulandi: @{bot_info.username} ---")
    print(f"--- Bot ID: {bot_info.id} ---")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🤖 TELEGRAM BOT HOSTING TIZIMI")
        print("=" * 50)
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot to'xtatildi")
    except Exception as e:
        logging.error(f"Xatolik: {e}")  logging.error(f"Xatolik: {e}")