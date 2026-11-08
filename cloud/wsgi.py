"""Production WSGI entrypoint; set server secrets via environment variables."""
from .portal import create_app

app = create_app()
