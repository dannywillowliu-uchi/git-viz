from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from . import git_ops

app = FastAPI(title="git-viz")

HTML_PATH = Path(__file__).resolve().parent / "index.html"


@app.get("/")
async def index():
	return FileResponse(HTML_PATH, media_type="text/html")


def _resolve_repo_path(path: str | None) -> Path:
	if not path:
		raise HTTPException(status_code=400, detail="Missing required query parameter: path")
	resolved = Path(path).expanduser().resolve()
	if not resolved.exists():
		raise HTTPException(status_code=404, detail=f"Path does not exist: {path}")
	if not (resolved / ".git").is_dir():
		raise HTTPException(status_code=400, detail=f"Path is not a git repository: {path}")
	return resolved


@app.get("/api/repo")
async def get_repo(path: str | None = Query(default=None)):
	repo_path = _resolve_repo_path(path)
	return git_ops.get_repo_metadata(repo_path)


@app.get("/api/commits")
async def get_commits(path: str | None = Query(default=None), limit: int = Query(default=500)):
	repo_path = _resolve_repo_path(path)
	return git_ops.get_commits(repo_path, limit=limit)


@app.get("/api/tree")
async def get_tree(path: str | None = Query(default=None), commit: str = Query(default="HEAD")):
	repo_path = _resolve_repo_path(path)
	return git_ops.get_tree(repo_path, commit=commit)


@app.get("/api/activity")
async def get_activity(path: str | None = Query(default=None)):
	repo_path = _resolve_repo_path(path)
	return git_ops.get_activity(repo_path)
