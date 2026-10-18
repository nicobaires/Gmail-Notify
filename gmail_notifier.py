import os
import subprocess
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Alcance que permite leer y modificar (marcar leído / papelera)
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
INTERVALO_SEGUNDOS = 120

def autenticar_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: No se encontró el archivo 'credentials.json'.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

def mostrar_notificacion(asunto, remitente):
    titulo = "Nuevo correo de Gmail"
    mensaje = f"{remitente}\nAsunto: {asunto}"
    try:
        subprocess.run(
            ["notify-send", titulo, mensaje, "-i", "mail-unread"],
            check=False
        )
    except Exception as e:
        print(f"Error al enviar notificación de escritorio: {e}")

def obtener_detalles_mensaje(service, msg_id):
    try:
        msg = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['From', 'Subject']).execute()
        headers = msg.get('payload', {}).get('headers', [])
        
        remitente = "Desconocido"
        asunto = "Sin asunto"
        
        for header in headers:
            if header['name'] == 'From':
                remitente = header['value']
            if header['name'] == 'Subject':
                asunto = header['value']
                
        return remitente, asunto
    except Exception as e:
        print(f"Error al obtener detalles del mensaje {msg_id}: {e}")
        return "Desconocido", "Sin asunto"

def marcar_como_leido(service, msg_id):
    try:
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': [msg_id],
                'removeLabelIds': ['UNREAD']
            }
        ).execute()
        print("\n✔ Correo marcado como leído con éxito.")
    except Exception as e:
        print(f"Error al marcar como leído: {e}")

def borrar_correo(service, msg_id):
    try:
        service.users().messages().trash(userId='me', id=msg_id).execute()
        print("\n🗑 Correo enviado a la papelera con éxito.")
    except Exception as e:
        print(f"Error al borrar el mensaje: {e}")

def menu_interactivo(service):
    """Muestra una lista de los últimos correos no leídos y permite gestionarlos desde la terminal."""
    while True:
        print("\n=== GESTOR DE GMAIL EN CONSOLA ===")
        print("1. Ver y gestionar correos no leídos")
        print("2. Iniciar modo monitor (notificaciones automáticas de fondo)")
        print("3. Salir")
        
        opcion = input("\nElige una opción (1-3): ").strip()
        
        if opcion == '1':
            try:
                results = service.users().messages().list(userId='me', q='is:unread in:inbox', maxResults=5).execute()
                messages = results.get('messages', [])
                
                if not messages:
                    print("\nNo hay correos no leídos en la bandeja de entrada.")
                    continue
                
                print("\n--- ÚLTIMOS CORREOS NO LEÍDOS ---")
                correos_cargados = []
                for i, msg in enumerate(messages, 1):
                    remitente, asunto = obtener_detalles_mensaje(service, msg['id'])
                    correos_cargados.append(msg['id'])
                    print(f"[{i}] De: {remitente}")
                    print(f"    Asunto: {asunto}")
                    print("-" * 40)
                
                print("\n¿Qué deseas hacer con alguno de estos correos?")
                print("Escribe el número del correo (1-5) para gestionarlo, o 0 para volver al menú.")
                sub_op = input("Selección: ").strip()
                
                if sub_op.isdigit() and 1 <= int(sub_op) <= len(correos_cargados):
                    selected_id = correos_cargados[int(sub_op) - 1]
                    print("\n¿Qué acción deseas realizar?")
                    print("[L] Marcar como leído")
                    print("[B] Enviar a la papelera (Borrar)")
                    print("[C] Cancelar")
                    accion = input("Acción (L/B/C): ").strip().upper()
                    
                    if accion == 'L':
                        marcar_como_leido(service, selected_id)
                    elif accion == 'B':
                        borrar_correo(service, selected_id)
                    else:
                        print("Acción cancelada.")
            except Exception as e:
                print(f"Error al listar correos: {e}")
                
        elif opcion == '2':
            iniciar_monitor(service)
        elif opcion == '3':
            print("\nSaliendo del programa. ¡Hasta luego!")
            break
        else:
            print("Opción inválida. Intenta nuevamente.")

def iniciar_monitor(service):
    print("\nIniciando servicio de notificación en segundo plano...")
    print(f"Comprobando nuevos mensajes cada {INTERVALO_SEGUNDOS} segundos. Presiona Ctrl+C para volver al menú.\n")
    
    try:
        ids_notificados = set()
        results = service.users().messages().list(userId='me', q='is:unread in:inbox').execute()
        messages = results.get('messages', [])
        if messages:
            ids_notificados.update({msg['id'] for msg in messages})
        
        while True:
            results = service.users().messages().list(userId='me', q='is:unread in:inbox').execute()
            messages = results.get('messages', [])
            
            if messages:
                current_ids = {msg['id'] for msg in messages}
                nuevos_ids = current_ids - ids_notificados
                
                for msg in messages:
                    msg_id = msg['id']
                    if msg_id in nuevos_ids:
                        remitente, asunto = obtener_detalles_mensaje(service, msg_id)
                        print(f"[{time.strftime('%H:%M:%S')}] Nuevo correo de: {remitente} - Asunto: {asunto}")
                        mostrar_notificacion(asunto, remitente)
                        ids_notificados.add(msg_id)
                
                ids_notificados = ids_notificados.intersection(current_ids)
                
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        print("\nSaliendo del modo monitor y volviendo al menú...")

def main():
    creds = autenticar_gmail()
    if not creds:
        return
    service = build('gmail', 'v1', credentials=creds)
    menu_interactivo(service)

if __name__ == '__main__':
    main()