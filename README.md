# Gmail Notify

Una herramienta CLI ligera y segura para gestionar correos de Gmail y recibir notificaciones de escritorio en Linux sin necesidad de mantener el navegador web abierto.

---

## 🚀 Características

- **Gestión interactiva desde la terminal**:
  - Lista los correos no leídos más recientes con remitente, asunto, fecha y vista previa (*snippet*).
  - **[L] Marcar como leído**: actualiza el estado del correo en Gmail.
  - **[A] Archivar**: remueve el correo de la bandeja de entrada (*Recibidos*) sin borrarlo.
  - **[B] Enviar a la papelera**: mueve el correo a la papelera de Gmail.
  - **[N] Abrir en el navegador**: lanza el enlace directo al correo en tu navegador predeterminado.
- **Modo Monitor en segundo plano**:
  - Consulta periódica automática (por defecto cada 120 segundos).
  - Emite alertas visuales de escritorio nativas con `notify-send`.
- **Integración con el sistema Linux**:
  - Lanzador `.desktop` listo para integrarse al menú de aplicaciones y al inicio automático del sistema.
- **Seguridad y robustez**:
  - Autenticación OAuth 2.0 oficial (`https://www.googleapis.com/auth/gmail.modify`).
  - Renovación automática y recuperación transparente si el token expira o es revocado.
  - Prevención de inyección de comandos shell al invocar notificaciones.
  - Archivos sensibles (`credentials.json`, `token.json`) protegidos en `.gitignore`.
- **Suite de pruebas completa**:
  - 35 pruebas unitarias automatizadas con `pytest` que garantizan la estabilidad del código.

---

## 📋 Requisitos Previos

1. **Linux** con servidor de notificaciones (`libnotify-bin` / `notify-send`).
2. **Python 3.10+** (o entorno administrado con **uv**).
3. **Credenciales de Google Cloud**:
   - Accede a [Google Cloud Console](https://console.cloud.google.com/).
   - Crea un proyecto nuevo o selecciona uno existente.
   - Habilita la **Gmail API** en la sección *APIs y servicios > Biblioteca*.
   - Configura la pantalla de consentimiento de OAuth (*OAuth consent screen*) como usuario de prueba.
   - En *Credenciales*, crea un **ID de cliente de OAuth 2.0** con tipo de aplicación: **App de escritorio** (*Desktop App*).
   - Descarga el archivo JSON y colócalo en `~/.config/gmail-notify/credentials.json` (estándar XDG) o en la raíz del proyecto como `credentials.json`.

---

## 🛠️ Instalación

Clona el repositorio y entra al directorio:

```bash
git clone https://github.com/nicobaires/Gmail-Notify.git
cd Gmail-Notify
```

### Opción 1: Usando `uv` (Recomendado)

```bash
# Sincroniza el entorno y dependencias automáticamente
uv sync
```

### Opción 2: Usando `pip` y entorno virtual estándar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 💻 Uso

### 1. Menú interactivo en consola

Inicia la aplicación:

```bash
uv run gmail-notify
# o:
python3 gmail_notifier.py
```

En la primera ejecución se abrirá una ventana en tu navegador para autorizar el acceso a Gmail. Una vez completado, se guardará `token.json` localmente para las siguientes sesiones.

Ejemplo del menú:
```text
=============================================
       GESTOR DE GMAIL EN CONSOLA
=============================================
1. Ver y gestionar correos no leídos
2. Iniciar modo monitor (notificaciones en segundo plano)
3. Salir

Elige una opción (1-3): 1

--- ÚLTIMOS CORREOS NO LEÍDOS ---

[1] De: Juan Pérez <juan@ejemplo.com>
    Asunto: Reporte semanal
    Fecha:  Sun, 18 Oct 2026 09:15:00 -0300
    Previa: Hola, adjunto el resumen de actividades del equipo...
---------------------------------------------

Escribe el número del correo (1-1) para gestionarlo, o 0 para volver.
Selección: 1

Acciones para: "Reporte semanal"
[L] Marcar como leído
[A] Archivar (quitar de Recibidos)
[B] Enviar a la papelera (Borrar)
[N] Abrir en el navegador web
[C] Cancelar
Acción (L/A/B/N/C): 
```

---

### 2. Modo Monitor (alertas de fondo)

Puedes ejecutar el monitor directamente sin pasar por el menú interactivo:

```bash
# Iniciar monitor con intervalo predeterminado (120 s)
uv run gmail-notify --monitor

# Iniciar comprobando cada 60 segundos
uv run gmail-notify --monitor --intervalo 60

# Ajustar la cantidad de correos a mostrar en la vista previa
uv run gmail-notify --limite 15
```

Para consultar todas las opciones disponibles:

```bash
uv run gmail-notify --help
```

---

## 🖥️ Integración como App de Escritorio

Para que la aplicación aparezca en tu menú de aplicaciones de Linux (GNOME, KDE, etc.) o se inicie automáticamente:

### Agregar al Menú de Aplicaciones

```bash
mkdir -p ~/.local/share/applications
cp gmail-notify.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
```

### Iniciar automáticamente al encender el equipo

```bash
mkdir -p ~/.config/autostart
cp gmail-notify.desktop ~/.config/autostart/
```

---

## 🧪 Pruebas Unitarias

El proyecto cuenta con una batería de pruebas unitarias que cubren autenticación, interfaz CLI, servicio de API y notificaciones:

```bash
# Ejecutar todas las pruebas
uv run pytest

# Ejecutar con salida detallada
uv run pytest -v
```

---

## 📁 Estructura del Proyecto

```text
gmail-notify/
├── credentials.json       # Credenciales OAuth descargadas (ignorado en git)
├── token.json             # Token de sesión generado (ignorado en git)
├── gmail-notify.desktop   # Lanzador para el menú de aplicaciones de Linux
├── gmail_notifier.py      # Punto de entrada directo por compatibilidad
├── pyproject.toml         # Configuración y dependencias del proyecto
├── uv.lock                # Bloqueo determinista de dependencias
├── README.md              # Documentación
├── src/
│   └── gmail_notify/
│       ├── __init__.py    # Exportación del paquete
│       ├── auth.py        # Manejo de credenciales y renovación OAuth2
│       ├── cli.py         # Interfaz de comandos y menú interactivo
│       ├── notifier.py    # Envío seguro de notificaciones de escritorio
│       └── service.py     # Operaciones con la API de Gmail
└── tests/
    ├── __init__.py
    ├── test_auth.py       # Pruebas de autenticación y renovación de token
    ├── test_cli.py        # Pruebas del menú y argumentos de línea de comandos
    ├── test_notifier.py   # Pruebas de notificaciones nativas y snippets
    └── test_service.py    # Pruebas de interacción con la API de Gmail
```

---

## 🔒 Privacidad y Seguridad

- Las credenciales nunca se transmiten a servidores externos; todo el tráfico se comunica directamente con las APIs oficiales de Google.
- El archivo `.gitignore` incluye por defecto `credentials.json`, `token.json` y variables de entorno para prevenir fugas accidentales al control de versiones.
