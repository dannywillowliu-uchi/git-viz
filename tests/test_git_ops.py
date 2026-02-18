import git
import pytest

from git_viz.git_ops import get_activity, get_commits, get_repo_metadata, get_tree


# --- get_repo_metadata ---


class TestGetRepoMetadata:
	def test_empty_repo(self, empty_repo):
		result = get_repo_metadata(empty_repo)
		assert result["commit_count"] == 0
		assert result["branch"] is None
		assert result["contributors"] == []
		assert result["name"] == empty_repo.name

	def test_single_commit(self, single_commit_repo):
		result = get_repo_metadata(single_commit_repo)
		assert result["commit_count"] == 1
		assert result["branch"] in ("main", "master")
		assert len(result["contributors"]) == 1
		assert result["contributors"][0]["name"] == "Test Author"
		assert result["contributors"][0]["commits"] == 1

	def test_multi_commit(self, multi_commit_repo):
		result = get_repo_metadata(multi_commit_repo)
		assert result["commit_count"] == 5

	def test_invalid_path(self, tmp_path):
		with pytest.raises(ValueError, match="Not a git repository"):
			get_repo_metadata(tmp_path)

	def test_nonexistent_path(self):
		with pytest.raises(ValueError, match="does not exist"):
			get_repo_metadata("/nonexistent/path")

	def test_detached_head(self, multi_commit_repo):
		repo = git.Repo(multi_commit_repo)
		first_commit = list(repo.iter_commits())[-1]
		repo.head.reference = first_commit
		result = get_repo_metadata(multi_commit_repo)
		assert "(detached)" in result["branch"]


# --- get_commits ---


class TestGetCommits:
	def test_empty_repo(self, empty_repo):
		result = get_commits(empty_repo)
		assert result == []

	def test_single_commit(self, single_commit_repo):
		result = get_commits(single_commit_repo)
		assert len(result) == 1
		c = result[0]
		assert "hash" in c
		assert c["author"] == "Test Author"
		assert c["email"] == "test@example.com"
		assert "date" in c
		assert c["message"] == "Commit 0"
		assert isinstance(c["files"], list)

	def test_commit_limit(self, multi_commit_repo):
		result = get_commits(multi_commit_repo, limit=2)
		assert len(result) == 2

	def test_file_stats_present(self, single_commit_repo):
		result = get_commits(single_commit_repo)
		files = result[0]["files"]
		assert len(files) >= 1
		f = files[0]
		assert "path" in f
		assert "insertions" in f
		assert "deletions" in f

	def test_commit_order_newest_first(self, multi_commit_repo):
		result = get_commits(multi_commit_repo)
		assert result[0]["message"] == "Commit 4"
		assert result[-1]["message"] == "Commit 0"

	def test_date_is_iso(self, single_commit_repo):
		result = get_commits(single_commit_repo)
		date_str = result[0]["date"]
		assert "T" in date_str
		assert "+" in date_str or "Z" in date_str


# --- get_tree ---


class TestGetTree:
	def test_empty_repo(self, empty_repo):
		result = get_tree(empty_repo)
		assert result["files"] == {}

	def test_single_commit(self, single_commit_repo):
		result = get_tree(single_commit_repo)
		assert "commit" in result
		assert len(result["files"]) >= 1
		for path, info in result["files"].items():
			assert info["type"] == "file"
			assert isinstance(info["size"], int)

	def test_specific_commit(self, multi_commit_repo):
		commits = get_commits(multi_commit_repo)
		oldest = commits[-1]["hash"]
		result = get_tree(multi_commit_repo, commit=oldest)
		assert result["commit"] == oldest
		# Oldest commit should have fewer files than HEAD
		head_tree = get_tree(multi_commit_repo)
		assert len(result["files"]) <= len(head_tree["files"])

	def test_invalid_commit(self, single_commit_repo):
		with pytest.raises(ValueError, match="Invalid commit reference"):
			get_tree(single_commit_repo, commit="deadbeef1234567890")


# --- get_activity ---


class TestGetActivity:
	def test_empty_repo(self, empty_repo):
		result = get_activity(empty_repo)
		assert result["commits_per_author"] == {}
		assert result["commits_over_time"] == []

	def test_single_commit(self, single_commit_repo):
		result = get_activity(single_commit_repo)
		assert result["commits_per_author"]["Test Author"] == 1
		assert len(result["commits_over_time"]) == 1
		assert result["commits_over_time"][0]["count"] == 1

	def test_multi_commit(self, multi_commit_repo):
		result = get_activity(multi_commit_repo)
		assert result["commits_per_author"]["Test Author"] == 5
		total = sum(w["count"] for w in result["commits_over_time"])
		assert total == 5

	def test_weekly_bucket_format(self, single_commit_repo):
		result = get_activity(single_commit_repo)
		week = result["commits_over_time"][0]["week"]
		# Format: YYYY-Www
		assert "-W" in week
		parts = week.split("-W")
		assert len(parts) == 2
		assert parts[0].isdigit()
		assert parts[1].isdigit()
