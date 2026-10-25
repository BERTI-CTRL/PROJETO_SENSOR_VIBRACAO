"""Checks that QR generation never accepts a placeholder publication URL."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("gerar_qr.py")


def carregar_gerador():
    spec = importlib.util.spec_from_file_location("gerar_qr", SCRIPT_PATH)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


class GerarQrTests(unittest.TestCase):
    def test_rejeita_url_de_exemplo(self):
        gerador = carregar_gerador()
        for url in ("https://SEU-APP.streamlit.app", "https://sua-url-real.streamlit.app"):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "fictícia"):
                gerador.validar_url(url)

    def test_aceita_url_publica_https(self):
        gerador = carregar_gerador()
        self.assertEqual(
            gerador.validar_url("https://portico-unifal.streamlit.app"),
            "https://portico-unifal.streamlit.app",
        )


if __name__ == "__main__":
    unittest.main()
