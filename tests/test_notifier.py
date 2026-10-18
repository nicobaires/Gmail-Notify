from unittest.mock import patch
from gmail_notify.notifier import mostrar_notificacion

def test_mostrar_notificacion_exitoso():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        resultado = mostrar_notificacion("Asunto de prueba", "remitente@test.com")
        
        assert resultado is True
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd[0] == "notify-send"
        assert cmd[1] == "Nuevo correo de Gmail"
        assert "remitente@test.com" in cmd[2]
        assert "Asunto de prueba" in cmd[2]
        assert "-i" in cmd
        assert "mail-unread" in cmd

def test_mostrar_notificacion_con_snippet():
    with patch("subprocess.run") as mock_run:
        resultado = mostrar_notificacion(
            asunto="Reunión",
            remitente="jefe@test.com",
            snippet="Hola equipo &amp; amigos"
        )
        assert resultado is True
        args, _ = mock_run.call_args
        mensaje = args[0][2]
        assert "Hola equipo & amigos" in mensaje

def test_mostrar_notificacion_snippet_largo_truncado():
    snippet_largo = "A" * 150
    with patch("subprocess.run") as mock_run:
        resultado = mostrar_notificacion("Largo", "test@test.com", snippet=snippet_largo)
        assert resultado is True
        args, _ = mock_run.call_args
        mensaje = args[0][2]
        assert "..." in mensaje
        # Verificar que el largo del snippet truncado no exceda 120 caracteres
        lineas = mensaje.split("\n")
        assert len(lineas) >= 3
        assert len(lineas[2]) <= 120

def test_mostrar_notificacion_comando_no_encontrado():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        resultado = mostrar_notificacion("Asunto", "remitente")
        assert resultado is False

def test_mostrar_notificacion_error_generico():
    with patch("subprocess.run", side_effect=Exception("Error desconocido")):
        resultado = mostrar_notificacion("Asunto", "remitente")
        assert resultado is False

