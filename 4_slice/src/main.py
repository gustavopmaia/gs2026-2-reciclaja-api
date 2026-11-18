"""Entrada do servidor: uvicorn main:app --app-dir src"""

from api.app import create_app

app = create_app()
