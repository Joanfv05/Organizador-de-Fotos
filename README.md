# Monitorizar Móvil Android

Este proyecto proporciona un **script en Python** para extraer, organizar y restaurar fotos y vídeos de un dispositivo Android conectado mediante **ADB** y visualizarlo con **scrcpy**. Permite gestionar tanto la **SD externa** como el **almacenamiento interno**, incluyendo medios de WhatsApp.

---

## 📦 Características principales

- Verificar si un dispositivo Android está conectado.
- Iniciar `scrcpy` para controlar el móvil desde el PC.
- Copiar y organizar fotos y vídeos desde la SD por fecha o mes.
- Copiar sólo fotos y vídeos de **hoy** o de una **fecha específica**.
- Copiar fotos y vídeos de WhatsApp y organizarlos por mes.
- Restaurar fotos y vídeos al móvil manteniendo fecha y hora originales.
- Detección automática de la SD donde se encuentra la carpeta `DCIM/Camera`.
- Soporta múltiples formatos de archivo: `.jpg, .jpeg, .png, .mp4, .mov, .heic, .avi, .3gp`.

---

## ⚡ Requisitos

- **Python 3.9+**
- **ADB** instalado y accesible desde la terminal (incluido en el proyecto: `adb.exe`)
- **scrcpy** para visualizar/controlar el móvil desde el PC
- Dispositivo Android con **depuración USB activada**.

---

## 📝 Instalación y uso

1. Clona el repositorio:
```bash
git clone https://github.com/Joanfv05/Organizador-de-Fotos.git
cd scrcpy-win64-v3.1
````

2. Conecta tu móvil y activa depuración USB.

3. Ejecuta el script:

```bash
python monitor_android.py
```

4. Sigue el **menú interactivo** para seleccionar la acción deseada:

* 1: Verificar dispositivo
* 2: Iniciar scrcpy
* 3: Copiar y organizar fotos/vídeos desde SD
* 4: Copiar sólo fotos y vídeos de hoy
* 5: Copiar fotos/vídeos de una fecha específica
* 6: Copiar fotos/vídeos de un mes específico
* 7: Copiar fotos/vídeos de un mes conservando fecha/hora
* 8: Copiar y organizar fotos/vídeos de WhatsApp
* 9: Restaurar fotos/vídeos al móvil
* 10: Salir

---

## 📁 Estructura de carpetas

* `monitor_android.py` → Script principal
* `Fotos Camara/` → Carpeta local de backup de fotos y vídeos de la cámara
* `WhatsApp Media/` → Carpeta local de backup de fotos y vídeos de WhatsApp
* `.gitignore` → Ignora automáticamente las carpetas de medios para no subir archivos pesados

---

## 🚀 Ejemplo de uso

Extraer sólo las fotos y vídeos de hoy desde la SD:

```
python monitor_android.py
# Selecciona la opción 4
```

Organizar WhatsApp Media por mes:

```
python monitor_android.py
# Selecciona la opción 8
```

Restaurar una carpeta local de fotos al móvil manteniendo las fechas:

```
python monitor_android.py
# Selecciona la opción 9
```

---

## 🛡️ Nota

Este script **no elimina archivos** del dispositivo, sólo los copia o restaura. Para eliminar archivos usa `adb` manualmente con cuidado.

---

## 📌 Autor

Joan Ferre
[GitHub](https://github.com/Joanfv05>)

