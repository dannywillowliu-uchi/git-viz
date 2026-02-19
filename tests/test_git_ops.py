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
		assert result["branch"] == "main"
		assert len(result["contributors"]) == 1
		assert result["contributors"][0]["name"] == "Test Author"
		assert result["contributors"][0]["commits"] == 1

	def test_multi_commit(self, multi_commit_repo):
		result = get_repo_metadata(multi_commit_repo)
		assert result["commit_count"] == 5

	def test_multi_branch_active_branch(self, multi_branch_repo):
		result = get_repo_metadata(multi_branch_repo)
		assert result["branch"] == "main"

	def test_multi_branch_commit_count(self, multi_branch_repo):
		result = get_repo_metadata(multi_branch_repo)
		# main has 2 commits; feature branch commits are not on main
		assert result["commit_count"] == 2

	def test_large_repo_commit_count(self, large_repo):
		result = get_repo_metadata(large_repo)
		assert result["commit_count"] == 110

	def test_large_repo_multiple_contributors(self, large_repo):
		result = get_repo_metadata(large_repo)
		names = {c["name"] for c in result["contributors"]}
		assert names == {"Alice Dev", "Bob Engineer", "Carol Tester"}

	def test_large_repo_contributors_sorted_by_commits(self, large_repo):
		result = get_repo_metadata(large_repo)
		commit_counts = [c["commits"] for c in result["contributors"]]
		assert commit_counts == sorted(commit_counts, reverse=True)

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

	def test_single_commit_structure(self, single_commit_repo):
		result = get_commits(single_commit_repo)
		assert len(result) == 1
		c = result[0]
		assert len(c["hash"]) == 40
		assert c["author"] == "Test Author"
		assert c["email"] == "test@example.com"
		assert "date" in c
		assert c["message"] == "Commit 0"
		assert isinstance(c["files"], list)

	def test_single_commit_files(self, single_commit_repo):
		result = get_commits(single_commit_repo)
		paths = {f["path"] for f in result[0]["files"]}
		assert "file_0.txt" in paths
		assert "README.md" in paths
		assert "main.py" in paths

	def test_commit_limit(self, multi_commit_repo):
		result = get_commits(multi_commit_repo, limit=2)
		assert len(result) == 2

	def test_file_stats_present(self, single_commit_repo):
		result = get_commits(single_commit_repo)
		f = result[0]["files"][0]
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

	def test_multi_branch_only_active_branch_commits(self, multi_branch_repo):
		result = get_commits(multi_branch_repo)
		messages = [c["message"] for c in result]
		assert "Base commit" in messages
		assert "Main commit 2" in messages
		# Feature branch commits should not appear on main
		assert "Feature commit 1" not in messages
		assert "Feature commit 2" not in messages

	def test_large_repo_default_limit(self, large_repo):
		result = get_commits(large_repo)
		assert len(result) == 110

	def test_large_repo_respects_limit(self, large_repo):
		result = get_commits(large_repo, limit=10)
		assert len(result) == 10

	def test_large_repo_multiple_authors(self, large_repo):
		result = get_commits(large_repo)
		authors = {c["author"] for c in result}
		assert authors == {"Alice Dev", "Bob Engineer", "Carol Tester"}


# --- get_tree ---


class TestGetTree:
	def test_empty_repo(self, empty_repo):
		result = get_tree(empty_repo)
		assert result["files"] == {}

	def test_single_commit_file_count(self, single_commit_repo):
		result = get_tree(single_commit_repo)
		assert len(result["files"]) == 3

	def test_single_commit_file_structure(self, single_commit_repo):
		result = get_tree(single_commit_repo)
		assert "commit" in result
		assert len(result["commit"]) == 40
		for path, info in result["files"].items():
			assert info["type"] == "file"
			assert isinstance(info["size"], int)
			assert info["size"] > 0

	def test_single_commit_file_paths(self, single_commit_repo):
		result = get_tree(single_commit_repo)
		assert "file_0.txt" in result["files"]
		assert "README.md" in result["files"]
		assert "main.py" in result["files"]

	def test_specific_commit(self, multi_commit_repo):
		commits = get_commits(multi_commit_repo)
		oldest = commits[-1]["hash"]
		result = get_tree(multi_commit_repo, commit=oldest)
		assert result["commit"] == oldest
		head_tree = get_tree(multi_commit_repo)
		assert len(result["files"]) <= len(head_tree["files"])

	def test_head_tree_has_all_files(self, multi_commit_repo):
		result = get_tree(multi_commit_repo)
		assert len(result["files"]) == 5

	def test_invalid_commit(self, single_commit_repo):
		with pytest.raises(ValueError, match="Invalid commit reference"):
			get_tree(single_commit_repo, commit="deadbeef1234567890")

	def test_large_repo_tree_has_subdirs(self, large_repo):
		result = get_tree(large_repo)
		paths = list(result["files"].keys())
		# Files should include subdirectory paths
		has_subdir = any("/" in p for p in paths)
		assert has_subdir
		assert len(result["files"]) == 110

	def test_multi_branch_tree_reflects_active_branch(self, multi_branch_repo):
		result = get_tree(multi_branch_repo)
		paths = set(result["files"].keys())
		assert "base.txt" in paths
		assert "main_file.txt" in paths
		# Feature branch files should not be in main's tree
		assert "feature_file.txt" not in paths


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

	def test_multi_commit_total(self, multi_commit_repo):
		result = get_activity(multi_commit_repo)
		assert result["commits_per_author"]["Test Author"] == 5
		total = sum(w["count"] for w in result["commits_over_time"])
		assert total == 5

	def test_weekly_bucket_format(self, single_commit_repo):
		result = get_activity(single_commit_repo)
		week = result["commits_over_time"][0]["week"]
		assert "-W" in week
		parts = week.split("-W")
		assert len(parts) == 2
		assert parts[0].isdigit()
		assert parts[1].isdigit()
		assert len(parts[0]) == 4
		assert 1 <= int(parts[1]) <= 53

	def test_weekly_buckets_sorted(self, large_repo):
		result = get_activity(large_repo)
		weeks = [entry["week"] for entry in result["commits_over_time"]]
		assert weeks == sorted(weeks)

	def test_large_repo_per_author_counts(self, large_repo):
		result = get_activity(large_repo)
		per_author = result["commits_per_author"]
		assert set(per_author.keys()) == {"Alice Dev", "Bob Engineer", "Carol Tester"}
		total = sum(per_author.values())
		assert total == 110

	def test_large_repo_weekly_total_matches(self, large_repo):
		result = get_activity(large_repo)
		weekly_total = sum(w["count"] for w in result["commits_over_time"])
		assert weekly_total == 110

	def test_commits_over_time_structure(self, single_commit_repo):
		result = get_activity(single_commit_repo)
		entry = result["commits_over_time"][0]
		assert "week" in entry
		assert "count" in entry
		assert isinstance(entry["count"], int)
