"""
Sistema de Controle de Estoque e Vendas - MMF (Manoel Modas e Família)
Projeto Integrador II - ADS - FASUL Educacional
Aluno: Edson José da Silva

Para rodar:  uvicorn app.main:app --reload
Telas:       http://127.0.0.1:8000
API (docs):  http://127.0.0.1:8000/docs
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .models import Produto, Usuario
from .routers import admin, auth, estoque, produtos, vendas
from .security import gerar_hash

PASTA_STATIC = Path(__file__).parent / "static"

app = FastAPI(
    title="MMF - Controle de Estoque e Vendas",
    description="Projeto Integrador II - API REST com autenticação, perfis e auditoria",
    version="1.0.0",
)
app.include_router(auth.router)
app.include_router(produtos.router)
app.include_router(estoque.router)
app.include_router(vendas.router)
app.include_router(admin.router)
app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")


@app.middleware("http")
async def cabecalhos_seguranca(request, call_next):
    """ETAPA 5 - Cabeçalhos HTTP de segurança (OWASP)."""
    resposta = await call_next(request)
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["Referrer-Policy"] = "no-referrer"
    return resposta


@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(PASTA_STATIC / "index.html")


# Produtos reais da loja MMF. Os PREÇOS SÃO DE EXEMPLO: confirmar com o Manoel.
CORES = ["Bordô", "Preto", "Cinza", "Azul Marinho", "Caqui"]
TAMANHOS = ["38", "40", "42", "44"]


def popular_banco() -> None:
    """Cria as tabelas e os dados iniciais na primeira execução."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Usuario).limit(1)):
            return
        db.add_all([
            Usuario(nome="Manoel", login="manoel", perfil="Administrador",
                    senha_hash=gerar_hash("Mmf@2026")),
            Usuario(nome="Vendedor Loja", login="vendedor", perfil="Vendedor",
                    senha_hash=gerar_hash("Venda@2026")),
        ])
        for cor in CORES:
            for i, tam in enumerate(TAMANHOS):
                # Algumas peças começam com pouco estoque para mostrar o alerta
                qtd = 1 if (cor == "Bordô" and tam == "44") or (cor == "Caqui" and tam == "38") else 6 + i
                db.add(Produto(nome="Calça Jeans", cor=cor, tamanho=tam, preco=89.90,
                               quantidade=qtd, estoque_minimo=2))
        db.add(Produto(nome="Bermuda Jeans", cor="Azul", tamanho="42", preco=59.90,
                       quantidade=4, estoque_minimo=2))
        db.commit()


popular_banco()
