from unittest.mock import MagicMock, patch
from pathlib import Path
from gmail_notify.auth import autenticar_gmail, SCOPES

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

def test_autenticar_gmail_sin_credentials(tmp_path):
    token_file = tmp_path / "token.json" # No existe
    cred_file = tmp_path / "credentials.json" # No existe
    
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
