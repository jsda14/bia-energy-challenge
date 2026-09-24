"""Paquete de tests unitarios de la capa de dominio."""

from pathlib import Path
import sys

# Garantiza que backend esté en sys.path al ejecutar pytest directamente
backend_dir = Path(__file__).resolve().parents[3]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
