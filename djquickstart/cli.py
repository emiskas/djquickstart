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
@click.argument("app_name")
@click.option("--preset", default="base", help="Choose project preset")
@click.option("--install", is_flag=True, help="Install dependencies automatically")
def project(project_name, app_name, preset, install):
    """Create Django project and app with chosen preset."""
    click.echo(f"Starting Django project '{project_name}' with preset '{preset}'")

    preset_path = PRESETS_DIR / preset
    if not preset_path.exists():
        click.echo(f"Preset '{preset}' not found.")
        raise SystemExit(1)

    # Clean names for Python imports
    safe_project_name = project_name.replace("-", "_")
    safe_app_name = app_name.replace("-", "_")

    # 1. Determine where the project will live
    project_root = Path.cwd() / project_name

    if project_root.exists() and any(project_root.iterdir()):
        click.echo(f"Directory '{project_name}' already exists and is not empty.")
        raise SystemExit(1)

    project_root.mkdir(exist_ok=True)

    # 2. Run django-admin inside that directory (flat layout)
    subprocess.run(
        ["django-admin", "startproject", safe_project_name, "."],
        check=True,
        cwd=project_root,
    )

    inner_project_path = project_root / safe_project_name

    # 3. Copy custom preset settings.py INTO the inner project folder (if provided)
    src_settings = preset_path / "settings.py"
    target_settings = inner_project_path / "settings.py"

    if src_settings.exists():
        shutil.copy(src_settings, target_settings)

        # Fix project references inside the preset settings
        fix_project_references(target_settings, safe_project_name)

    # 4. Create the app inside the project
    subprocess.run(
        ["python", "manage.py", "startapp", safe_app_name],
        check=True,
        cwd=project_root,
    )

    # 5. Now safely add app to INSTALLED_APPS
    add_app_to_settings(target_settings, safe_app_name)

    # 6. Copy remaining preset files (requirements.txt only)
    ALLOWED_PRESET_FILES = {"requirements.txt"}
    for file in preset_path.iterdir():
        if file.name not in ALLOWED_PRESET_FILES:
            continue
        shutil.copy(file, project_root / file.name)

    # 7. Handle .env.template → .env with SECRET_KEY
    template_env = preset_path / ".env.template"
    env_path = project_root / ".env"

    if template_env.exists():
        content = template_env.read_text().replace(
            "{{SECRET_KEY}}", get_random_secret_key()
        )
        env_path.write_text(content)

    # 8. Optionally install dependencies
    if install:
        subprocess.run(
            ["pip", "install", "-r", "requirements.txt"],
            check=False,
            cwd=project_root,
        )

    click.echo(f"Project '{project_name}' with app '{app_name}' is ready.")


if __name__ == "__main__":
    cli()
