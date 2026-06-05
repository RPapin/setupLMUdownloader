"""
Mapping des combos voiture/circuit.
"""

# Liste indicative — à compléter avec le contenu réel de LMU / hymosetups
CARS = [
    # LMGT3
{ "car_hymo": "aston-martin-vantage-gt3-evo", "car_drive": "Aston Martin EVO", "class_code": "LMGT3"},
{ "car_hymo": "bmw-m4-lmgt3", "car_drive": "BMW M4 GT3", "class_code": "LMGT3"},
{ "car_hymo": "corvette-z06-gt3-r", "car_drive": "Corvette Z06 LMGT3", "class_code": "LMGT3"},
{ "car_hymo": "ferrari-296-lmgt3", "car_drive": "Ferrari 296 GT3", "class_code": "LMGT3"},
{ "car_hymo": "ford-mustang-lmgt3", "car_drive": "Ford Mustang", "class_code": "LMGT3"},
{ "car_hymo": "lamborghini-huracan-lmgt3-evo2", "car_drive": "Lamborghini GT3 evo", "class_code": "LMGT3"},
{ "car_hymo": "lexus-rcf-lmgt3", "car_drive": "Lexus", "class_code": "LMGT3"},
{ "car_hymo": "mclaren-720s-lmgt3-evo", "car_drive": "McLaren GT3 EVO", "class_code": "LMGT3"},
{ "car_hymo": "mercedes-amg-lmgt3", "car_drive": "Mercedes AMG LMGT3", "class_code": "LMGT3"},
{ "car_hymo": "porsche-911-gt3-r-992", "car_drive": "Porsche 992", "class_code": "LMGT3"},
]

TRACKS = [
    { "track_hymo" : "bahrain", "track_drive" : "Bahrain"},
    { "track_hymo" : "circuit-de-barcelona", "track_drive" : "Barcelona"},
    { "track_hymo" : "cota", "track_drive" : "COTA"},
    { "track_hymo" : "fuji", "track_drive" : "Fuji"},
    { "track_hymo" : "imola", "track_drive" : "Imola"},
    { "track_hymo" : "interlagos", "track_drive" : "Interlagos"},
    { "track_hymo" : "lemans", "track_drive" : "Le Mans"},
    { "track_hymo" : "monza", "track_drive" : "Monza"},
    { "track_hymo" : "paul-ricard", "track_drive" : "Paul Ricard"},
    { "track_hymo" : "portimao", "track_drive" : "Portimao"},
    { "track_hymo" : "qatar", "track_drive" : "Qatar"},
    { "track_hymo" : "sebring", "track_drive" : "Sebring"},
    { "track_hymo" : "silverstone", "track_drive" : "Silverstone"},
    { "track_hymo" : "spa", "track_drive" : "Spa"},
]


def is_valid_combo(car: str, track: str) -> bool:
    """Validation simple. Adapter selon la stratégie retenue."""
    return car in CARS and track in TRACKS
