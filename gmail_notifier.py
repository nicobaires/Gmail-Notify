#!/usr/bin/env python3
"""Punto de entrada directo para el gestor y notificador de Gmail."""

import sys
from pathlib import Path

# Asegurar que el paquete en src esté en el path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gmail_notify.cli import main

if __name__ == "__main__":
    main()