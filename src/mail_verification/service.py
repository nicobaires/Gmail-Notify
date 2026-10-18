from googleapiclient.discovery import build
import html

def obtener_servicio_gmail(creds):
    """Inicializa y retorna la instancia del cliente de la API de Gmail."""
    return build('gmail', 'v1', credentials=creds)

def obtener_mensajes_no_leidos(service, max_results: int = 10, query: str = 'is:unread in:inbox'):
    """Lista los identificadores de correos no leídos en la bandeja de entrada."""
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results,
            fields='messages(id,threadId),resultSizeEstimate'
        ).execute()
        return results.get('messages', [])
    except Exception as e:
        print(f"Error al listar mensajes: {e}")
        return []

def obtener_detalles_mensaje(service, msg_id: str):
    """Obtiene metadatos clave (remitente, asunto, fecha) y el snippet del mensaje."""
    try:
        msg = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Date'],
            fields='id,snippet,payload/headers'
        ).execute()
        
        headers = msg.get('payload', {}).get('headers', [])
        remitente = "Desconocido"
        asunto = "Sin asunto"
        fecha = ""
        
        for header in headers:
            name = header.get('name')
            if name == 'From':
                remitente = header.get('value', 'Desconocido')
            elif name == 'Subject':
                asunto = header.get('value', 'Sin asunto')
            elif name == 'Date':
                fecha = header.get('value', '')
                
        snippet = html.unescape(msg.get('snippet', ''))
        return {
            'id': msg_id,
            'remitente': remitente,
            'asunto': asunto,
            'fecha': fecha,
            'snippet': snippet
        }
    except Exception as e:
        print(f"Error al obtener detalles del mensaje {msg_id}: {e}")
        return {
            'id': msg_id,
            'remitente': "Desconocido",
            'asunto': "Sin asunto",
            'fecha': "",
            'snippet': ""
        }

def marcar_como_leido(service, msg_id: str) -> bool:
    """Remueve la etiqueta UNREAD de un mensaje."""
    try:
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': [msg_id],
                'removeLabelIds': ['UNREAD']
            }
        ).execute()
        print("\n✔ Correo marcado como leído con éxito.")
        return True
    except Exception as e:
        print(f"Error al marcar como leído: {e}")
        return False

def borrar_correo(service, msg_id: str) -> bool:
    """Envía el mensaje especificado a la papelera (Trash)."""
    try:
        service.users().messages().trash(userId='me', id=msg_id).execute()
        print("\n🗑 Correo enviado a la papelera con éxito.")
        return True
    except Exception as e:
        print(f"Error al borrar el mensaje: {e}")
        return False

def archivar_correo(service, msg_id: str) -> bool:
    """Archiva el mensaje removiendo la etiqueta INBOX sin eliminarlo."""
    try:
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': [msg_id],
                'removeLabelIds': ['INBOX']
            }
        ).execute()
        print("\n📦 Correo archivado con éxito (removido de Recibidos).")
        return True
    except Exception as e:
        print(f"Error al archivar el mensaje: {e}")
        return False
