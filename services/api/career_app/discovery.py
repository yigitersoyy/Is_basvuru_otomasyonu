import html
import re

import httpx

from .domain import fail


def board_jobs(provider: str, board: str) -> list[dict]:
    # Only documented public ATS hosts. User input cannot select an arbitrary fetch host/port.
    urls = {
        "greenhouse": f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true",
        "ashby": f"https://api.ashbyhq.com/posting-api/job-board/{board}",
    }
    try:
        with httpx.stream("GET", urls[provider], timeout=20, follow_redirects=False) as response:
            response.raise_for_status()
            chunks, size = [], 0
            for part in response.iter_bytes():
                size += len(part)
                if size > 3 * 1024 * 1024:
                    fail("job board exceeds response-size limit", 422)
                chunks.append(part)
            data = httpx.Response(200, content=b"".join(chunks)).json()
    except (httpx.HTTPError, ValueError, KeyError):
        fail("public job board unavailable or invalid; use URL/text import", 502)
    jobs = []
    for row in data.get("jobs", [])[:200]:
        if row.get("isListed") is False:
            continue
        url = row.get("absolute_url") or row.get("jobUrl")
        raw = row.get("content") or row.get("descriptionPlain") or row.get("descriptionHtml") or ""
        description = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        if not url or not description.strip():
            continue
        jobs.append(
            {
                "external_key": f"{provider}:{board}:{row.get('id') or url}",
                "title": row["title"],
                "description": description[:30000],
                "source_url": url,
            }
        )
    return jobs
