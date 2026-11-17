"""Bounded official-site research with pinned public IPs and no redirects."""

import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urlsplit

import httpx

from .domain import fail


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def public_page(url, domain):
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        fail("only public HTTPS pages on the official company domain are supported", 422)
    if host != domain and not host.endswith("." + domain):
        fail("source is outside the official company domain", 422)
    try:
        addresses = {row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    except OSError:
        fail("company domain could not be resolved", 502)
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        fail("private or non-public fetch destinations are forbidden", 422)
    address = sorted(addresses)[0]
    pinned = httpx.URL(url).copy_with(host=address)
    try:
        # IP remains pinned through connection/proxy resolution, TLS verifies the original host.
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            request = client.build_request(
                "GET",
                pinned,
                headers={"Host": host, "User-Agent": "PersonalCareerResearch/0.2"},
                extensions={"sni_hostname": host},
            )
            response = client.send(request, stream=True)
            try:
                response.raise_for_status()
                if "text/html" not in response.headers.get("content-type", ""):
                    fail("source must be HTML", 422)
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 1024 * 1024:
                        fail("source page exceeds 1 MB", 422)
            finally:
                response.close()
    except httpx.HTTPError:
        fail("source unavailable; paste a permitted company/job URL instead", 502)
    parser = Text()
    parser.feed(body.decode("utf-8", errors="replace"))
    text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()[:20000]
    emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@" + re.escape(domain) + r"\b", text, re.I)))
    return {"url": url, "text": text, "published_emails": emails, "contact_status": "requires_source_review"}


def search(settings, query):
    try:
        response = httpx.get(
            settings.searxng_url + "/search", params={"q": query, "format": "json"}, timeout=25
        )
        response.raise_for_status()
        results = response.json().get("results", [])[:10]
    except (httpx.HTTPError, ValueError):
        fail("local SearXNG unavailable; start the research profile or add an official company URL", 503)
    return [
        {
            "title": str(r.get("title", ""))[:200],
            "url": r.get("url"),
            "snippet": str(r.get("content", ""))[:1000],
            "status": "source_review_required",
        }
        for r in results
        if str(r.get("url", "")).startswith("https://")
    ]
