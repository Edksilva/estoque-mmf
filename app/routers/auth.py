"""ETAPA 5 - Login com auditoria de sucesso, falha e bloqueio."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auditoria import registrar
from ..database import get_db
from ..models import Usuario
from ..schemas import LoginEntrada
from ..security import (conferir_senha, criar_token, limpar_falhas, login_bloqueado,
                        registrar_falha, usuario_atual)

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/login")
def login(dados: LoginEntrada, request: Request, db: Session = Depends(get_db)):
    if login_bloqueado(dados.login):
        registrar(db, None, "LOGIN_BLOQUEADO", "Muitas tentativas erradas",
                  request=request, login=dados.login)
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Muitas tentativas. Aguarde 5 minutos.")

    usuario = db.scalar(select(Usuario).where(Usuario.login == dados.login))
    if usuario is None or not usuario.ativo or not conferir_senha(dados.senha, usuario.senha_hash):
        registrar_falha(dados.login)
        registrar(db, usuario, "LOGIN_FALHA", "Usuário ou senha incorretos",
                  request=request, login=dados.login)
        # Mensagem genérica: não revela se o usuário existe
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário ou senha incorretos")

    limpar_falhas(dados.login)
    registrar(db, usuario, "LOGIN_SUCESSO", f"Perfil {usuario.perfil}", request=request)
    return {"token": criar_token(usuario), "nome": usuario.nome, "perfil": usuario.perfil}


@router.get("/eu")
def eu(usuario: Usuario = Depends(usuario_atual)):
    return {"nome": usuario.nome, "login": usuario.login, "perfil": usuario.perfil}
