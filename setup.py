import subprocess
import sys
import os

def install_requirements():
    print("--- Hosting Botni sozlash boshlandi ---")
    
    # Asosiy kutubxonalar
    requirements = [
        "aiogram",
        "pyTelegramBotAPI",
        "requests"
    ]
    
    print(f"Kutubxonalar o'rnatilmoqda: {', '.join(requirements)}")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install"] + requirements, check=True)
        print("✅ Barcha kutubxonalar muvaffaqiyatli o'rnatildi.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        sys.exit(1)

    # Papkalarni yaratish
    if not os.path.exists("hosted_bots"):
        os.makedirs("hosted_bots")
        print("📁 'hosted_bots' papkasi yaratildi.")

    print("\n--- Sozlash yakunlandi ---")
    print("Botni ishga tushirish uchun: python main.py")

if __name__ == "__main__":
    install_requirements()
