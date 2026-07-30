"""Estatisticas descritivas para os sinais de vibracao.

Este modulo nao le a serial, nao altera o buffer e nao atualiza a interface.
Sua unica responsabilidade e receber uma sequencia numerica (por exemplo,
os valores de ``ax`` das ultimas 1.000 amostras) e devolver medidas prontas
para serem mostradas no painel de estatisticas ou salvas em uma analise.

Exemplo futuro na janela::

    from utils.statistics import calcular_estatisticas

    dados = manager.buffer.snapshot(1000)
    estatisticas_ax = calcular_estatisticas(dados["ax"])
    self.label_media_ax.setText(f"Media Ax: {estatisticas_ax.media:.3f}")

As variancias e desvios padrao usam ``ddof=0`` por padrao. Isto descreve a
janela inteira que esta no buffer (populacao observada), o que e apropriado
para monitoramento em tempo real. Para estimar uma populacao maior a partir
de uma amostra, use ``ddof=1``.
"""

from dataclasses import dataclass
from typing import Iterable

import numpy as np


__all__ = ["EstatisticasBasicas", "calcular_estatisticas"]


@dataclass(frozen=True, slots=True)
class EstatisticasBasicas:
    """Resultado das estatisticas descritivas de um unico sinal.

    Os campos numericos sao ``nan`` quando nao ha amostras validas ou quando
    uma medida nao pode ser calculada. Por exemplo, a variancia amostral com
    ``ddof=1`` exige pelo menos duas amostras.
    """

    quantidade: int
    amostras_invalidas: int
    media: float
    mediana: float
    minimo: float
    maximo: float
    amplitude_pico_a_pico: float
    variancia: float
    desvio_padrao: float
    rms: float
    coeficiente_variacao_percentual: float
    assimetria: float
    curtose_excesso: float


def calcular_estatisticas(
    valores: Iterable[float],
    *,
    ddof: int = 0,
) -> EstatisticasBasicas:
    """Calcula estatisticas basicas para uma sequencia de amostras.

    Args:
        valores: Valores de um unico eixo, como ``snapshot["ax"]``.
        ddof: Graus de liberdade da variancia. Use 0 para descrever a janela
            atual do buffer e 1 para a variancia amostral.

    Returns:
        Um :class:`EstatisticasBasicas`. Valores ``nan`` indicam que aquela
        medida nao e definida para a quantidade de amostras recebida.

    Notes:
        ``nan``, ``inf`` e ``-inf`` nao participam dos calculos. A quantidade
        descartada fica registrada em ``amostras_invalidas`` para que a
        interface possa sinalizar uma eventual falha no sinal.
    """
    if ddof < 0:
        raise ValueError("ddof deve ser maior ou igual a zero")

    # Converte qualquer iteravel (list, deque, numpy array ou generator) para
    # um vetor NumPy. A conversao ocorre uma unica vez por atualizacao da UI.
    amostras = np.asarray(list(valores), dtype=float).reshape(-1)

    # Dados do MPU6050 deveriam ser finitos. Filtrar valores invalidos evita
    # que uma unica leitura corrompida transforme todas as medidas em nan.
    mascara_valida = np.isfinite(amostras)
    validas = amostras[mascara_valida]
    quantidade = int(validas.size)
    amostras_invalidas = int(amostras.size - validas.size)

    if quantidade == 0:
        return _resultado_indefinido(amostras_invalidas)

    media = float(np.mean(validas))
    mediana = float(np.median(validas))
    minimo = float(np.min(validas))
    maximo = float(np.max(validas))
    amplitude_pico_a_pico = maximo - minimo

    # RMS (root mean square) e muito usado em vibracao porque representa uma
    # medida de intensidade energetica do sinal, independentemente do sinal.
    rms = float(np.sqrt(np.mean(np.square(validas))))

    if quantidade > ddof:
        variancia = float(np.var(validas, ddof=ddof))
        desvio_padrao = float(np.sqrt(variancia))
    else:
        variancia = float("nan")
        desvio_padrao = float("nan")

    # Coeficiente de variacao permite comparar dispersao relativa. Nao faz
    # sentido dividir por uma media nula ou por um desvio padrao indefinido.
    if np.isfinite(desvio_padrao) and not np.isclose(media, 0.0):
        coeficiente_variacao_percentual = float(
            (desvio_padrao / abs(media)) * 100
        )
    else:
        coeficiente_variacao_percentual = float("nan")

    # Assimetria e curtose descrevem a forma da distribuicao. Sao calculadas
    # por momentos populacionais; o excesso de curtose de uma normal e zero.
    if quantidade >= 2 and np.isfinite(desvio_padrao) and desvio_padrao > 0:
        valores_padronizados = (validas - media) / desvio_padrao
        assimetria = float(np.mean(np.power(valores_padronizados, 3)))
        curtose_excesso = float(np.mean(np.power(valores_padronizados, 4)) - 3)
    else:
        assimetria = float("nan")
        curtose_excesso = float("nan")

    return EstatisticasBasicas(
        quantidade=quantidade,
        amostras_invalidas=amostras_invalidas,
        media=media,
        mediana=mediana,
        minimo=minimo,
        maximo=maximo,
        amplitude_pico_a_pico=amplitude_pico_a_pico,
        variancia=variancia,
        desvio_padrao=desvio_padrao,
        rms=rms,
        coeficiente_variacao_percentual=coeficiente_variacao_percentual,
        assimetria=assimetria,
        curtose_excesso=curtose_excesso,
    )


def _resultado_indefinido(amostras_invalidas: int) -> EstatisticasBasicas:
    """Cria o resultado usado quando a sequencia nao possui valor valido."""
    nan = float("nan")
    return EstatisticasBasicas(
        quantidade=0,
        amostras_invalidas=amostras_invalidas,
        media=nan,
        mediana=nan,
        minimo=nan,
        maximo=nan,
        amplitude_pico_a_pico=nan,
        variancia=nan,
        desvio_padrao=nan,
        rms=nan,
        coeficiente_variacao_percentual=nan,
        assimetria=nan,
        curtose_excesso=nan,
    )
