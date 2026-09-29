# ComicCraft — AI Comic Story Creator

ComicCraft is an end-to-end web application that turns a user story prompt into a five-panel comic. It follows the project documentation's architecture: HTML/Jinja2 frontend, FastAPI backend, Gemini-based outline/story generation, Stable Diffusion-based image generation, layout assembly, and PDF export.

## What was implemented

The original documentation describes these main inputs: story prompt, main character, setting, story tone, and art style. The implemented app keeps those inputs and provides three frontend pages plus a developer image-test utility.

The core pipeline is:

1. `generate_outline()` creates exactly five panel outlines.
2. `generate_story()` expands those outlines into captions, narration, and dialogue.
3. `generate_image()` creates one illustration for every panel.
4. `build_comic_layout()` joins text and images into renderable panel records.
5. `save_pdf()` exports the five panels to a PDF.
6. `/generate`, `/generate-comic/json`, `/download/{filename}`, `/export-success`, and `/test-image` expose the browser/API workflow.

The source document originally names Gemini 1.5 Flash and Gemini 1.5 Pro. Those model IDs are no longer a good default for a new 2026 build, so the code makes the model names configurable in `.env`; the included defaults use a current Gemini 3.8 Flash model for outline generation and Gemini 2.5 Pro for detailed story writing. Google's current Gemini documentation shows `gemini-3.8-flash` as a stable model and confirms structured output support. See the project notes below for citations.

For image generation, the default is Hugging Face Inference Providers with Stable Diffusion 3.5 Large. The project also includes an optional local Diffusers provider and a `mock` provider for tests and UI development.

## Project structure

```text
ComicCraft/
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ schemas.py
│  ├─ gemini_client.py
│  ├─ gemini_flash.py
│  ├─ gemini_pro.py
│  ├─ image_generator.py
│  ├─ layout_builder.py
│  ├─ exporters.py
│  ├─ routes.py
│  └─ main.py
├─ templates/
│  ├─ index.html
│  ├─ comic_preview.html
│  ├─ export_success.html
│  └─ test_image.html
├─ static/
│  ├─ app.css
│  ├─ app.js
│  ├─ panels/.gitkeep
│  └─ exports/.gitkeep
├─ tests/
│  └─ test_app.py
├─ .env.example
├─ .gitignore
├─ .dockerignore
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ requirements-local.txt
└─ README.md
```

## VS Code setup (Windows)

Open the `ComicCraft` folder in VS Code.

Create a virtual environment:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
```

Install the main dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your API keys.

```powershell
copy .env.example .env
```

Start the app:

```powershell
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000 — web UI
- http://127.0.0.1:8000/docs — Swagger API docs
- http://127.0.0.1:8000/health — configuration/status check

## Fastest way to test without API keys

Use the built-in mock provider. This exercises the FastAPI routes, Jinja templates, layout builder, and PDF exporter without making network calls.

In `.env`:

```dotenv
IMAGE_PROVIDER=mock
GEMINI_API_KEY=
HF_TOKEN=
```

Run:

```powershell
uvicorn app.main:app --reload
```

Then create a comic from the homepage. The generated images are intentionally simple test illustrations, but the full application flow and PDF export are real.

Run automated tests:

```powershell
pytest -q
```

## Real Gemini + Hugging Face generation

Set:

```dotenv
GEMINI_API_KEY=...
HF_TOKEN=...
IMAGE_PROVIDER=hf
```

The app uses the modern `google-genai` Python SDK (`from google import genai`) and Gemini structured output rather than the older `google-generativeai` SDK. The current Google API documentation shows `client.models.generate_content(...)` and structured JSON output through `response_mime_type` / `response_schema`.

For image generation, the app uses `huggingface_hub.InferenceClient.text_to_image(...)`. Hugging Face documents Inference Providers as a way to run text-to-image models with a token and provider routing.

## Optional: self-host Stable Diffusion with Diffusers

Install the optional local stack:

```powershell
pip install -r requirements-local.txt
```

Then configure:

```dotenv
IMAGE_PROVIDER=diffusers
LOCAL_DEVICE=auto
LOCAL_DIFFUSION_MODEL=stable-diffusion-v1-5/stable-diffusion-v1-5
```

The first local generation downloads model weights from Hugging Face and needs suitable CPU/GPU memory. This mode is intentionally separate from the default HF Inference Providers path so a normal laptop can run the rest of the application without downloading a multi-gigabyte local model.

## API example

POST `/generate-comic/json` with:

```json
{
  "story_prompt": "A brave fox explores an enchanted forest and discovers a hidden clock.",
  "character_name": "Ember",
  "setting": "forest",
  "tone": "dramatic",
  "art_style": "comic book"
}
```

The response contains the title, request data, five rendered layout records, the PDF filesystem path, and the browser download URL.

## API image test

The documentation calls for `/test-image`. In the implemented version the browser route supports both GET and POST, so you can quickly test an image prompt in the UI.

## Error handling

The backend validates form/JSON inputs with Pydantic, verifies that required API credentials exist, checks that exactly five panels are returned, and constrains PDF download paths to the generated export directory.

## Docker

With a populated `.env`:

```powershell
docker compose up --build
```

Then open http://127.0.0.1:8000.

## Notes on the supplied project document

The supplied document is a 23-page project guide. Page 2 contains the architecture diagram showing browser → FastAPI → Jinja templates → AI generation → layout builder → PDF exporter → comic preview/export success. Pages 4–6 describe Gemini Flash for structured outline generation, Gemini Pro for detailed narration/dialogue, and Stable Diffusion for illustrations. Pages 7–11 define the functions `generate_outline()`, `generate_story()`, `generate_image()`, `build_comic_layout()`, and `save_pdf()`. Pages 12–14 describe the `/`, `/generate`, `/generate-comic/json`, `/export-success`, and `/test-image` routes. Pages 15–22 describe the Jinja2 pages and PDF download flow.

The implementation above uses that organization while filling in the missing production details: typed schemas, safer file handling, structured Gemini JSON, configurable image providers, a working download route, tests, Docker, and a mock mode.

## VS Code automation files

The included `.vscode` folder contains a Uvicorn debug configuration, a Pytest configuration, and common install/run/test tasks. After opening the folder in VS Code, select the `.venv` interpreter and use the Run and Debug panel or Terminal → Run Task.
