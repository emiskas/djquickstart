import re
import shutil
import subprocess
from pathlib import Path

import click
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent
PRESETS_DIR = BASE_DIR / "presets"


def add_app_to_settings(settings_path: Path, app_name: str):
    """Insert app_name into INSTALLED_APPS list if not already present."""
    content = settings_path.read_text()
    if app_name in content:
        return  # already added

    new_content = ""
    in_installed = False
    for line in content.splitlines():
        if "INSTALLED_APPS" in line:
            in_installed = True
        if in_installed and line.strip().startswith("]"):
            new_content += f"    '{app_name}',\n"
            in_installed = False
        new_content += line + "\n"

    settings_path.write_text(new_content)


def fix_project_references(settings_path: Path, safe_project_name: str):
    """Fix ROOT_URLCONF and WSGI_APPLICATION to match the new project name."""
    text = settings_path.read_text()

    text = re.sub(
        r'ROOT_URLCONF\s*=\s*["\'].*?["\']',
        f'ROOT_URLCONF = "{safe_project_name}.urls"',
        text,
    )

    text = re.sub(
        r'WSGI_APPLICATION\s*=\s*["\'].*?["\']',
        f'WSGI_APPLICATION = "{safe_project_name}.wsgi.application"',
        text,
    )

    settings_path.write_text(text)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("project_name")
@click.argument("app_name", required=False)
@click.option("--preset", default="base", help="Choose project preset")
@click.option("--install", is_flag=True, help="Install dependencies automatically")
def project(project_name, app_name, preset, install):
    """Create Django project or copy preset project."""
    click.echo(f"Starting Django project '{project_name}' with preset '{preset}'")

    preset_path = PRESETS_DIR / preset
    if not preset_path.exists():
        click.echo(f"Preset '{preset}' not found.")
        raise SystemExit(1)

    safe_project_name = project_name.replace("-", "_")
    project_root = Path.cwd() / project_name

    if project_root.exists() and any(project_root.iterdir()):
        click.echo(f"Directory '{project_name}' already exists and is not empty.")
        raise SystemExit(1)

    project_root.mkdir(exist_ok=True)

    # Detect if this preset is a full Django project
    is_full_project = (preset_path / "manage.py").exists()

    if is_full_project:
        # Copy entire preset project
        shutil.copytree(preset_path, project_root, dirs_exist_ok=True)

        # Dynamically find the folder containing settings.py
        inner_project_dirs = [
            d for d in project_root.iterdir() if (d / "settings.py").exists()
        ]
        if not inner_project_dirs:
            raise SystemExit(f"No settings.py found in preset '{preset}'")
        inner_project_path = inner_project_dirs[0]
        target_settings = inner_project_path / "settings.py"

        # Rename inner folder to match new project name
        new_inner_path = project_root / safe_project_name
        if inner_project_path.name != safe_project_name:
            inner_project_path.rename(new_inner_path)
            inner_project_path = new_inner_path
            target_settings = inner_project_path / "settings.py"

        # Patch settings.py references
        fix_project_references(target_settings, safe_project_name)

        # patch wsgi/asgi
        for file_name in ["wsgi.py", "asgi.py"]:
            file_path = inner_project_path / file_name
            if file_path.exists():
                text = file_path.read_text()
                text = text.replace(
                    'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "barber.settings")',
                    f'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{safe_project_name}.settings")',
                )
                file_path.write_text(text)

        # patch manage.py
        manage_path = project_root / "manage.py"
        if manage_path.exists():
            text = manage_path.read_text()
            text = text.replace(
                'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "barber.settings")',
                f'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{safe_project_name}.settings")',
            )
            manage_path.write_text(text)
    else:
        # Standard startproject flow
        subprocess.run(
            ["django-admin", "startproject", safe_project_name, "."],
            check=True,
            cwd=project_root,
        )
        inner_project_path = project_root / safe_project_name

        # Copy preset settings.py if exists
        src_settings = preset_path / "settings.py"
        target_settings = inner_project_path / "settings.py"
        if src_settings.exists():
            shutil.copy(src_settings, target_settings)
            fix_project_references(target_settings, safe_project_name)

    # SECRET_KEY handling
    env_file = None
    for candidate in [".env.template", ".env"]:
        path = preset_path / candidate
        if path.exists():
            env_file = path
            break

    if env_file:
        content = env_file.read_text().replace("{{SECRET_KEY}}", get_random_secret_key())
        (project_root / ".env").write_text(content)
        click.echo(f"Created .env from preset template: {env_file.name}")

        # Delete the copied template from the project
        copied_template = project_root / env_file.name
        if copied_template.exists():
            try:
                copied_template.unlink()
                click.echo(f"Removed template from project: {copied_template.name}")
            except Exception as e:
                click.echo(f"Could not remove template from project: {copied_template} ({e})")

    else:
        # fallback: patch settings.py directly
        text = target_settings.read_text()
        text = re.sub(
            r'SECRET_KEY\s*=\s*["\'].*?["\']',
            f'SECRET_KEY = "{get_random_secret_key()}"',
            text,
        )
        target_settings.write_text(text)

    # App creation: skipped for full project presets
    if not is_full_project and app_name:
        safe_app_name = app_name.replace("-", "_")
        subprocess.run(
            ["python", "manage.py", "startapp", safe_app_name],
            check=True,
            cwd=project_root,
        )
        add_app_to_settings(target_settings, safe_app_name)

    # Copy allowed preset files (requirements.txt)
    ALLOWED_PRESET_FILES = {"requirements.txt"}
    for file in preset_path.iterdir():
        if file.name in ALLOWED_PRESET_FILES:
            shutil.copy(file, project_root / file.name)

    # Optionally install dependencies
    if install:
        subprocess.run(
            ["pip", "install", "-r", "requirements.txt"],
            check=False,
            cwd=project_root,
        )

    click.echo(f"Project '{project_name}' is ready.")


cli()
