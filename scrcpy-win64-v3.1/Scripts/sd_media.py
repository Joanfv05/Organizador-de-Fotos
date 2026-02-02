import subprocess
import os
import re
from datetime import datetime
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).parent.parent  
ADB_PATH = BASE_DIR / "adb.exe"
SCRCPY_PATH = BASE_DIR / "scrcpy.exe"
LOCAL_BACKUP_DIR = "Fotos Camara"
MEDIA_EXTENSIONS = [".jpg", ".jpeg", ".png", ".mp4", ".mov", ".heic", ".avi", ".3gp"]
FILENAME_DATE_REGEX = r'(?:[A-Z]+_)?(\d{8})_\d{6}.*'

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# --- FUNCIONES ---

def run_command_list(cmd_list):
    """Ejecuta un comando con subprocess.run usando lista de argumentos"""
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def check_device():
    print("🔍 Buscando dispositivos conectados...")
    result = run_command_list([str(ADB_PATH), "devices"])
    print(result)
    if "device" in result and "unauthorized" not in result:
        print("✅ Dispositivo conectado.")
        return True
    elif "unauthorized" in result:
        print("⚠️ Autoriza la conexión en tu móvil.")
    else:
        print("❌ No se detectó ningún dispositivo.")
    return False

def start_scrcpy():
    print("🚀 Iniciando scrcpy...")
    result = subprocess.run([str(SCRCPY_PATH)])
    if result.returncode != 0:
        print(f"⚠️ Error al iniciar scrcpy: {result}")

def detect_sdcard_path():
    output = run_command_list([str(ADB_PATH), "shell", "ls", "/storage"])
    for line in output.splitlines():
        if "-" in line and len(line) == 9:
            test = run_command_list([str(ADB_PATH), "shell", "ls", f"/storage/{line}/DCIM/Camera"])
            if "No such file or directory" not in test:
                return f"/storage/{line}/DCIM/Camera"
    return None

def list_files_on_device(remote_dir):
    output = run_command_list([str(ADB_PATH), "shell", "ls", remote_dir])
    if "No such file" in output or "Error" in output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]

def pull_file_from_device(remote_path, local_path):
    local_path = str(local_path)
    cmd = [str(ADB_PATH), "pull", remote_path, local_path]
    return run_command_list(cmd)

def push_file_to_device(local_path, remote_path):
    local_path = str(local_path)
    cmd = [str(ADB_PATH), "push", "-a", local_path, remote_path]
    return run_command_list(cmd)

# --- FUNCIONES DE EXTRACCIÓN ---

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

    remote_dir = detect_sdcard_path()
    if not remote_dir:
        print("❌ No se encontró la carpeta DCIM/Camera en la SD externa.")
        return

    year_selected = input("📅 Introduce el AÑO a organizar (YYYY): ").strip()
    if not (year_selected.isdigit() and len(year_selected) == 4):
        print("❌ Año inválido.")
        return

    # Crear carpeta base local
    base_dir = Path(LOCAL_BACKUP_DIR)
    base_dir.mkdir(parents=True, exist_ok=True)

    # Listar archivos del dispositivo
    print(f"📋 Escaneando archivos en {remote_dir}...")
    files = list_files_on_device(remote_dir)
    
    if not files:
        print("❌ No hay archivos en la carpeta remota.")
        return

    # Filtrar archivos por año
    print("🔍 Filtrando archivos por año...")
    files_to_copy = []
    for filename in files:
        # Ignorar archivos trashed
        if filename.startswith(".trashed-"):
            continue
        
        # Solo extensiones de media
        if not any(filename.lower().endswith(ext) for ext in MEDIA_EXTENSIONS):
            continue
        
        # Extraer fecha del nombre del archivo
        match = re.search(FILENAME_DATE_REGEX, filename)
        if not match:
            continue
        
        date_str = match.group(1)
        year = date_str[:4]
        
        # Solo archivos del año seleccionado
        if year == year_selected:
            files_to_copy.append(filename)

    if not files_to_copy:
        print(f"❌ No se encontraron archivos del año {year_selected} en la SD.")
        return

    print(f"📥 Encontrados {len(files_to_copy)} archivos del año {year_selected}.")
    print("⏳ Copiando y organizando...")
    print()

    # Función para mostrar barra de progreso
    def show_progress_bar(completed, total, width=50):
        percent = completed / total
        filled = int(width * percent)
        bar = "█" * filled + "░" * (width - filled)
        percentage = f"{percent:.1%}"
        return f"[{bar}] {percentage} ({completed}/{total})"

    total_files = len(files_to_copy)
    copied_files = {}
    
    # Contar archivos por mes para estadísticas
    month_stats = {}
    
    # Copiar archivos con barra de progreso
    for i, filename in enumerate(files_to_copy, 1):
        # Extraer información de fecha
        match = re.search(FILENAME_DATE_REGEX, filename)
        date_str = match.group(1)
        
        # Crear estructura de carpetas
        month_number = int(date_str[4:6])
        month_name = MESES_ES[month_number]
        month_folder = f"{month_number:02d}-{month_name}"
        
        # Actualizar estadísticas
        if month_folder not in month_stats:
            month_stats[month_folder] = 0
        month_stats[month_folder] += 1
        
        destination_folder = base_dir / year_selected / month_folder
        destination_folder.mkdir(parents=True, exist_ok=True)
        
        # Ruta destino final
        local_path = destination_folder / filename
        
        # Evitar sobrescrituras
        if local_path.exists():
            base_name = Path(filename).stem
            ext = Path(filename).suffix
            counter = 1
            while local_path.exists():
                new_name = f"{base_name}_{counter}{ext}"
                local_path = destination_folder / new_name
                counter += 1
        
        # Copiar archivo desde el dispositivo
        remote_path = f"{remote_dir}/{filename}"
        pull_result = pull_file_from_device(remote_path, local_path)
        
        if "Error" in pull_result:
            print(f"\r⚠️ Error copiando {filename}")
            # Mostrar barra de progreso actualizada
            print(f"\r{show_progress_bar(i, total_files)}", end="")
        else:
            # Guardar archivo copiado para resumen
            if month_folder not in copied_files:
                copied_files[month_folder] = []
            copied_files[month_folder].append(filename)
            
            # Mostrar barra de progreso
            print(f"\r{show_progress_bar(i, total_files)}", end="")

    # Línea en blanco después de la barra de progreso
    print("\n")
    
    # Mostrar resumen detallado
    print("📊 RESUMEN DE COPIA:")
    print("-" * 50)
    
    total_copied = sum(len(files) for files in copied_files.values())
    
    for month_folder, file_list in sorted(copied_files.items()):
        print(f"📁 {month_folder}: {len(file_list)} archivos")
    
    print("-" * 50)
    print(f"🎉 Total: {total_copied} archivos copiados exitosamente")
    
    if total_copied < total_files:
        print(f"⚠️  {total_files - total_copied} archivos no se pudieron copiar")
    
    print(f"📁 Archivos organizados en: '{LOCAL_BACKUP_DIR}/{year_selected}/'")

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
            cmd = [str(ADB_PATH), "pull", "-a", remote_path, str(local_path)]
            result = run_command_list(cmd)

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
            run_command_list([str(ADB_PATH), "shell", "mkdir", "-p", dir_remote])

            # Subir el archivo manteniendo fecha/hora (-a)
            result = push_file_to_device(str(file), remote_path)
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
        print("3. Copiar y organizar fotos/vídeos de un AÑO específico por MESES (SD Card)")
        print("4. Copiar SOLO fotos y vídeos de HOY desde la SD")
        print("5. Copiar fotos/vídeos de una FECHA ESPECÍFICA desde la SD")
        print("6. Copiar fotos/vídeos de un MES ESPECÍFICO desde la SD")
        print("7. Copiar fotos/vídeos de un MES (CONSERVANDO FECHA/HORA)")
        print("8. Restaurar fotos/vídeos al móvil (manteniendo fechas)")
        print("9. Salir")

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
            restore_media_to_device()
        elif choice == "9":
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    menu()