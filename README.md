# MMF: Controle de Estoque e Vendas

Projeto Integrador II · Tecnologia em Análise e Desenvolvimento de Sistemas · FASUL Educacional
Aluno: **Edson José da Silva** · Cliente: **MMF – Manoel Modas e Família**

Sistema web para controlar o estoque e as vendas de uma loja de jeans, com autenticação, perfis de acesso e trilha de auditoria.

**Comece pelo arquivo [`GUIA_PRINTS.md`](GUIA_PRINTS.md)**: ele explica cada etapa e marca cada print do relatório.

## Funcionalidades
- Cadastro de produtos por modelo, cor e tamanho
- Entrada de mercadoria e ajuste de estoque com motivo
- Registro de vendas com baixa automática do estoque
- Alerta de estoque mínimo
- Relatório de vendas por período e produtos mais vendidos
- Login com senha em hash bcrypt, token JWT e bloqueio após 5 tentativas erradas
- Perfis Administrador e Vendedor
- Log de auditoria (usuário, ação, antes/depois, IP, data e hora)
- Backup do banco de dados
- 22 testes automatizados

## Tecnologias
Python · FastAPI · SQLAlchemy · SQLite · bcrypt · PyJWT · pytest · HTML/CSS/JavaScript

## Estrutura (por etapa do relatório)
```
estoque-mmf/
├── app/
│   ├── models.py            ETAPA 3 - tabelas do banco
│   ├── database.py          ETAPA 3/4 - conexão (ORM, anti SQL Injection)
│   ├── main.py              ETAPA 4 - aplicação e dados iniciais da MMF
│   ├── schemas.py           ETAPA 5 - validação dos dados recebidos
│   ├── security.py          ETAPA 5 - hash, token, perfis, bloqueio
│   ├── auditoria.py         ETAPA 5 - registro no log
│   ├── routers/
│   │   ├── produtos.py      ETAPA 4 - produtos e alertas
│   │   ├── estoque.py       ETAPA 4 - entradas e ajustes
│   │   ├── vendas.py        ETAPA 4 - vendas e relatório
│   │   ├── auth.py          ETAPA 5 - login
│   │   └── admin.py         ETAPA 5 - auditoria e backup
│   └── static/              Telas (login, produtos, venda, alertas, auditoria)
├── tests/test_sistema.py    ETAPA 6 - testes automatizados
├── docs/
│   ├── diagrama_banco.png   ETAPA 3 - FOTO 2 do relatório
│   ├── diagrama_banco.dot   Fonte do diagrama (Graphviz)
│   └── questionario_SUS.md  ETAPA 6 - teste de usabilidade
└── GUIA_PRINTS.md           Passo a passo com os prints
```

## Rodar rapidamente
```
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
Abra http://127.0.0.1:8000 · Documentação da API: http://127.0.0.1:8000/docs

## Segurança: leia antes de usar de verdade
As senhas `Mmf@2026` (manoel) e `Venda@2026` (vendedor) são **apenas de demonstração** para o Projeto Integrador.
Antes de usar o sistema na loja, troque essas senhas e defina a variável de ambiente `MMF_SECRET_KEY`.

> Os preços cadastrados são de exemplo. Para apagar os dados e recomeçar, pare o sistema e apague o arquivo `estoque_mmf.db`.
