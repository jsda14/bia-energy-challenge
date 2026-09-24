"""Paquete de tests."""

from pathlib import Path
import sys

# Asegura que backend esté en el sys.path para imports de app.domain
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
