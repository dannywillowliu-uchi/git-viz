import os
import time

import git
import pytest


@pytest.fixture
def temp_git_repo(tmp_path):
	"""Factory fixture: creates a bare-bones git repo in a temp directory."""
	def _make_repo(*, commits=0, branches=None):
		repo_dir = tmp_path / f"repo-{time.monotonic_ns()}"
		repo_dir.mkdir()
		repo = git.Repo.init(repo_dir)
		repo.config_writer().set_value("user", "name", "Test Author").release()
		repo.config_writer().set_value("user", "email", "test@example.com").release()

		for i in range(commits):
			fpath = repo_dir / f"file_{i}.txt"
			fpath.write_text(f"content {i}\n")
			repo.index.add([str(fpath)])
			repo.index.commit(f"Commit {i}")

		if branches:
			for branch_name in branches:
				repo.create_head(branch_name)

		return repo_dir

	return _make_repo


@pytest.fixture
def empty_repo(temp_git_repo):
	return temp_git_repo(commits=0)


@pytest.fixture
def single_commit_repo(temp_git_repo):
	return temp_git_repo(commits=1)


@pytest.fixture
def multi_commit_repo(temp_git_repo):
	return temp_git_repo(commits=5)


@pytest.fixture
def multi_branch_repo(temp_git_repo):
	return temp_git_repo(commits=3, branches=["feature-a", "feature-b"])


@pytest.fixture
def large_repo(temp_git_repo):
	return temp_git_repo(commits=25)
