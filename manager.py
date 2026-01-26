import subprocess
import os
import signal
import logging
import sys
import time
from dependency_detector import detect_dependencies

class BotManager:
    def __init__(self, base_path="hosted_bots"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        self.processes = {}  # bot_id: process_object

    def clean_python_file(self, file_path):
        """Python faylini requirements.txt dan tozalaydi"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Python kodini topish
            python_lines = []
            requirements_lines = []
            in_python_code = False
            
            for line in lines:
                # Python kodini topish
                if line.strip().startswith(('import ', 'from ', 'def ', 'class ', '#', 'if __name__', 'async def')):
                    in_python_code = True
                
                if in_python_code:
                    python_lines.append(line)
                elif '==' in line and not line.strip().startswith('#'):
                    requirements_lines.append(line.strip())
            
            # Agar requirements.txt satrlari topilsa
            if requirements_lines:
                req_dir = os.path.dirname(file_path)
                req_file = os.path.join(req_dir, 'requirements.txt')
                
                # requirements.txt mavjud bo'lsa, uni yangilash
                if os.path.exists(req_file):
                    with open(req_file, 'a', encoding='utf-8') as f:
                        f.write('\n' + '\n'.join(requirements_lines))
                else:
                    with open(req_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(requirements_lines))
                
                logging.info(f"Requirements.txt yangilandi: {req_file}")
            
            # Python kodini qayta yozish
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(''.join(python_lines))
            
            return True
        except Exception as e:
            logging.error(f"Faylni tozalashda xatolik: {e}")
            return False

    def fix_file_encoding(self, file_path):
        """Fayl encoding'ini UTF-8 ga o'zgartiradi va BOM ni olib tashlaydi"""
        try:
            with open(file_path, 'rb') as f:
                raw_content = f.read()
            
            # BOM belgisini olib tashlash
            bom_removed = False
            for bom in [b'\xef\xbb\xbf', b'\xfe\xff', b'\xff\xfe']:
                if raw_content.startswith(bom):
                    raw_content = raw_content[len(bom):]
                    bom_removed = True
                    logging.info(f"BOM removed from {file_path}")
                    break
            
            encodings_to_try = ['utf-8', 'cp1251', 'iso-8859-1', 'windows-1251']
            
            for encoding in encodings_to_try:
                try:
                    decoded_content = raw_content.decode(encoding)
                    
                    # Faylni UTF-8 bilan qayta yozish
                    with open(file_path, 'w', encoding='utf-8') as f:
                        # Encoding deklaratsiyasini qo'shamiz
                        f.write('# -*- coding: utf-8 -*-\n')
                        f.write(decoded_content)
                    
                    return True
                except UnicodeDecodeError:
                    continue
            
            # Agar encoding topilmasa, oddiy bot kodi yozamiz
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('# -*- coding: utf-8 -*-\n')
                f.write('import os\n')
                f.write('import telebot\n\n')
                f.write('TOKEN = "TOKEN_BERILMAGAN"\n')
                f.write('bot = telebot.TeleBot(TOKEN)\n\n')
                f.write('@bot.message_handler(commands=[\'start\'])\n')
                f.write('def send_welcome(message):\n')
                f.write('    bot.reply_to(message, "Bot ishga tushdi!")\n\n')
                f.write('if __name__ == "__main__":\n')
                f.write('    print("Bot ishga tushdi!")\n')
                f.write('    try:\n')
                f.write('        bot.polling()\n')
                f.write('    except Exception as e:\n')
                f.write('        print(f"Xatolik: {e}")\n')
            
            return True
            
        except Exception as e:
            logging.error(f"Encoding tuzatishda xatolik: {e}")
            return False

    def start_bot(self, bot_id, bot_path, token, env_vars=None):
        if bot_id in self.processes:
            return False, "Bot allaqachon ishlayapti"

        full_path = os.path.join(self.base_path, bot_path)
        main_file = os.path.join(full_path, "main.py")
        
        # Agar main.py bo'lmasa, birinchi uchragan .py faylni main deb olamiz
        if not os.path.exists(main_file):
            py_files = [f for f in os.listdir(full_path) if f.endswith('.py')]
            if py_files:
                main_file = os.path.join(full_path, py_files[0])
            else:
                return False, "Hech qanday .py fayl topilmadi"

        # 1. Avval BOM ni olib tashlash
        try:
            with open(main_file, 'rb') as f:
                content = f.read()
            
            # BOM belgisini olib tashlash
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]
                with open(main_file, 'wb') as f:
                    f.write(content)
                logging.info(f"BOM olib tashlandi: {main_file}")
        except Exception as e:
            logging.error(f"BOM olib tashlashda xatolik: {e}")

        # 2. Fayl encoding va tozalash
        self.fix_file_encoding(main_file)
        self.clean_python_file(main_file)

        # 3. Tokenni fayl ichiga yozish
        try:
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Token qatori topish va almashtirish
            lines = content.split('\n')
            new_lines = []
            token_written = False
            
            for line in lines:
                if line.strip().startswith('TOKEN') and ('=' in line) and ('telebot' not in line):
                    # Token qatorini yangilash
                    new_line = f'TOKEN = "{token}"'
                    new_lines.append(new_line)
                    token_written = True
                elif 'TOKEN = os.getenv' in line:
                    # Environment tokenni to'g'ridan tokenga almashtirish
                    new_line = f'TOKEN = "{token}"'
                    new_lines.append(new_line)
                    token_written = True
                elif line.strip().startswith('import telebot'):
                    # telebot importidan keyin token qatorini qo'shish
                    new_lines.append(line)
                    if not token_written:
                        new_lines.append('')
                        new_lines.append(f'TOKEN = "{token}"')
                        token_written = True
                else:
                    new_lines.append(line)
            
            # Agar token yozilmagan bo'lsa, fayl oxiriga qo'shamiz
            if not token_written:
                # Import qismini topamiz
                for i, line in enumerate(new_lines):
                    if line.strip().startswith('import telebot'):
                        # telebot importidan keyin token qatorini qo'shamiz
                        new_lines.insert(i + 1, '')
                        new_lines.insert(i + 2, f'TOKEN = "{token}"')
                        break
            
            # Faylni qayta yozish
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
                
            logging.info(f"Token faylga yozildi: {main_file}")
            
        except Exception as e:
            logging.error(f"Token yozishda xatolik: {e}")

        # 4. Environment variables
        env = os.environ.copy()
        env["BOT_TOKEN"] = token
        if env_vars:
            env.update(env_vars)

        log_file_path = os.path.join(full_path, "bot.log")
        log_file = open(log_file_path, "a", encoding="utf-8")
        
        # 5. Avtomatik dependency tahlili va requirements.txt ni yangilash
        log_file.write("🔍 Bot kodi tahlil qilinmoqda va kerakli kutubxonalar aniqlanmoqda...\n")
        log_file.flush()
        try:
            detected_deps = detect_dependencies(full_path)
            req_file = os.path.join(full_path, "requirements.txt")
            
            # Mavjud requirements.txt ni o'qish
            existing_deps = set()
            if os.path.exists(req_file):
                with open(req_file, "r", encoding="utf-8") as f:
                    for line in f:
                        dep = line.strip()
                        if dep and not dep.startswith("#"):
                            # Versiyani olib tashlab faqat nomini saqlaymiz (taqqoslash uchun)
                            dep_name = dep.split("==")[0].split(">=")[0].split("<=")[0].strip()
                            existing_deps.add(dep_name.lower())
            
            # Yangi aniqlanganlarni qo'shish (agar mavjud bo'lmasa)
            new_deps_to_add = []
            for dep in detected_deps:
                if dep.lower() not in existing_deps:
                    new_deps_to_add.append(dep)
            
            if new_deps_to_add:
                log_file.write(f"📦 Yangi aniqlangan kutubxonalar qo'shilmoqda: {', '.join(new_deps_to_add)}\n")
                with open(req_file, "a", encoding="utf-8") as f:
                    if not os.path.exists(req_file) or os.path.getsize(req_file) == 0:
                        pass # Fayl bo'sh bo'lsa hech narsa qilmaymiz
                    else:
                        f.write("\n") # Yangi qatordan boshlash
                    for dep in new_deps_to_add:
                        f.write(f"{dep}\n")
            else:
                log_file.write("ℹ️ Barcha kerakli kutubxonalar requirements.txt da mavjud.\n")
        except Exception as e:
            log_file.write(f"⚠️ Tahlil jarayonida xatolik: {e}\n")
        log_file.flush()

        # 6. Kutubxonalarni o'rnatish
        try:
            log_file.write("📥 Kutubxonalar o'rnatilmoqda...\n")
            log_file.flush()
            
            req_file = os.path.join(full_path, "requirements.txt")
            if os.path.exists(req_file):
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", req_file],
                    capture_output=True,
                    text=True,
                    timeout=180,
                    cwd=full_path
                )
                if result.returncode == 0:
                    log_file.write("✅ Barcha kutubxonalar muvaffaqiyatli o'rnatildi.\n")
                else:
                    log_file.write(f"⚠️ Ba'zi kutubxonalarni o'rnatishda xatolik: {result.stderr}\n")
            else:
                log_file.write("ℹ️ requirements.txt topilmadi, o'rnatish o'tkazib yuborildi.\n")
        except Exception as e:
            log_file.write(f"❌ O'rnatishda xatolik: {e}\n")
        log_file.flush()
        
        # 7. Botni ishga tushirish
        python_cmd = sys.executable
        
        popen_kwargs = {
            "args": [python_cmd, "-u", "main.py"],
            "env": env,
            "stdout": log_file,
            "stderr": subprocess.STDOUT,
            "cwd": full_path,
            "text": True,
            "encoding": "utf-8",
        }

        if os.name != 'nt':  # Linux/Unix
            popen_kwargs["preexec_fn"] = os.setsid
        else:  # Windows
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            log_file.write(f"🚀 Bot ishga tushmoqda: {python_cmd} -u main.py\n")
            log_file.write(f"📂 Working directory: {full_path}\n")
            log_file.write(f"🔑 Token uzunligi: {len(token)}\n")
            log_file.flush()
            
            process = subprocess.Popen(**popen_kwargs)
            self.processes[bot_id] = process
            
            # Bir oz kutish
            time.sleep(5)
            
            # Bot ishlayotganini tekshirish
            if process.poll() is not None:
                # Loglarni o'qish
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    error_log = f.read()
                return False, "Bot o'chib qoldi. Loglarni tekshiring."
            
            return True, "✅ Bot muvaffaqiyatli ishga tushdi!"
            
        except Exception as e:
            error_msg = f"❌ Xatolik: {str(e)}"
            log_file.write(f"{error_msg}\n")
            log_file.close()
            return False, error_msg

    def stop_bot(self, bot_id):
        if bot_id not in self.processes:
            return False, "Bot ishlamayapti"

        process = self.processes[bot_id]
        try:
            if os.name != 'nt':  # Linux/Unix
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:  # Windows
                process.terminate()
                process.wait(timeout=5)
            
            del self.processes[bot_id]
            return True, "✅ Bot to'xtatildi"
        except Exception as e:
            # Force kill if normal terminate fails
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
                del self.processes[bot_id]
                return True, "⚠️ Bot majburan to'xtatildi"
            except Exception as e2:
                return False, f"❌ To'xtatishda xatolik: {str(e2)}"

    def get_logs(self, bot_path, lines=20):
        log_path = os.path.join(self.base_path, bot_path, "bot.log")
        if not os.path.exists(log_path):
            return "📭 Loglar topilmadi"
        
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.readlines()
                if len(content) == 0:
                    return "📭 Loglar bo'sh"
                
                result = "".join(content[-lines:])
                if len(result) > 4000:  # Telegram xabar chegarasi
                    result = "..." + result[-4000:]
                return result
        except Exception as e:
            return f"❌ Loglarni o'qishda xatolik: {str(e)}"