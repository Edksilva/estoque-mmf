"""ETAPA 4 - Entradas de mercadoria e ajustes de estoque (meta 1)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auditoria import registrar
from ..database import get_db
from ..models import Movimentacao, Produto, Usuario
from ..schemas import MovimentoEntrada
from ..security import somente_admin, usuario_atual

router = APIRouter(prefix="/api/estoque", tags=["Estoque"])


@router.post("/movimentar", status_code=201)
def movimentar(dados: MovimentoEntrada, request: Request, db: Session = Depends(get_db),
               admin: Usuario = Depends(somente_admin)):
    p = db.get(Produto, dados.produto_id)
    if p is None or not p.ativo:
        raise HTTPException(404, "Produto não encontrado")
    if dados.tipo == "ENTRADA" and dados.quantidade <= 0:
        raise HTTPException(422, "A entrada precisa de quantidade maior que zero")
    if dados.tipo == "AJUSTE" and not dados.motivo.strip():
        raise HTTPException(422, "Informe o motivo do ajuste")
    if p.quantidade + dados.quantidade < 0:
        raise HTTPException(422, "O estoque não pode ficar negativo")

    anterior = p.quantidade
    p.quantidade += dados.quantidade
    db.add(Movimentacao(produto_id=p.id, usuario_id=admin.id, tipo=dados.tipo,
                        quantidade=dados.quantidade, motivo=dados.motivo))
    db.commit()
    acao = "ESTOQUE_ENTRADA" if dados.tipo == "ENTRADA" else "ESTOQUE_AJUSTE"
    registrar(db, admin, acao, f"#{p.id} {p.nome} {p.cor} tam. {p.tamanho} {dados.motivo}".strip(),
              anterior=str(anterior), novo=str(p.quantidade), request=request)
    return {"produto_id": p.id, "quantidade_atual": p.quantidade}


@router.get("/movimentacoes")
def movimentacoes(db: Session = Depends(get_db), _: Usuario = Depends(usuario_atual)):
    linhas = db.execute(
        select(Movimentacao, Produto).join(Produto, Produto.id == Movimentacao.produto_id)
        .order_by(Movimentacao.data_hora.desc()).limit(100)
    ).all()
    return [{"data_hora": m.data_hora, "produto": f"{p.nome} {p.cor} {p.tamanho}",
             "tipo": m.tipo, "quantidade": m.quantidade, "motivo": m.motivo}
            for m, p in linhas]
