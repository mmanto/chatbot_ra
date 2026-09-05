from app.services.bot_engine import bot_reply, first_match, normalize

REGLAS = [
    {"keyword": "precio", "respuesta": "El precio es $10."},
    {"keyword": "horario", "respuesta": "Abierto de 9 a 18."},
]


def test_normalize_minusculas_acentos_puntuacion():
    assert normalize("¿Cuánto cuesta el pan?") == "cuanto cuesta el pan"
    assert normalize("  HOLA   MUNDO  ") == "hola mundo"
    assert normalize("NADIE@ejemplo.com") == "nadie ejemplo com"


def test_contiene_insensible_acentos():
    # "¿Cuánto cuesta?" contiene "cuanto cuesta" (sin acentos/puntuación)
    assert first_match(normalize("¿Cuánto cuesta?"), REGLAS) is None  # no es regla "precio"
    assert first_match(normalize("¿Cuánto cuesta el pan?"), [{"keyword": "cuanto cuesta", "respuesta": "r"}]) == "r"


def test_precedencia_por_posicion():
    reglas = [
        {"keyword": "precio", "respuesta": "primera"},
        {"keyword": "precio del pan", "respuesta": "segunda"},
    ]
    assert first_match(normalize("me interesa el precio del pan"), reglas) == "primera"


def test_bot_reply_sin_match_default():
    assert bot_reply("hola", REGLAS, default_reply="default") == "default"


def test_bot_reply_con_match_gana_default():
    assert bot_reply("¿cuál es el precio?", REGLAS, default_reply="default") == "El precio es $10."


def test_bot_reply_sin_match_sin_default_none():
    assert bot_reply("hola que tal", REGLAS, default_reply=None) is None


def test_bot_reply_vacio_none():
    assert bot_reply("   ", REGLAS) is None
    assert bot_reply("", REGLAS, default_reply="x") is None


def test_acepta_objetos_con_atributos():
    class Regla:
        def __init__(self, keyword, respuesta):
            self.keyword = keyword
            self.respuesta = respuesta

    reglas = [Regla("horario", "Abrimos a las 9")]
    assert bot_reply("cuál es su horario", reglas) == "Abrimos a las 9"
