# Brainrot AI Studio for Kaggle

**A community browser interface and workflow companion for Hypit.** The backend runs in your Kaggle notebook; you operate it from a temporary browser URL.

> **Attribution and license:** This repository contains Hypit source code and a companion interface. Hypit remains a project of Hypit.AI. The upstream `LICENSE` has additional restrictions beyond plain Apache-2.0, including restrictions on hosted multi-tenant services and commercial redistribution. Read it before publishing, redistributing, or offering hosted access. A public GitHub repository is not permission to remove attribution or bypass those conditions.

## What it currently does

- Chat-style assistant with optional Google Gemini or OpenAI-compatible API configuration.
- Reference video, character image, audio, and asset uploads into a selected project folder.
- Selected Hypit CLI operations for status, diagnostics, media probing, frame extraction, and contact sheets.
- Optional SVD-XT image-to-video generation when the Diffusers model and dependencies are available.
- Output listing and preview.

**Scope:** This is an additive companion UI, not a full reimplementation of every Hypit feature or the official Hypit Studio. It does not execute arbitrary AI-generated shell commands. SVD-XT is image-conditioned and does not by itself reproduce the exact motion of a reference video.

## Quick start in Kaggle

1. Create a Kaggle notebook and enable a GPU if you plan local video generation. Enable Internet if you need to clone the repo, install dependencies, or download models. Kaggle availability, quotas, storage, and session duration can change.
2. Clone your public repository (replace the URL with your own):

```python
%cd /kaggle/working
!git clone https://github.com/YOUR-USERNAME/brainrot-ai.git
%cd /kaggle/working/brainrot-ai
```

3. If you already have the Hypit CLI installed under `/kaggle/working/tools/node-v22`, preserve it. Otherwise install the CLI version permitted by the repository and its license: 

```python
import os
os.environ['PATH'] = '/kaggle/working/tools/node-v22/bin:' + os.environ.get('PATH', '')
```

If Hypit is installed somewhere else, set `HYPIT_BIN` to the executable path. Do not install over an existing setup unless you intend to change versions.

4. Install the browser app dependencies:

```python
%pip install -r /kaggle/working/brainrot-ai/kaggle-studio/requirements.txt
```

5. Create a separate project folder (this keeps generated files out of the Git clone):

```python
from pathlib import Path
project = Path('/kaggle/working/hypit-video')
(project / 'assets').mkdir(parents=True, exist_ok=True)
(project / 'output').mkdir(parents=True, exist_ok=True)
```

6. Launch the UI from a notebook cell:

```python
import os
os.environ['HYPIT_PROJECT_ROOT'] = '/kaggle/working/hypit-video'
os.environ['GRADIO_SHARE'] = '1'
os.environ['PATH'] = '/kaggle/working/tools/node-v22/bin:' + os.environ.get('PATH', '')
%run /kaggle/working/brainrot-ai/kaggle-studio/app.py
```

7. Open the Gradio public URL printed by the cell. It is temporary and works only while the notebook process/session is running. Do not share a running session if it contains private assets or credentials.

## If you are starting from a fresh Kaggle notebook

- Run the clone, dependency-install, project-folder, and launch steps above.
- Check `!which hypit` and `!hypit --help`. If the command is missing, install/configure the Hypit CLI according to the upstream project instructions and the license; then restart the app cell.
- For local video generation, confirm `torch.cuda.is_available()` and install/verify compatible `diffusers`, `transformers`, `accelerate`, and video export dependencies. Avoid downloading a model until checking available disk space.
- The SVD-XT model can consume several gigabytes and inference may be slow on Kaggle. Start with a short clip, low frame count, and modest inference steps.

## Configure AI APIs

Open **API Settings** in the UI. Set the provider, model ID, and API key. For OpenAI-compatible endpoints, also set the base URL. Use a model actually available to your account. API usage may cost money and is subject to provider quotas and terms. Keys should be entered at runtime, not committed to GitHub or pasted into public notebook output.

## Save your outputs

Kaggle `/kaggle/working` storage is temporary. Download outputs from the UI or use Kaggle's notebook output/version workflow before the session ends. Never commit private videos, character images, model weights, API keys, `.env` files, or personal data to a public repository.

## Troubleshooting

- **`hypit: command not found`:** Check `!which hypit`, add the actual CLI folder to `PATH`, or set `HYPIT_BIN`.
- **UI cannot find project:** Set `HYPIT_PROJECT_ROOT` before launching and ensure the folder exists.
- **Gradio URL does not open:** Confirm the launch cell is still running and Internet/share access is allowed by the environment. Restart the app cell if the session has stopped.
- **GPU out of memory:** Reduce frames/resolution/steps, close other GPU jobs, and use CPU offload if supported.
- **Model download/storage error:** Check `shutil.disk_usage('/kaggle/working')` before retrying; do not repeatedly download a large checkpoint.
- **API error:** Verify provider, model name, key, quota, and account access.

## Repository layout

- `kaggle-studio/`: community browser UI and Kaggle instructions.
- `README.md`: project overview and full beginner guide.
- `UPSTREAM_AND_LICENSE.md`: attribution, licensing and public-access notes.
- `LICENSE`: upstream license included with the source.

For exact supported Hypit commands, consult the repository docs and `hypit --help`. The UI intentionally exposes selected safe workflows rather than claiming all CLI functionality has a GUI.
