"""
ETAPA 3 - Modelagem do banco de dados
Tabelas: usuarios, produtos, movimentacoes, vendas, itens_venda, log_auditoria.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    login: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(100))  # nunca a senha pura
    perfil: Mapped[str] = mapped_column(String(20))  # "Administrador" ou "Vendedor"
    ativo: Mapped[bool] = mapped_column(default=True)


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))  # ex.: Calça Jeans
    cor: Mapped[str] = mapped_column(String(30))
    tamanho: Mapped[str] = mapped_column(String(10))
    preco: Mapped[float] = mapped_column(Numeric(10, 2))
    quantidade: Mapped[int] = mapped_column(Integer, default=0)
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=2)
    ativo: Mapped[bool] = mapped_column(default=True)


class Movimentacao(Base):
    """Toda entrada ou saída de estoque fica registrada (meta 1)."""
    __tablename__ = "movimentacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    tipo: Mapped[str] = mapped_column(String(10))  # ENTRADA, SAIDA, AJUSTE
    quantidade: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str] = mapped_column(String(200), default="")
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Venda(Base):
    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    total: Mapped[float] = mapped_column(Numeric(10, 2))
    forma_pagamento: Mapped[str] = mapped_column(String(20))
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    itens: Mapped[list["ItemVenda"]] = relationship(back_populates="venda")


class ItemVenda(Base):
    __tablename__ = "itens_venda"

    id: Mapped[int] = mapped_column(primary_key=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    quantidade: Mapped[int] = mapped_column(Integer)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2))

    venda: Mapped[Venda] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship()


class LogAuditoria(Base):
    """ETAPA 5 - Trilha de auditoria: quem fez o quê, quando, valor antes/depois (meta 3)."""
    __tablename__ = "log_auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    usuario_login: Mapped[str] = mapped_column(String(50))
    acao: Mapped[str] = mapped_column(String(50))
    detalhe: Mapped[str] = mapped_column(Text, default="")
    valor_anterior: Mapped[str] = mapped_column(Text, default="")
    valor_novo: Mapped[str] = mapped_column(Text, default="")
    ip: Mapped[str] = mapped_column(String(45), default="")
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
