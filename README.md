# Django Quickstart CLI Automation

This CLI tool automates the creation of a new Django project and its first app, preconfigured with your custom base preset files and environment setup. Designed for developers who repeatedly spin up Django projects and want the initial setup done in seconds — not minutes.

---

## Disclaimer

- Requires Python 3.11+ and Django installed globally (`pip install Django`).
- Intended for **local development** scaffolding — not for modifying live or existing projects.
- Running this in a non-empty directory will abort to prevent overwriting files.
- Automatically installs dependencies if `--install` is passed (requires internet access).
- Presets must exist inside the tool’s `/presets/` folder (`base`, `api`, `barber`, etc.).
- Do not include production secrets in preset `.env.template` files.
- The generated `.env` will contain a random Django `SECRET_KEY` each time.

---

## Usage

1. **Install the tool in editable mode** (once per machine, inside the root `djquickstart`):

```bash
pip install -e .
```

2. **Confirm installation worked:**

```bash
djquickstart --help
```

3. **Create a new Django project and its first app**:

```bash
djquickstart project <project_name> <app_name> --preset base [--install]
```

Example:

```bash
djquickstart project mysite blog --preset base --install
```

4. **Open the new project folder**:

```bash
cd mysite
python manage.py runserver
```

---

## What it Does

- Creates a **new folder** named after your project.
- Initializes a **flat Django layout** inside that folder (no double nesting).
- Copies your chosen **preset files** (`settings.py`, `.env.template`, `requirements.txt`).
- Generates a fresh `.env` with a unique `SECRET_KEY`.
- Creates the first **app** automatically (unless using a full project preset).
- Injects the app name into `INSTALLED_APPS` inside `settings.py`.
- Optionally installs dependencies listed in `requirements.txt` if `--install` is passed.

---

## Full Project Presets

You can use a **complete Django project** as a preset, not just individual files. This is useful if you have a standard project layout, preconfigured apps, or advanced settings you want to reuse.

### How it Works

1. Place your full Django project inside `djquickstart/presets/<preset_name>/`.
   - The project folder should contain `manage.py` and the inner project folder with `settings.py`.

2. Run:

```bash
djquickstart project <new_project_name> --preset <preset_name>
```

The CLI will:

- Copy the entire preset project into a new folder named `<new_project_name>`.
- Rename the inner project folder to match `<new_project_name>`.
- Update `settings.py`, `wsgi.py`, `asgi.py`, and `manage.py` to reference the new project name.
- Generate a fresh `.env` with a unique `SECRET_KEY`.

> No app injection occurs — the preset’s apps are preserved as-is.

### Example Preset Layout (`barber`)

```
barber/
├── manage.py
├── barber/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── blog/
├── .env.template
└── requirements.txt
```

### Creating a Project from the Preset

```bash
djquickstart project barbershop-web --preset barber
```

Resulting structure:

```
kirpykla/
├── manage.py
├── kirpykla/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── blog/
├── .env
└── requirements.txt
```

- `.env.template` is automatically converted to `.env` with a new `SECRET_KEY`.
- The original preset folder **is not modified**.

---

## Project Structure Example

```
mysite/
├── manage.py
├── mysite/
│   ├── settings.py     ← includes 'blog' in INSTALLED_APPS
│   ├── urls.py
│   └── ...
├── blog/
│   ├── models.py
│   ├── views.py
│   └── ...
├── .env
└── requirements.txt
```

---

## Troubleshooting

If you get an error like `'djquickstart' is not recognized as an internal or external command`:

1. Check where Python installs your scripts:

```bash
python -m site --user-base
```

Then navigate to that path and open the `Scripts` folder. Example: `C:\Users\<YourName>\AppData\Roaming\Python\Python313\Scripts`

2. If `djquickstart.exe` is there, add that folder to your PATH:

- Open **Start → Edit system environment variables**
- Click **Environment Variables**
- Under **User variables**, select `Path → Edit`
- Add: `C:\Users\<YourName>\AppData\Roaming\Python\Python313\Scripts`
- Restart PowerShell or CMD

3. Alternatively, run the tool directly with Python:

```bash
python -m djquickstart.cli --help
```

4. Still not working? Reinstall it:

```bash
pip uninstall djquickstart -y
pip install -e .
```

---

## Notes

- The tool won’t overwrite existing projects; delete or rename old directories before rerunning.
- Preset files should live under `djquickstart/presets/<preset_name>/`.
- Add or edit your own presets to match your usual stack (DRF, Tailwind, JWT, etc.).
- `.env.template` placeholders must use the format `{{SECRET_KEY}}`.
- Use `--install` only when you want to auto-install dependencies — otherwise skip it to stay fast.

---

## Examples

**Base project creation:**

```bash
djquickstart project booking_platform services
```

**With dependency install:**

```bash
djquickstart project shop ecommerce --preset base --install
```

**With a custom preset:**

```bash
djquickstart project api backend --preset api
```

**With a full Django project preset:**

```bash
djquickstart project really-great-project-name --preset test-project
```

