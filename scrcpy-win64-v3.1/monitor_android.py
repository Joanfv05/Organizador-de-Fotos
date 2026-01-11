import subprocess
import os
import re
from datetime import datetime
from pathlib import Path
import shutil

ADB_PATH = "adb.exe"
SCRCPY_PATH = "scrcpy.exe"
LOCAL_BACKUP_DIR = "Fotos Camara"
MEDIA_EXTENSIONS = [".jpg", ".jpeg", ".png", ".mp4", ".mov", ".heic", ".avi", ".3gp"]
FILENAME_DATE_REGEX = r'(?:[A-Z]+_)?(\d{8})_\d{6}.*'


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

        match = re.search(FILENAME_DATE_REGEX, filename)
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

        match = re.search(FILENAME_DATE_REGEX, filename)
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
            match = re.search(FILENAME_DATE_REGEX, file.stem)

            if match:
                date_str = match.group(1)
                month_number = int(date_str[4:6])
                folder_name = f"{month_number:02d}-{MESES_ES[month_number]}"
                destination_folder = source / folder_name
            else:
                destination_folder = source / "SinFecha"
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



    print(f"✅ Archivos organizados por mes en '{LOCAL_BACKUP_DIR}'.")

def copy_and_organize_whatsapp_media():
    if not check_device():
        return

    WA_PATHS = [
        "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Images",
        "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Video"
    ]
    LOCAL_WA_DIR = "WhatsApp Media"
    Path(LOCAL_WA_DIR).mkdir(parents=True, exist_ok=True)

    # Copiar contenido
    for remote_path in WA_PATHS:
        print(f"📥 Copiando archivos desde {remote_path}...")
        result = run_command(f'{ADB_PATH} pull "{remote_path}" "{LOCAL_WA_DIR}"')
        print("Resultado adb pull:", result)

    source = Path(LOCAL_WA_DIR)
    if not source.exists():
        print(f"❌ No se pudo encontrar la carpeta local '{LOCAL_WA_DIR}'.")
        return

    # Buscar fotos y vídeos
    files_to_move = []
    for ext in MEDIA_EXTENSIONS:
        files_to_move.extend(source.rglob(f"*{ext}"))

    for file in files_to_move:
        if file.is_file():
            # ⚠️ Ignorar archivos de papelera de WhatsApp
            if file.name.startswith(".trashed-"):
                continue

            # Extraer fecha de nombres tipo IMG-YYYYMMDD-WAxxxx / VID-YYYYMMDD-WAxxxx
            match = re.search(r'(?:IMG|VID)-(\d{4})(\d{2})(\d{2})-WA\d+', file.stem)
            if match:
                year, month_str, _ = match.groups()
                month_number = int(month_str)
                folder_name = f"{month_number:02d}-{MESES_ES[month_number]}"
                destination_folder = source / folder_name
            else:
                destination_folder = source / "SinFecha"

            destination_folder.mkdir(parents=True, exist_ok=True)
            new_path = destination_folder / file.name

            # Evitar sobrescribir archivos repetidos
            if new_path.exists():
                base = file.stem
                ext = file.suffix
                counter = 1
                while new_path.exists():
                    new_path = destination_folder / f"{base}_{counter}{ext}"
                    counter += 1

            shutil.move(str(file), new_path)

    print(f"✅ Archivos de WhatsApp organizados por mes en '{LOCAL_WA_DIR}'.")

def extract_media_from_specific_month():
    if not check_device():
        return

    remote_dir = detect_sdcard_path()
    if not remote_dir:
        print("❌ No se encontró la carpeta DCIM/Camera en la SD externa.")
        return

    year = input("📅 Introduce el AÑO (YYYY): ").strip()
    month = input("📅 Introduce el MES (MM): ").strip()

    if not (year.isdigit() and month.isdigit() and 1 <= int(month) <= 12):
        print("❌ Año o mes inválidos.")
        return

    month = month.zfill(2)
    folder_name = f"{year}-{month}"
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

        # Detectar fechas universalmente
        match = re.search(FILENAME_DATE_REGEX, filename)
        if not match:
            continue

        date_str = match.group(1)
        f_year = date_str[:4]
        f_month = date_str[4:6]

        if f_year == year and f_month == month:
            remote_path = f"{remote_dir}/{filename}"
            local_path = local_dir / filename
            pull_result = pull_file_from_device(remote_path, local_path)

            if "Error" in pull_result:
                print(f"⚠️ Error extrayendo {filename}: {pull_result}")
                continue

            total += 1
            print(f"✅ {filename} copiado.")

    print(f"\n🎉 Proceso completado. {total} archivos copiados a '{folder_name}'.")

def extract_media_from_specific_month_preserve_metadata():
    if not check_device():
        return

    remote_dir = detect_sdcard_path()
    if not remote_dir:
        print("❌ No se encontró la carpeta DCIM/Camera en la SD externa.")
        return

    year = input("📅 Introduce el AÑO (YYYY): ").strip()
    month = input("📅 Introduce el MES (MM): ").strip()

    if not (year.isdigit() and month.isdigit() and 1 <= int(month) <= 12):
        print("❌ Año o mes inválidos.")
        return

    month = month.zfill(2)
    folder_name = f"{year}-{month}_METADATA_OK"
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

        match = re.search(FILENAME_DATE_REGEX, filename)
        if not match:
            continue

        date_str = match.group(1)
        f_year = date_str[:4]
        f_month = date_str[4:6]

        if f_year == year and f_month == month:
            remote_path = f"{remote_dir}/{filename}"
            local_path = local_dir / filename

            # 👇 CLAVE: -a preserva fecha y hora originales
            cmd = f'{ADB_PATH} pull -a "{remote_path}" "{local_path}"'
            result = run_command(cmd)

            if "Error" in result:
                print(f"⚠️ Error extrayendo {filename}: {result}")
                continue

            total += 1
            print(f"✅ {filename} copiado (metadatos conservados).")

    print(f"\n🎉 Proceso completado.")
    print(f"📁 {total} archivos copiados a '{folder_name}' manteniendo fecha y hora originales.")

def restore_media_to_device():
    if not check_device():
        return

    # Detectar automáticamente la SD donde está DCIM/Camera
    target_path = detect_sdcard_path()
    if not target_path:
        print("❌ No se encontró ninguna SD con carpeta DCIM/Camera.")
        return

    print(f"📱 Restaurando a SD detectada → {target_path}")

    # Carpeta local que quieres restaurar
    print(f"📍 Carpeta actual del script: {Path.cwd()}")
    local_folder = input("📂 Introduce la carpeta local a restaurar: ").strip()
    local_path = Path(local_folder).expanduser().resolve()

    if not local_path.exists() or not local_path.is_dir():
        print(f"❌ La carpeta no existe:\n{local_path}")
        return

    print("⏳ Copiando archivos a la SD (manteniendo fecha y hora)...")

    # Recorrer todos los archivos de la carpeta local
    total = 0
    for file in local_path.rglob("*"):
        if file.is_file():
            # Construir ruta destino en SD
            relative_path = file.relative_to(local_path)
            remote_path = f"{target_path}/{relative_path}".replace("\\", "/")

            # Crear carpeta remota si no existe
            dir_remote = os.path.dirname(remote_path)
            run_command(f'{ADB_PATH} shell mkdir -p "{dir_remote}"')

            # Subir el archivo manteniendo fecha/hora (-a)
            cmd = f'"{ADB_PATH}" push -a "{file}" "{remote_path}"'
            result = run_command(cmd)
            if "error" in result.lower():
                print(f"⚠️ Error subiendo {file.name}: {result}")
            else:
                print(f"✅ {file.name} restaurado.")
                total += 1

    print(f"\n🎉 Restauración completada. {total} archivos subidos a la SD.")

def menu():
    while True:
        print("\n--- MONITORIZAR MÓVIL ANDROID ---")
        print("1. Verificar dispositivo")
        print("2. Iniciar scrcpy")
        print("3. Copiar y organizar fotos/vídeos (SD Card completa)")
        print("4. Copiar SOLO fotos y vídeos de HOY desde la SD")
        print("5. Copiar fotos/vídeos de una FECHA ESPECÍFICA desde la SD")
        print("6. Copiar fotos/vídeos de un MES ESPECÍFICO desde la SD")
        print("7. Copiar fotos/vídeos de un MES (CONSERVANDO FECHA/HORA)")
        print("8. Copiar y organizar fotos/vídeos de WhatsApp")
        print("9. Restaurar fotos/vídeos al móvil (manteniendo fechas)")
        print("10. Salir")

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
            extract_media_from_specific_month()
        elif choice == "7":
            extract_media_from_specific_month_preserve_metadata()
        elif choice == "8":
            copy_and_organize_whatsapp_media()
        elif choice == "9":
            restore_media_to_device()
        elif choice == "10":
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    menu()
