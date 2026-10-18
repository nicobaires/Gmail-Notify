import argparse
import sys
import time
import webbrowser
from .auth import autenticar_gmail
from .notifier import mostrar_notificacion
from .service import (
    obtener_servicio_gmail,
    obtener_mensajes_no_leidos,
    obtener_detalles_mensaje,
    marcar_como_leido,
    borrar_correo,
    archivar_correo,
)

def abrir_en_navegador(msg_id: str) -> None:
    """Abre el correo seleccionado en la interfaz web de Gmail."""
    url = f"https://mail.google.com/mail/u/0/#inbox/{msg_id}"
    print(f"\n🌐 Abriendo en el navegador: {url}")
    webbrowser.open(url)

def menu_interactivo(service, limite_correos: int = 10, intervalo_monitor: int = 120) -> None:
    """Muestra una lista de los últimos correos no leídos y permite gestionarlos interactivamente."""
    while True:
        print("\n" + "=" * 45)
        print("       GESTOR DE GMAIL EN CONSOLA")
        print("=" * 45)
        print("1. Ver y gestionar correos no leídos")
        print("2. Iniciar modo monitor (notificaciones en segundo plano)")
        print("3. Salir")
        
        opcion = input("\nElige una opción (1-3): ").strip()
        
        if opcion == '1':
            try:
                messages = obtener_mensajes_no_leidos(service, max_results=limite_correos)
                
                if not messages:
                    print("\n🎉 No hay correos no leídos en la bandeja de entrada.")
                    continue
                
                print(f"\n--- ÚLTIMOS {len(messages)} CORREOS NO LEÍDOS ---")
                correos_cargados = []
                for i, msg in enumerate(messages, 1):
                    detalles = obtener_detalles_mensaje(service, msg['id'])
                    correos_cargados.append(detalles)
                    
                    print(f"\n[{i}] De: {detalles['remitente']}")
                    print(f"    Asunto: {detalles['asunto']}")
                    if detalles['fecha']:
                        print(f"    Fecha:  {detalles['fecha']}")
                    if detalles['snippet']:
                        print(f"    Previa: {detalles['snippet']}")
                    print("-" * 45)
                
                print("\nEscribe el número del correo (1-{}) para gestionarlo, o 0 para volver.".format(len(correos_cargados)))
                sub_op = input("Selección: ").strip()
                
                if sub_op.isdigit() and 1 <= int(sub_op) <= len(correos_cargados):
                    correo_sel = correos_cargados[int(sub_op) - 1]
                    selected_id = correo_sel['id']
                    
                    print(f"\nAcciones para: \"{correo_sel['asunto']}\"")
                    print("[L] Marcar como leído")
                    print("[A] Archivar (quitar de Recibidos)")
                    print("[B] Enviar a la papelera (Borrar)")
                    print("[N] Abrir en el navegador web")
                    print("[C] Cancelar")
                    accion = input("Acción (L/A/B/N/C): ").strip().upper()
                    
                    if accion == 'L':
                        marcar_como_leido(service, selected_id)
                    elif accion == 'A':
                        archivar_correo(service, selected_id)
                    elif accion == 'B':
                        borrar_correo(service, selected_id)
                    elif accion == 'N':
                        abrir_en_navegador(selected_id)
                    else:
                        print("Acción cancelada.")
            except Exception as e:
                print(f"Error al listar correos: {e}")
                
        elif opcion == '2':
            iniciar_monitor(service, intervalo_segundos=intervalo_monitor)
        elif opcion == '3':
            print("\nSaliendo del programa. ¡Hasta luego!")
            break
        else:
            print("Opción inválida. Intenta nuevamente.")

def iniciar_monitor(service, intervalo_segundos: int = 120) -> None:
    """Monitorea la bandeja de entrada periódicamente y emite notificaciones de escritorio."""
    print("\nIniciando servicio de notificación en segundo plano...")
    print(f"Comprobando nuevos mensajes cada {intervalo_segundos} segundos. Presiona Ctrl+C para volver al menú.\n")
    
    try:
        ids_notificados = set()
        mensajes_iniciales = obtener_mensajes_no_leidos(service, max_results=50)
        if mensajes_iniciales:
            ids_notificados.update({msg['id'] for msg in mensajes_iniciales})
        
        while True:
            messages = obtener_mensajes_no_leidos(service, max_results=50)
            
            if messages:
                current_ids = {msg['id'] for msg in messages}
                nuevos_ids = current_ids - ids_notificados
                
                for msg in messages:
                    msg_id = msg['id']
                    if msg_id in nuevos_ids:
                        detalles = obtener_detalles_mensaje(service, msg_id)
                        remitente = detalles['remitente']
                        asunto = detalles['asunto']
                        snippet = detalles['snippet']
                        hora = time.strftime('%H:%M:%S')
                        print(f"[{hora}] 📩 De: {remitente} | Asunto: {asunto}")
                        mostrar_notificacion(asunto, remitente, snippet=snippet)
                        ids_notificados.add(msg_id)
                
                ids_notificados = ids_notificados.intersection(current_ids)
            else:
                ids_notificados.clear()
                
            time.sleep(intervalo_segundos)
    except KeyboardInterrupt:
        print("\nSaliendo del modo monitor...")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Gestor y notificador de correos de Gmail en terminal."
    )
    parser.add_argument(
        "--monitor", "-m",
        action="store_true",
        help="Iniciar directamente el servicio de monitoreo en segundo plano."
    )
    parser.add_argument(
        "--intervalo", "-i",
        type=int,
        default=120,
        help="Intervalo de sondeo en segundos para el modo monitor (por defecto: 120)."
    )
    parser.add_argument(
        "--limite", "-n",
        type=int,
        default=10,
        help="Cantidad de correos no leídos a mostrar en la lista (por defecto: 10)."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    creds = autenticar_gmail()
    if not creds:
        sys.exit(1)
        
    service = obtener_servicio_gmail(creds)
    
    if args.monitor:
        iniciar_monitor(service, intervalo_segundos=args.intervalo)
    else:
        menu_interactivo(service, limite_correos=args.limite, intervalo_monitor=args.intervalo)

if __name__ == '__main__':
    main()
