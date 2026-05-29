import sys
from pathlib import Path

# Agrega backend/ al path para que pytest resuelva "from app.queries import ..."
# cuando se ejecuta desde la raíz del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parent))
