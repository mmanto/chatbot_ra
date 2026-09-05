from tests.conftest import crear_negocio

GREETING = "¡Hola! Soy el asistente virtual."
DEFAULT_REPLY = "Un asesor te atenderá en breve."
REGLA_PRECIO = "Nuestro kilo de pan sale $3.500."


async def _negocio_listo(authed_client, slug: str | None = None, **patch) -> dict:
    payload = {"nombre": "Panadería La Aurora"}
    if slug:
        payload["slug"] = slug
    negocio = await crear_negocio(authed_client, payload)
    await authed_client.post(
        f"/api/negocios/{negocio['id']}/reglas",
        json={"keyword": "precio", "respuesta": REGLA_PRECIO},
    )
    await authed_client.post(
        f"/api/negocios/{negocio['id']}/reglas",
        json={"keyword": "horario", "respuesta": "Abierto lun-sáb de 7 a 20 h."},
    )
    # PATCH: los campos de comportamiento (autoresponder, activo, textos)
    # no se aceptan al crear; se aplican aquí.
    resp = await authed_client.patch(
        f"/api/negocios/{negocio['id']}",
        json={"greeting": GREETING, "default_reply": DEFAULT_REPLY, **patch},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _start(authed_client, slug: str) -> dict:
    resp = await authed_client.get(f"/api/public/{slug}/start")
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_start_devuelve_greeting(authed_client):
    negocio = await _negocio_listo(authed_client)
    data = await _start(authed_client, negocio["slug"])

    assert data["negocio"] == {"slug": negocio["slug"], "nombre": negocio["nombre"]}
    assert len(data["mensajes"]) == 1
    m = data["mensajes"][0]
    assert m["autor"] == "bot"
    assert m["contenido"] == GREETING
    assert m["created_at"] is not None

    # segundo start genera otra conversación
    data2 = await _start(authed_client, negocio["slug"])
    assert data2["token"] != data["token"]


async def test_message_regla_y_default(authed_client):
    negocio = await _negocio_listo(authed_client)
    data = await _start(authed_client, negocio["slug"])

    # el mensaje contiene la keyword "precio" (insensible a acentos no aplica acá)
    resp = await authed_client.post(
        f"/api/public/{negocio['slug']}/message",
        json={"token": data["token"], "contenido": "¿cuál es el PRECIO del pan?"},
    )
    assert resp.status_code == 200
    assert resp.json()["reply"] == REGLA_PRECIO

    resp2 = await authed_client.post(
        f"/api/public/{negocio['slug']}/message",
        json={"token": data["token"], "contenido": "hola, buen día"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["reply"] == DEFAULT_REPLY

    # historial: greeting + visitor + bot + visitor + bot
    hist = await authed_client.get(
        f"/api/public/{negocio['slug']}/history", params={"token": data["token"]}
    )
    assert hist.status_code == 200
    autores = [m["autor"] for m in hist.json()]
    assert autores == ["bot", "visitor", "bot", "visitor", "bot"]
    contenidos = [m["contenido"] for m in hist.json()]
    assert contenidos[0] == GREETING
    assert contenidos[2] == REGLA_PRECIO
    assert contenidos[4] == DEFAULT_REPLY


async def test_keyword_con_acentos_y_puntuacion(authed_client):
    """Un keyword con acentos detecta la frase escrita sin acentos y con signos."""
    negocio = await crear_negocio(authed_client, {"nombre": "Ferretería"})
    resp = await authed_client.post(
        f"/api/negocios/{negocio['id']}/reglas",
        json={"keyword": "cuánto cuesta", "respuesta": "Te paso el precio."},
    )
    assert resp.status_code == 200
    data = await _start(authed_client, negocio["slug"])
    msg = await authed_client.post(
        f"/api/public/{negocio['slug']}/message",
        json={"token": data["token"], "contenido": "¿Cuánto cuesta?"},
    )
    assert msg.json()["reply"] == "Te paso el precio."


async def test_message_sin_match_sin_default_no_responde(authed_client):
    negocio = await _negocio_listo(authed_client)
    # sin default_reply ni greeting
    await authed_client.patch(
        f"/api/negocios/{negocio['id']}", json={"default_reply": None, "greeting": None}
    )
    data = await _start(authed_client, negocio["slug"])
    assert data["mensajes"] == []

    resp = await authed_client.post(
        f"/api/public/{negocio['slug']}/message",
        json={"token": data["token"], "contenido": "frase aleatoria sin match"},
    )
    assert resp.status_code == 200
    assert resp.json()["reply"] is None

    hist = await authed_client.get(
        f"/api/public/{negocio['slug']}/history", params={"token": data["token"]}
    )
    autores = [m["autor"] for m in hist.json()]
    assert autores == ["visitor"]  # sin greeting ni bot


async def test_autoresponder_false_no_contesta(authed_client):
    negocio = await _negocio_listo(authed_client, autoresponder=False)
    data = await _start(authed_client, negocio["slug"])
    assert data["mensajes"] == []  # sin greeting

    resp = await authed_client.post(
        f"/api/public/{negocio['slug']}/message",
        json={"token": data["token"], "contenido": "¿cuál es el precio del pan?"},
    )
    assert resp.status_code == 200
    assert resp.json()["reply"] is None

    hist = await authed_client.get(
        f"/api/public/{negocio['slug']}/history", params={"token": data["token"]}
    )
    autores = [m["autor"] for m in hist.json()]
    assert autores == ["visitor"]  # el mensaje queda registrado, sin bot


async def test_token_de_otra_conversacion_es_valido(authed_client):
    """D1: el token vale si su conversación pertenece al slug (aunque sea otra)."""
    negocio = await _negocio_listo(authed_client)
    data = await _start(authed_client, negocio["slug"])
    data_otro = await _start(authed_client, negocio["slug"])

    resp = await authed_client.post(
        f"/api/public/{negocio['slug']}/message",
        json={"token": data_otro["token"], "contenido": "hola"},
    )
    assert resp.status_code == 200
    assert resp.json()["reply"] == DEFAULT_REPLY

    # el mensaje quedó en la otra conversación
    hist = await authed_client.get(
        f"/api/public/{negocio['slug']}/history", params={"token": data_otro["token"]}
    )
    assert len(hist.json()) == 3  # greeting + visitor + bot


async def test_token_cruzado_entre_slugs_404(authed_client):
    negocio = await _negocio_listo(authed_client)
    otro = await _negocio_listo(authed_client, slug="otro-negocio")
    data = await _start(authed_client, negocio["slug"])

    resp = await authed_client.post(
        f"/api/public/{otro['slug']}/message",
        json={"token": data["token"], "contenido": "hola"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "no_disponible"


async def test_negocio_inactivo_404(authed_client):
    negocio = await _negocio_listo(authed_client)
    resp = await authed_client.patch(
        f"/api/negocios/{negocio['id']}", json={"activo": False}
    )
    assert resp.status_code == 200

    start = await authed_client.get(f"/api/public/{negocio['slug']}/start")
    assert start.status_code == 404
    assert start.json()["detail"] == "no_disponible"

    message = await authed_client.post(
        f"/api/public/{negocio['slug']}/message",
        json={"token": "00000000-0000-0000-0000-000000000000", "contenido": "hola"},
    )
    assert message.status_code == 404

    hist = await authed_client.get(
        f"/api/public/{negocio['slug']}/history", params={"token": "00000000-0000-0000-0000-000000000000"}
    )
    assert hist.status_code == 404


async def test_slug_inexistente_404(authed_client):
    resp = await authed_client.get("/api/public/no-existe/start")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "no_disponible"


async def test_contenido_vacio_o_largo_422(authed_client):
    negocio = await _negocio_listo(authed_client)
    data = await _start(authed_client, negocio["slug"])

    resp = await authed_client.post(
        f"/api/public/{negocio['slug']}/message",
        json={"token": data["token"], "contenido": "   "},
    )
    assert resp.status_code == 422

    resp2 = await authed_client.post(
        f"/api/public/{negocio['slug']}/message",
        json={"token": data["token"], "contenido": "x" * 2001},
    )
    assert resp2.status_code == 422
