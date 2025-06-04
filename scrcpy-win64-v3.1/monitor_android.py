import subprocess
import os
import re
from datetime import datetime
from pathlib import Path
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

def extract_today_media_from_sd():
    if not check_device():
        return

    remote_dir = detect_sdcard_path()
    if not remote_dir:
        print("❌ No se encontró la carpeta DCIM/Camera en la SD externa.")
        return

    hoy_str = datetime.now().strftime("%Y%m%d")
    print(f"📆 Hoy es: {hoy_str}")
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

        print(f"⏱ Procesando {filename}")
        remote_path = f"{remote_dir}/{filename}"
        temp_local = local_dir / filename

        # Buscar fecha en el nombre del archivo (formato: IMG_YYYYMMDD_HHMMSS)
        match = re.search(r'(\d{8})_\d{6}', filename)
        if match:
            fecha_archivo = match.group(1)
            print(f"📁 Fecha detectada en nombre: {fecha_archivo}")
        else:
            print(f"⚠️ No se detectó fecha válida en el nombre de {filename}, descartando.")
            continue

        # Si coincide con hoy, se descarga y se mantiene
        if fecha_archivo == hoy_str:
            pull_result = pull_file_from_device(remote_path, temp_local)
            if "Error" in pull_result:
                print(f"⚠️ Error extrayendo {filename}: {pull_result}")
                continue
            total += 1
            print(f"✅ {filename} copiado.")
        else:
            print(f"🗑️ {filename} no es de hoy. Ignorado.")

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
        print("4. Copiar SOLO fotos y vídeos de HOY desde la SD")
        print("5. Salir")

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
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    menu()
