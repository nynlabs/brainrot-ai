# Brainrot AI Studio

**A browser-based AI video workflow companion for Kaggle, built around Hypit.**

Brainrot AI Studio brings reference-video analysis, character and asset uploads, selected Hypit CLI/media tools, configurable model APIs, and optional local image-to-video generation into a notebook-launched browser interface. Kaggle provides the backend compute; the UI is served through a temporary Gradio link.

> This is a community companion/fork, not an official Hypit.AI product. Hypit source code, CLI, and upstream components retain their original names and attribution. Read [`LICENSE`](LICENSE) and [`UPSTREAM_AND_LICENSE.md`](UPSTREAM_AND_LICENSE.md) before use or redistribution. The upstream license restricts certain hosted multi-tenant and commercial redistribution use cases. Public source availability does not remove those restrictions.

## Features in this build

- Chat-style assistant with optional Gemini and OpenAI-compatible API settings.
- Reference video/image/audio uploads and media analysis utilities.
- Selected Hypit status, diagnostics, probing, frame extraction, and contact sheets.
- Optional SVD-XT image-to-video generation and MP4 preview/export when dependencies and model weights are available.
- Output gallery and project-folder controls.

This is an **incremental companion UI**, not a complete reimplementation of every Hypit Studio/CLI feature. The app does not run arbitrary model-generated shell commands. SVD-XT creates motion from an image and does not automatically clone a reference video's exact actions.

## Start on Kaggle

Read the complete step-by-step guide: [`kaggle-studio/README.md`](kaggle-studio/README.md). In short: create a Kaggle notebook with Internet enabled as needed, enable GPU for local generation, clone this public repository, install `kaggle-studio/requirements.txt`, set `HYPIT_PROJECT_ROOT`, and run `kaggle-studio/app.py`. Keep your existing Hypit CLI install if it is already working.

```python
%cd /kaggle/working
!git clone https://github.com/YOUR-USERNAME/brainrot-ai.git
%pip install -r /kaggle/working/brainrot-ai/kaggle-studio/requirements.txt
```

Then launch from a notebook cell:

```python
import os
os.environ['HYPIT_PROJECT_ROOT'] = '/kaggle/working/hypit-video'
os.environ['GRADIO_SHARE'] = '1'
os.environ['PATH'] = '/kaggle/working/tools/node-v22/bin:' + os.environ.get('PATH', '')
%run /kaggle/working/brainrot-ai/kaggle-studio/app.py
```

Replace `YOUR-USERNAME` with your GitHub username. The public Gradio URL is temporary and works only while the notebook is running.

## Public GitHub repository setup

Suggested repository name: **`brainrot-ai`** (URL: `https://github.com/YOUR-USERNAME/brainrot-ai`). Set repository visibility to **Public** if you want anyone to browse and clone the source. Do not put API keys, private assets, videos, model weights, or personal data in the repo.

## License and attribution

This repository includes the upstream Hypit license. Read [`UPSTREAM_AND_LICENSE.md`](UPSTREAM_AND_LICENSE.md) and the complete [`LICENSE`](LICENSE). Do not remove upstream attribution. Publishing the source publicly is different from operating a hosted public service; the upstream license places additional restrictions on multi-tenant hosted access and commercial redistribution. Obtain written permission/a commercial license from the rights holder before offering a hosted multi-user service or commercially redistributing a derivative if required by that license.

## Status

The code and guide are packaged for community testing. Kaggle end-to-end operation, model downloads, API providers, and every Hypit command have not all been validated in every environment. Report issues with the notebook output and environment details.
