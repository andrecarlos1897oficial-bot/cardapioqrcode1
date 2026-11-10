import os
import re
from pathlib import Path
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=BASE_DIR / "templates",
    static_folder=BASE_DIR / "static",
)

# Chave secreta segura obtida via variável de ambiente ou fallback aleatório seguro
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["TEMPLATES_AUTO_RELOAD"] = os.environ.get("FLASK_ENV") == "development"

# Catálogo canônico gerenciado exclusivamente no servidor para prevenir manipulação de preços
CARDAPIO = [
    {
        "categoria": "Entradas",
        "itens": [
            {
                "id": "ent_1",
                "nome": "Coxinha de Costela Defumada",
                "descricao": "Massa crocante recheada com costela premium defumada lentamente e requeijão artesanal (4 unid).",
                "preco": 29.90,
                "imagem": "cardapio-png/Coxinha-de-Costela-Defumada.png",
            },
            {
                "id": "ent_2",
                "nome": "Batata Crinkle Trufada",
                "descricao": "Nossas batatas crinkle crocantes, finalizadas com azeite de trufas brancas e generosa chuva de queijo grana padano ralado na hora. Acompanha molho ranch.",
                "preco": 32.50,
                "imagem": "cardapio-png/Batata-Crinkle-Trufada.png",
            },
            {
                "id": "ent_3",
                "nome": "Mini Croquetes de Angus com Gorgonzola",
                "descricao": "Croquetes suculentos feitos com carne Angus selecionada, recheados com creme de queijo gorgonzola (6 unidades). Acompanha geleia de pimenta levemente picante.",
                "preco": 34.00,
                "imagem": "cardapio-png/Mini-Croquetes-de-Angus-com-Gorgonzola.png",
            },
            {
                "id": "ent_4",
                "nome": "Onion Rings Gourmet na Cerveja",
                "descricao": "Anéis de cebola graúdos empanados em massa artesanal leve com toque de cerveja escura, super crocantes. Acompanha maionese verde artesanal.",
                "preco": 27.90,
                "imagem": "cardapio-png/Onion-Rings-Gourmet-na-Cerveja.png",
            },
        ],
    },
    {
        "categoria": "Pratos Principais",
        "itens": [
            {
                "id": "prato_1",
                "nome": "The Black Angus Burger",
                "descricao": "Blend 180g de carne Angus, queijo cheddar inglês maturadíssimo, bacon crispy artesanal e maionese de alho negro no pão brioche tostado na manteiga.",
                "preco": 42.90,
                "imagem": "cardapio-png/The-Black-Angus-Burger.png",
            },
            {
                "id": "prato_2",
                "nome": "Hambúrguer de Queijo (Cheeseburger)",
                "descricao": "Hambúrguer de carne bovina grelhado na chama com queijo cheddar americano derretido, alface, tomate, cebola roxa e picles no pão brioche torrado.",
                "preco": 38.50,
                "imagem": "cardapio-png/Hamburguer-de-Queijo.png",
            },
            {
                "id": "prato_3",
                "nome": "Queijo Gorgonzola e Cebola Caramelizada",
                "descricao": "Hambúrguer de carne bovina grelhado com queijo gorgonzola derretido, cebola caramelizada, rúcula fresca e maionese de páprica defumada no pão brioche.",
                "preco": 45.00,
                "imagem": "cardapio-png/Queijo-Gorgonzola-e-Cebola-Caramelizada.png",
            },
            {
                "id": "prato_4",
                "nome": " Batatas Fritas com Queijo Cheddar e Bacon",
                "descricao": "Batatas fritas crocantes com queijo cheddar derretido e pedaços de bacon crocante.",
                "preco": 15.00,
                "imagem": "cardapio-png/Batatas-Fritas-com-Queijo-Cheddar-e-Bacon.png",
            },
        ],
    },
    {
        "categoria": "Bebidas",
        "itens": [
            {
                "id": "beb_1",
                "nome": "Soda Italiana de Frutas Vermelhas",
                "descricao": "Xarope artesanal de amoras, framboesas e mirtilos, misturado com água com gás geladíssima, limão espremido e hortelã fresca.",
                "preco": 14.90,
                "imagem": "cardapio-png/Soda-Italiana-de-Frutas-Vermelhas.png",
            },
            {
                "id": "beb_2",
                "nome": "Long Neck Cerveja Stout  Malzbier (330ml)",
                "descricao": "Cerveja escura com notas tostadas de café e chocolate amargo. (330ml)",
                "preco": 16.50,
                "imagem": "cardapio-png/Long-Neck-Cerveja-Stout-Malzbier.png",
            },
            {
                "id": "beb_3",
                "nome": "Coca-Cola (Lata 350ml)",
                "descricao": "Gelada no ponto ideal.",
                "preco": 7.50,
                "imagem": "cardapio-png/Coca-Cola-Lata-350ml.png",
            },
            {
                "id": "beb_4",
                "nome": "Água Mineral (500ml)",
                "descricao": "Opções tradicional e zero açúcar geladas.",
                "preco": 8.00,
                "imagem": "cardapio-png/Agua-Mineral-500-ML.png",
            },
        ],
    },
    {
        "categoria": "Sobremesas",
        "itens": [
            {
                "id": "sob_1",
                "nome": "Brownie de Chocolate Belga com Sorvete de Baunilha da Cátedra",
                "descricao": "Brownie denso e úmido feito com chocolate belga meio amargo e nozes pecãs, servido quente com uma bola de sorvete artesanal de baunilha de fava real e calda de caramelo salgado.",
                "preco": 24.90,
                "imagem": "cardapio-png/Brownie-de-Chocolate-Belga-com-Sorvete-de-Baunilha-da-Cátedra.png",
            },
            {
                "id": "sob_2",
                "nome": "Cheesecake de Frutas Vermelhas com Calda Rústica",
                "descricao": "Fatia generosa de cheesecake estilo Nova York com base crocante de biscoito amanteigado, creme leve de cream cheese e cobertura farta de calda artesanal de amoras e framboesas frescas.",
                "preco": 26.00,
                "imagem": "cardapio-png/Cheesecake-de-Frutas-Vermelhas-com-Calda-Rústica.png",
            },
            {
                "id": "sob_3",
                "nome": "Mini Churros Recheados com Doce de Leite Artesanal",
                "descricao": "Seis mini churros crocantes e sequinhos, polvilhados com açúcar e canela, acompanhados de uma porção generosa de doce de leite artesanal da casa para mergulhar.",
                "preco": 28.50,
                "imagem": "cardapio-png/Mini-Churros.png",
            },
              ],
    },
]

# Mapa auxiliar indexado por ID para busca rápida e validação de preços
ITENS_MAP = {}
for cat in CARDAPIO:
    for it in cat["itens"]:
        ITENS_MAP[it["id"]] = it

LIMITE_QUANTIDADE_ITEM = 20


@app.after_request
def add_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "script-src 'none'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


def sanitizar_nome(nome_bruto):
    """Sanitiza e valida o nome do cliente."""
    if not nome_bruto:
        return ""
    # Remove espaços extras e caracteres de controle
    nome_limpo = " ".join(nome_bruto.strip().split())
    # Limita tamanho para evitar abusos
    return nome_limpo[:60]


def validar_numero_mesa(mesa_bruta):
    """Valida se o número da mesa é um inteiro positivo válido."""
    try:
        mesa_num = int(str(mesa_bruta).strip())
        if 1 <= mesa_num <= 999:
            return mesa_num
    except (ValueError, TypeError):
        pass
    return None


def validar_quantidades_pedido(formulario):
    """Valida quantidades enviadas e rejeita IDs, valores ou duplicatas inválidas."""
    quantidades = {}

    for campo in formulario.keys():
        if not campo.startswith("qtd_"):
            continue

        item_id = campo[len("qtd_"):]
        valores = formulario.getlist(campo)
        if item_id not in ITENS_MAP or len(valores) != 1:
            return None

        try:
            quantidade = int(valores[0].strip())
        except (ValueError, TypeError):
            return None

        if quantidade < 0 or quantidade > LIMITE_QUANTIDADE_ITEM:
            return None

        quantidades[item_id] = quantidade

    return quantidades


def limpar_dados_pedido():
    """Remove do cookie os dados de um pedido anterior."""
    for chave in (
        "pedido_itens",
        "pedido_total",
        "pagamento_escolhido",
        "pagamento_nome",
        "pedido_confirmado",
    ):
        session.pop(chave, None)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        mesa_post = request.form.get("mesa", "")
        nome_post = request.form.get("nome", "")

        mesa_valida = validar_numero_mesa(mesa_post)
        nome_sanitizado = sanitizar_nome(nome_post)

        if not mesa_valida:
            flash("Por favor, informe um número de mesa válido (entre 1 e 999).", "error")
            return render_template("identificacao.html", mesa=mesa_post, nome=nome_post)

        if len(nome_sanitizado) < 2:
            flash("Por favor, informe seu nome (mínimo de 2 caracteres).", "error")
            return render_template("identificacao.html", mesa=mesa_valida, nome=nome_post)

        # Registra mesa e cliente na sessão
        session["mesa"] = mesa_valida
        session["cliente"] = nome_sanitizado
        return redirect(url_for("cardapio"))

    # Método GET: verifica se veio parâmetro ?mesa=<numero>
    mesa_param = request.args.get("mesa")
    mesa_sugerida = ""
    if mesa_param is not None:
        mesa_val = validar_numero_mesa(mesa_param)
        if mesa_val:
            mesa_sugerida = mesa_val
            session["mesa"] = mesa_val
        else:
            flash("O número de mesa no link QR Code é inválido. Por favor, confirme abaixo.", "warning")
    elif "mesa" in session:
        mesa_sugerida = session["mesa"]

    nome_sugerido = session.get("cliente", "")
    return render_template("identificacao.html", mesa=mesa_sugerida, nome=nome_sugerido)


@app.route("/cardapio", methods=["GET"])
def cardapio():
    mesa = session.get("mesa")
    cliente = session.get("cliente")

    if not mesa or not cliente:
        flash("Por favor, identifique sua mesa e seu nome antes de acessar o cardápio.", "info")
        return redirect(url_for("index"))

    return render_template(
        "cardapio.html",
        mesa=mesa,
        cliente=cliente,
        categorias=CARDAPIO,
    )


@app.route("/pedido", methods=["GET", "POST"])
@app.route("/resumo", methods=["GET", "POST"])
def pedido():
    mesa = session.get("mesa")
    cliente = session.get("cliente")

    if not mesa or not cliente:
        flash("Por favor, identifique sua mesa e seu nome para continuar.", "info")
        return redirect(url_for("index"))

    if request.method == "POST":
        # Processamento e cálculo de preços 100% no servidor
        limpar_dados_pedido()
        quantidades = validar_quantidades_pedido(request.form)
        if quantidades is None:
            flash(
                f"Uma ou mais quantidades são inválidas. Informe valores entre 0 e {LIMITE_QUANTIDADE_ITEM}.",
                "error",
            )
            return redirect(url_for("cardapio"))

        itens_selecionados = []
        total_centavos = 0

        for item_id, item_dados in ITENS_MAP.items():
            qtd = quantidades.get(item_id, 0)

            if qtd > 0:
                # Preço canônico vem estritamente do dicionário do servidor
                preco_unitario = item_dados["preco"]
                preco_unit_cent = round(preco_unitario * 100)
                subtotal_cent = preco_unit_cent * qtd
                total_centavos += subtotal_cent

                itens_selecionados.append({
                    "id": item_id,
                    "nome": item_dados["nome"],
                    "descricao": item_dados["descricao"],
                    "preco_unitario": preco_unitario,
                    "quantidade": qtd,
                    "subtotal": subtotal_cent / 100.0,
                })

        if not itens_selecionados:
            flash("Selecione a quantidade de pelo menos um item para montar seu pedido.", "warning")
            return redirect(url_for("cardapio"))

        # Salva dados do pedido na sessão
        session["pedido_itens"] = itens_selecionados
        session["pedido_total"] = total_centavos / 100.0
        return redirect(url_for("pedido"))

    # Método GET
    itens_pedido = session.get("pedido_itens")
    total_pedido = session.get("pedido_total")

    if not itens_pedido or total_pedido is None:
        flash("Você ainda não selecionou itens para o pedido.", "info")
        return redirect(url_for("cardapio"))

    return render_template(
        "pedido.html",
        mesa=mesa,
        cliente=cliente,
        itens=itens_pedido,
        total=total_pedido,
    )


@app.route("/confirmar-pedido", methods=["POST"])
def confirmar_pedido():
    mesa = session.get("mesa")
    cliente = session.get("cliente")
    itens_pedido = session.get("pedido_itens")
    total_pedido = session.get("pedido_total")

    if not mesa or not cliente or not itens_pedido or total_pedido is None:
        flash("Sessão expirada ou pedido não encontrado. Por favor, reinicie.", "error")
        return redirect(url_for("index"))

    metodo_pagamento = request.form.get("pagamento", "").strip().lower()
    metodos_validos = {
        "debito": "Cartão de Débito",
        "credito": "Cartão de Crédito",
        "pix": "Pix",
        "dinheiro": "Dinheiro",
    }

    if metodo_pagamento not in metodos_validos:
        flash("Por favor, selecione uma forma de pagamento válida.", "error")
        return redirect(url_for("pedido"))

    # Salva confirmação na sessão
    session["pagamento_escolhido"] = metodo_pagamento
    session["pagamento_nome"] = metodos_validos[metodo_pagamento]
    session["pedido_confirmado"] = True

    return redirect(url_for("confirmacao"))


@app.route("/confirmacao", methods=["GET"])
@app.route("/pedido/sucesso", methods=["GET"])
def confirmacao():
    mesa = session.get("mesa")
    cliente = session.get("cliente")
    itens_pedido = session.get("pedido_itens")
    total_pedido = session.get("pedido_total")
    metodo = session.get("pagamento_escolhido")
    metodo_nome = session.get("pagamento_nome")
    confirmado = session.get("pedido_confirmado")

    if not (mesa and cliente and itens_pedido and total_pedido is not None and metodo and confirmado):
        flash("Nenhum pedido confirmado encontrado.", "info")
        return redirect(url_for("index"))

    return render_template(
        "confirmacao.html",
        mesa=mesa,
        cliente=cliente,
        itens=itens_pedido,
        total=total_pedido,
        metodo=metodo,
        metodo_nome=metodo_nome,
    )


@app.route("/novo-pedido", methods=["POST"])
def novo_pedido():
    # Limpa apenas os dados do pedido, mantendo mesa e cliente se desejado
    limpar_dados_pedido()
    flash("Novo pedido iniciado para a mesa.", "info")
    return redirect(url_for("cardapio"))


@app.route("/sair", methods=["POST"])
def sair():
    session.clear()
    flash("Sessão finalizada com sucesso.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
    porta = int(os.environ.get("PORT", "5000"))
    print(f"Iniciando Cardápio Digital na porta {porta} (debug={debug})...")
    app.run(host="127.0.0.1", port=porta, debug=debug)
