import os


async def test_login_ok(authed_client):
    resp = await authed_client.post(
        "/api/auth/login",
        json={
            "email": os.environ["OPERATOR_EMAIL"],
            "password": os.environ["OPERATOR_PASSWORD"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == os.environ["OPERATOR_EMAIL"]
    set_cookie = resp.headers.get("set-cookie", "")
    assert "ra_token=" in set_cookie
    assert "HttpOnly" in set_cookie


async def test_login_credenciales_invalidas(client):
    resp = await client.post(
        "/api/auth/login",
        json={"email": "nadie@example.com", "password": "incorrecta"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Credenciales incorrectas"


async def test_login_email_existente_password_mal(client):
    resp = await client.post(
        "/api/auth/login",
        json={
            "email": os.environ["OPERATOR_EMAIL"],
            "password": "password-incorrecta",
        },
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Credenciales incorrectas"


async def test_me_con_cookie(authed_client):
    resp = await authed_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == os.environ["OPERATOR_EMAIL"]


async def test_me_sin_cookie(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_logout_limpia_cookie(authed_client):
    resp = await authed_client.post("/api/auth/logout")
    assert resp.status_code == 200
    set_cookie = resp.headers.get("set-cookie", "")
    assert "ra_token=" in set_cookie and "Max-Age=0" in set_cookie

    me = await authed_client.get("/api/auth/me")
    assert me.status_code == 401
