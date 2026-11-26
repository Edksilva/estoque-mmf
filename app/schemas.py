"""
ETAPA 5 - Validação de todos os dados recebidos (Pydantic).
Dados fora das regras são recusados antes de chegar ao banco.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginEntrada(BaseModel):
    login: str = Field(min_length=3, max_length=50)
    senha: str = Field(min_length=6, max_length=100)


class ProdutoEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    cor: str = Field(min_length=2, max_length=30)
    tamanho: str = Field(min_length=1, max_length=10)
    preco: float = Field(gt=0, le=100000)
    quantidade: int = Field(ge=0, le=100000)
    estoque_minimo: int = Field(ge=0, le=10000)


class ProdutoAtualizar(BaseModel):
    preco: float | None = Field(default=None, gt=0, le=100000)
    estoque_minimo: int | None = Field(default=None, ge=0, le=10000)


class ProdutoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    cor: str
    tamanho: str
    preco: float
    quantidade: int
    estoque_minimo: int
    abaixo_minimo: bool = False


class MovimentoEntrada(BaseModel):
    produto_id: int
    tipo: Literal["ENTRADA", "AJUSTE"]
    quantidade: int = Field(ge=-100000, le=100000)
    motivo: str = Field(default="", max_length=200)


class ItemVendaEntrada(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0, le=1000)


class VendaEntrada(BaseModel):
    itens: list[ItemVendaEntrada] = Field(min_length=1)
    forma_pagamento: Literal["Dinheiro", "PIX", "Cartão Débito", "Cartão Crédito"]


class LogSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_login: str
    acao: str
    detalhe: str
    valor_anterior: str
    valor_novo: str
    ip: str
    data_hora: datetime
