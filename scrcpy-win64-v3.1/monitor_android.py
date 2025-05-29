import subprocess
import os
import re
from datetime import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import shutil

ADB_PATH = "adb.exe"
SCRCPY_PATH = "scrcpy.exe"
LOCAL_BACKUP_DIR = "Fotos Camara"

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

def run_command(command):
    try:
        result = subprocess.check_output(command, shell=True, text=True)
        return result.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

def check_device():
    print("🔍 Buscando dispositivos conectados...")
    result = run_command(f"{ADB_PATH} devices")
    print(result)
    if "device" in result and not "unauthorized" in result:
        print("✅ Dispositivo conectado.")
        return True
    elif "unauthorized" in result:
        print("⚠️ Autoriza la conexión en tu móvil.")
    else:
        print("❌ No se detectó ningún dispositivo.")
    return False

def start_scrcpy():
    print("🚀 Iniciando scrcpy...")
    os.system(SCRCPY_PATH)

def get_image_date(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                decoded_tag = TAGS.get(tag, tag)
                if decoded_tag == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None

def get_video_date(file):
    # Intenta extraer la fecha del nombre del archivo, ej: VID_20250528_134740.mp4
    match = re.search(r'(\d{8})_(\d{6})', file.stem)
    if match:
        date_str = match.group(1) + match.group(2)
        try:
            return datetime.strptime(date_str, "%Y%m%d%H%M%S")
        except Exception:
            pass
    # Si falla, usa la fecha de modificación
    return datetime.fromtimestamp(file.stat().st_mtime)

def detect_sdcard_path():
    # Busca un directorio tipo XXXX-XXXX en /storage
    output = run_command(f"{ADB_PATH} shell ls /storage")
    for line in output.splitlines():
        if "-" in line and len(line) == 9:  # Formato típico de SD externa
            # Verifica que exista DCIM/Camera dentro
            test = run_command(f'{ADB_PATH} shell ls "/storage/{line}/DCIM/Camera"')
            if "No such file or directory" not in test:
                return f"/storage/{line}/DCIM/Camera"
    return None

def copy_and_organize_media():
    if not check_device():
        return

    # Detectar ruta real de la SD externa
    sd_camera_path = detect_sdcard_path()
    if not sd_camera_path:
        print("❌ No se encontró la carpeta DCIM/Camera en la SD externa.")
        return

    # Crear la carpeta de destino si no existe
    Path(LOCAL_BACKUP_DIR).mkdir(parents=True, exist_ok=True)

    print(f"📥 Copiando archivos desde {sd_camera_path} a '{LOCAL_BACKUP_DIR}'...")
    result = run_command(f'{ADB_PATH} pull "{sd_camera_path}" "{LOCAL_BACKUP_DIR}"')
    print("Resultado adb pull:", result)

    source = Path(LOCAL_BACKUP_DIR)
    if not source.exists():
        print(f"❌ No se pudo encontrar la carpeta local '{LOCAL_BACKUP_DIR}'.")
        return

    media_extensions = [".jpg", ".jpeg", ".png", ".mp4", ".mov"]
    files_to_move = []
    for ext in media_extensions:
        files_to_move.extend(source.rglob(f"*{ext}"))

    for file in files_to_move:
        if file.is_file():
            date_taken = None
            if file.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                date_taken = get_image_date(file)
            elif file.suffix.lower() in [".mp4", ".mov"]:
                date_taken = get_video_date(file)
            if not date_taken:
                date_taken = datetime.fromtimestamp(file.stat().st_mtime)

            month_number = date_taken.month
            month_folder = f"{month_number}-{MESES_ES[month_number]}"
            destination_folder = source / month_folder
            destination_folder.mkdir(parents=True, exist_ok=True)

            new_path = destination_folder / file.name
            if new_path.exists():
                base = file.stem
                ext = file.suffix
                counter = 1
                while new_path.exists():
                    new_path = destination_folder / f"{base}_{counter}{ext}"
                    counter += 1
            shutil.move(str(file), new_path)

    print(f"✅ Archivos organizados en carpetas mensuales: {', '.join(MESES_ES.values())}")

def menu():
    while True:
        print("\n--- MONITORIZAR MÓVIL ANDROID ---")
        print("1. Verificar dispositivo")
        print("2. Iniciar scrcpy")
        print("3. Copiar y organizar fotos/vídeos (SD Card)")
        print("4. Salir")

        choice = input("Selecciona una opción: ")

        if choice == "1":
            check_device()
        elif choice == "2":
            if check_device():
                start_scrcpy()
        elif choice == "3":
            copy_and_organize_media()
        elif choice == "4":
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    menu()
