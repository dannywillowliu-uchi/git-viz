from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import git


def _open_repo(path: str | Path) -> git.Repo:
	resolved = Path(path).expanduser().resolve()
	if not resolved.exists():
		raise ValueError(f"Path does not exist: {path}")
	try:
		return git.Repo(resolved)
	except git.InvalidGitRepositoryError:
		raise ValueError(f"Not a git repository: {path}")


def _is_empty(repo: git.Repo) -> bool:
	try:
		repo.head.commit
		return False
	except ValueError:
		return True


def get_repo_metadata(path: str | Path) -> dict:
	repo = _open_repo(path)
	if _is_empty(repo):
		return {
			"name": Path(repo.working_dir).name,
			"branch": None,
			"commit_count": 0,
			"contributors": [],
		}

	try:
		branch = repo.active_branch.name
	except TypeError:
		branch = str(repo.head.commit.hexsha[:8]) + " (detached)"

	contributors: dict[str, int] = defaultdict(int)
	count = 0
	for c in repo.iter_commits():
		contributors[c.author.name] += 1
		count += 1

	contributor_list = [
		{"name": name, "commits": commits}
		for name, commits in sorted(contributors.items(), key=lambda x: -x[1])
	]

	return {
		"name": Path(repo.working_dir).name,
		"branch": branch,
		"commit_count": count,
		"contributors": contributor_list,
	}


def get_commits(path: str | Path, limit: int = 500) -> list[dict]:
	repo = _open_repo(path)
	if _is_empty(repo):
		return []

	result = []
	for c in repo.iter_commits(max_count=limit):
		files = []
		for fname, stat in c.stats.files.items():
			files.append({
				"path": fname,
				"insertions": stat.get("insertions", 0),
				"deletions": stat.get("deletions", 0),
			})

		result.append({
			"hash": c.hexsha,
			"author": c.author.name,
			"email": c.author.email,
			"date": datetime.fromtimestamp(c.committed_date, tz=timezone.utc).isoformat(),
			"message": c.message.strip(),
			"files": files,
		})

	return result


def _build_tree(tree: git.Tree) -> dict:
	result: dict[str, dict] = {}
	for blob in tree.traverse():
		if blob.type == "blob":
			result[blob.path] = {
				"type": "file",
				"size": blob.size,
			}
	return result


def get_tree(path: str | Path, commit: str = "HEAD") -> dict:
	repo = _open_repo(path)
	if _is_empty(repo):
		return {"commit": commit, "files": {}}

	try:
		commit_obj = repo.commit(commit)
	except (git.BadName, ValueError):
		raise ValueError(f"Invalid commit reference: {commit}")

	return {
		"commit": commit_obj.hexsha,
		"files": _build_tree(commit_obj.tree),
	}


def get_activity(path: str | Path) -> dict:
	repo = _open_repo(path)
	if _is_empty(repo):
		return {"commits_per_author": {}, "commits_over_time": []}

	commits_per_author: dict[str, int] = defaultdict(int)
	weekly_buckets: dict[str, int] = defaultdict(int)

	for c in repo.iter_commits():
		commits_per_author[c.author.name] += 1
		dt = datetime.fromtimestamp(c.committed_date, tz=timezone.utc)
		# ISO week bucket: YYYY-Www
		week_key = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
		weekly_buckets[week_key] += 1

	commits_over_time = [
		{"week": week, "count": count}
		for week, count in sorted(weekly_buckets.items())
	]

	return {
		"commits_per_author": dict(commits_per_author),
		"commits_over_time": commits_over_time,
	}
