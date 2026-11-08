"""Run from PythonAnywhere's file editor to install the uploaded web bundle."""
from pathlib import Path
import subprocess
import venv


def main():
    home = Path.home()
    source = home/"lingostep-web"
    archive = home/"lingostep-web.zip"
    if not source.is_dir():
        from zipfile import ZipFile
        with ZipFile(archive) as uploaded:
            # This is the allowlisted source bundle made by build_web_bundle.py.
            for member in uploaded.namelist():
                target = (home/member).resolve()
                if not target.is_relative_to(source.resolve()):
                    raise ValueError("Unexpected path in deployment bundle")
            uploaded.extractall(home)
    environment = home/".virtualenvs/lingostep"
    python = environment/"bin/python"
    if not python.is_file():
        venv.EnvBuilder(with_pip=True, symlinks=True).create(environment)
    subprocess.run([str(python), "-m", "pip", "install", "-r",
                    str(source/"cloud/requirements-hosting.txt")], check=True)
    public_url = f"https://{home.name}.pythonanywhere.com"
    subprocess.run([str(python), str(source/"scripts/setup_hosted_web.py"),
                    "--url", public_url], check=True)
    wsgi = Path("/var/www")/(home.name+"_pythonanywhere_com_wsgi.py")
    if not wsgi.is_file():
        raise RuntimeError("Create the Manual Configuration web app before running this installer")
    wsgi.write_text("import sys\nsys.path.insert(0, "+repr(str(source))+ ")\n"
                    "from cloud.pythonanywhere_wsgi import application\n", encoding="utf-8")
    print("READY: Set the Web tab virtualenv to", environment)
    print("Source/working directory:", source)
    print("Then Reload the web app:", public_url)


if __name__ == "__main__":
    main()
