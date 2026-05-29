"""Punto de entrada del servidor de desarrollo — se completa en Etapa 2."""
from app import create_app

if __name__ == "__main__":
    app = create_app()
    if app:
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        print("[run.py] App factory vacía — completar en Etapa 2.")
