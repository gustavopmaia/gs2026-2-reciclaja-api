"""GET /v1/points e /v1/points/{id}: caminho feliz, erros e contrato."""


def test_get_point_happy_path(client, assert_contract):
    resp = client.get("/v1/points/PC-001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "PC-001"
    assert body["data_source"] == "sintetico"
    assert resp.headers["X-Request-ID"]
    assert_contract("/v1/points/{point_id}", "get", resp)


def test_get_point_inexistente_retorna_404(client, assert_contract):
    resp = client.get("/v1/points/PC-999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
    assert_contract("/v1/points/{point_id}", "get", resp)


def test_get_point_id_malformado_retorna_400(client, assert_contract):
    resp = client.get("/v1/points/abc")
    assert resp.status_code == 400
    assert resp.json()["error"]["details"][0]["field"] == "path.point_id"
    assert_contract("/v1/points/{point_id}", "get", resp)


def test_list_points_filtra_e_pagina(client, assert_contract):
    resp = client.get("/v1/points", params={"material": "pilha_bateria", "limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4
    assert len(body["items"]) == 2
    assert all("pilha_bateria" in p["materials"] for p in body["items"])
    assert body["next"] == "/v1/points?material=pilha_bateria&limit=2&offset=2"
    assert_contract("/v1/points", "get", resp)

    last = client.get(body["next"]).json()
    assert len(last["items"]) == 2
    assert last["next"] is None


def test_list_points_filtro_bairro_ignora_acento_e_caixa(client):
    body = client.get("/v1/points", params={"neighborhood": "TATUAPE", "status": "aberto"}).json()
    assert {p["id"] for p in body["items"]} == {"PC-003", "PC-019"}


def test_list_points_material_invalido_retorna_400(client, assert_contract):
    resp = client.get("/v1/points", params={"material": "radioativo"})
    assert resp.status_code == 400
    assert_contract("/v1/points", "get", resp)


def test_list_points_limit_fora_da_faixa_retorna_400(client):
    assert client.get("/v1/points", params={"limit": 0}).status_code == 400
    assert client.get("/v1/points", params={"limit": 51}).status_code == 400


def test_health_informa_provedor(client, assert_contract):
    resp = client.get("/v1/health")
    assert resp.json() == {
        "status": "ok",
        "llm_provider": "fake",
        "llm_model": "fake-deterministic-v1",
        "points_loaded": 24,
    }
    assert_contract("/v1/health", "get", resp)
