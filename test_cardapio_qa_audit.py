import os
import re
import unittest
from pathlib import Path
import sys

# Import app from shared cardapio-qrcode directory
SHARED_DIR = Path(r"C:\Users\andre\OpenBot\Shared\cardapio-qrcode")
sys.path.insert(0, str(SHARED_DIR))

from app import app, CARDAPIO, ITENS_MAP, sanitizar_nome, validar_numero_mesa


class TestQAComprehensiveAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "qa-audit-secret-key-super-secure"

    def setUp(self):
        self.client = app.test_client()

    # =========================================================================
    # 1. ESTRUTURA E AUSÊNCIA DE JS / TS
    # =========================================================================
    def test_zero_javascript_typescript_files(self):
        """Verifica se não há qualquer arquivo .js, .ts, .jsx, .tsx no projeto."""
        bad_extensions = {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}
        found_files = []
        for p in SHARED_DIR.rglob("*"):
            if p.is_file() and p.suffix.lower() in bad_extensions:
                found_files.append(str(p))
        self.assertEqual(found_files, [], f"Arquivos JS/TS encontrados: {found_files}")

    def test_zero_script_tags_and_inline_handlers_in_templates(self):
        """Varre todos os templates em busca de tags <script> e event handlers inline como onclick, onload."""
        templates_dir = SHARED_DIR / "templates"
        self.assertTrue(templates_dir.is_dir())
        
        inline_handler_pattern = re.compile(r'\bon\w+\s*=', re.IGNORECASE)
        javascript_uri_pattern = re.compile(r'href\s*=\s*["\']javascript:', re.IGNORECASE)

        for template_file in templates_dir.glob("*.html"):
            content = template_file.read_text(encoding="utf-8")
            # Verifica tags <script>
            self.assertNotIn("<script", content.lower(), f"Tag <script> encontrada em {template_file.name}")
            # Verifica event handlers inline (onclick, onchange, etc.)
            self.assertFalse(
                inline_handler_pattern.search(content),
                f"Handler inline (on*) encontrado em {template_file.name}"
            )
            # Verifica URLs javascript:
            self.assertFalse(
                javascript_uri_pattern.search(content),
                f"Protocolo javascript: encontrado em {template_file.name}"
            )

    def test_html_semantic_and_accessibility_structure(self):
        """Verifica estrutura semântica (DOCTYPE, lang, viewport, tags semânticas)."""
        res = self.client.get("/")
        html = res.data.decode("utf-8")
        
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn('lang="pt-BR"', html)
        self.assertIn('name="viewport"', html)
        self.assertIn("<header", html)
        self.assertIn("<main", html)
        self.assertIn("<footer", html)

    # =========================================================================
    # 2. HEADERS HTTP DE SEGURANÇA E COOKIES
    # =========================================================================
    def test_security_headers_and_cookie_policy(self):
        """Audita headers HTTP estritos e diretivas CSP."""
        res = self.client.get("/")
        headers = res.headers

        # CSP
        csp = headers.get("Content-Security-Policy", "")
        self.assertIn("script-src 'none'", csp, "CSP deve proibir execução de scripts ('none')")
        self.assertIn("default-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("base-uri 'self'", csp)

        # Headers anti-clickjacking, sniffing e MIME
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("camera=()", headers.get("Permissions-Policy", ""))

        # Cookies de Sessão
        self.assertTrue(app.config.get("SESSION_COOKIE_HTTPONLY"))
        self.assertEqual(app.config.get("SESSION_COOKIE_SAMESITE"), "Lax")

    # =========================================================================
    # 3. VALIDAÇÃO DE ENTRADA: NÚMERO DA MESA (1 A 999)
    # =========================================================================
    def test_validar_numero_mesa_unitario(self):
        """Testes de limites e tipos para validação de mesa."""
        # Válidos
        self.assertEqual(validar_numero_mesa(1), 1)
        self.assertEqual(validar_numero_mesa(999), 999)
        self.assertEqual(validar_numero_mesa("42"), 42)
        self.assertEqual(validar_numero_mesa(" 15 "), 15)

        # Limites inválidos
        self.assertIsNone(validar_numero_mesa(0))
        self.assertIsNone(validar_numero_mesa(1000))
        self.assertIsNone(validar_numero_mesa(-1))
        self.assertIsNone(validar_numero_mesa(-999))

        # Tipos / Entradas corrompidas
        self.assertIsNone(validar_numero_mesa("abc"))
        self.assertIsNone(validar_numero_mesa("12.5"))
        self.assertIsNone(validar_numero_mesa(""))
        self.assertIsNone(validar_numero_mesa(None))
        self.assertIsNone(validar_numero_mesa("1; DROP TABLE"))

    def test_qr_code_get_param_mesa(self):
        """GET /?mesa=X com mesa válida e inválida."""
        # Mesa válida 7
        res = self.client.get("/?mesa=7")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'value="7"', res.data)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("mesa"), 7)

        # Mesa inválida 1050 via QR Code
        res_inv = self.client.get("/?mesa=1050")
        self.assertEqual(res_inv.status_code, 200)
        self.assertIn("O número de mesa no link QR Code é inválido".encode("utf-8"), res_inv.data)

    # =========================================================================
    # 4. VALIDAÇÃO E SANITIZAÇÃO DE NOME
    # =========================================================================
    def test_sanitizar_nome_unitario(self):
        """Testes de sanitização de espaços, tamanho máximo e strings vazias."""
        self.assertEqual(sanitizar_nome("   Carlos   da   Silva   "), "Carlos da Silva")
        self.assertEqual(sanitizar_nome(""), "")
        self.assertEqual(sanitizar_nome(None), "")
        
        # Truncamento em 60 caracteres
        nome_longo = "A" * 80
        sanitizado = sanitizar_nome(nome_longo)
        self.assertEqual(len(sanitizado), 60)

    def test_validacao_post_identificacao(self):
        """Valida regras de POST na rota de identificação."""
        # Sucesso
        res = self.client.post("/", data={"mesa": "12", "nome": "Maria Santos"})
        self.assertEqual(res.status_code, 302)
        self.assertIn("/cardapio", res.headers.get("Location"))

        # Nome com 1 letra (rejeitado)
        res_curto = self.client.post("/", data={"mesa": "12", "nome": "M"}, follow_redirects=True)
        self.assertEqual(res_curto.status_code, 200)
        self.assertIn("mínimo de 2 caracteres".encode("utf-8"), res_curto.data)

        # Mesa ausente ou fora da faixa
        res_mesa_ruim = self.client.post("/", data={"mesa": "0", "nome": "Maria Santos"}, follow_redirects=True)
        self.assertEqual(res_mesa_ruim.status_code, 200)
        self.assertIn("entre 1 e 999".encode("utf-8"), res_mesa_ruim.data)

    # =========================================================================
    # 5. CONTROLE DE ACESSO E SESSÃO (ROUTE GUARDS)
    # =========================================================================
    def test_acesso_rotas_protegidas_sem_sessao(self):
        """Garante que rotas internas redirecionam para a raiz quando não há identificação."""
        rotas = ["/cardapio", "/pedido", "/confirmacao"]
        for rota in rotas:
            res = self.client.get(rota)
            self.assertEqual(res.status_code, 302, f"Rota {rota} deveria redirecionar")
            self.assertEqual(res.headers.get("Location"), "/")

    def test_post_confirmar_pedido_sem_sessao(self):
        """POST /confirmar-pedido sem sessão deve redirecionar para a raiz."""
        res = self.client.post("/confirmar-pedido", data={"pagamento": "pix"})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get("Location"), "/")

    # =========================================================================
    # 6. CÁLCULO E INTEGRIDADE DE PREÇOS NO SERVIDOR
    # =========================================================================
    def test_integridade_precos_tentativa_adulteracao_pelo_cliente(self):
        """Simula tentativa de injeção de parâmetros de preços adulterados pelo cliente."""
        # 1. Identificar
        self.client.post("/", data={"mesa": "20", "nome": "Cliente Teste"})

        # 2. Cliente envia preços forjados nos campos
        payload = {
            "qtd_ent_1": "3",  # Bruschetta: 24.90 * 3 = 74.70
            "qtd_beb_1": "2",  # Suco: 12.00 * 2 = 24.00
            "preco_ent_1": "0.01",  # Tentativa de burlar preço
            "preco_beb_1": "0.05",  # Tentativa de burlar preço
            "total": "0.06",        # Tentativa de injetar total
            "subtotal": "0.06",
        }
        res = self.client.post("/pedido", data=payload, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Total calculado pelo servidor: 74.70 + 24.00 = 98.70
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("pedido_total"), 98.70)
            itens = sess.get("pedido_itens")
            self.assertEqual(len(itens), 2)
            self.assertEqual(itens[0]["subtotal"], 74.70)
            self.assertEqual(itens[1]["subtotal"], 24.00)

        self.assertIn("98,70".encode("utf-8"), res.data)

    def test_quantidade_limites_e_valores_negativos(self):
        """Quantidades negativas, acima de 20 ou IDs desconhecidos são estritamente rejeitadas."""
        self.client.post("/", data={"mesa": "20", "nome": "Cliente Teste"})

        # Quantidade negativa é rejeitada com flash de erro
        payload_negativo = {
            "qtd_ent_1": "-5",
            "qtd_prat_1": "1",
        }
        res_neg = self.client.post("/pedido", data=payload_negativo, follow_redirects=True)
        self.assertEqual(res_neg.status_code, 200)
        self.assertIn("quantidades são inválidas".encode("utf-8"), res_neg.data)

        # Quantidade acima de LIMITE_QUANTIDADE_ITEM (20) é rejeitada
        payload_excesso = {
            "qtd_beb_3": "25",
        }
        res_exc = self.client.post("/pedido", data=payload_excesso, follow_redirects=True)
        self.assertEqual(res_exc.status_code, 200)
        self.assertIn("quantidades são inválidas".encode("utf-8"), res_exc.data)

        # ID desconhecido é rejeitado
        payload_id_falso = {
            "qtd_item_fantasma": "2",
        }
        res_falso = self.client.post("/pedido", data=payload_id_falso, follow_redirects=True)
        self.assertEqual(res_falso.status_code, 200)
        self.assertIn("quantidades são inválidas".encode("utf-8"), res_falso.data)

        # Quantidade válida entre 1 e 20 é aceita com cálculo exato
        payload_valido = {
            "qtd_beb_3": "20",  # 20 * 6.50 = 130.00
        }
        res_val = self.client.post("/pedido", data=payload_valido, follow_redirects=True)
        self.assertEqual(res_val.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("pedido_total"), 130.00)
            self.assertEqual(sess.get("pedido_itens")[0]["quantidade"], 20)

    # =========================================================================
    # 7. FLUXO DE PAGAMENTO E AVISO OBRIGATÓRIO DE 'DINHEIRO'
    # =========================================================================
    def test_regra_especifica_pagamento_dinheiro(self):
        """Verifica a regra de pagamento 'dinheiro' e a mensagem textual exata."""
        self.client.post("/", data={"mesa": "15", "nome": "Joana Dark"})
        self.client.post("/pedido", data={"qtd_prat_2": "1"})  # Filé Mignon

        res = self.client.post("/confirmar-pedido", data={"pagamento": "dinheiro"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Validação do texto exato
        texto_obrigatorio = "Pagamento pendente no balcão/final do atendimento."
        self.assertIn(texto_obrigatorio.encode("utf-8"), res.data)

    def test_metodos_pagamento_debito_credito_pix(self):
        """Verifica os fluxos de pagamento débito, crédito e pix."""
        self.client.post("/", data={"mesa": "15", "nome": "Joana Dark"})
        self.client.post("/pedido", data={"qtd_prat_2": "1"})

        # Débito
        res_deb = self.client.post("/confirmar-pedido", data={"pagamento": "debito"}, follow_redirects=True)
        self.assertEqual(res_deb.status_code, 200)
        self.assertIn("maquininha de cartão de débito".encode("utf-8"), res_deb.data)

        # Crédito
        res_cred = self.client.post("/confirmar-pedido", data={"pagamento": "credito"}, follow_redirects=True)
        self.assertEqual(res_cred.status_code, 200)
        self.assertIn("maquininha de cartão de crédito".encode("utf-8"), res_cred.data)

        # Pix
        res_pix = self.client.post("/confirmar-pedido", data={"pagamento": "pix"}, follow_redirects=True)
        self.assertEqual(res_pix.status_code, 200)
        self.assertIn("Aguardando confirmação do Pix".encode("utf-8"), res_pix.data)

    def test_rejeicao_pagamento_invalido(self):
        """Método de pagamento forjado ou não suportado deve ser rejeitado."""
        self.client.post("/", data={"mesa": "15", "nome": "Joana Dark"})
        self.client.post("/pedido", data={"qtd_prat_2": "1"})

        res = self.client.post("/confirmar-pedido", data={"pagamento": "boleto"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("selecione uma forma de pagamento válida".encode("utf-8"), res.data)

    # =========================================================================
    # 8. LIFECYCLE: NOVO PEDIDO E SAIR
    # =========================================================================
    def test_ciclo_novo_pedido_mantem_identificacao(self):
        """POST /novo-pedido limpa itens do pedido mas mantém cliente e mesa."""
        self.client.post("/", data={"mesa": "22", "nome": "Lucas Pires"})
        self.client.post("/pedido", data={"qtd_ent_3": "1"})
        self.client.post("/confirmar-pedido", data={"pagamento": "pix"})

        res = self.client.post("/novo-pedido")
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get("Location"), "/cardapio")

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("mesa"), 22)
            self.assertEqual(sess.get("cliente"), "Lucas Pires")
            self.assertNotIn("pedido_itens", sess)
            self.assertNotIn("pedido_total", sess)
            self.assertNotIn("pedido_confirmado", sess)

    def test_sair_limpa_toda_sessao(self):
        """POST /sair executa session.clear() completo e retorna para /."""
        self.client.post("/", data={"mesa": "22", "nome": "Lucas Pires"})
        self.client.post("/pedido", data={"qtd_ent_3": "1"})

        res = self.client.post("/sair")
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get("Location"), "/")

        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get("mesa"))
            self.assertIsNone(sess.get("cliente"))
            self.assertIsNone(sess.get("pedido_itens"))
            self.assertIn("_flashes", sess)


if __name__ == "__main__":
    unittest.main()
