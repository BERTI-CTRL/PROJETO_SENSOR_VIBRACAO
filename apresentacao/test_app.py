"""Checks for the compact public-presentation data analysis."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


PASTA_APRESENTACAO = Path(__file__).resolve().parent
APP_PATH = Path(__file__).with_name("app.py")


def carregar_app():
    spec = importlib.util.spec_from_file_location("apresentacao_app", APP_PATH)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


class AnaliseEnsaioTests(unittest.TestCase):
    def test_explica_referencia_do_poster_sem_ocultar_pico_calculado(self):
        app = carregar_app()

        texto = app.rotulo_frequencia(2.0078312402, 2.02)

        self.assertEqual(
            texto,
            "Frequência dominante apresentada: ≈ 2,02 Hz. "
            "Pico calculado nesta visualização: 2,01 Hz.",
        )

    def test_identifica_frequencia_dominante_do_ensaio_com_tres_massas(self):
        app = carregar_app()
        resultado = app.analisar_ensaio(
            PASTA_APRESENTACAO / "data" / "csv" / "dados_aceleracao_giro-2026-09-21_14-47-18.csv",
            "ay",
        )

        self.assertEqual(resultado["amostras"], 5011)
        self.assertAlmostEqual(resultado["duracao_s"], 22.816, places=2)
        self.assertAlmostEqual(resultado["frequencia_aquisicao_hz"], 219.6, places=0)
        self.assertAlmostEqual(resultado["frequencia_dominante_hz"], 2.02, delta=0.08)

    def test_rejeita_tempo_arduino_sem_incremento_positivo(self):
        app = carregar_app()
        conteudo = (
            "tempo_arduino_us,tempo_relogio_pc,contador,ax,ay,az,gx,gy,gz\n"
            "1000,0,0,0,0,0,0,0,0\n"
            "1000,0.1,1,0,0,0,0,0,0\n"
        )
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "invalido.csv"
            arquivo.write_text(conteudo, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "tempo"):
                app.analisar_ensaio(arquivo, "ay")


if __name__ == "__main__":
    unittest.main()
