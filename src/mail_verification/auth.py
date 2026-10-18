from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TOKEN_PATH = PROJECT_ROOT / 'token.json'
CREDENTIALS_PATH = PROJECT_ROOT / 'credentials.json'

def autenticar_gmail(token_file: Path = TOKEN_PATH, credentials_file: Path = CREDENTIALS_PATH):
    """Autentica al usuario contra Gmail OAuth2 con manejo robusto de tokens vencidos o revocados."""
    creds = None
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
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
            if not credentials_file.exists():
                print(f"Error: No se encontró el archivo '{credentials_file}'.")
                print("Descarga tus credenciales OAuth client ID de Google Cloud Console y colócalas aquí.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())

    return creds
