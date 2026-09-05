import uuid

from tests.conftest import crear_negocio


async def _negocio_con_reglas(authed_client, n=2) -> dict:
    negocio = await crear_negocio(authed_client, {"nombre": "Con reglas"})
    reglas = []
    for i in range(n):
        resp = await authed_client.post(
            f"/api/negocios/{negocio['id']}/reglas",
            json={"keyword": f"clave{i}", "respuesta": f"Respuesta {i}"},
        )
        assert resp.status_code == 200, resp.text
        reglas.append(resp.json())
    return negocio, reglas


async def test_append_orden(authed_client):
    negocio, reglas = await _negocio_con_reglas(authed_client, 3)
    assert [r["posicion"] for r in reglas] == [0, 1, 2]

    lista = await authed_client.get(f"/api/negocios/{negocio['id']}/reglas")
    assert [r["keyword"] for r in lista.json()] == ["clave0", "clave1", "clave2"]


async def test_regla_keyword_respuesta_vacios_422(authed_client):
    negocio = await crear_negocio(authed_client, {"nombre": "N"})
    for payload in ({"keyword": "  ", "respuesta": "x"}, {"keyword": "x", "respuesta": ""}):
        resp = await authed_client.post(
            f"/api/negocios/{negocio['id']}/reglas", json=payload
        )
        assert resp.status_code == 422


async def test_regla_en_negocio_inexistente_404(authed_client):
    resp = await authed_client.post(
        f"/api/negocios/{uuid.uuid4()}/reglas",
        json={"keyword": "k", "respuesta": "r"},
    )
    assert resp.status_code == 404


async def test_patch_regla(authed_client):
    negocio, [regla] = await _negocio_con_reglas(authed_client, 1)
    resp = await authed_client.patch(
        f"/api/reglas/{regla['id']}",
        json={"keyword": "nueva", "respuesta": "  Nueva respuesta  "},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["keyword"] == "nueva"
    assert body["respuesta"] == "Nueva respuesta"
    assert body["negocio_id"] == negocio["id"]


async def test_patch_regla_404(authed_client):
    resp = await authed_client.patch(
        f"/api/reglas/{uuid.uuid4()}", json={"keyword": "x"}
    )
    assert resp.status_code == 404


async def test_delete_regla(authed_client):
    negocio, [regla] = await _negocio_con_reglas(authed_client, 1)
    resp = await authed_client.delete(f"/api/reglas/{regla['id']}")
    assert resp.status_code == 204
    lista = await authed_client.get(f"/api/negocios/{negocio['id']}/reglas")
    assert lista.json() == []


async def test_reorder_valido(authed_client):
    negocio, reglas = await _negocio_con_reglas(authed_client, 3)
    orden_invertido = [reglas[2]["id"], reglas[0]["id"], reglas[1]["id"]]
    resp = await authed_client.put(
        f"/api/negocios/{negocio['id']}/reglas/orden", json={"regla_ids": orden_invertido}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [r["id"] for r in body] == orden_invertido
    assert [r["posicion"] for r in body] == [0, 1, 2]


async def test_reorder_con_regla_de_otro_negocio_404(authed_client):
    _, [ajena] = await _negocio_con_reglas(authed_client, 1)
    negocio, reglas = await _negocio_con_reglas(authed_client, 2)
    ids = [reglas[0]["id"], reglas[1]["id"], ajena["id"]]
    resp = await authed_client.put(
        f"/api/negocios/{negocio['id']}/reglas/orden", json={"regla_ids": ids}
    )
    assert resp.status_code == 404


async def test_reorder_conjunto_incompleto_422(authed_client):
    negocio, reglas = await _negocio_con_reglas(authed_client, 3)
    resp = await authed_client.put(
        f"/api/negocios/{negocio['id']}/reglas/orden",
        json={"regla_ids": [reglas[0]["id"], reglas[1]["id"]]},
    )
    assert resp.status_code == 422


async def test_reorder_duplicados_422(authed_client):
    negocio, reglas = await _negocio_con_reglas(authed_client, 2)
    resp = await authed_client.put(
        f"/api/negocios/{negocio['id']}/reglas/orden",
        json={"regla_ids": [reglas[0]["id"], reglas[0]["id"]]},
    )
    assert resp.status_code == 422


async def test_reorder_negocio_inexistente_404(authed_client):
    resp = await authed_client.put(
        f"/api/negocios/{uuid.uuid4()}/reglas/orden",
        json={"regla_ids": [str(uuid.uuid4())]},
    )
    assert resp.status_code == 404
