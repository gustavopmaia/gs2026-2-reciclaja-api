"""Contrato × código: o YAML é válido e cada rota do YAML existe no app (e vice-versa)."""

from openapi_spec_validator import validate

from conftest import CONTRACT_FILE

OPERATIONAL_ROUTES = {"/metrics"}  # fora do contrato de negócio (scrape do Prometheus)


def test_contrato_openapi_valido(contract):
    validate(contract)  # levanta exceção se o YAML for inválido


def test_rotas_do_codigo_batem_com_o_contrato(client, contract):
    documented = {(path, method.upper()) for path, ops in contract["paths"].items() for method in ops}
    implemented = {
        (route.path, method)
        for route in client.app.routes
        if route.path not in OPERATIONAL_ROUTES
        for method in getattr(route, "methods", set())
        if method != "HEAD"
    }
    assert documented == implemented, f"divergência YAML × código: {documented ^ implemented}"


def test_erros_padronizados_documentados(contract):
    for path, ops in contract["paths"].items():
        for method, op in ops.items():
            if path == "/v1/health":
                continue
            assert "400" in op["responses"] and "503" in op["responses"], f"{method} {path}"
    assert "404" in contract["paths"]["/v1/points/{point_id}"]["get"]["responses"]
    assert "422" in contract["paths"]["/v1/ask"]["post"]["responses"]


def test_contrato_arquivo_existe():
    assert CONTRACT_FILE.name == "2_contrato_api.yaml"
