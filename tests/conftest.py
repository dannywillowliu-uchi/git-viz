import time

import git
import pytest
from starlette.testclient import TestClient

from git_viz.app import app


@pytest.fixture
def temp_git_repo(tmp_path):
	"""Factory fixture: creates a disposable git repo in a temp directory."""

	def _make_repo(*, commits=0, branches=None, authors=None):
		repo_dir = tmp_path / f"repo-{time.monotonic_ns()}"
		repo_dir.mkdir()
		repo = git.Repo.init(repo_dir)
		repo.config_writer().set_value("user", "name", "Test Author").release()
		repo.config_writer().set_value("user", "email", "test@example.com").release()

		default_author = git.Actor("Test Author", "test@example.com")

		for i in range(commits):
			fpath = repo_dir / f"file_{i}.txt"
			fpath.write_text(f"content {i}\n")
			repo.index.add([str(fpath)])

			if authors and i < len(authors):
				author = git.Actor(authors[i], f"{authors[i].lower().replace(' ', '.')}@example.com")
			else:
				author = default_author

			repo.index.commit(f"Commit {i}", author=author, committer=author)

		if branches:
			for branch_name in branches:
				repo.create_head(branch_name)

		return repo_dir

	return _make_repo


@pytest.fixture
def client():
	"""httpx-compatible TestClient against the FastAPI app."""
	return TestClient(app)


@pytest.fixture
def empty_repo(tmp_path):
	"""Git repo with init only, no commits."""
	repo_dir = tmp_path / f"empty-{time.monotonic_ns()}"
	repo_dir.mkdir()
	repo = git.Repo.init(repo_dir)
	repo.config_writer().set_value("user", "name", "Test Author").release()
	repo.config_writer().set_value("user", "email", "test@example.com").release()
	return repo_dir


@pytest.fixture
def single_commit_repo(tmp_path):
	"""One commit with a few files of different types."""
	repo_dir = tmp_path / f"single-{time.monotonic_ns()}"
	repo_dir.mkdir()
	repo = git.Repo.init(repo_dir)
	repo.config_writer().set_value("user", "name", "Test Author").release()
	repo.config_writer().set_value("user", "email", "test@example.com").release()

	(repo_dir / "file_0.txt").write_text("content 0\n")
	(repo_dir / "README.md").write_text("# Test Project\n")
	(repo_dir / "main.py").write_text("print('hello')\n")
	repo.index.add(["file_0.txt", "README.md", "main.py"])
	repo.index.commit("Commit 0")
	return repo_dir


@pytest.fixture
def multi_commit_repo(temp_git_repo):
	"""Five sequential commits for general testing."""
	return temp_git_repo(commits=5)


@pytest.fixture
def multi_branch_repo(tmp_path):
	"""Main + feature branch with divergent commits."""
	repo_dir = tmp_path / f"branched-{time.monotonic_ns()}"
	repo_dir.mkdir()
	repo = git.Repo.init(repo_dir)
	repo.config_writer().set_value("user", "name", "Test Author").release()
	repo.config_writer().set_value("user", "email", "test@example.com").release()

	# Two commits on main
	(repo_dir / "base.txt").write_text("base content\n")
	repo.index.add(["base.txt"])
	repo.index.commit("Base commit")

	(repo_dir / "main_file.txt").write_text("main branch work\n")
	repo.index.add(["main_file.txt"])
	repo.index.commit("Main commit 2")

	# Create feature branch from first commit
	base_commit = list(repo.iter_commits())[-1]
	feature = repo.create_head("feature", base_commit)
	feature.checkout()

	(repo_dir / "feature_file.txt").write_text("feature work\n")
	repo.index.add(["feature_file.txt"])
	repo.index.commit("Feature commit 1")

	(repo_dir / "feature_extra.txt").write_text("more feature work\n")
	repo.index.add(["feature_extra.txt"])
	repo.index.commit("Feature commit 2")

	# Switch back to main
	repo.heads.master.checkout() if "master" in [h.name for h in repo.heads] else repo.heads.main.checkout()

	return repo_dir


@pytest.fixture
def large_repo(tmp_path):
	"""100+ commits with varied files and multiple authors."""
	repo_dir = tmp_path / f"large-{time.monotonic_ns()}"
	repo_dir.mkdir()
	repo = git.Repo.init(repo_dir)
	repo.config_writer().set_value("user", "name", "Test Author").release()
	repo.config_writer().set_value("user", "email", "test@example.com").release()

	authors = [
		git.Actor("Alice Dev", "alice@example.com"),
		git.Actor("Bob Engineer", "bob@example.com"),
		git.Actor("Carol Tester", "carol@example.com"),
	]

	extensions = [".py", ".js", ".md", ".txt", ".json", ".css", ".html"]
	subdirs = ["src", "tests", "docs", "config"]

	for d in subdirs:
		(repo_dir / d).mkdir()

	for i in range(110):
		ext = extensions[i % len(extensions)]
		subdir = subdirs[i % len(subdirs)]
		fpath = repo_dir / subdir / f"file_{i}{ext}"
		fpath.write_text(f"content for file {i}\n" * ((i % 5) + 1))
		repo.index.add([str(fpath)])

		author = authors[i % len(authors)]
		repo.index.commit(f"Commit {i}: update {subdir}/file_{i}{ext}", author=author, committer=author)

	return repo_dir
