# git-viz

Browser-based git repository visualizer. Point it at any local repo and get an animated, interactive force-directed graph of commit history, file relationships, and contributor activity.

## Features

- Force-directed graph of files and commit relationships (D3.js)
- Timeline slider to scrub through commit history with animated playback
- Contributor filtering and activity charts
- Dark theme, responsive layout

## Stack

- **Backend:** FastAPI + GitPython
- **Frontend:** Single self-contained HTML file with inline CSS/JS, D3.js via CDN

## Development

```bash
uv sync
.venv/bin/uvicorn git_viz.app:app --reload
```

## Testing

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check src/
```
