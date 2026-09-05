from tests.conftest import crear_negocio


async def test_lista_vacia(authed_client):
    resp = await authed_client.get("/api/negocios")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_crear_slug_autogenerado(authed_client):
    negocio = await crear_negocio(authed_client, {"nombre": "Panadería La Aurora"})
    assert negocio["slug"] == "panaderia-la-aurora"
    assert negocio["nombre"] == "Panadería La Aurora"
    assert negocio["activo"] is True
    assert negocio["autoresponder"] is True
    assert negocio["greeting"] is None
    assert negocio["default_reply"] is None


async def test_slug_explícito_y_colisión_autogenerada(authed_client):
    await crear_negocio(authed_client, {"nombre": "Panadería La Aurora"})

    # colisión con slug autogenerado → -2
    segundo = await crear_negocio(authed_client, {"nombre": "Panadería La Aurora"})
    assert segundo["slug"] == "panaderia-la-aurora-2"

    # tercero → -3
    tercero = await crear_negocio(authed_client, {"nombre": "Panadería La Aurora"})
    assert tercero["slug"] == "panaderia-la-aurora-3"


async def test_slug_explícito_duplicado_409(authed_client):
    await crear_negocio(authed_client, {"nombre": "Uno", "slug": "mi-negocio"})
    resp = await authed_client.post(
        "/api/negocios", json={"nombre": "Otro", "slug": "mi-negocio"}
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "El slug ya está en uso"


async def test_slug_invalido_422(authed_client):
    for slug in ("Mi Slug", "slug_guion_bajo", "UPPER", "-inicio", "fin-", ""):
        resp = await authed_client.post(
            "/api/negocios", json={"nombre": "X", "slug": slug}
        )
        assert resp.status_code == 422, slug


async def test_nombre_vacio_422(authed_client):
    resp = await authed_client.post("/api/negocios", json={"nombre": "   "})
    assert resp.status_code == 422


async def test_patch_campos(authed_client):
    negocio = await crear_negocio(authed_client, {"nombre": "Original"})
    negocio_id = negocio["id"]

    resp = await authed_client.patch(
        f"/api/negocios/{negocio_id}",
        json={
            "nombre": "Renombrado",
            "greeting": "  ¡Hola!  ",
            "default_reply": "",
            "activo": False,
            "autoresponder": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["nombre"] == "Renombrado"
    assert body["greeting"] == "¡Hola!"
    assert body["default_reply"] is None
    assert body["activo"] is False
    assert body["autoresponder"] is False


async def test_patch_slug_duplicado_409(authed_client):
    await crear_negocio(authed_client, {"nombre": "A", "slug": "ocupado"})
    negocio = await crear_negocio(authed_client, {"nombre": "B"})
    resp = await authed_client.patch(
        f"/api/negocios/{negocio['id']}", json={"slug": "ocupado"}
    )
    assert resp.status_code == 409


async def test_patch_slug_propio_sin_cambio_ok(authed_client):
    negocio = await crear_negocio(authed_client, {"nombre": "A", "slug": "mismo"})
    resp = await authed_client.patch(
        f"/api/negocios/{negocio['id']}", json={"slug": "mismo"}
    )
    assert resp.status_code == 200


async def test_404_cruzados_negocio(authed_client):
    import uuid

    nid = uuid.uuid4()
    assert (await authed_client.get(f"/api/negocios/{nid}")).status_code == 404
    assert (await authed_client.patch(f"/api/negocios/{nid}", json={})).status_code == 404
    assert (await authed_client.delete(f"/api/negocios/{nid}")).status_code == 404


async def test_negocios_sin_auth_401(client):
    resp = await client.get("/api/negocios")
    assert resp.status_code == 401
    resp = await client.post("/api/negocios", json={"nombre": "X"})
    assert resp.status_code == 401


async def test_eliminar_204_y_desaparece(authed_client):
    negocio = await crear_negocio(authed_client, {"nombre": "Para borrar"})
    resp = await authed_client.delete(f"/api/negocios/{negocio['id']}")
    assert resp.status_code == 204
    lista = await authed_client.get("/api/negocios")
    assert lista.json() == []
