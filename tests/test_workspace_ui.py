import httpx
from streamlit.testing.v1 import AppTest


def test_local_workspace_pages_render(monkeypatch):
    monkeypatch.setenv("API_KEY", "x" * 48)

    class API:
        def __init__(self, *a, **k):
            pass

        def request(self, method, path, **kwargs):
            payload = []
            if path == "/v1/overview":
                payload = {"counts": {}, "outbox": []}
            if path == "/v1/gmail/status":
                payload = {"connected": False, "live_enabled": False}
            if path == "/v1/roles":
                payload = {"applied_ai": {"title": "Junior AI Engineer"}}
            return httpx.Response(200, json=payload)

    monkeypatch.setattr(httpx, "Client", API)
    app = AppTest.from_file("services/workspace/app.py").run(timeout=20)
    assert not app.exception
    for name in [
        "CV & facts",
        "Companies & research",
        "Opportunities",
        "Contacts",
        "Review & outbox",
        "Gmail & conversations",
    ]:
        app.sidebar.radio[0].set_value(name).run(timeout=20)
        assert not app.exception, name
