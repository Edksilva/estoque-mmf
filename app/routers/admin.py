"""ETAPA 5 - Consulta do log de auditoria e backup do banco (só Administrador)."""
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auditoria import registrar
from ..database import DATABASE_URL, get_db
from ..models import LogAuditoria, Usuario
from ..schemas import LogSaida
from ..security import somente_admin

router = APIRouter(prefix="/api/admin", tags=["Administração"])

PASTA_BACKUP = Path("backups")


@router.get("/auditoria", response_model=list[LogSaida])
def ver_auditoria(acao: str | None = None, db: Session = Depends(get_db),
                  _: Usuario = Depends(somente_admin)):
    consulta = select(LogAuditoria).order_by(LogAuditoria.id.desc()).limit(200)
    if acao:
        consulta = consulta.where(LogAuditoria.acao == acao)
    return db.scalars(consulta).all()


def fazer_backup() -> Path:
    if not DATABASE_URL.startswith("sqlite:///"):
        raise RuntimeError("Backup automático disponível apenas para SQLite")
    origem = Path(DATABASE_URL.replace("sqlite:///", ""))
    PASTA_BACKUP.mkdir(exist_ok=True)
    destino = PASTA_BACKUP / f"estoque_mmf_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(origem, destino)
    return destino


@router.post("/backup")
def backup(request: Request, db: Session = Depends(get_db),
           admin: Usuario = Depends(somente_admin)):
    try:
        destino = fazer_backup()
    except (RuntimeError, OSError) as erro:
        raise HTTPException(500, f"Falha no backup: {erro}")
    registrar(db, admin, "BACKUP_REALIZADO", str(destino), request=request)
    return {"arquivo": str(destino)}
