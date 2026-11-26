"""
ETAPA 6 - Testes automatizados (Qualidade de Software)
Cada grupo de testes comprova uma meta do relatório.
Rodar:  python -m pytest -v
"""


def _produto(cliente, admin, **extra):
    dados = {"nome": "Calça Teste", "cor": "Azul", "tamanho": "40", "preco": 100.0,
             "quantidade": 5, "estoque_minimo": 2, **extra}
    r = cliente.post("/api/produtos", json=dados, headers=admin)
    assert r.status_code == 201, r.text
    return r.json()


def _logs(cliente, admin, acao):
    return cliente.get(f"/api/admin/auditoria?acao={acao}", headers=admin).json()


# ---------- Segurança: autenticação ----------
def test_login_correto_retorna_token(cliente):
    r = cliente.post("/api/auth/login", json={"login": "manoel", "senha": "Mmf@2026"})
    assert r.status_code == 200
    assert r.json()["perfil"] == "Administrador"


def test_login_senha_errada_e_recusado(cliente):
    r = cliente.post("/api/auth/login", json={"login": "manoel", "senha": "errada123"})
    assert r.status_code == 401


def test_senha_guardada_como_hash_bcrypt():
    from sqlalchemy import select
    from app.database import SessionLocal
    from app.models import Usuario
    with SessionLocal() as db:
        u = db.scalar(select(Usuario).where(Usuario.login == "manoel"))
        assert u.senha_hash != "Mmf@2026"
        assert u.senha_hash.startswith("$2")  # prefixo do bcrypt


def test_bloqueio_apos_5_tentativas_erradas(cliente):
    for _ in range(5):
        cliente.post("/api/auth/login", json={"login": "vendedor", "senha": "errada123"})
    r = cliente.post("/api/auth/login", json={"login": "vendedor", "senha": "Venda@2026"})
    assert r.status_code == 429


def test_rota_protegida_sem_token_e_recusada(cliente):
    assert cliente.get("/api/produtos").status_code == 401


def test_token_falso_e_recusado(cliente):
    r = cliente.get("/api/produtos", headers={"Authorization": "Bearer token.falso.123"})
    assert r.status_code == 401


def test_sql_injection_no_login_nao_funciona(cliente):
    r = cliente.post("/api/auth/login", json={"login": "manoel' OR '1'='1", "senha": "qualquer1"})
    assert r.status_code == 401


# ---------- Meta 4: perfil Vendedor bloqueado ----------
def test_vendedor_nao_cadastra_produto(cliente, vendedor):
    r = cliente.post("/api/produtos", headers=vendedor, json={
        "nome": "X", "cor": "Y", "tamanho": "1", "preco": 1, "quantidade": 1, "estoque_minimo": 0})
    assert r.status_code == 403


def test_vendedor_nao_ve_auditoria_nem_relatorio(cliente, vendedor):
    assert cliente.get("/api/admin/auditoria", headers=vendedor).status_code == 403
    assert cliente.get("/api/vendas/relatorio?inicio=2026-01-01&fim=2026-12-31",
                       headers=vendedor).status_code == 403


def test_acesso_negado_fica_no_log(cliente, admin, vendedor):
    cliente.delete("/api/produtos/1", headers=vendedor)
    assert any("DELETE" in l["detalhe"] for l in _logs(cliente, admin, "ACESSO_NEGADO"))


# ---------- Meta 1: registro de vendas e movimentações ----------
def test_venda_baixa_o_estoque(cliente, admin, vendedor):
    p = _produto(cliente, admin, quantidade=10)
    r = cliente.post("/api/vendas", headers=vendedor, json={
        "itens": [{"produto_id": p["id"], "quantidade": 3}], "forma_pagamento": "PIX"})
    assert r.status_code == 201
    assert r.json()["total"] == 300.0
    atual = next(x for x in cliente.get("/api/produtos", headers=admin).json() if x["id"] == p["id"])
    assert atual["quantidade"] == 7


def test_venda_sem_estoque_e_recusada_e_nada_muda(cliente, admin, vendedor):
    p = _produto(cliente, admin, quantidade=2)
    r = cliente.post("/api/vendas", headers=vendedor, json={
        "itens": [{"produto_id": p["id"], "quantidade": 5}], "forma_pagamento": "Dinheiro"})
    assert r.status_code == 422
    atual = next(x for x in cliente.get("/api/produtos", headers=admin).json() if x["id"] == p["id"])
    assert atual["quantidade"] == 2


def test_entrada_de_estoque_soma_quantidade(cliente, admin):
    p = _produto(cliente, admin, quantidade=1)
    r = cliente.post("/api/estoque/movimentar", headers=admin, json={
        "produto_id": p["id"], "tipo": "ENTRADA", "quantidade": 9, "motivo": "NF 123"})
    assert r.json()["quantidade_atual"] == 10


def test_estoque_nunca_fica_negativo(cliente, admin):
    p = _produto(cliente, admin, quantidade=1)
    r = cliente.post("/api/estoque/movimentar", headers=admin, json={
        "produto_id": p["id"], "tipo": "AJUSTE", "quantidade": -5, "motivo": "perda"})
    assert r.status_code == 422


def test_dados_invalidos_sao_recusados(cliente, admin):
    r = cliente.post("/api/produtos", headers=admin, json={
        "nome": "X", "cor": "Azul", "tamanho": "40", "preco": -10, "quantidade": 1,
        "estoque_minimo": 1})
    assert r.status_code == 422


# ---------- Meta 2: alerta de estoque mínimo ----------
def test_alerta_aparece_quando_estoque_chega_no_minimo(cliente, admin, vendedor):
    p = _produto(cliente, admin, quantidade=4, estoque_minimo=2)
    r = cliente.post("/api/vendas", headers=vendedor, json={
        "itens": [{"produto_id": p["id"], "quantidade": 2}], "forma_pagamento": "PIX"})
    assert r.json()["alertas_estoque"]
    alertas = cliente.get("/api/produtos/alertas", headers=vendedor).json()
    assert any(a["id"] == p["id"] for a in alertas)


# ---------- Meta 3: log de auditoria das ações críticas ----------
def test_alteracao_de_preco_registra_antes_e_depois(cliente, admin):
    p = _produto(cliente, admin, preco=89.90)
    cliente.patch(f"/api/produtos/{p['id']}", headers=admin, json={"preco": 99.90})
    log = _logs(cliente, admin, "PRECO_ALTERADO")[0]
    assert log["valor_anterior"] == "R$ 89.90" and log["valor_novo"] == "R$ 99.90"
    assert log["usuario_login"] == "manoel"


def test_exclusao_de_produto_fica_no_log(cliente, admin):
    p = _produto(cliente, admin)
    assert cliente.delete(f"/api/produtos/{p['id']}", headers=admin).status_code == 204
    assert any(f"#{p['id']} " in l["detalhe"] for l in _logs(cliente, admin, "PRODUTO_EXCLUIDO"))


def test_login_com_falha_fica_no_log(cliente, admin):
    cliente.post("/api/auth/login", json={"login": "manoel", "senha": "tentativa1"})
    assert _logs(cliente, admin, "LOGIN_FALHA")


def test_venda_fica_no_log(cliente, admin):
    assert _logs(cliente, admin, "VENDA_REGISTRADA")


# ---------- Relatório e backup ----------
def test_relatorio_de_vendas(cliente, admin):
    from datetime import date
    hoje = date.today().isoformat()
    r = cliente.get(f"/api/vendas/relatorio?inicio={hoje}&fim={hoje}", headers=admin)
    assert r.status_code == 200
    assert r.json()["quantidade_vendas"] >= 1


def test_backup_gera_arquivo(cliente, admin):
    from pathlib import Path
    r = cliente.post("/api/admin/backup", headers=admin)
    assert r.status_code == 200
    assert Path(r.json()["arquivo"]).exists()
