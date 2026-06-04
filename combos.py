"""
Mapping des combos voiture/circuit.

Deux usages possibles :
- proposer des choix (autocomplétion) dans la commande Discord,
- valider/normaliser ce que l'utilisateur saisit.

TODO: remplir avec les vraies voitures/circuits de LMU disponibles sur
hymosetups, ou basculer sur une recherche dynamique du site si la liste est
trop grande / change souvent.
"""

# Liste indicative — à compléter avec le contenu réel de LMU / hymosetups
CARS = [
    #LMGT3
    "aston-martin-vantage-gt3-evo",
    "bmw-m4-lmgt3",
    "corvette-z06-gt3-r",
    "mercedes-amg-lmgt3",
]

TRACKS = [
    "bahrain",
    "circuit-de-barcelona",
    "cota",
    "lemans",
    "Imola",
    "Fuji",
    "Sebring",
    "Portimão",
]


def is_valid_combo(car: str, track: str) -> bool:
    """Validation simple. Adapter selon la stratégie retenue."""
    return car in CARS and track in TRACKS
