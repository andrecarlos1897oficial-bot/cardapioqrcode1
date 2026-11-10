# Governança e Gestão Operacional: Cardápio Digital por QR Code

## 1. Visão Geral e Escopo do Projeto

### 1.1 Objetivo
Disponibilizar uma aplicação web leve, segura e intuitiva para restaurantes, permitindo que os clientes acessem o cardápio em suas mesas via QR Code, façam a escolha dos itens e finalizem o pedido informando a forma de pagamento, tudo sem necessidade de download de aplicativo ou execução de scripts no navegador.

### 1.2 Fluxo Operacional
1. **Entrada via QR Code na Mesa:** O cliente aponta a câmera para o QR Code da mesa, acessando a URL parametrizada `/?mesa=XX`.
2. **Identificação do Cliente:** Entrada do nome do cliente e validação do número da mesa (armazenados em sessão segura assinada no servidor).
3. **Cardápio por Categorias:** Exibição estruturada do menu por seções (Ex.: Entradas, Principais, Bebidas, Sobremesas), com seleção de quantidades via formulário nativo.
4. **Checkout e Forma de Pagamento:** Revisão do pedido e escolha da forma de pagamento (Débito, Crédito, Pix ou Dinheiro com acerto final).

### 1.3 Diretrizes e Restrições Técnicas
- **Backend:** Python com Flask, estruturado de forma modular e didática (nível júnior, com comentários explicativos e padrões limpos).
- **Frontend:** HTML5 semântico e CSS3 puro, responsivo (mobile-first), com total ausência de JavaScript/TypeScript (`script-src 'none'`).
- **Segurança Máxima:**
  - Content Security Policy (CSP) rigorosa, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Referrer-Policy estrita.
  - Sessões assinadas com cookies `HttpOnly` e `SameSite=Lax`.
  - Proteção contra manipulação de preços: o cálculo financeiro é 100% executado no backend a partir do catálogo oficial (o cliente envia apenas IDs e quantidades).
  - Sanitização e validação estrita de inputs (mesa positiva, limites de caracteres e escape automático de tags/XSS via Jinja2).

---

## 2. Marcos e Fases de Entrega

| Fase | Nome | Escopo & Entregáveis | Status Operacional |
| :--- | :--- | :--- | :--- |
| **Fase 1** | **Especificação e Design** | - Definição da arquitetura de fluxo (Mesa -> Nome -> Menu -> Checkout).<br>- Elaboração do documento visual e diretrizes em `DESIGN_SPEC.md`.<br>- Especificação de contratos de rotas e dados. | **Concluída** |
| **Fase 2** | **Implementação Backend e Frontend** | - Estruturação da aplicação modular em `app.py`.<br>- Desenvolvimento dos templates Jinja2 (`identificacao.html`, `cardapio.html`, `checkout.html`, `confirmacao.html`).<br>- Estilização responsiva em CSS puro (`style.css`), sem dependência de JS. | **Concluída** |
| **Fase 3** | **Validação QA e Cibersegurança** | - Bateria de testes unitários e de integração em `test_cardapio.py`.<br>- Validação de sanitização contra XSS e injeção de parâmetros.<br>- Verificação de headers de segurança e integridade de sessão. | **Concluída (12/12 testes OK)** |

---

## 3. Matriz de Riscos Operacionais

| ID | Risco Identificado | Probabilidade | Impacto | Estratégia de Mitigação | Plano de Contingência |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **R01** | **Injeção de código / XSS no campo de identificação** | Baixa | Alto | Sanitização rigorosa no backend e escape contextual obrigatório no Jinja2. CSP configurada com `script-src 'none'`. | Rejeição automática de strings fora do padrão alfanumérico estendido e log de alerta de segurança. |
| **R02** | **Fraude / Adulteração de valores de itens no envio** | Média | Crítico | O front-end envia apenas IDs de produto e quantidades inteiras. Todos os cálculos de subtotal e total são recalculados no servidor. | Qualquer ID inválido ou quantidade negativa anula a transação e redireciona com mensagem de erro. |
| **R03** | **Perda ou inconsistência de sessão da mesa** | Média | Médio | Validação da existência de mesa e nome em cada rota autenticada. Persistência em cookie assinado e seguro. | Redirecionamento automático para a tela inicial preservando o parâmetro `?mesa=XX` se disponível. |
| **R04** | **Incompatibilidade ou falha de renderização sem JavaScript** | Baixa | Alto | Uso exclusivo de elementos nativos HTML5 (`<form method="POST">`, `<input type="number">`, `<details>/<summary>`) e CSS3 puro. | Teste de regressão com navegadores com JavaScript desativado para garantir 100% de usabilidade. |
| **R05** | **Conflito de capacidade / concorrência de agentes** | Baixa | Baixo | Registro transparente de governança em `OPERATIONS.md` e divisão clara de papéis entre Big Boss, Dev Lead, QA e Operações. | Alinhamento de cadência assíncrona com prestação de contas direta ao Big Boss. |

---

## 4. Critérios de Aceitação

### 4.1 Critérios Funcionais
- [x] O sistema captura automaticamente o parâmetro `?mesa=XX` e pré-preenche o campo da mesa.
- [x] O usuário não consegue prosseguir sem informar um nome válido (mínimo 2 caracteres) e um número de mesa positivo.
- [x] O cardápio exibe itens organizados por categorias com descrições e preços formatados em moeda brasileira (BRL).
- [x] A tela de checkout detalha o resumo dos itens selecionados, quantidades, subtotais e valor total exato.
- [x] As opções de pagamento (Débito, Crédito, Pix e Dinheiro com acerto final) estão disponíveis e são registradas no fechamento do pedido.

### 4.2 Critérios de Segurança e Não-Funcionais
- [x] **Zero JavaScript:** A aplicação deve funcionar com precisão mesmo em ambientes com scripts bloqueados.
- [x] **Headers HTTP:** Presença obrigatória de `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` e `Referrer-Policy`.
- [x] **Testes Automatizados:** 100% dos testes unitários cobrindo fluxos felizes e exceções de segurança em `test_cardapio.py`.
- [x] **Código Nível Júnior:** Código conciso, didático, modular, sem acoplamentos desnecessários ou bibliotecas externas complexas.

---

## 5. Governança e Próximos Passos
- **Responsável Operacional:** Líder de Administração (Operations Lead).
- **Supervisão:** Big Boss e Dono do Negócio.
- **Próximos Passos:** 
  1. Manter a cadência de auditoria de testes e integridade do repositório compartilhado.
  2. Monitorar solicitações de expansão de escopo ou novos métodos de pagamento, submetendo qualquer alteração de prioridade ou orçamento para aprovação prévia.
