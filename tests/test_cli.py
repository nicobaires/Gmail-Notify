from unittest.mock import MagicMock, patch
import pytest
from gmail_notify.cli import (
    parse_args,
    abrir_en_navegador,
    iniciar_monitor,
    menu_interactivo,
    main,
)

def test_parse_args_valores_por_defecto():
    with patch("sys.argv", ["gmail-notify"]):
        args = parse_args()
        assert args.monitor is False
        assert args.intervalo == 120
        assert args.limite == 10

def test_parse_args_personalizados():
    with patch("sys.argv", ["gmail-notify", "--monitor", "-i", "45", "-n", "20"]):
        args = parse_args()
        assert args.monitor is True
        assert args.intervalo == 45
        assert args.limite == 20

def test_abrir_en_navegador():
    with patch("webbrowser.open") as mock_open:
        abrir_en_navegador("msg_xyz")
        mock_open.assert_called_once_with("https://mail.google.com/mail/u/0/#inbox/msg_xyz")

def test_iniciar_monitor_detecta_nuevo_correo():
    mock_service = MagicMock()
    # Primera llamada (inicial): sin correos. Segunda llamada: nuevo correo. Tercera llamada: KeyboardInterrupt para salir.
    mensajes_paso_1 = []
    mensajes_paso_2 = [{"id": "new_001"}]
    
    with patch("gmail_notify.cli.obtener_mensajes_no_leidos", side_effect=[mensajes_paso_1, mensajes_paso_2]) as mock_get_msgs, \
         patch("gmail_notify.cli.obtener_detalles_mensaje") as mock_get_det, \
         patch("gmail_notify.cli.mostrar_notificacion") as mock_notif, \
         patch("time.sleep", side_effect=KeyboardInterrupt):
        
        mock_get_det.return_value = {
            "id": "new_001",
            "remitente": "rem@test.com",
            "asunto": "Urgente",
            "snippet": "Cuerpo del correo"
        }
        
        iniciar_monitor(mock_service, intervalo_segundos=10)
        
        mock_notif.assert_called_once_with("Urgente", "rem@test.com", snippet="Cuerpo del correo")

def test_menu_interactivo_salir():
    mock_service = MagicMock()
    with patch("builtins.input", side_effect=["3"]):
        menu_interactivo(mock_service)

def test_menu_interactivo_sin_correos():
    mock_service = MagicMock()
    with patch("gmail_notify.cli.obtener_mensajes_no_leidos", return_value=[]), \
         patch("builtins.input", side_effect=["1", "3"]):
        menu_interactivo(mock_service)

def test_menu_interactivo_acciones():
    mock_service = MagicMock()
    mensajes = [{"id": "m1"}]
    detalles = {
        "id": "m1",
        "remitente": "alguien@test.com",
        "asunto": "Tema",
        "fecha": "Hoy",
        "snippet": "Previa"
    }
    
    # 1. Probar acción Leer (L)
    with patch("gmail_notify.cli.obtener_mensajes_no_leidos", return_value=mensajes), \
         patch("gmail_notify.cli.obtener_detalles_mensaje", return_value=detalles), \
         patch("gmail_notify.cli.marcar_como_leido") as mock_leer, \
         patch("builtins.input", side_effect=["1", "1", "L", "3"]):
        menu_interactivo(mock_service)
        mock_leer.assert_called_once_with(mock_service, "m1")

    # 2. Probar acción Archivar (A)
    with patch("gmail_notify.cli.obtener_mensajes_no_leidos", return_value=mensajes), \
         patch("gmail_notify.cli.obtener_detalles_mensaje", return_value=detalles), \
         patch("gmail_notify.cli.archivar_correo") as mock_archivar, \
         patch("builtins.input", side_effect=["1", "1", "A", "3"]):
        menu_interactivo(mock_service)
        mock_archivar.assert_called_once_with(mock_service, "m1")

    # 3. Probar acción Borrar (B)
    with patch("gmail_notify.cli.obtener_mensajes_no_leidos", return_value=mensajes), \
         patch("gmail_notify.cli.obtener_detalles_mensaje", return_value=detalles), \
         patch("gmail_notify.cli.borrar_correo") as mock_borrar, \
         patch("builtins.input", side_effect=["1", "1", "B", "3"]):
        menu_interactivo(mock_service)
        mock_borrar.assert_called_once_with(mock_service, "m1")

    # 4. Probar acción Navegador (N)
    with patch("gmail_notify.cli.obtener_mensajes_no_leidos", return_value=mensajes), \
         patch("gmail_notify.cli.obtener_detalles_mensaje", return_value=detalles), \
         patch("gmail_notify.cli.abrir_en_navegador") as mock_nav, \
         patch("builtins.input", side_effect=["1", "1", "N", "3"]):
        menu_interactivo(mock_service)
        mock_nav.assert_called_once_with("m1")

def test_main_autenticacion_fallida():
    with patch("sys.argv", ["gmail-notify"]), \
         patch("gmail_notify.cli.autenticar_gmail", return_value=None):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

def test_main_modo_monitor():
    with patch("sys.argv", ["gmail-notify", "--monitor"]), \
         patch("gmail_notify.cli.autenticar_gmail", return_value=MagicMock()), \
         patch("gmail_notify.cli.obtener_servicio_gmail"), \
         patch("gmail_notify.cli.iniciar_monitor") as mock_monitor:
        main()
        mock_monitor.assert_called_once()

