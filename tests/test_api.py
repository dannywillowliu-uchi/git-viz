import pathlib


HTML_PATH = pathlib.Path(__file__).resolve().parent.parent / "src" / "git_viz" / "index.html"


def test_index_html_exists():
	assert HTML_PATH.is_file(), "index.html must exist"


def test_index_html_has_required_containers():
	content = HTML_PATH.read_text()
	for container_id in ("graph-container", "timeline-container", "sidebar", "activity-chart"):
		assert f'id="{container_id}"' in content, f"Missing #{container_id}"


def test_index_html_has_d3_cdn():
	content = HTML_PATH.read_text()
	assert "d3js.org" in content or "d3.v7" in content


def test_index_html_has_dark_theme():
	content = HTML_PATH.read_text()
	assert "#1a1a2e" in content, "Missing dark theme background color"


def test_index_html_has_loading_overlay():
	content = HTML_PATH.read_text()
	assert "loading-overlay" in content


def test_index_html_has_responsive_breakpoints():
	content = HTML_PATH.read_text()
	assert "@media" in content, "Missing responsive breakpoints"


def test_index_html_is_self_contained():
	content = HTML_PATH.read_text()
	assert "<style>" in content, "CSS must be inline"
	assert "<script>" in content, "JS must be inline"


def test_api_repo_default_path(client):
	resp = client.get("/api/repo")
	assert resp.status_code == 200
	data = resp.json()
	assert "name" in data
	assert "branch" in data


def test_api_commits_default_path(client):
	resp = client.get("/api/commits")
	assert resp.status_code == 200
	data = resp.json()
	assert isinstance(data, list)
	assert len(data) > 0


def test_api_tree_default_path(client):
	resp = client.get("/api/tree")
	assert resp.status_code == 200
	data = resp.json()
	assert isinstance(data, dict)
	assert "files" in data


def test_api_activity_default_path(client):
	resp = client.get("/api/activity")
	assert resp.status_code == 200
	data = resp.json()
	assert "authors" in data or "weekly" in data or isinstance(data, dict)
