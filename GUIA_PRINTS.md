# Guia passo a passo: etapas, código e PRINTS

**Projeto Integrador II: Sistema de Controle de Estoque e Vendas da MMF (Manoel Modas e Família)**
Aluno: Edson José da Silva · ADS / FASUL

Cada etapa abaixo é igual à seção "4. Etapas de execução" do relatório.
Onde aparecer **📸 PRINT**, tire a captura e salve com o nome indicado.

> **Como tirar print**
> - Windows: `Win + Shift + S`, selecione a área e cole no Paint (`Ctrl + V`) para salvar.
> - Linux (Xubuntu): tecla `Print Screen`.
> - Deixe o navegador em **tela cheia (F11)** para o print ficar limpo.

---

## ETAPA 1: Planejamento e aprovação do tema

Não tem código nesta etapa.
- [ ] Mande ao professor orientador o tema: *"Sistema web de controle de estoque e vendas para a microempresa MMF"*.
- [ ] Guarde a resposta de aprovação (print da mensagem). Ela não entra como foto, mas protege você.

---

## ETAPA 2: Levantamento de requisitos com o Manoel

Não tem código nesta etapa.
- [ ] Converse com o Manoel e anote: como ele controla o estoque hoje, que problemas tem, quais produtos e tamanhos vende.
- [ ] **Confirme os preços reais.** Os preços no sistema (R$ 89,90 a calça e R$ 59,90 a bermuda) são **de exemplo**.

📸 **FOTO 1 (celular, foto real):** você e o Manoel conversando na loja, com o caderno ou a planilha antiga aparecendo.
Salvar como: `foto1_levantamento.jpg`

---

## ETAPA 3: Modelagem do banco de dados

Arquivos: `app/models.py` (tabelas) e `docs/diagrama_banco.dot` (diagrama).

📸 **FOTO 2: já está pronta**, não precisa tirar print: `docs/diagrama_banco.png`
(se mudar algo no diagrama: `dot -Tpng docs/diagrama_banco.dot -o docs/diagrama_banco.png`)

---

## ETAPA 4: Desenvolvimento do back-end

Arquivos: `app/main.py`, `app/database.py`, `app/schemas.py`, `app/routers/produtos.py`, `app/routers/estoque.py`, `app/routers/vendas.py`

### 4.1 Instalar (só na primeira vez)

Precisa do **Python 3.10 ou mais novo** (python.org, marque "Add Python to PATH").
Abra o terminal **dentro da pasta `estoque-mmf`**:

**Windows**
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Linux**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.2 Ligar o sistema
```
python -m uvicorn app.main:app --reload
```
Abra no navegador: **http://127.0.0.1:8000**

| Usuário | Senha | Perfil |
|---|---|---|
| `manoel` | `Mmf@2026` | Administrador |
| `vendedor` | `Venda@2026` | Vendedor |

📸 **PRINT EXTRA (opcional, bom para o relatório):** a página **http://127.0.0.1:8000/docs** mostra todas as rotas da API.
Salvar como: `extra_api_docs.png`

### 4.3 Registrar uma venda
1. Entre como `manoel`.
2. Clique em **Nova Venda**.
3. Escolha *Calça Jeans Azul Marinho tam. 40*, quantidade **5**, clique **Adicionar**.
4. Escolha outra peça, quantidade **1**, clique **Adicionar**.
5. Pagamento: **PIX**.

📸 **FOTO 4a: PRINT AGORA** (carrinho montado, antes de finalizar). Salvar como: `foto4a_venda_carrinho.png`

6. Clique **Finalizar venda**.

📸 **FOTO 4b: PRINT AGORA** (mensagem "Venda registrada… Estoque atualizado"). Salvar como: `foto4b_venda_ok.png`

### 4.4 Alerta de estoque mínimo
1. Clique em **Alertas** (o número vermelho mostra quantos produtos estão baixos).

📸 **FOTO 5: PRINT AGORA** (lista em vermelho + aviso "precisam de reposição"). Salvar como: `foto5_alerta_estoque.png`

---

## ETAPA 5: Segurança e auditoria

Arquivos: `app/security.py`, `app/auditoria.py`, `app/routers/auth.py`, `app/routers/admin.py`

### 5.1 Tela de login
1. Clique **Sair**.

📸 **FOTO 3: PRINT AGORA** (tela de login). Salvar como: `foto3_login.png`

2. Digite `manoel` com a senha **errada** `teste123` e clique Entrar.

📸 **PRINT EXTRA:** mensagem "Usuário ou senha incorretos". Salvar como: `extra_login_erro.png`

3. Entre com a senha certa.

### 5.2 Gerar ações para o log
1. Em **Produtos**, clique **Alterar preço** em qualquer peça e digite um novo valor.
2. Em **Auditoria**, clique **Fazer backup agora**.

📸 **FOTO 6: PRINT AGORA** (tabela do log: falha de login, login, alteração de preço com valor ANTES e DEPOIS, venda, backup).
Salvar como: `foto6_log_auditoria.png`

### 5.3 Bloqueio do perfil Vendedor (meta 4)
1. Clique **Sair** e entre como `vendedor` / `Venda@2026`.
2. Clique em **Auditoria**.

📸 **PRINT EXTRA (recomendado):** mensagem vermelha "Acesso negado: função exclusiva do Administrador".
Salvar como: `extra_vendedor_bloqueado.png`

3. Saia, entre de novo como `manoel` e abra **Auditoria**: vai aparecer a linha **ACESSO_NEGADO** do vendedor. Pode tirar um segundo print do log.

---

## ETAPA 6: Testes, usabilidade e implantação

Arquivos: `tests/test_sistema.py` (22 testes) e `docs/questionario_SUS.md`

### 6.1 Testes automatizados
Pare o sistema (`Ctrl + C` no terminal) e rode:
```
python -m pytest -v
```

📸 **FOTO 7: PRINT AGORA** do terminal com **22 passed** em verde. Salvar como: `foto7_testes_aprovados.png`
Anote no relatório (meta 6): **22 de 22 testes aprovados**.

### 6.2 Teste de usabilidade com usuário real
1. Leve o notebook à loja, ligue o sistema e peça ao Manoel (e a quem mais vende) para:
   cadastrar um produto, registrar uma venda e consultar os alertas. **Não ajude**, só observe e anote onde a pessoa travou.
2. Ao final, aplique o questionário de `docs/questionario_SUS.md` e calcule a nota.

📸 **FOTO 8 (celular, foto real):** o Manoel usando o sistema no notebook. Salvar como: `foto8_teste_usuario.jpg`

---

## Resumo dos prints para o relatório

| Foto | Tipo | Arquivo | Etapa |
|---|---|---|---|
| 1 | Foto real (celular) | `foto1_levantamento.jpg` | 2 |
| 2 | **Pronta** | `docs/diagrama_banco.png` | 3 |
| 3 | Print | `foto3_login.png` | 5 |
| 4 | Print | `foto4a_venda_carrinho.png` / `foto4b_venda_ok.png` | 4 |
| 5 | Print | `foto5_alerta_estoque.png` | 4 |
| 6 | Print | `foto6_log_auditoria.png` | 5 |
| 7 | Print | `foto7_testes_aprovados.png` | 6 |
| 8 | Foto real (celular) | `foto8_teste_usuario.jpg` | 6 |
| Extras | Print | `extra_*.png` | 4 e 5 |

Ao terminar, volte ao relatório e troque cada **[inserir …]** pela imagem correspondente.
