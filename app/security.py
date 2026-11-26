"""
ETAPA 5 - Segurança e Auditoria de Sistemas
- Senhas guardadas como hash bcrypt (nunca em texto puro)
- Token JWT com validade de 8 horas (um turno de trabalho)
- Controle de acesso por perfil (Administrador x Vendedor) - meta 4
- Bloqueio temporário após 5 tentativas de login erradas (força bruta)
"""
import os
import secrets
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Usuario

# A chave vem de variável de ambiente; sem ela, uma chave aleatória forte é gerada
# a cada início do servidor (nunca fica escrita no código).
CHAVE_SECRETA = os.getenv("MMF_SECRET_KEY") or secrets.token_urlsafe(48)
ALGORITMO = "HS256"
VALIDADE_HORAS = 8

MAX_TENTATIVAS = 5
BLOQUEIO_SEGUNDOS = 300
_tentativas: dict[str, list[float]] = {}

esquema = HTTPBearer(auto_error=False)


def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def conferir_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def login_bloqueado(login: str) -> bool:
    agora = time.time()
    recentes = [t for t in _tentativas.get(login, []) if agora - t < BLOQUEIO_SEGUNDOS]
    _tentativas[login] = recentes
    return len(recentes) >= MAX_TENTATIVAS


def registrar_falha(login: str) -> None:
    _tentativas.setdefault(login, []).append(time.time())


def limpar_falhas(login: str) -> None:
    _tentativas.pop(login, None)


def criar_token(usuario: Usuario) -> str:
    expira = datetime.now(timezone.utc) + timedelta(hours=VALIDADE_HORAS)
    dados = {"sub": str(usuario.id), "perfil": usuario.perfil, "exp": expira}
    return jwt.encode(dados, CHAVE_SECRETA, algorithm=ALGORITMO)


def usuario_atual(
    cred: HTTPAuthorizationCredentials | None = Depends(esquema),
    db: Session = Depends(get_db),
) -> Usuario:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Faça login para continuar")
    try:
        dados = jwt.decode(cred.credentials, CHAVE_SECRETA, algorithms=[ALGORITMO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada, faça login novamente")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    usuario = db.get(Usuario, int(dados["sub"]))
    if usuario is None or not usuario.ativo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inativo")
    return usuario


def somente_admin(request: Request, usuario: Usuario = Depends(usuario_atual),
                  db: Session = Depends(get_db)) -> Usuario:
    """Bloqueia o perfil Vendedor nas funções administrativas e registra a tentativa."""
    if usuario.perfil != "Administrador":
        from .auditoria import registrar
        registrar(db, usuario, "ACESSO_NEGADO",
                  f"Tentou acessar {request.method} {request.url.path}", request=request)
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Acesso negado: função exclusiva do Administrador")
    return usuario
