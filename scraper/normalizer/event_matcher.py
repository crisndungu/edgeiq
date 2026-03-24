"""
Fuzzy-match the same sporting event across different bookmakers.
e.g. 'Man Utd' == 'Manchester United' == 'Manchester Utd'
"""
import hashlib
from thefuzz import fuzz

TEAM_ALIASES = {
    "man utd": "manchester united",
    "man city": "manchester city",
    "spurs": "tottenham",
    "tottenham hotspur": "tottenham",
    "wolves": "wolverhampton",
    "brighton & hove albion": "brighton",
    "west ham united": "west ham",
    "nottingham forest": "nottm forest",
    "afc bournemouth": "bournemouth",
    "newcastle united": "newcastle",
    "atletico": "atletico madrid",
    "inter": "inter milan",
    "ac milan": "milan",
    "psg": "paris saint-germain",
    "paris sg": "paris saint-germain",
    "rb leipzig": "leipzig",
    "gor mahia": "gor mahia fc",
    "afc leopards": "leopards",
    "tusker fc": "tusker",
    "kariobangi sharks": "sharks",
}

MATCH_THRESHOLD = 80  # minimum fuzz score to consider a match


def _normalize_team(name: str) -> str:
    name = name.lower().strip()
    return TEAM_ALIASES.get(name, name)


def make_event_id(home_team: str, away_team: str, start_time: str) -> str:
    """
    Deterministic event ID from normalized team names + date (not full timestamp).
    Two bookmakers listing the same match will produce the same ID.
    """
    home = _normalize_team(home_team)
    away = _normalize_team(away_team)
    date = start_time[:10]  # YYYY-MM-DD only
    raw = f"{home}|{away}|{date}"
    return hashlib.md5(raw.encode()).hexdigest()


def teams_match(name_a: str, name_b: str) -> bool:
    """Return True if two team name strings refer to the same team."""
    a = _normalize_team(name_a)
    b = _normalize_team(name_b)
    if a == b:
        return True
    score = fuzz.token_sort_ratio(a, b)
    return score >= MATCH_THRESHOLD


def events_match(event_a: dict, event_b: dict) -> bool:
    """
    Compare two event dicts with keys: home_team, away_team, start_time.
    Returns True if they represent the same match.
    """
    home_ok = teams_match(event_a["home_team"], event_b["home_team"])
    away_ok = teams_match(event_a["away_team"], event_b["away_team"])
    date_ok = event_a["start_time"][:10] == event_b["start_time"][:10]
    return home_ok and away_ok and date_ok
