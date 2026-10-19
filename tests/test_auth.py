import os
import stat
from unittest.mock import MagicMock, patch
from pathlib import Path
from gmail_notify.auth import (
    autenticar_gmail,
    resolver_rutas_auth,
    guardar_token,
    obtener_directorio_config,
    SCOPES,
)

def test_obtener_directorio_config_con_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
    directorio = obtener_directorio_config()
    assert directorio == Path("/custom/config/gmail-notify")

def test_obtener_directorio_config_sin_xdg(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    directorio = obtener_directorio_config()
    assert directorio == Path.home() / ".config" / "gmail-notify"

def test_resolver_rutas_auth_xdg_existente(tmp_path, monkeypatch):
    xdg_dir = tmp_path / "config" / "gmail-notify"
    xdg_dir.mkdir(parents=True)
    (xdg_dir / "credentials.json").write_text("{}")
    (xdg_dir / "token.json").write_text("{}")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    tok, cred = resolver_rutas_auth()
    assert tok == xdg_dir / "token.json"
    assert cred == xdg_dir / "credentials.json"

def test_guardar_token_aplica_permisos_600(tmp_path):
    token_file = tmp_path / "token.json"
    mock_creds = MagicMock()
    mock_creds.to_json.return_value = '{"token": "secure"}'

    guardar_token(token_file, mock_creds)

    assert token_file.exists()
    assert token_file.read_text(encoding="utf-8") == '{"token": "secure"}'
    # Validar permisos 0o600 (-rw-------)
    modo = stat.S_IMODE(os.stat(token_file).st_mode)
    assert modo == 0o600

def test_autenticar_gmail_token_valido(tmp_path):
    token_file = tmp_path / "token.json"
    token_file.write_text('{"token": "dummy"}')
    
    mock_creds = MagicMock()
    mock_creds.valid = True
    
    with patch("gmail_notify.auth.Credentials.from_authorized_user_file", return_value=mock_creds) as mock_from_file:
        creds = autenticar_gmail(token_file=token_file)
        assert creds == mock_creds
        mock_from_file.assert_called_once_with(str(token_file), SCOPES)

def test_autenticar_gmail_token_expirado_renovado(tmp_path):
    token_file = tmp_path / "token.json"
    token_file.write_text('{"token": "expired"}')
    
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "dummy_refresh"
    mock_creds.to_json.return_value = '{"token": "renewed"}'
    
    with patch("gmail_notify.auth.Credentials.from_authorized_user_file", return_value=mock_creds):
        with patch("gmail_notify.auth.Request"):
            creds = autenticar_gmail(token_file=token_file)
            mock_creds.refresh.assert_called_once()
            assert creds == mock_creds
            assert token_file.read_text(encoding="utf-8") == '{"token": "renewed"}'
            modo = stat.S_IMODE(os.stat(token_file).st_mode)
            assert modo == 0o600

def test_autenticar_gmail_sin_credentials(tmp_path):
    token_file = tmp_path / "token.json"
    cred_file = tmp_path / "credentials.json"
    
    creds = autenticar_gmail(token_file=token_file, credentials_file=cred_file)
    assert creds is None

def test_autenticar_gmail_flujo_nuevo_exitoso(tmp_path):
    token_file = tmp_path / "token.json"
    cred_file = tmp_path / "credentials.json"
    cred_file.write_text('{"installed": {}}')
    
    mock_flow = MagicMock()
    mock_new_creds = MagicMock()
    mock_new_creds.to_json.return_value = '{"token": "fresh"}'
    mock_flow.run_local_server.return_value = mock_new_creds
    
    with patch("gmail_notify.auth.InstalledAppFlow.from_client_secrets_file", return_value=mock_flow) as mock_from_secrets:
        creds = autenticar_gmail(token_file=token_file, credentials_file=cred_file)
        assert creds == mock_new_creds
        mock_from_secrets.assert_called_once_with(str(cred_file), SCOPES)
        mock_flow.run_local_server.assert_called_once_with(port=0)
        assert token_file.read_text(encoding="utf-8") == '{"token": "fresh"}'
        modo = stat.S_IMODE(os.stat(token_file).st_mode)
        assert modo == 0o600

def test_autenticar_gmail_fallo_refresh_inicia_flujo(tmp_path):
    token_file = tmp_path / "token.json"
    token_file.write_text('{"token": "expired"}')
    cred_file = tmp_path / "credentials.json"
    cred_file.write_text('{"installed": {}}')
    
    mock_expired_creds = MagicMock()
    mock_expired_creds.valid = False
    mock_expired_creds.expired = True
    mock_expired_creds.refresh_token = "invalid_refresh"
    mock_expired_creds.refresh.side_effect = Exception("Revoked token")
    
    mock_new_creds = MagicMock()
    mock_new_creds.to_json.return_value = '{"token": "recovered"}'
    
    mock_flow = MagicMock()
    mock_flow.run_local_server.return_value = mock_new_creds
    
    with patch("gmail_notify.auth.Credentials.from_authorized_user_file", return_value=mock_expired_creds):
        with patch("gmail_notify.auth.InstalledAppFlow.from_client_secrets_file", return_value=mock_flow):
            creds = autenticar_gmail(token_file=token_file, credentials_file=cred_file)
            assert creds == mock_new_creds
            assert token_file.read_text(encoding="utf-8") == '{"token": "recovered"}'
            modo = stat.S_IMODE(os.stat(token_file).st_mode)
            assert modo == 0o600
