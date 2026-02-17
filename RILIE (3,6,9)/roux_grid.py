# roux_grid.py

from typing import List, Tuple

# (city, channel) pairs derived from PRE-RESPONSE.txt
ROUX_GRID: List[Tuple[str, str]] = [
    ("BROOKLYN", "MIND"),
    ("BROOKLYN", "BODY"),
    ("BROOKLYN", "SOUL"),
    ("BROOKLYN", "FOOD"),
    ("BROOKLYN", "MUSIC"),
    ("BROOKLYN", "FUNNY"),
    ("BROOKLYN", "FILM"),

    ("NEW ORLEANS", "MIND"),
    ("NEW ORLEANS", "BODY"),
    ("NEW ORLEANS", "SOUL"),
    ("NEW ORLEANS", "FOOD"),
    ("NEW ORLEANS", "MUSIC"),
    ("NEW ORLEANS", "FUNNY"),
    ("NEW ORLEANS", "FILM"),

    ("NICE, FRANCE", "MIND"),
    ("NICE, FRANCE", "BODY"),
    ("NICE, FRANCE", "SOUL"),
    ("NICE, FRANCE", "FOOD"),
    ("NICE, FRANCE", "MUSIC"),
    ("NICE, FRANCE", "FUNNY"),
    ("NICE, FRANCE", "FILM"),

    ("NEW YORK CITY", "MIND"),
    ("NEW YORK CITY", "BODY"),
    ("NEW YORK CITY", "SOUL"),
    ("NEW YORK CITY", "FOOD"),
    ("NEW YORK CITY", "MUSIC"),
    ("NEW YORK CITY", "FUNNY"),

    ("PARIS, FRANCE", "MIND"),
    ("PARIS, FRANCE", "BODY"),
    ("PARIS, FRANCE", "SOUL"),
    ("PARIS, FRANCE", "FOOD"),
    ("PARIS, FRANCE", "MUSIC"),
    ("PARIS, FRANCE", "FUNNY"),
    ("PARIS, FRANCE", "FILM"),

    ("MANHATTAN", "MIND"),
    ("MANHATTAN", "BODY"),
    ("MANHATTAN", "SOUL"),
    ("MANHATTAN", "FOOD"),
    ("MANHATTAN", "MUSIC"),
    ("MANHATTAN", "FUNNY"),
    ("MANHATTAN", "FILM"),

    ("QUEENS", "MIND"),
    ("QUEENS", "BODY"),
    ("QUEENS", "SOUL"),
    ("QUEENS", "FOOD"),
    ("QUEENS", "MUSIC"),
    ("QUEENS", "FUNNY"),
    ("QUEENS", "FILM"),

    ("BRONX", "MIND"),
    ("BRONX", "BODY"),
    ("BRONX", "SOUL"),
    ("BRONX", "FOOD"),
    ("BRONX", "MUSIC"),
    ("BRONX", "FUNNY"),
    ("BRONX", "FILM"),

    ("LOS ANGELES", "MIND"),
    ("LOS ANGELES", "BODY"),
    ("LOS ANGELES", "SOUL"),
    ("LOS ANGELES", "FOOD"),
    ("LOS ANGELES", "MUSIC"),
    ("LOS ANGELES", "FUNNY"),
    ("LOS ANGELES", "FILM"),

    ("MIAMI", "MIND"),
    ("MIAMI", "BODY"),
    ("MIAMI", "SOUL"),
    ("MIAMI", "FOOD"),
    ("MIAMI", "MUSIC"),
    ("MIAMI", "FUNNY"),
    ("MIAMI", "FILM"),

    ("PUERTO RICO", "MIND"),
    ("PUERTO RICO", "BODY"),
    ("PUERTO RICO", "SOUL"),
    ("PUERTO RICO", "FOOD"),
    ("PUERTO RICO", "MUSIC"),
    ("PUERTO RICO", "FUNNY"),
    ("PUERTO RICO", "FILM"),

    ("DOMINICAN REPUBLIC", "MIND"),
    ("DOMINICAN REPUBLIC", "BODY"),
    ("DOMINICAN REPUBLIC", "SOUL"),
    ("DOMINICAN REPUBLIC", "FOOD"),
    ("DOMINICAN REPUBLIC", "MUSIC"),
    ("DOMINICAN REPUBLIC", "FUNNY"),
    ("DOMINICAN REPUBLIC", "FILM"),

    ("MEXICO", "MIND"),
    ("MEXICO", "BODY"),
    ("MEXICO", "SOUL"),
    ("MEXICO", "FOOD"),
    ("MEXICO", "MUSIC"),
    ("MEXICO", "FUNNY"),
    ("MEXICO", "FILM"),

    ("JAMAICA", "MIND"),
    ("JAMAICA", "BODY"),
    ("JAMAICA", "SOUL"),
    ("JAMAICA", "FOOD"),
    ("JAMAICA", "MUSIC"),
    ("JAMAICA", "FUNNY"),
    ("JAMAICA", "FILM"),

    ("LONDON, ENGLAND", "MIND"),
    ("LONDON, ENGLAND", "BODY"),
    ("LONDON, ENGLAND", "SOUL"),
    ("LONDON, ENGLAND", "FOOD"),
    ("LONDON, ENGLAND", "MUSIC"),
    ("LONDON, ENGLAND", "FUNNY"),
    ("LONDON, ENGLAND", "FILM"),

    ("GLOBAL", "HIP-HOP"),
    ("GLOBAL", "HARDCORE"),
    ("GLOBAL", "BRUTAL"),
    ("GLOBAL", "BOARD"),
    ("GLOBAL", "SKATE"),
    ("GLOBAL", "SURF"),
    ("GLOBAL", "FUNK"),
    ("GLOBAL", "ROCK"),
    ("GLOBAL", "BREAK"),
]


def build_pre_response_queries(q: str, shallow: bool = True):
    q = q.strip()
    if not q:
        return []

    if shallow:
        # PRE-RESPONSE: "IF QUESTION IS CLEAR AND SHALLOW, GOOGLE Q..."
        return [q]

    # ELSE: expand across the Roux grid
    queries = []
    for city, channel in ROUX_GRID:
        queries.append(f"{q} {city} {channel}")
    return queries
