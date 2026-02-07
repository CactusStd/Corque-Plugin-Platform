# Suggested filename: tools/swapiTools.py

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

import requests
from langchain_core.tools import tool

from config.settings import settings

_SWAPI_ALLOWED_RESOURCES = {"people", "planets", "films", "species", "starships", "vehicles"}


def _get_base_url() -> str:
    """
    Read base URL from settings if present; otherwise use default SWAPI.
    """
    base_url = getattr(settings, "swapiApiBaseUrl", None) or getattr(settings, "swapi_base_url", None)
    if isinstance(base_url, str) and base_url.strip():
        return base_url.strip().rstrip("/")
    return "https://swapi.dev/api"


def _validate_timeout(timeout_s: int) -> Optional[str]:
    if not isinstance(timeout_s, int):
        return "Error: timeout_s must be an integer."
    if timeout_s < 3 or timeout_s > 30:
        return "Error: timeout_s must be between 3 and 30."
    return None


def _request_json(url: str, params: Optional[Dict[str, Any]], timeout_s: int) -> Tuple[Optional[Any], Optional[str]]:
    headers = {
        "User-Agent": "corque-plugin/1.0 (SWAPI tool)",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, params=params or {}, headers=headers, timeout=timeout_s)
    except Exception as e:
        return None, f"request error: {str(e)}"

    if resp.status_code != 200:
        return None, f"http {resp.status_code}: {(resp.text or '')[:300]}"

    try:
        return resp.json(), None
    except Exception:
        return None, "failed to parse json response"


@tool
def swapi_get(resource: str, entity_id: int, timeout_s: int = 12) -> str:
    """
    Get a Star Wars entity from SWAPI (no-auth).
    Use this tool when the user asks for Star Wars data by id (e.g., people/1, films/2).

    Args:
        resource (str): Required. One of: people, planets, films, species, starships, vehicles.
        entity_id (int): Required. Positive integer id.
        timeout_s (int): Optional. HTTP timeout seconds (3-30). Default 12.

    Returns:
        str: JSON string {"resource":..., "id":..., "data":{...}}.
             On failure returns "Error: ...".
    """
    err = _validate_timeout(timeout_s)
    if err:
        return err

    if not isinstance(resource, str) or resource.strip().lower() not in _SWAPI_ALLOWED_RESOURCES:
        return f"Error: resource must be one of {sorted(_SWAPI_ALLOWED_RESOURCES)}."
    if not isinstance(entity_id, int) or entity_id <= 0:
        return "Error: entity_id must be a positive integer."

    base = _get_base_url()
    res = resource.strip().lower()
    url = f"{base}/{res}/{entity_id}/"

    payload, e = _request_json(url, params=None, timeout_s=timeout_s)
    if e:
        return f"Error: failed to fetch SWAPI data. {e}"

    try:
        return json.dumps({"resource": res, "id": entity_id, "data": payload}, ensure_ascii=False)
    except Exception as ex:
        return f"Error: failed to serialize result to JSON. {str(ex)}"


@tool
def swapi_search(resource: str, query: str, page: int = 1, timeout_s: int = 12) -> str:
    """
    Search Star Wars entities on SWAPI (no-auth).
    Use this tool when the user asks to search by name/title (e.g., "Luke" in people, "Hope" in films).

    Args:
        resource (str): Required. One of: people, planets, films, species, starships, vehicles.
        query (str): Required. Search keyword (non-empty).
        page (int): Optional. Page number (>=1). Default 1.
        timeout_s (int): Optional. HTTP timeout seconds (3-30). Default 12.

    Returns:
        str: JSON string {"resource":..., "query":..., "page":..., "count":..., "results":[...], "next":..., "previous":...}.
             On failure returns "Error: ...".
    """
    err = _validate_timeout(timeout_s)
    if err:
        return err

    if not isinstance(resource, str) or resource.strip().lower() not in _SWAPI_ALLOWED_RESOURCES:
        return f"Error: resource must be one of {sorted(_SWAPI_ALLOWED_RESOURCES)}."
    if not isinstance(query, str) or not query.strip():
        return "Error: query must be a non-empty string."
    if not isinstance(page, int) or page < 1:
        return "Error: page must be an integer >= 1."

    base = _get_base_url()
    res = resource.strip().lower()
    url = f"{base}/{res}/"
    params = {"search": query.strip(), "page": page}

    payload, e = _request_json(url, params=params, timeout_s=timeout_s)
    if e:
        return f"Error: failed to search SWAPI. {e}"

    if not isinstance(payload, dict):
        return "Error: unexpected SWAPI response format."

    out = {
        "resource": res,
        "query": query.strip(),
        "page": page,
        "count": payload.get("count"),
        "results": payload.get("results") if isinstance(payload.get("results"), list) else [],
        "next": payload.get("next"),
        "previous": payload.get("previous"),
    }

    try:
        return json.dumps(out, ensure_ascii=False)
    except Exception as ex:
        return f"Error: failed to serialize result to JSON. {str(ex)}"