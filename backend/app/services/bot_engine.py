"""Motor de reglas del bot: función pura sin I/O.

Semántica: cada regla es una frase; coincide si el mensaje normalizado
*contiene* el keyword normalizado. Gana la primera regla por `posicion`.
Todo insensible a mayúsculas/acentos/puntuación.
"""
import re
import unicodedata
from collections.abc import Sequence

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize(text: str) -> str:
    """Minúsculas, sin acentos, solo alfanuméricos y espacios, colapsados."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = _NON_ALNUM_RE.sub(" ", text.lower())
    return " ".join(text.split())


def first_match(normalized_message: str, reglas: Sequence) -> str | None:
    """Primera regla (por orden de la secuencia) cuyo keyword está contenido.

    `reglas` acepta objetos con `.keyword`/`.respuesta` o dicts.
    Devuelve la `respuesta` o None.
    """
    for regla in reglas:
        if isinstance(regla, dict):
            keyword = regla.get("keyword", "")
            respuesta = regla.get("respuesta")
        else:
            keyword = regla.keyword
            respuesta = regla.respuesta
        if not keyword:
            continue
        if normalize(keyword) in normalized_message:
            return respuesta
    return None


def bot_reply(text: str, reglas: Sequence, default_reply: str | None = None) -> str | None:
    """Responde según reglas; si nada coincide usa `default_reply`; None si no hay respuesta."""
    normalized = normalize(text)
    if not normalized:
        return None
    respuesta = first_match(normalized, reglas)
    if respuesta is None:
        respuesta = default_reply
    return respuesta if respuesta else None
