# git-viz - Project Instructions

Browser-based git repository visualizer with interactive force-directed graphs of commit history, file relationships, and contributor activity.

## Tech Stack

- Python 3.12+, FastAPI, uvicorn
- GitPython for git operations (fall back to subprocess if simpler for specific operations)
- D3.js via CDN for force-directed graph visualization
- Single self-contained HTML file for frontend (inline CSS/JS, no build tools)

## Project Structure

```
src/git_viz/       # All backend code
  __init__.py
  app.py           # FastAPI app, route definitions, serves frontend HTML
  git_ops.py       # Git repository operations (reading commits, trees, activity)
tests/             # All tests
  conftest.py      # Shared fixtures (temp git repo factory)
  test_api.py      # Backend endpoint tests using httpx TestClient
```

## Coding Standards

- Indentation: Tabs
- Quotes: Double quotes
- Comments: Minimal, only when logic is complex
- Type hints: Use where beneficial
- No emojis in code, commits, or messages

## API Endpoints

1. `GET /` -- Serve the frontend HTML file
2. `GET /api/repo?path=<path>` -- Repo metadata (name, branch, commit count, contributors)
3. `GET /api/commits?path=<path>&limit=500` -- Commit history with file stats
4. `GET /api/tree?path=<path>&commit=<hash>` -- File tree at a given commit
5. `GET /api/activity?path=<path>` -- Contributor activity data

## Frontend Requirements

- Force-directed graph: files as nodes, directories as clusters, edges connect co-modified files
- Node size = file size (log scale), node color = file extension
- Timeline slider with play/pause for animated commit playback
- Sidebar: contributor list with filtering, file path search
- Activity sparkline/bar chart
- Dark theme, smooth CSS transitions, responsive layout
- Must handle repos with 1000+ commits without freezing

## Architecture Constraints

- Backend serves JSON, frontend fetches on load and caches client-side
- No WebSocket -- load all data upfront, animate client-side
- Frontend HTML must be fully self-contained (inline styles, inline JS, CDN for D3 only)
- Keep git operations efficient -- avoid loading full diffs for large repos

## Testing

- Use httpx TestClient for backend tests
- Create temp git repos as pytest fixtures for testing
- Test scenarios: empty repo, single-commit repo, multi-branch repo, repo with 100+ commits
- Test each endpoint returns correct JSON structure

## Verification

```bash
.venv/bin/python -m pytest -q && .venv/bin/ruff check src/
```
