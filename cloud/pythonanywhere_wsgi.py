"""Import this application from the WSGI file in PythonAnywhere's Web tab."""
from cloud.hosting import create_hosted_app

application = create_hosted_app()
