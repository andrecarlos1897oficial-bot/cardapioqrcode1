import unittest
from app import app, ITENS_MAP


class TestCardapioQRCode(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key-123"
        self.client = app.test_client()

    def test_security_headers_present(self):
        """Verifica se todos os headers de segurança obrigatórios estão presentes."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        csp = res.headers.get("Content-Security-Policy", "")
        self.assertIn("script-src 'none'", csp)
        self.assertIn("default-src 'self'", csp)
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(res.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("camera=()", res.headers.get("Permissions-Policy", ""))

    def test_index_com_qr_code_mesa_valida(self):
        """Acesso via QR Code com ?mesa=14 deve pré-preencher a mesa e salvar na sessão."""
        res = self.client.get("/?mesa=14")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'value="14"', res.data)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("mesa"), 14)

    def test_identificacao_validacao_rejeita_mesa_invalida(self):
        """Rejeita mesa negativa, zero, ou não-numérica."""
        res = self.client.post("/", data={"mesa": "-5", "nome": "Carlos"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("número de mesa válido".encode("utf-8"), res.data)

        res2 = self.client.post("/", data={"mesa": "abc", "nome": "Carlos"}, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        self.assertIn("número de mesa válido".encode("utf-8"), res2.data)

    def test_identificacao_validacao_rejeita_nome_muito_curto(self):
        """Rejeita nome com menos de 2 caracteres."""
        res = self.client.post("/", data={"mesa": "10", "nome": "A"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("mínimo de 2 caracteres".encode("utf-8"), res.data)

    def test_protecao_xss_no_nome_cliente(self):
        """Nome com tags html/script deve ser sanitizado e escapado com segurança pelo Jinja2."""
        nome_malicioso = "<script>alert('xss')</script>João"
        res = self.client.post("/", data={"mesa": "10", "nome": nome_malicioso}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        # O HTML não pode conter a tag bruta desescapada
        self.assertNotIn(b"<script>alert('xss')</script>", res.data)
        # Deve estar escapado
        self.assertIn(b"&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;", res.data)

    def test_redirecionamento_cardapio_sem_identificacao(self):
        """Acesso direto a /cardapio sem sessão deve redirecionar para /."""
        res = self.client.get("/cardapio")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/", res.headers.get("Location"))

    def test_fluxo_completo_pedido_e_calculo_preco_servidor(self):
        """Garante que preços são calculados pelo servidor, ignorando manipulações do cliente."""
        # 1. Identificar cliente na Mesa 8
        self.client.post("/", data={"mesa": "8", "nome": "Mariana Silva"})

        # 2. Enviar pedido com 2x Bruschetta (ent_1: 24.90) e 1x Hambúrguer (prat_1: 42.00)
        # Mesmo se o cliente tentar enviar um campo fake de preco_total=1.00, o backend ignora
        res_pedido = self.client.post(
            "/pedido",
            data={
                "qtd_ent_1": "2",
                "qtd_prat_1": "1",
                "preco_total_fake": "0.50",
            },
            follow_redirects=True,
        )
        self.assertEqual(res_pedido.status_code, 200)

        # Total esperado: (2 * 24.90) + (1 * 42.00) = 49.80 + 42.00 = 91.80
        total_esperado = (2 * ITENS_MAP["ent_1"]["preco"]) + (1 * ITENS_MAP["prat_1"]["preco"])
        self.assertAlmostEqual(total_esperado, 91.80, places=2)

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("pedido_total"), 91.80)
            self.assertEqual(len(sess.get("pedido_itens")), 2)

        # Verifica se o resumo exibe o valor correto formatado
        self.assertIn("91,80".encode("utf-8"), res_pedido.data)

    def test_pedido_sem_itens_rejeitado(self):
        """Se o usuário tentar avançar sem selecionar nenhum item, deve retornar ao cardápio."""
        self.client.post("/", data={"mesa": "8", "nome": "Mariana Silva"})
        res = self.client.post("/pedido", data={"qtd_ent_1": "0"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Selecione a quantidade de pelo menos um item".encode("utf-8"), res.data)

    def test_pedido_rejeita_quantidades_invalidas(self):
        """Valores inválidos não podem ser convertidos silenciosamente em zero ou limitados."""
        self.client.post("/", data={"mesa": "8", "nome": "Mariana Silva"})

        for data in (
            {"qtd_ent_1": "-1"},
            {"qtd_ent_1": "21"},
            {"qtd_ent_1": "invalido"},
            {"qtd_item_inexistente": "1"},
            {"qtd_ent_1": ["1", "2"]},
        ):
            res = self.client.post("/resumo", data=data, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("quantidades são inválidas".encode("utf-8"), res.data)
            with self.client.session_transaction() as sess:
                self.assertNotIn("pedido_itens", sess)

    def test_pedido_aceita_limite_de_20_unidades(self):
        """O limite máximo do formulário é aplicado também no servidor."""
        self.client.post("/", data={"mesa": "8", "nome": "Mariana Silva"})
        res = self.client.post(
            "/resumo",
            data={"qtd_ent_1": "20"},
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["pedido_itens"][0]["quantidade"], 20)
            self.assertEqual(sess["pedido_total"], 498.0)

    def test_confirmacao_pagamento_dinheiro_exibe_aviso_obrigatorio(self):
        """Forma de pagamento Dinheiro deve exibir o aviso exato exigido pela especificação."""
        self.client.post("/", data={"mesa": "5", "nome": "Roberto Carlos"})
        self.client.post("/pedido", data={"qtd_beb_1": "2"})  # 2 sucos

        res_conf = self.client.post("/confirmar-pedido", data={"pagamento": "dinheiro"}, follow_redirects=True)
        self.assertEqual(res_conf.status_code, 200)
        # Texto obrigatório da especificação
        self.assertIn("Pagamento pendente no balcão/final do atendimento".encode("utf-8"), res_conf.data)

    def test_confirmacao_pagamento_pix(self):
        """Forma de pagamento Pix deve exibir instruções de pagamento Pix."""
        self.client.post("/", data={"mesa": "5", "nome": "Roberto Carlos"})
        self.client.post("/pedido", data={"qtd_beb_1": "1"})

        res_conf = self.client.post("/confirmar-pedido", data={"pagamento": "pix"}, follow_redirects=True)
        self.assertEqual(res_conf.status_code, 200)
        self.assertIn("/pedido/sucesso", res_conf.request.path)
        self.assertIn("Instruções para Pagamento via Pix".encode("utf-8"), res_conf.data)
        self.assertIn("Aguardando confirmação do Pix".encode("utf-8"), res_conf.data)

    def test_confirmacao_pagamento_cartao_credito_e_debito(self):
        """Cartão deve avisar que a máquina será levada à mesa."""
        self.client.post("/", data={"mesa": "3", "nome": "Ana Paula"})
        self.client.post("/pedido", data={"qtd_sob_1": "1"})

        res_conf = self.client.post("/confirmar-pedido", data={"pagamento": "credito"}, follow_redirects=True)
        self.assertEqual(res_conf.status_code, 200)
        self.assertIn("maquininha de cartão".encode("utf-8"), res_conf.data)
        self.assertIn("Pedido Confirmado".encode("utf-8"), res_conf.data)

    def test_rejeicao_metodo_pagamento_invalido(self):
        """Forma de pagamento desconhecida/adulterada deve ser rejeitada."""
        self.client.post("/", data={"mesa": "3", "nome": "Ana Paula"})
        self.client.post("/pedido", data={"qtd_sob_1": "1"})

        res = self.client.post("/confirmar-pedido", data={"pagamento": "bitcoin"}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("selecione uma forma de pagamento válida".encode("utf-8"), res.data)


if __name__ == "__main__":
    unittest.main()
