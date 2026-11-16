"""Generate importable inactive n8n workflows; credentials must be bound after import."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def workflow(name, path, method="GET", webhook=False, schedule=None):
    nodes = []
    if webhook:
        trigger = {
            "id": "trigger",
            "name": "Authenticated request",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [0, 0],
            "webhookId": name.lower().replace(" ", "-"),
            "parameters": {
                "httpMethod": "POST",
                "path": name.lower().replace(" ", "-"),
                "authentication": "headerAuth",
                "responseMode": "lastNode",
            },
            "credentials": {"httpHeaderAuth": {"id": "career-inbound", "name": "Career inbound key"}},
        }
    elif schedule:
        trigger = {
            "id": "trigger",
            "name": "Schedule",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 0],
            "parameters": {"rule": {"interval": [{"field": "minutes", "minutesInterval": schedule}]}},
        }
    else:
        trigger = {
            "id": "trigger",
            "name": "Run manually",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {},
        }
    nodes.append(trigger)
    params = {
        "method": method,
        "url": "http://api:8000" + path,
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "options": {"timeout": 240000 if path == "/v1/packages" else 60000},
    }
    if webhook:
        params.update(sendBody=True, specifyBody="json", jsonBody="={{ JSON.stringify($json.body) }}")
    nodes.append(
        {
            "id": "api",
            "name": "Career API",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [260, 0],
            "parameters": params,
            "credentials": {"httpHeaderAuth": {"id": "career-api", "name": "Career API key"}},
        }
    )
    return {
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "active": False,
        "nodes": nodes,
        "connections": {trigger["name"]: {"main": [[{"node": "Career API", "type": "main", "index": 0}]]}},
        "settings": {
            "executionOrder": "v1",
            "timezone": "Europe/Istanbul",
            "saveDataSuccessExecution": "none",
        },
    }


specs = [
    ("Career Overview", "/v1/overview", "GET", False, None),
    ("Career Import Company", "/v1/companies", "POST", True, None),
    ("Career Import Opportunity", "/v1/opportunities", "POST", True, None),
    ("Career Prepare Package", "/v1/packages", "POST", True, None),
    ("Career Import Public Board", "/v1/boards/import", "POST", True, None),
    ("Career Dispatch Test", "/v1/outbox/dispatch-test", "POST", False, 1),
    ("Career Recover Interrupted", "/v1/outbox/recover", "POST", False, 5),
]
for args in specs:
    data = workflow(*args)
    (root / "n8n/workflows" / (data["id"] + ".json")).write_text(json.dumps(data, indent=2) + "\n")
print("Generated seven inactive workflows backed by real API endpoints.")
