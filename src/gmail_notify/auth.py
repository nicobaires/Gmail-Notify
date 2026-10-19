import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def obtener_directorio_config() -> Path:
    """Retorna la ruta al directorio de configuración XDG (~/.config/gmail-notify)."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "gmail-notify"
    return Path.home() / ".config" / "gmail-notify"

def resolver_rutas_auth(
    token_file: Path | str | None = None,
    credentials_file: Path | str | None = None
) -> tuple[Path, Path]:
    """
    Resuelve las rutas de credentials.json y token.json según estándar XDG con fallback local.
    Prioridad:
    1. Argumentos explícitos pasados a la función.
    2. Archivos en ~/.config/gmail-notify/ (o $XDG_CONFIG_HOME).
    3. Archivos locales en el directorio del proyecto (fallback de desarrollo).
    """
    config_dir = obtener_directorio_config()

    if credentials_file is not None:
        cred_path = Path(credentials_file)
    else:
        xdg_cred = config_dir / "credentials.json"
        local_cred = PROJECT_ROOT / "credentials.json"
        if xdg_cred.exists():
            cred_path = xdg_cred
        elif local_cred.exists():
            cred_path = local_cred
        else:
            cred_path = xdg_cred

    if token_file is not None:
        tok_path = Path(token_file)
    else:
        xdg_token = config_dir / "token.json"
        local_token = PROJECT_ROOT / "token.json"
        if xdg_token.exists():
            tok_path = xdg_token
        elif local_token.exists():
            tok_path = local_token
        else:
            tok_path = xdg_token

    return tok_path, cred_path

def guardar_token(token_file: Path, creds: Credentials) -> None:
    """Guarda el token OAuth en disco con permisos restrictivos (chmod 600)."""
    token_file.parent.mkdir(parents=True, exist_ok=True)
    with open(token_file, 'w', encoding='utf-8') as token:
        token.write(creds.to_json())
    try:
        os.chmod(token_file, 0o600)
    except OSError:
        pass

def autenticar_gmail(
    token_file: Path | str | None = None,
    credentials_file: Path | str | None = None
):
    """Autentica al usuario contra Gmail OAuth2 con soporte XDG y manejo robusto de tokens."""
    tok_path, cred_path = resolver_rutas_auth(token_file, credentials_file)
    creds = None

    if tok_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(tok_path), SCOPES)
        except Exception as e:
            print(f"Aviso: No se pudo cargar el archivo de token existente: {e}")
            creds = None

    if not creds or not creds.valid:
        token_refrescado = False
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Renovando token de acceso expirado...")
                creds.refresh(Request())
                token_refrescado = True
            except Exception as e:
                print(f"No fue posible renovar el token ({e}). Se iniciará una nueva autorización.")
                creds = None

        if not token_refrescado or not creds:
            if not cred_path.exists():
                print(f"Error: No se encontró el archivo de credenciales en:")
                print(f"  - {cred_path}")
                print("Descarga tus credenciales OAuth client ID de Google Cloud Console y colócalas allí.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)

        guardar_token(tok_path, creds)

    return creds
