import subprocess
import html

def mostrar_notificacion(asunto: str, remitente: str, snippet: str = "") -> bool:
    """Envía una notificación de escritorio nativa mediante notify-send de forma segura."""
    titulo = "Nuevo correo de Gmail"
    
    # Limpiamos entidades html si vinieran en el snippet
    snippet_limpio = html.unescape(snippet).strip() if snippet else ""
    if snippet_limpio:
        if len(snippet_limpio) > 120:
            snippet_limpio = snippet_limpio[:117] + "..."
        mensaje = f"{remitente}\nAsunto: {asunto}\n{snippet_limpio}"
    else:
        mensaje = f"{remitente}\nAsunto: {asunto}"

    try:
        subprocess.run(
            ["notify-send", titulo, mensaje, "-i", "mail-unread"],
            check=False
        )
        return True
    except FileNotFoundError:
        # En sistemas sin notify-send (ej. servidores o entornos headless)
        return False
    except Exception as e:
        print(f"Error al enviar notificación de escritorio: {e}")
        return False
