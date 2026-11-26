"""ETAPA 4 - Registro de vendas com baixa automática do estoque (metas 1 e 2)."""
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auditoria import registrar
from ..database import get_db
from ..models import ItemVenda, Movimentacao, Produto, Usuario, Venda
from ..schemas import VendaEntrada
from ..security import somente_admin, usuario_atual

router = APIRouter(prefix="/api/vendas", tags=["Vendas"])


@router.post("", status_code=201)
def registrar_venda(dados: VendaEntrada, request: Request, db: Session = Depends(get_db),
                    usuario: Usuario = Depends(usuario_atual)):
    total = 0.0
    itens = []
    # Confere tudo antes de gravar: ou a venda inteira entra, ou nada entra.
    for item in dados.itens:
        p = db.get(Produto, item.produto_id)
        if p is None or not p.ativo:
            raise HTTPException(404, f"Produto {item.produto_id} não encontrado")
        if p.quantidade < item.quantidade:
            raise HTTPException(422, f"Estoque insuficiente: {p.nome} {p.cor} tam. {p.tamanho} "
                                     f"(disponível: {p.quantidade})")
        itens.append((p, item.quantidade))
        total += float(p.preco) * item.quantidade

    venda = Venda(usuario_id=usuario.id, total=round(total, 2),
                  forma_pagamento=dados.forma_pagamento)
    db.add(venda)
    db.flush()
    alertas = []
    for p, qtd in itens:
        db.add(ItemVenda(venda_id=venda.id, produto_id=p.id, quantidade=qtd,
                         preco_unitario=p.preco))
        p.quantidade -= qtd
        db.add(Movimentacao(produto_id=p.id, usuario_id=usuario.id, tipo="SAIDA",
                            quantidade=-qtd, motivo=f"Venda #{venda.id}"))
        if p.quantidade <= p.estoque_minimo:
            alertas.append(f"{p.nome} {p.cor} tam. {p.tamanho}: restam {p.quantidade}")
    db.commit()
    registrar(db, usuario, "VENDA_REGISTRADA", f"Venda #{venda.id} ({dados.forma_pagamento})",
              novo=f"R$ {total:.2f}", request=request)
    return {"venda_id": venda.id, "total": round(total, 2), "alertas_estoque": alertas}


@router.get("/relatorio")
def relatorio(inicio: date, fim: date, db: Session = Depends(get_db),
              _: Usuario = Depends(somente_admin)):
    """Relatório de vendas por período e produtos mais vendidos (só Administrador)."""
    if fim < inicio:
        raise HTTPException(422, "A data final deve ser depois da inicial")
    de, ate = datetime.combine(inicio, time.min), datetime.combine(fim, time.max)
    qtd_vendas, total = db.execute(
        select(func.count(Venda.id), func.coalesce(func.sum(Venda.total), 0))
        .where(Venda.data_hora.between(de, ate))).one()
    mais_vendidos = db.execute(
        select(Produto.nome, Produto.cor, Produto.tamanho,
               func.sum(ItemVenda.quantidade).label("qtd"))
        .join(ItemVenda, ItemVenda.produto_id == Produto.id)
        .join(Venda, Venda.id == ItemVenda.venda_id)
        .where(Venda.data_hora.between(de, ate))
        .group_by(Produto.id).order_by(func.sum(ItemVenda.quantidade).desc()).limit(10)).all()
    return {
        "periodo": f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}",
        "quantidade_vendas": qtd_vendas,
        "faturamento": round(float(total), 2),
        "mais_vendidos": [{"produto": f"{n} {c} tam. {t}", "quantidade": int(q)}
                          for n, c, t, q in mais_vendidos],
    }
