// MMF - Controle de Estoque e Vendas (interface)
// Os dados da tela são sempre inseridos como texto (textContent) para evitar XSS.

const estado = { token: sessionStorage.getItem("token"), perfil: sessionStorage.getItem("perfil"),
                 nome: sessionStorage.getItem("nome"), produtos: [], carrinho: [] };
const $ = (id) => document.getElementById(id);
const real = (v) => Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

async function api(caminho, opcoes = {}) {
  const resp = await fetch(caminho, {
    ...opcoes,
    headers: { "Content-Type": "application/json",
               ...(estado.token ? { Authorization: "Bearer " + estado.token } : {}) },
  });
  if (resp.status === 204) return null;
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    let texto = dados.detail;
    if (Array.isArray(texto)) texto = "Dados inválidos: confira os campos preenchidos";
    const erro = new Error(texto || "Erro " + resp.status);
    erro.status = resp.status;
    throw erro;
  }
  return dados;
}

function mensagem(texto, tipo = "ok") {
  const m = $("msg");
  m.textContent = texto;
  m.className = "msg " + tipo;
  m.hidden = false;
  clearTimeout(mensagem.t);
  if (tipo !== "erro") mensagem.t = setTimeout(() => (m.hidden = true), 8000);
}

function celula(tr, texto, classe) {
  const td = document.createElement("td");
  td.textContent = texto;
  if (classe) td.className = classe;
  tr.appendChild(td);
  return td;
}

// ---------- LOGIN ----------
$("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("erro-login").hidden = true;
  try {
    const r = await api("/api/auth/login", { method: "POST",
      body: JSON.stringify({ login: $("login").value.trim(), senha: $("senha").value }) });
    Object.assign(estado, { token: r.token, perfil: r.perfil, nome: r.nome });
    sessionStorage.setItem("token", r.token);
    sessionStorage.setItem("perfil", r.perfil);
    sessionStorage.setItem("nome", r.nome);
    abrirSistema();
  } catch (erro) {
    $("erro-login").textContent = erro.message;
    $("erro-login").hidden = false;
  }
});

$("sair").addEventListener("click", () => {
  sessionStorage.clear();
  location.reload();
});

function abrirSistema() {
  $("tela-login").hidden = true;
  $("tela-sistema").hidden = false;
  $("usuario-nome").textContent = estado.nome;
  $("usuario-perfil").textContent = estado.perfil;
  const admin = estado.perfil === "Administrador";
  document.querySelectorAll(".so-admin").forEach((el) => (el.hidden = !admin));
  mostrar("produtos");
}

// ---------- NAVEGAÇÃO ----------
document.querySelectorAll("#menu button").forEach((b) =>
  b.addEventListener("click", () => mostrar(b.dataset.tela)));

async function mostrar(tela) {
  document.querySelectorAll(".tela").forEach((t) => (t.hidden = true));
  document.querySelectorAll("#menu button").forEach((b) =>
    b.classList.toggle("ativo", b.dataset.tela === tela));
  $("tela-" + tela).hidden = false;
  $("msg").hidden = true;
  try {
    await carregarProdutos();
    if (tela === "alertas") await carregarAlertas();
    if (tela === "auditoria") await carregarAuditoria();
    if (tela === "relatorio") prepararRelatorio();
  } catch (erro) {
    if (erro.status === 401) { sessionStorage.clear(); location.reload(); return; }
    $("tela-" + tela).hidden = erro.status === 403;
    mensagem("⛔ " + erro.message, "erro");
  }
}

// ---------- PRODUTOS ----------
async function carregarProdutos() {
  estado.produtos = await api("/api/produtos");
  const admin = estado.perfil === "Administrador";
  const corpo = $("lista-produtos");
  corpo.replaceChildren();
  for (const p of estado.produtos) {
    const tr = document.createElement("tr");
    if (p.abaixo_minimo) tr.className = "baixo";
    [p.id, p.nome, p.cor, p.tamanho, real(p.preco), p.quantidade, p.estoque_minimo]
      .forEach((v) => celula(tr, v));
    const sit = celula(tr, "");
    const tag = document.createElement("span");
    tag.className = "tag " + (p.abaixo_minimo ? "baixo" : "ok");
    tag.textContent = p.abaixo_minimo ? "Estoque baixo" : "OK";
    sit.appendChild(tag);
    if (admin) {
      const acoes = celula(tr, "");
      const editar = document.createElement("button");
      editar.className = "botao mini";
      editar.textContent = "Alterar preço";
      editar.onclick = () => alterarPreco(p);
      const excluir = document.createElement("button");
      excluir.className = "botao mini perigo";
      excluir.textContent = "Excluir";
      excluir.style.marginLeft = "6px";
      excluir.onclick = () => excluirProduto(p);
      acoes.append(editar, excluir);
    }
    corpo.appendChild(tr);
  }
  const baixos = estado.produtos.filter((p) => p.abaixo_minimo).length;
  $("qtd-alertas").textContent = baixos;
  $("qtd-alertas").hidden = baixos === 0;
  preencherSelects();
}

function preencherSelects() {
  for (const id of ["v-produto", "e-produto"]) {
    const sel = $(id);
    const atual = sel.value;
    sel.replaceChildren();
    for (const p of estado.produtos) {
      const op = document.createElement("option");
      op.value = p.id;
      op.textContent = `${p.nome} ${p.cor} tam. ${p.tamanho} — ${real(p.preco)} (estoque: ${p.quantidade})`;
      sel.appendChild(op);
    }
    if (atual) sel.value = atual;
  }
}

$("form-produto").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/produtos", { method: "POST", body: JSON.stringify({
      nome: $("p-nome").value, cor: $("p-cor").value, tamanho: $("p-tam").value,
      preco: Number($("p-preco").value), quantidade: Number($("p-qtd").value),
      estoque_minimo: Number($("p-min").value) }) });
    e.target.reset();
    await carregarProdutos();
    mensagem("Produto cadastrado com sucesso.");
  } catch (erro) { mensagem(erro.message, "erro"); }
});

async function alterarPreco(p) {
  const novo = prompt(`Novo preço para ${p.nome} ${p.cor} tam. ${p.tamanho}:`, p.preco);
  if (novo === null) return;
  try {
    await api("/api/produtos/" + p.id, { method: "PATCH",
      body: JSON.stringify({ preco: Number(String(novo).replace(",", ".")) }) });
    await carregarProdutos();
    mensagem("Preço alterado e registrado no log de auditoria.");
  } catch (erro) { mensagem(erro.message, "erro"); }
}

async function excluirProduto(p) {
  if (!confirm(`Excluir ${p.nome} ${p.cor} tam. ${p.tamanho}?`)) return;
  try {
    await api("/api/produtos/" + p.id, { method: "DELETE" });
    await carregarProdutos();
    mensagem("Produto excluído e registrado no log de auditoria.");
  } catch (erro) { mensagem(erro.message, "erro"); }
}

// ---------- VENDA ----------
$("v-adicionar").addEventListener("click", () => {
  const p = estado.produtos.find((x) => x.id === Number($("v-produto").value));
  const qtd = Number($("v-qtd").value);
  if (!p || qtd < 1) return;
  const item = estado.carrinho.find((i) => i.produto.id === p.id);
  if (item) item.quantidade += qtd; else estado.carrinho.push({ produto: p, quantidade: qtd });
  desenharCarrinho();
});

function desenharCarrinho() {
  const corpo = $("carrinho");
  corpo.replaceChildren();
  let total = 0;
  estado.carrinho.forEach((i, n) => {
    const tr = document.createElement("tr");
    const sub = i.produto.preco * i.quantidade;
    total += sub;
    [`${i.produto.nome} ${i.produto.cor} tam. ${i.produto.tamanho}`, i.quantidade,
     real(i.produto.preco), real(sub)].forEach((v) => celula(tr, v));
    const td = celula(tr, "");
    const rem = document.createElement("button");
    rem.className = "botao mini perigo";
    rem.textContent = "Remover";
    rem.onclick = () => { estado.carrinho.splice(n, 1); desenharCarrinho(); };
    td.appendChild(rem);
    corpo.appendChild(tr);
  });
  $("v-total").textContent = real(total);
}

$("v-finalizar").addEventListener("click", async () => {
  if (!estado.carrinho.length) return mensagem("Adicione pelo menos um produto.", "aviso");
  try {
    const r = await api("/api/vendas", { method: "POST", body: JSON.stringify({
      forma_pagamento: $("v-pagamento").value,
      itens: estado.carrinho.map((i) => ({ produto_id: i.produto.id, quantidade: i.quantidade })) }) });
    estado.carrinho = [];
    desenharCarrinho();
    await carregarProdutos();
    let texto = `✅ Venda #${r.venda_id} registrada: ${real(r.total)}. Estoque atualizado.`;
    if (r.alertas_estoque.length) {
      texto += "  ⚠ Estoque baixo: " + r.alertas_estoque.join("; ");
      mensagem(texto, "aviso");
    } else mensagem(texto);
  } catch (erro) { mensagem(erro.message, "erro"); }
});

// ---------- ALERTAS ----------
async function carregarAlertas() {
  const lista = await api("/api/produtos/alertas");
  const corpo = $("lista-alertas");
  corpo.replaceChildren();
  for (const p of lista) {
    const tr = document.createElement("tr");
    tr.className = "baixo";
    [p.nome, p.cor, p.tamanho, p.quantidade, p.estoque_minimo].forEach((v) => celula(tr, v));
    corpo.appendChild(tr);
  }
  if (!lista.length) mensagem("Nenhum produto abaixo do estoque mínimo.");
  else mensagem(`⚠ ${lista.length} produto(s) precisam de reposição.`, "aviso");
}

// ---------- ENTRADA DE ESTOQUE ----------
$("form-entrada").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const r = await api("/api/estoque/movimentar", { method: "POST", body: JSON.stringify({
      produto_id: Number($("e-produto").value), tipo: $("e-tipo").value,
      quantidade: Number($("e-qtd").value), motivo: $("e-motivo").value }) });
    e.target.reset();
    await carregarProdutos();
    mensagem(`Estoque atualizado. Quantidade atual: ${r.quantidade_atual}.`);
  } catch (erro) { mensagem("⛔ " + erro.message, "erro"); }
});

// ---------- RELATÓRIO ----------
function prepararRelatorio() {
  const hoje = new Date().toISOString().slice(0, 10);
  if (!$("r-inicio").value) $("r-inicio").value = hoje.slice(0, 8) + "01";
  if (!$("r-fim").value) $("r-fim").value = hoje;
}

$("form-relatorio").addEventListener("submit", async (e) => {
  e.preventDefault();
  const area = $("resultado-relatorio");
  area.replaceChildren();
  try {
    const r = await api(`/api/vendas/relatorio?inicio=${$("r-inicio").value}&fim=${$("r-fim").value}`);
    const resumo = document.createElement("div");
    resumo.className = "resumo";
    for (const [rotulo, valor] of [["Período", r.periodo], ["Vendas", r.quantidade_vendas],
                                   ["Faturamento", real(r.faturamento)]]) {
      const c = document.createElement("div");
      c.className = "cartao";
      c.textContent = rotulo;
      const s = document.createElement("strong");
      s.textContent = valor;
      c.appendChild(s);
      resumo.appendChild(c);
    }
    const tabela = document.createElement("table");
    tabela.innerHTML = "<thead><tr><th>Mais vendidos</th><th>Quantidade</th></tr></thead>";
    const corpo = document.createElement("tbody");
    r.mais_vendidos.forEach((m) => {
      const tr = document.createElement("tr");
      celula(tr, m.produto); celula(tr, m.quantidade);
      corpo.appendChild(tr);
    });
    tabela.appendChild(corpo);
    area.append(resumo, tabela);
  } catch (erro) { mensagem("⛔ " + erro.message, "erro"); }
});

// ---------- AUDITORIA ----------
async function carregarAuditoria() {
  const logs = await api("/api/admin/auditoria");
  const corpo = $("lista-auditoria");
  corpo.replaceChildren();
  for (const l of logs) {
    const tr = document.createElement("tr");
    if (l.acao.includes("FALHA") || l.acao.includes("NEGADO") || l.acao.includes("BLOQUEADO"))
      tr.className = "baixo";
    [l.id, new Date(l.data_hora).toLocaleString("pt-BR"), l.usuario_login, l.acao, l.detalhe,
     l.valor_anterior, l.valor_novo, l.ip].forEach((v) => celula(tr, v));
    corpo.appendChild(tr);
  }
}

$("fazer-backup").addEventListener("click", async () => {
  try {
    const r = await api("/api/admin/backup", { method: "POST" });
    await carregarAuditoria();
    mensagem("Backup salvo em " + r.arquivo);
  } catch (erro) { mensagem("⛔ " + erro.message, "erro"); }
});

if (estado.token) abrirSistema();
