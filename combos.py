"""
Mapping des combos voiture/circuit.
"""

# Liste indicative — à compléter avec le contenu réel de LMU / hymosetups
CARS = [# LMGT3
{ "car_hymo": "aston-martin-vantage-gt3-evo", "car_drive": "Aston Martin EVO", "class_code": "LMGT3"},
{ "car_hymo": "bmw-m4-lmgt3", "car_drive": "BMW M4 GT3", "class_code": "LMGT3"},
{ "car_hymo": "corvette-z06-gt3-r", "car_drive": "Corvette Z06 LMGT3", "class_code": "LMGT3"},
{ "car_hymo": "mercedes-amg-lmgt3", "car_drive": "Mercedes AMG LMGT3", "class_code": "LMGT3"},
]

TRACKS = [
    { "track_hymo" : "bahrain", "track_drive" : "Bahrain"},
    { "track_hymo" : "circuit-de-barcelona", "track_drive" : "Barcelona"},
    { "track_hymo" : "cota", "track_drive" : "COTA"},
    { "track_hymo" : "lemans", "track_drive" : "Le Mans"},
]


def is_valid_combo(car: str, track: str) -> bool:
    """Validation simple. Adapter selon la stratégie retenue."""
    return car in CARS and track in TRACKS
