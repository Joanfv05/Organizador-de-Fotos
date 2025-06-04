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
MEDIA_EXTENSIONS = [".jpg", ".jpeg", ".png", ".mp4", ".mov", ".heic"]

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

def detect_sdcard_path():
    output = run_command(f"{ADB_PATH} shell ls /storage")
    for line in output.splitlines():
        if "-" in line and len(line) == 9:
            test = run_command(f'{ADB_PATH} shell ls "/storage/{line}/DCIM/Camera"')
            if "No such file or directory" not in test:
                return f"/storage/{line}/DCIM/Camera"
    return None

def list_files_on_device(remote_dir):
    output = run_command(f'{ADB_PATH} shell ls "{remote_dir}"')
    if "No such file" in output or "Error" in output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]

def pull_file_from_device(remote_path, local_path):
    cmd = f'{ADB_PATH} pull "{remote_path}" "{local_path}"'
    return run_command(cmd)

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
    match = re.search(r'(\d{8})_(\d{6})', file.stem)
    if match:
        try:
            return datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M%S")
        except Exception:
            pass
    return datetime.fromtimestamp(file.stat().st_mtime)

def extract_today_media_from_sd():
    if not check_device():
        return

    remote_dir = detect_sdcard_path()
    if not remote_dir:
        print("❌ No se encontró la carpeta DCIM/Camera en la SD externa.")
        return

    hoy = datetime.now().strftime("%Y%m%d")
    folder_name = datetime.now().strftime("%Y-%m-%d")
    local_dir = Path(folder_name)
    local_dir.mkdir(parents=True, exist_ok=True)

    files = list_files_on_device(remote_dir)
    if not files:
        print("❌ No hay archivos en la carpeta remota.")
        return

    total = 0
    for filename in files:
        if not any(filename.lower().endswith(ext) for ext in MEDIA_EXTENSIONS):
            continue

        match = re.search(r'(\d{8})_\d{6}', filename)
        if not match:
            continue

        if match.group(1) != hoy:
            continue

        remote_path = f"{remote_dir}/{filename}"
        local_path = local_dir / filename
        pull_result = pull_file_from_device(remote_path, local_path)
        if "Error" in pull_result:
            print(f"⚠️ Error extrayendo {filename}: {pull_result}")
            continue
        total += 1
        print(f"✅ {filename} copiado.")

    print(f"\n🎉 Proceso completado. {total} archivos copiados a '{folder_name}'.")

def extract_media_from_specific_date():
    if not check_device():
        return

    remote_dir = detect_sdcard_path()
    if not remote_dir:
        print("❌ No se encontró la carpeta DCIM/Camera en la SD externa.")
        return

    fecha_input = input("📅 Introduce la fecha deseada (formato YYYYMMDD): ").strip()
    try:
        datetime_obj = datetime.strptime(fecha_input, "%Y%m%d")
    except ValueError:
        print("❌ Fecha inválida. Asegúrate de usar el formato YYYYMMDD.")
        return

    folder_name = datetime_obj.strftime("%Y-%m-%d")
    local_dir = Path(folder_name)
    local_dir.mkdir(parents=True, exist_ok=True)

    files = list_files_on_device(remote_dir)
    if not files:
        print("❌ No hay archivos en la carpeta remota.")
        return

    total = 0
    for filename in files:
        if not any(filename.lower().endswith(ext) for ext in MEDIA_EXTENSIONS):
            continue

        match = re.search(r'(\d{8})_\d{6}', filename)
        if not match:
            continue

        if match.group(1) != fecha_input:
            continue

        remote_path = f"{remote_dir}/{filename}"
        local_path = local_dir / filename
        pull_result = pull_file_from_device(remote_path, local_path)
        if "Error" in pull_result:
            print(f"⚠️ Error extrayendo {filename}: {pull_result}")
            continue
        total += 1
        print(f"✅ {filename} copiado.")

    print(f"\n🎉 Proceso completado. {total} archivos copiados a '{folder_name}'.")

def copy_and_organize_media():
    if not check_device():
        return

    sd_camera_path = detect_sdcard_path()
    if not sd_camera_path:
        print("❌ No se encontró la carpeta DCIM/Camera en la SD externa.")
        return

    Path(LOCAL_BACKUP_DIR).mkdir(parents=True, exist_ok=True)

    print(f"📥 Copiando archivos desde {sd_camera_path} a '{LOCAL_BACKUP_DIR}'...")
    result = run_command(f'{ADB_PATH} pull "{sd_camera_path}" "{LOCAL_BACKUP_DIR}"')
    print("Resultado adb pull:", result)

    source = Path(LOCAL_BACKUP_DIR)
    if not source.exists():
        print(f"❌ No se pudo encontrar la carpeta local '{LOCAL_BACKUP_DIR}'.")
        return

    files_to_move = []
    for ext in MEDIA_EXTENSIONS:
        files_to_move.extend(source.rglob(f"*{ext}"))

    for file in files_to_move:
        if file.is_file():
            if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".heic"]:
                date_taken = get_image_date(file)
            else:
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
        print("3. Copiar y organizar fotos/vídeos (SD Card completa)")
        print("4. Copiar SOLO fotos y vídeos de HOY desde la SD")
        print("5. Copiar fotos/vídeos de una FECHA ESPECÍFICA desde la SD")
        print("6. Salir")

        choice = input("Selecciona una opción: ")

        if choice == "1":
            check_device()
        elif choice == "2":
            if check_device():
                start_scrcpy()
        elif choice == "3":
            copy_and_organize_media()
        elif choice == "4":
            extract_today_media_from_sd()
        elif choice == "5":
            extract_media_from_specific_date()
        elif choice == "6":
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    menu()
