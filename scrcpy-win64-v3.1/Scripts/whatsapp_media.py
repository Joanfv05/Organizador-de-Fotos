import subprocess
import re
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).parent.parent  
ADB_PATH = BASE_DIR / "adb.exe"
LOCAL_WA_DIR = "WhatsApp Media"
MEDIA_EXTENSIONS = [".jpg", ".jpeg", ".png", ".mp4", ".mov", ".heic", ".avi", ".3gp"]

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

WA_PATHS = [
    "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Images",
    "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Video"
]


def run_command(command):
    try:
        return subprocess.check_output(command, shell=True, text=True).strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


def check_device():
    print("🔍 Buscando dispositivo...")
    result = run_command(f"{ADB_PATH} devices")
    print(result)
    return "device" in result and "unauthorized" not in result


def copy_whatsapp_media():
    if not check_device():
        print("❌ Dispositivo no disponible.")
        return

    Path(LOCAL_WA_DIR).mkdir(parents=True, exist_ok=True)

    for remote in WA_PATHS:
        print(f"📥 Copiando desde {remote}...")
        result = run_command(f'{ADB_PATH} pull "{remote}" "{LOCAL_WA_DIR}"')
        print(result)


def organize_whatsapp_media():
    source = Path(LOCAL_WA_DIR)
    if not source.exists():
        print("❌ No existe la carpeta de WhatsApp.")
        return

    files = []
    for ext in MEDIA_EXTENSIONS:
        files.extend(source.rglob(f"*{ext}"))

    total = 0
    for file in files:
        if file.name.startswith(".trashed-"):
            continue

        match = re.search(r'(?:IMG|VID)-(\d{4})(\d{2})(\d{2})-WA', file.stem)
        if match:
            year, month, _ = match.groups()
            month = int(month)
            dest = source / year / f"{month:02d}-{MESES_ES[month]}"
        else:
            dest = source / "SinFecha"

        dest.mkdir(parents=True, exist_ok=True)
        new_path = dest / file.name

        if new_path.exists():
            base, ext = file.stem, file.suffix
            i = 1
            while new_path.exists():
                new_path = dest / f"{base}_{i}{ext}"
                i += 1

        shutil.move(str(file), new_path)
        total += 1

    print(f"✅ {total} archivos de WhatsApp organizados.")


def menu():
    while True:
        print("\n--- WHATSAPP MEDIA ---")
        print("1. Copiar fotos y vídeos de WhatsApp")
        print("2. Organizar WhatsApp por AÑO y MES")
        print("3. Copiar + organizar (todo)")
        print("4. Salir")

        choice = input("Selecciona una opción: ")

        if choice == "1":
            copy_whatsapp_media()
        elif choice == "2":
            organize_whatsapp_media()
        elif choice == "3":
            copy_whatsapp_media()
            organize_whatsapp_media()
        elif choice == "4":
            break
        else:
            print("❌ Opción inválida.")


if __name__ == "__main__":
    menu()
