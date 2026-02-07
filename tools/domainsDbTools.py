"""
Domain search tool using the free DomainsDB API (api.domainsdb.info).
No API key required.
"""
import time
import requests
from langchain_core.tools import tool

from config.settings import settings

BASE_PATH = "/v1/domains/search"


def _get_base_url() -> str:
    url = getattr(settings, "domainsDbApiBaseUrl", None)
    if isinstance(url, str):
        url = url.strip()
    return url or "https://api.domainsdb.info"


@tool
def search_domains(domain: str, zone: str = "", limit: int = 15) -> str:
    """
    Search for registered domain names matching a keyword using DomainsDB.
    Use when the user wants to find domains containing a name, check if a domain is taken, or discover similar domains.

    Args:
        domain (str): Search term or domain keyword (e.g. 'myapp', 'google'). Required.
        zone (str): Top-level domain / zone to filter by (e.g. 'com', 'io', 'org'). Optional; leave empty for all zones.
        limit (int): Maximum number of results to return (default 15).

    Returns:
        str: Human-readable list of matching domains, or an error message.
    """
    base_url = _get_base_url().rstrip("/")
    url = base_url + BASE_PATH

    if not (domain and domain.strip()):
        return "Error: domain search term is required."

    params = {"domain": domain.strip()}
    if zone and zone.strip():
        params["zone"] = zone.strip().lower()

    headers = {
        "Accept": "application/json",
        "User-Agent": "Corque-AI-agent/1.0 (domain search)",
    }

    try:
        start = time.time()
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        elapsed = time.time() - start
        print(f"DomainsDB request took: {elapsed:.2f} s")
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return f"Error calling DomainsDB API: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

    # API may return {"domains": ["a.com", "b.com"]} or {"domains": [{"domain": "a.com"}, ...]}
    raw = data.get("domains") or data.get("results") or []
    if not isinstance(raw, list):
        return "No domains found for that search."

    domains = []
    for item in raw[: limit + 50]:
        if isinstance(item, str):
            domains.append(item)
        elif isinstance(item, dict) and item.get("domain"):
            domains.append(item["domain"])
        elif isinstance(item, dict) and item.get("name"):
            domains.append(item["name"])
        if len(domains) >= limit:
            break

    if not domains:
        return f"No domains found matching '{domain}'" + (f" in .{zone}" if zone else "") + "."

    lines = [f"- {d}" for d in domains[:limit]]
    return "\n".join(lines)
