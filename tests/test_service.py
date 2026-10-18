from unittest.mock import MagicMock, patch
from gmail_notify.service import (
    obtener_servicio_gmail,
    obtener_mensajes_no_leidos,
    obtener_detalles_mensaje,
    marcar_como_leido,
    borrar_correo,
    archivar_correo,
)

def test_obtener_servicio_gmail():
    mock_creds = MagicMock()
    with patch("gmail_notify.service.build") as mock_build:
        mock_build.return_value = MagicMock()
        service = obtener_servicio_gmail(mock_creds)
        mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds)
        assert service is not None

def test_obtener_mensajes_no_leidos():
    mock_service = MagicMock()
    mock_list = mock_service.users().messages().list
    mock_list.return_value.execute.return_value = {
        "messages": [{"id": "123", "threadId": "t1"}, {"id": "456", "threadId": "t2"}]
    }
    
    mensajes = obtener_mensajes_no_leidos(mock_service, max_results=5)
    assert len(mensajes) == 2
    assert mensajes[0]["id"] == "123"
    assert mensajes[1]["id"] == "456"

def test_obtener_mensajes_no_leidos_error():
    mock_service = MagicMock()
    mock_service.users().messages().list.side_effect = Exception("API error")
    mensajes = obtener_mensajes_no_leidos(mock_service)
    assert mensajes == []

def test_obtener_detalles_mensaje_completo():
    mock_service = MagicMock()
    mock_get = mock_service.users().messages().get
    mock_get.return_value.execute.return_value = {
        "id": "msg_001",
        "snippet": "Este es el cuerpo &amp; previa",
        "payload": {
            "headers": [
                {"name": "From", "value": "remitente@test.com"},
                {"name": "Subject", "value": "Aviso importante"},
                {"name": "Date", "value": "Sun, 18 Oct 2026 10:00:00 -0300"},
            ]
        }
    }
    
    detalles = obtener_detalles_mensaje(mock_service, "msg_001")
    assert detalles["id"] == "msg_001"
    assert detalles["remitente"] == "remitente@test.com"
    assert detalles["asunto"] == "Aviso importante"
    assert detalles["fecha"] == "Sun, 18 Oct 2026 10:00:00 -0300"
    assert detalles["snippet"] == "Este es el cuerpo & previa"

def test_obtener_detalles_mensaje_sin_cabeceras():
    mock_service = MagicMock()
    mock_get = mock_service.users().messages().get
    mock_get.return_value.execute.return_value = {
        "id": "msg_002",
        "snippet": "Sin headers",
        "payload": {}
    }
    
    detalles = obtener_detalles_mensaje(mock_service, "msg_002")
    assert detalles["id"] == "msg_002"
    assert detalles["remitente"] == "Desconocido"
    assert detalles["asunto"] == "Sin asunto"
    assert detalles["fecha"] == ""

def test_obtener_detalles_mensaje_error():
    mock_service = MagicMock()
    mock_service.users().messages().get.side_effect = Exception("Not found")
    detalles = obtener_detalles_mensaje(mock_service, "msg_error")
    assert detalles["id"] == "msg_error"
    assert detalles["remitente"] == "Desconocido"
    assert detalles["asunto"] == "Sin asunto"

def test_marcar_como_leido_exitoso():
    mock_service = MagicMock()
    exito = marcar_como_leido(mock_service, "msg_123")
    assert exito is True
    mock_service.users().messages().batchModify.assert_called_once_with(
        userId="me",
        body={"ids": ["msg_123"], "removeLabelIds": ["UNREAD"]}
    )

def test_marcar_como_leido_error():
    mock_service = MagicMock()
    mock_service.users().messages().batchModify.side_effect = Exception("Mod error")
    exito = marcar_como_leido(mock_service, "msg_123")
    assert exito is False

def test_borrar_correo_exitoso():
    mock_service = MagicMock()
    exito = borrar_correo(mock_service, "msg_123")
    assert exito is True
    mock_service.users().messages().trash.assert_called_once_with(userId="me", id="msg_123")

def test_borrar_correo_error():
    mock_service = MagicMock()
    mock_service.users().messages().trash.side_effect = Exception("Trash error")
    exito = borrar_correo(mock_service, "msg_123")
    assert exito is False

def test_archivar_correo_exitoso():
    mock_service = MagicMock()
    exito = archivar_correo(mock_service, "msg_123")
    assert exito is True
    mock_service.users().messages().batchModify.assert_called_once_with(
        userId="me",
        body={"ids": ["msg_123"], "removeLabelIds": ["INBOX"]}
    )

def test_archivar_correo_error():
    mock_service = MagicMock()
    mock_service.users().messages().batchModify.side_effect = Exception("Archive error")
    exito = archivar_correo(mock_service, "msg_123")
    assert exito is False

