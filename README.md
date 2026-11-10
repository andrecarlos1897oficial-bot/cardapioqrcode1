# Cardápio Digital por QR Code

Aplicação web limpa, didática e segura desenvolvida para atendimento em mesas via QR Code, seguindo o padrão júnior de código simples, modular e sem dependências desnecessárias.

## 🛠️ Stack Tecnológica
- **Back-end:** Python 3 + Flask (`app.py`).
- **Front-end:** HTML5 semântico e CSS3 puro mobile-first (`templates/` e `static/style.css`).
- **Zero JavaScript / TypeScript:** Navegação baseada exclusivamente em requisições HTTP normais (GET e POST) e sessão assinada criptograficamente.

## 🔒 Diretrizes de Cibersegurança Implementadas
1. **Validação e Cálculo de Preços 100% no Servidor:**
   - O formulário submete apenas o identificador do item e a quantidade.
   - Os preços são obtidos diretamente do catálogo canônico no backend, impossibilitando qualquer adulteração ou injeção de valores pelo cliente.
2. **Sanitização e Validação Rigorosa de Entrada:**
   - Mesa validada como inteiro positivo (1 a 999).
   - Nome do cliente validado (mínimo de 2 e máximo de 60 caracteres) e autoescapado pelo Jinja2 para prevenir XSS.
   - Forma de pagamento restrita a uma lista fechada (`pix`, `dinheiro`, `credito`, `debito`).
3. **Sessão Segura:**
   - Chave secreta obtida da variável de ambiente `FLASK_SECRET_KEY` com fallback para `os.urandom(32)`.
   - Cookies com flag `HttpOnly` e `SameSite=Lax`.
4. **Headers HTTP de Segurança (CSP Estrito):**
   - `Content-Security-Policy: default-src 'self'; script-src 'none'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: camera=(), microphone=(), geolocation=()`

## 🧭 Fluxo da Aplicação
1. `/?mesa=<numero>`: Rota inicial via link do QR Code com identificação da mesa e formulário para nome do cliente.
2. `/cardapio`: Catálogo de pratos e bebidas organizados por categoria (Entradas, Pratos Principais, Bebidas, Sobremesas) com seleção de quantidades.
3. `/resumo` (compatível também em `/pedido`): Resumo dos itens selecionados com subtotais, valor total calculado pelo servidor e seleção do método de pagamento. Quantidades são validadas no servidor entre 0 e 20 por item.
4. `/pedido/sucesso` (compatível também em `/confirmacao`): Confirmação do pedido:
   - **Dinheiro:** Exibe destaque obrigatório *"Pagamento pendente no balcão/final do atendimento"*.
   - **Pix:** A integração ainda não está configurada; a tela orienta o cliente a solicitar a chave oficial à equipe. Não use credenciais de demonstração para pagamentos.
   - **Crédito / Débito:** Informa que a máquina de cartão será levada à mesa.

## 🚀 Como Executar Localmente
No terminal, dentro da pasta do projeto:
```bash
python app.py
```
Acesse no navegador:
```text
http://127.0.0.1:5000/?mesa=12
```

## 🧪 Como Executar os Testes Automatizados
```bash
python -m unittest test_cardapio.py
```
*(Todos os 12 testes cobrem rotas, cálculos de preço, segurança, fluxo de pagamento e sanitização de dados)*.
