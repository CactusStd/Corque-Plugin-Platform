# Suggested filename: tools/pokeTools.py

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

import requests
from langchain_core.tools import tool

from config.settings import settings

_POKEAPI_ALLOWED_RESOURCES = {
    "pokemon",
    "ability",
    "type",
    "move",
    "item",
    "berry",
    "pokemon-species",
    "evolution-chain",
    "location",
    "location-area",
}


def _get_base_url() -> str:
    """
    Read base URL from settings if present; otherwise use default PokéAPI.
    """
    base_url = (
        getattr(settings, "pokeApiBaseUrl", None)
        or getattr(settings, "pokeapiApiBaseUrl", None)
        or getattr(settings, "pokeapi_base_url", None)
    )
    if isinstance(base_url, str) and base_url.strip():
        return base_url.strip().rstrip("/")
    return "https://pokeapi.co/api/v2"


def _validate_timeout(timeout_s: int) -> Optional[str]:
    if not isinstance(timeout_s, int):
        return "Error: timeout_s must be an integer."
    if timeout_s < 3 or timeout_s > 30:
        return "Error: timeout_s must be between 3 and 30."
    return None


def _request_json(url: str, timeout_s: int) -> Tuple[Optional[Any], Optional[str]]:
    headers = {
        "User-Agent": "corque-plugin/1.0 (PokéAPI tool)",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout_s)
    except Exception as e:
        return None, f"request error: {str(e)}"

    if resp.status_code != 200:
        return None, f"http {resp.status_code}: {(resp.text or '')[:300]}"

    try:
        return resp.json(), None
    except Exception:
        return None, "failed to parse json response"


@tool
def pokeapi_get_pokemon(name_or_id: str, timeout_s: int = 12) -> str:
    """
    Get Pokémon data from PokéAPI (no-auth).
    Use this tool when the user asks about a Pokémon by name or Pokédex id (e.g., "pikachu" or "25").

    Args:
        name_or_id (str): Required. Pokémon name or id.
        timeout_s (int): Optional. HTTP timeout seconds (3-30). Default 12.

    Returns:
        str: JSON string {"resource":"pokemon","key":..., "data":{...}}.
             On failure returns "Error: ...".
    """
    err = _validate_timeout(timeout_s)
    if err:
        return err

    if not isinstance(name_or_id, str) or not name_or_id.strip():
        return "Error: name_or_id must be a non-empty string."

    base = _get_base_url()
    key = name_or_id.strip().lower()
    url = f"{base}/pokemon/{key}"

    payload, e = _request_json(url, timeout_s=timeout_s)
    if e:
        return f"Error: failed to fetch PokéAPI pokemon data. {e}"

    try:
        return json.dumps({"resource": "pokemon", "key": key, "data": payload}, ensure_ascii=False)
    except Exception as ex:
        return f"Error: failed to serialize result to JSON. {str(ex)}"


@tool
def pokeapi_get(resource: str, name_or_id: str, timeout_s: int = 12) -> str:
    """
    Get a resource from PokéAPI (no-auth).
    Use this tool when the user asks about abilities, types, moves, items, berries, species, evolution chains, etc.

    Args:
        resource (str): Required. One of: pokemon, ability, type, move, item, berry, pokemon-species, evolution-chain, location, location-area.
        name_or_id (str): Required. Resource key (name or id).
        timeout_s (int): Optional. HTTP timeout seconds (3-30). Default 12.

    Returns:
        str: JSON string {"resource":..., "key":..., "data":{...}}.
             On failure returns "Error: ...".
    """
    err = _validate_timeout(timeout_s)
    if err:
        return err

    if not isinstance(resource, str) or resource.strip().lower() not in _POKEAPI_ALLOWED_RESOURCES:
        return f"Error: resource must be one of {sorted(_POKEAPI_ALLOWED_RESOURCES)}."
    if not isinstance(name_or_id, str) or not name_or_id.strip():
        return "Error: name_or_id must be a non-empty string."

    base = _get_base_url()
    res = resource.strip().lower()
    key = name_or_id.strip().lower()
    url = f"{base}/{res}/{key}"

    payload, e = _request_json(url, timeout_s=timeout_s)
    if e:
        return f"Error: failed to fetch PokéAPI data. {e}"

    try:
        return json.dumps({"resource": res, "key": key, "data": payload}, ensure_ascii=False)
    except Exception as ex:
        return f"Error: failed to serialize result to JSON. {str(ex)}"