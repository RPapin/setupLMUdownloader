"""
Mapping des combos voiture/circuit.
"""

# Liste indicative — à compléter avec le contenu réel de LMU / hymosetups
CARS = [
    # LMGT3
    {"car_hymo": "aston-martin-vantage-gt3-evo", "car_drive": "Aston Martin EVO", "class_code": "LMGT3",
     "car_titan": "Vantage_AMR_GT3Evo_2024", "car_gosetup": "Aston+Martin+Vantage+AMR+LMGT3"},
    {"car_hymo": "bmw-m4-lmgt3", "car_drive": "BMW M4 GT3", "class_code": "LMGT3", "car_titan": "BMW_M4_LMGT3_2023",
     "car_gosetup": "BMW+M4+LMGT3"},
    {"car_hymo": "corvette-z06-gt3-r", "car_drive": "Corvette Z06 LMGT3", "class_code": "LMGT3",
     "car_titan": "Corvette_Z06GT3R_2023", "car_gosetup": "Chevrolet+Corvette+Z06+LMGT3"},
    {"car_hymo": "ferrari-296-lmgt3", "car_drive": "Ferrari 296 GT3", "class_code": "LMGT3",
     "car_titan": "Ferrari_296GT3_2023", "car_gosetup": "Ferrari+296+LMGT3"},
    {"car_hymo": "ford-mustang-lmgt3", "car_drive": "Ford Mustang", "class_code": "LMGT3",
     "car_titan": "Ford_Mustang_GT3_2024", "car_gosetup": "Ford+Mustang+LMGT3"},
    {"car_hymo": "lamborghini-huracan-lmgt3-evo2", "car_drive": "Lamborghini GT3 evo", "class_code": "LMGT3",
     "car_titan": "Lamborghini_Huracan_GT3_2024", "car_gosetup": "Lamborghini+Huracan+EVO2+LMGT3"},
    {"car_hymo": "lexus-rcf-lmgt3", "car_drive": "Lexus", "class_code": "LMGT3", "car_titan": "LexusRCF_GT3_2024",
     "car_gosetup": "Lexus+RCF+LMGT3"},
    {"car_hymo": "mclaren-720s-lmgt3-evo", "car_drive": "McLaren GT3 EVO", "class_code": "LMGT3",
     "car_titan": "McLaren_720sGT3Evo_2023", "car_gosetup": "Mclaren+720s+LMGT3+EVO"},
    {"car_hymo": "mercedes-amg-lmgt3", "car_drive": "Mercedes AMG LMGT3", "class_code": "LMGT3",
     "car_titan": "Mercedes_AMGGT3Evo_2025", "car_gosetup": "Mercedes+AMG+LMGT3"},
    {"car_hymo": "porsche-911-gt3-r-992", "car_drive": "Porsche 992", "class_code": "LMGT3",
     "car_titan": "Porsche_992_GT3R_2023", "car_gosetup": "Porsche+992+LMGT3"},
    # Hypercar
    {"car_hymo": "alpine-a424", "car_drive": "Alpine A424", "class_code": "HYPERCAR",
     "car_titan": "Alpine_A424_2024", "car_gosetup": "Alpine+A424"},
    {"car_hymo": "aston-martin-valkyrie-amr-lmh", "car_drive": "Aston Martin Valkyrie LMH", "class_code": "HYPERCAR",
     "car_titan": "Aston_Martin_Valkyrie_2025", "car_gosetup": "Aston+Martin+Valkyrie+LMH"},
    {"car_hymo": "bmw-m-hybrid-v8", "car_drive": "BMW M Hybrid V8", "class_code": "HYPERCAR",
     "car_titan": "BMW_M_Hybrid_V8_2023", "car_gosetup": "BMW+M+Hybrid+V8"},
    {"car_hymo": "cadillac-v-series-r", "car_drive": "Cadillac V Series.R", "class_code": "HYPERCAR",
     "car_titan": "Cadillac_V-lmdh_2023", "car_gosetup": "Cadillac+V+Series.R"},
    {"car_hymo": "ferrari-499p", "car_drive": "Ferrari 499P", "class_code": "HYPERCAR",
     "car_titan": "Ferrari_499P_2023", "car_gosetup": "Ferrari+499P"},
    {"car_hymo": "genesis-gmr-001", "car_drive": "Genesis GMR001", "class_code": "HYPERCAR",
     "car_titan": "Genesis_GMR_001", "car_gosetup": "Genesis+GMR001"},
    {"car_hymo": "NOT-FOUND", "car_drive": "Glickenhaus SCG 007", "class_code": "HYPERCAR",
     "car_titan": "SGC_007_2023", "car_gosetup": "Glickenhaus+SCG+007"},
    {"car_hymo": "isotta-fraschini-tipo-6-lmh-c", "car_drive": "Isotta Fraschini Tipo 6", "class_code": "HYPERCAR",
     "car_titan": "Isotta_Tipo6_2024", "car_gosetup": "Isotta+Fraschini+Tipo+6"},
    {"car_hymo": "lamborghini-sc63", "car_drive": "Lamborghini SC63", "class_code": "HYPERCAR",
     "car_titan": "Lamborghini_SC63_2024", "car_gosetup": "Lamborghini+SC63"},
    {"car_hymo": "peugeot-9x8-wingless", "car_drive": "Peugeot 9X8", "class_code": "HYPERCAR",
     "car_titan": "Peugeot_9x8_2023", "car_gosetup": "Peugeot+9X8"},
    {"car_hymo": "peugeot-9x8-evo", "car_drive": "Peugeot 9X8 EVO", "class_code": "HYPERCAR",
     "car_titan": "Peugeot_9x8_2024", "car_gosetup": "Peugeot+9X8+EVO"},
    {"car_hymo": "porsche-963", "car_drive": "Porsche 963", "class_code": "HYPERCAR",
     "car_titan": "Porsche_963_2023", "car_gosetup": "Porsche+963"},
    {"car_hymo": "toyota-tr010-hybrid", "car_drive": "Toyota TR10", "class_code": "HYPERCAR",
     "car_titan": "Toyota_TR10_2026", "car_gosetup": "Toyota+GR010"},
    # LMP2
    {"car_hymo": "oreca-07-gibson-2024-wec", "car_drive": "ORECA 07 2024", "class_code": "LMP2",
     "car_titan": "Oreca_07_LM_2023", "car_gosetup": "Oreca+07+2024"},
    {"car_hymo": "oreca-07-gibson-2024-elms", "car_drive": "ORECA 07 ELMS", "class_code": "LMP2",
     "car_titan": "Oreca_07_LM_2023", "car_gosetup": "Oreca+07+ELMS"},
    # LMP3
    {"car_hymo": "NOT-FOUND", "car_drive": "Adess AD25 LMP3", "class_code": "LMP3",
     "car_titan": "Porsche_992_GT3R_2023", "car_gosetup": "Adess+AD25+LMP3"},
    {"car_hymo": "duqueine-d09", "car_drive": "Duqueine D09 P3", "class_code": "LMP3",
     "car_titan": "Duqueine_D09_P3", "car_gosetup": "Duqueine+D09+P3"},
    {"car_hymo": "ginetta-g61-lt-p325-evo", "car_drive": "Ginetta G61 LT P325 EVO", "class_code": "LMP3",
     "car_titan": "Ginetta_G61-LT-P3", "car_gosetup": "Ginetta+G61+LT+P325+EVO"},
    {"car_hymo": "ligier-js-p325", "car_drive": "Ligier JS P325 LMP3", "class_code": "LMP3",
     "car_titan": "Ligier_JS_P325", "car_gosetup": "Ligier+JS+P325+LMP3"},
]

TRACKS = [
    {"track_hymo": "bahrain", "track_drive": "Bahrain", "track_titan": "Bahrainwec",
     "track_gosetup": "Bahrain+Endurance"},
    {"track_hymo": "circuit-de-barcelona", "track_drive": "Barcelona", "track_titan": "circuit_de_barcelona",
     "track_gosetup": "Barcelona"},
    {"track_hymo": "cota", "track_drive": "COTA", "track_titan": "cotaWEC_2024", "track_gosetup": "COTA"},
    {"track_hymo": "daytona", "track_drive": "Daytona", "track_titan": "8129126", "track_gosetup": "Daytona"},
    {"track_hymo": "fuji", "track_drive": "Fuji", "track_titan": "Fujiwec", "track_gosetup": "Fuji"},
    {"track_hymo": "imola", "track_drive": "Imola", "track_titan": "ImolaWEC_2024", "track_gosetup": "Imola"},
    {"track_hymo": "interlagos", "track_drive": "Interlagos", "track_titan": "interlagosWEC_2024",
     "track_gosetup": "Interlagos"},
    {"track_hymo": "laguna-seca", "track_drive": "Laguna Seca", "track_titan": "9591888",
     "track_gosetup": "Laguna+Seca"},
    {"track_hymo": "lemans", "track_drive": "Le Mans", "track_titan": "Lemans2023Wec", "track_gosetup": "Le+Mans"},
    {"track_hymo": "monza", "track_drive": "Monza", "track_titan": "Monzawec", "track_gosetup": "Monza"},
    {"track_hymo": "paul-ricard", "track_drive": "Paul Ricard", "track_titan": "paul_ricard_-_elms",
     "track_gosetup": "Paul+Ricard+ELMS"},
    {"track_hymo": "portimao", "track_drive": "Portimao", "track_titan": "Portimaowec", "track_gosetup": "Portimao"},
    {"track_hymo": "qatar", "track_drive": "Qatar", "track_titan": "Losail", "track_gosetup": "Qatar"},
    {"track_hymo": "sebring", "track_drive": "Sebring", "track_titan": "Sebringwec", "track_gosetup": "Sebring"},
    {"track_hymo": "silverstone", "track_drive": "Silverstone", "track_titan": "silverstone_grand_prix_circuit_-_elms",
     "track_gosetup": "Silverstone+WEC"},
    {"track_hymo": "spa", "track_drive": "Spa", "track_titan": "Spawec", "track_gosetup": "Spa+Francorchamps"},
]


def is_valid_combo(car: str, track: str) -> bool:
    """Validation simple. Adapter selon la stratégie retenue."""
    return car in CARS and track in TRACKS
