"""ETAPA 4 - Cadastro de produtos e alerta de estoque mínimo (meta 2)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auditoria import registrar
from ..database import get_db
from ..models import Produto, Usuario
from ..schemas import ProdutoAtualizar, ProdutoEntrada, ProdutoSaida
from ..security import somente_admin, usuario_atual

router = APIRouter(prefix="/api/produtos", tags=["Produtos"])


def _saida(p: Produto) -> ProdutoSaida:
    s = ProdutoSaida.model_validate(p)
    s.abaixo_minimo = p.quantidade <= p.estoque_minimo
    return s


@router.get("", response_model=list[ProdutoSaida])
def listar(db: Session = Depends(get_db), _: Usuario = Depends(usuario_atual)):
    produtos = db.scalars(select(Produto).where(Produto.ativo)
                          .order_by(Produto.nome, Produto.cor, Produto.tamanho))
    return [_saida(p) for p in produtos]


@router.get("/alertas", response_model=list[ProdutoSaida])
def alertas(db: Session = Depends(get_db), _: Usuario = Depends(usuario_atual)):
    """Produtos com quantidade igual ou abaixo do estoque mínimo."""
    produtos = db.scalars(select(Produto).where(
        Produto.ativo, Produto.quantidade <= Produto.estoque_minimo).order_by(Produto.quantidade))
    return [_saida(p) for p in produtos]


@router.post("", response_model=ProdutoSaida, status_code=201)
def cadastrar(dados: ProdutoEntrada, request: Request, db: Session = Depends(get_db),
              admin: Usuario = Depends(somente_admin)):
    p = Produto(**dados.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    registrar(db, admin, "PRODUTO_CADASTRADO",
              f"#{p.id} {p.nome} {p.cor} tam. {p.tamanho}",
              novo=f"preço R$ {p.preco:.2f}, qtd {p.quantidade}", request=request)
    return _saida(p)


@router.patch("/{produto_id}", response_model=ProdutoSaida)
def atualizar(produto_id: int, dados: ProdutoAtualizar, request: Request,
              db: Session = Depends(get_db), admin: Usuario = Depends(somente_admin)):
    p = db.get(Produto, produto_id)
    if p is None or not p.ativo:
        raise HTTPException(404, "Produto não encontrado")
    if dados.preco is not None and float(dados.preco) != float(p.preco):
        anterior = f"R$ {float(p.preco):.2f}"
        p.preco = dados.preco
        db.commit()
        registrar(db, admin, "PRECO_ALTERADO", f"#{p.id} {p.nome} {p.cor} tam. {p.tamanho}",
                  anterior=anterior, novo=f"R$ {dados.preco:.2f}", request=request)
    if dados.estoque_minimo is not None and dados.estoque_minimo != p.estoque_minimo:
        anterior = str(p.estoque_minimo)
        p.estoque_minimo = dados.estoque_minimo
        db.commit()
        registrar(db, admin, "MINIMO_ALTERADO", f"#{p.id} {p.nome}",
                  anterior=anterior, novo=str(dados.estoque_minimo), request=request)
    db.refresh(p)
    return _saida(p)


@router.delete("/{produto_id}", status_code=204)
def excluir(produto_id: int, request: Request, db: Session = Depends(get_db),
            admin: Usuario = Depends(somente_admin)):
    """Exclusão lógica: o produto some da lista, mas o histórico de vendas é preservado."""
    p = db.get(Produto, produto_id)
    if p is None or not p.ativo:
        raise HTTPException(404, "Produto não encontrado")
    p.ativo = False
    db.commit()
    registrar(db, admin, "PRODUTO_EXCLUIDO", f"#{p.id} {p.nome} {p.cor} tam. {p.tamanho}",
              anterior=f"qtd {p.quantidade}", request=request)
