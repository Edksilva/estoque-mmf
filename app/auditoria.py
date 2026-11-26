"""
ETAPA 5 - Log de auditoria
Função única usada por todo o sistema para registrar ações críticas.
"""
from fastapi import Request
from sqlalchemy.orm import Session

from .models import LogAuditoria, Usuario


def registrar(db: Session, usuario: Usuario | None, acao: str, detalhe: str = "",
              anterior: str = "", novo: str = "", request: Request | None = None,
              login: str | None = None) -> None:
    ip = request.client.host if request and request.client else ""
    db.add(LogAuditoria(
        usuario_id=usuario.id if usuario else None,
        usuario_login=usuario.login if usuario else (login or "desconhecido"),
        acao=acao,
        detalhe=detalhe,
        valor_anterior=anterior,
        valor_novo=novo,
        ip=ip,
    ))
    db.commit()
