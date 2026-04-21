"""
Backend tests for NEW script generation endpoints:
1. POST /api/projects/{id}/generate-full-script  (5 hooks + body + cta)
2. POST /api/projects/{id}/regenerate-body       (regenerate body from chosen hook, archive old)
3. POST /api/projects/{id}/generate-script-captions (3-5 caption options)
"""
import os, time, pytest, requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

TRANSCRIPT = (
    "This is a test video about a new AI gadget. It can summarize documents "
    "in seconds, translate to 20 languages, and runs fully offline on your phone. "
    "Battery lasts 3 days. Price is $199. Ships worldwide next month."
)


@pytest.fixture(scope="module")
def ready_project():
    # ensure profile
    r = requests.get(f"{BASE_URL}/api/profiles")
    profiles = r.json()
    if not profiles:
        requests.post(f"{BASE_URL}/api/profiles/seed")
        profiles = requests.get(f"{BASE_URL}/api/profiles").json()
    pid = profiles[0]["id"]

    proj = requests.post(f"{BASE_URL}/api/projects", json={
        "profile_id": pid,
        "name": f"TEST_FullScript_{int(time.time())}",
        "is_ad": False,
        "video_urls": [],
        "key_features": ["offline AI", "3 day battery"],
    }).json()
    project_id = proj["id"]

    # add manual transcript so generation has source
    requests.post(
        f"{BASE_URL}/api/projects/{project_id}/add-transcript-manual",
        json={"transcript": TRANSCRIPT, "source_url": "manual-input", "language": "en"},
    )
    yield project_id
    requests.delete(f"{BASE_URL}/api/projects/{project_id}")


class TestGenerateFullScript:
    def test_generate_full_script_auto(self, ready_project):
        r = requests.post(
            f"{BASE_URL}/api/projects/{ready_project}/generate-full-script",
            json={"project_id": ready_project, "mode": "auto", "hook_count": 5},
            timeout=180,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:500]}"
        data = r.json()
        assert "hooks" in data and isinstance(data["hooks"], list)
        assert len(data["hooks"]) >= 3, f"expected ~5 hooks, got {len(data['hooks'])}"
        # hooks must have id and text
        for h in data["hooks"]:
            assert h.get("id"), "hook missing id"
            assert h.get("text"), "hook missing text"
        assert data.get("body_content"), "body_content should be generated"
        assert data.get("cta_content"), "cta_content should be generated"
        # persistence check
        g = requests.get(f"{BASE_URL}/api/projects/{ready_project}").json()
        assert len(g.get("hooks", [])) == len(data["hooks"])
        assert g.get("body_content") == data["body_content"]
        print(f"OK full-script: {len(data['hooks'])} hooks, body={len(data['body_content'])}ch")


class TestRegenerateBody:
    def test_regenerate_body_archives_and_replaces(self, ready_project):
        proj = requests.get(f"{BASE_URL}/api/projects/{ready_project}").json()
        assert proj.get("hooks"), "need hooks from previous test"
        first_hook_id = proj["hooks"][0]["id"]
        second_hook_id = proj["hooks"][1]["id"] if len(proj["hooks"]) > 1 else first_hook_id
        old_body = proj.get("body_content", "")

        r = requests.post(
            f"{BASE_URL}/api/projects/{ready_project}/regenerate-body",
            json={"project_id": ready_project, "hook_id": second_hook_id},
            timeout=180,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:500]}"
        data = r.json()
        assert data.get("body_content"), "new body should exist"
        # old version archived
        assert len(data.get("body_versions", [])) >= 1, "old body should be archived in body_versions"
        if old_body:
            assert old_body in [v.get("body_content", "") for v in data["body_versions"]], \
                "old body must be in body_versions"
        # selected_hook_indices points to new hook
        new_sel = data.get("selected_hook_indices", [])
        assert new_sel, "selected_hook_indices should be set"
        print(f"OK regenerate-body: archived {len(data['body_versions'])} version(s)")

    def test_regenerate_body_bad_hook_id(self, ready_project):
        r = requests.post(
            f"{BASE_URL}/api/projects/{ready_project}/regenerate-body",
            json={"project_id": ready_project, "hook_id": "nonexistent"},
            timeout=30,
        )
        assert r.status_code == 400, f"expected 400, got {r.status_code}"


class TestGenerateScriptCaptions:
    def test_generate_script_captions_default(self, ready_project):
        r = requests.post(
            f"{BASE_URL}/api/projects/{ready_project}/generate-script-captions",
            json={"project_id": ready_project, "count": 5},
            timeout=120,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:500]}"
        data = r.json()
        # response should include captions list
        caps = data.get("captions") or data.get("script_captions") or []
        assert isinstance(caps, list), f"expected list of captions, got {type(caps)}"
        assert 3 <= len(caps) <= 7, f"expected 3-5 captions, got {len(caps)}"
        for c in caps:
            # can be string or dict
            text = c if isinstance(c, str) else (c.get("text") or c.get("caption") or "")
            assert text and len(text) > 5, "caption should have non-empty text"
        print(f"OK script-captions: {len(caps)} captions")

    def test_generate_script_captions_with_ref(self, ready_project):
        r = requests.post(
            f"{BASE_URL}/api/projects/{ready_project}/generate-script-captions",
            json={
                "project_id": ready_project,
                "count": 3,
                "ref_caption": "POV: you just found the AI tool that replaces your whole team 👀 #AItools",
            },
            timeout=120,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:500]}"
        data = r.json()
        caps = data.get("captions") or data.get("script_captions") or []
        assert len(caps) >= 2, "should return captions"
        print(f"OK script-captions with ref: {len(caps)} captions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
