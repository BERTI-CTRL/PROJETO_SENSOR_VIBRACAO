#!/usr/bin/env python3
"""Teste de consistência dos dados CSV do sensor MPU6050.
Uso: python dados\testar_dados.py [caminho_do_arquivo]
Se nenhum arquivo informado, pega o mais recente em dados/.


"""

import sys
import glob
import os
from pathlib import Path

try:
    import numpy as np
except ImportError:
    print("Erro: numpy não instalado. pip install numpy")
    sys.exit(1)


def testar_arquivo(caminho: str) -> dict:
    """Executa todos os testes de consistência em um arquivo CSV.
    Retorna dict com resultados.
    """
    print(f"\n{'='*60}")
    print(f"TESTANDO: {caminho}")
    print(f"{'='*60}")

    with open(caminho, 'r') as f:
        linhas = f.readlines()

    if not linhas:
        return {"erro": "Arquivo vazio"}

    header = linhas[0].strip().split(',')
    esperados = ['tempo_arduino_us', 'tempo_relogio_pc', 'contador',
                 'ax', 'ay', 'az', 'gx', 'gy', 'gz']

    if header != esperados:
        return {"erro": f"Header inesperado: {header}"}

    dados = []
    for i, linha in enumerate(linhas[1:], 1):
        linha = linha.strip()
        if not linha:
            continue
        partes = linha.split(',')
        if len(partes) != 9:
            return {"erro": f"Linha {i}: {len(partes)} colunas (esperado 9)"}
        try:
            dados.append([float(x) for x in partes])
        except ValueError:
            return {"erro": f"Linha {i}: valor não numérico"}

    if not dados:
        return {"erro": "Nenhum dado válido"}

    arr = np.array(dados)
    t_arduino = arr[:, 0]
    t_pc = arr[:, 1]
    contador = arr[:, 2]
    sensores = arr[:, 3:]

    n = len(arr)
    print(f"Total de amostras: {n}")

    # 1. Contador sequencial
    diffs = np.diff(contador)
    saltos = np.where(diffs > 1)[0]
    n_saltos = len(saltos)
    total_perdidas = int(np.sum(diffs[saltos] - 1)) if n_saltos > 0 else 0
    print(f"\n1. CONTADOR:")
    print(f"   Início: {contador[0]:.0f} | Fim: {contador[-1]:.0f}")
    print(f"   Saltos: {n_saltos} | Amostras perdidas: {total_perdidas}")
    if n_saltos > 0:
        for idx in saltos[:5]:
            print(f"   - Salto {idx}: {contador[idx]:.0f} -> {contador[idx+1]:.0f} (perdidas: {int(diffs[idx]-1)})")
        if n_saltos > 5:
            print(f"   ... e mais {n_saltos-5} saltos")

    # 2. Taxa de amostragem (Hz)
    dt_arduino = np.diff(t_arduino) / 1_000_000  # segundos
    dt_arduino = dt_arduino[dt_arduino > 0]
    hz_inst = 1.0 / dt_arduino
    hz_medio = (n - 1) / ((t_arduino[-1] - t_arduino[0]) / 1_000_000)
    print(f"\n2. TAXA (Hz):")
    print(f"   Média: {hz_medio:.2f}")
    print(f"   Inst. média: {np.mean(hz_inst):.2f} | std: {np.std(hz_inst):.2f}")
    print(f"   Min: {np.min(hz_inst):.2f} | Max: {np.max(hz_inst):.2f}")

    # 3. Valores dos sensores (range físico)
    nomes = ['ax', 'ay', 'az', 'gx', 'gy', 'gz']
    limites = {
        'ax': (-16, 16), 'ay': (-16, 16), 'az': (-16, 16),  # g (±16g)
        'gx': (-2000, 2000), 'gy': (-2000, 2000), 'gz': (-2000, 2000)  # °/s (±2000)
    }
    print(f"\n3. SENSORES (range físico):")
    for i, nome in enumerate(nomes):
        col = sensores[:, i]
        mn, mx = np.min(col), np.max(col)
        media, std = np.mean(col), np.std(col)
        rms = np.sqrt(np.mean(col**2))
        lim_min, lim_max = limites[nome]
        fora = np.sum((col < lim_min) | (col > lim_max))
        status = "⚠ FORA" if fora > 0 else "OK"
        print(f"   {nome:3s}: [{mn:8.3f}, {mx:8.3f}] media={media:7.3f} std={std:7.3f} rms={rms:7.3f} {status}")

    # 4. Tempo PC (monotonicidade)
    dt_pc = np.diff(t_pc)
    negativos = np.sum(dt_pc < 0)
    print(f"\n4. TEMPO PC:")
    print(f"   Deltas negativos: {negativos} (esperado 0)")
    print(f"   Duração total: {t_pc[-1] - t_pc[0]:.1f}s")

    # 5. NaN/Inf
    nan_count = np.sum(~np.isfinite(arr))
    print(f"\n5. VALORES INVÁLIDOS:")
    print(f"   NaN/Inf: {nan_count} (esperado 0)")

    # Resumo
    ok = (n_saltos == 0 and negativos == 0 and nan_count == 0 and
          all(np.sum((sensores[:, i] < limites[n][0]) | (sensores[:, i] > limites[n][1])) == 0
              for i, n in enumerate(nomes)))

    print(f"\n{'='*60}")
    print(f"RESULTADO: {'PASSOU' if ok else 'FALHOU'}")
    print(f"{'='*60}\n")

    return {
        "arquivo": caminho,
        "amostras": n,
        "saltos": int(n_saltos),
        "perdidas": total_perdidas,
        "hz_medio": float(hz_medio),
        "hz_std": float(np.std(hz_inst)),
        "fora_range": {n: int(np.sum((sensores[:, i] < limites[n][0]) | (sensores[:, i] > limites[n][1])))
                       for i, n in enumerate(nomes)},
        "negativos_pc": int(negativos),
        "nan_inf": int(nan_count),
        "ok": ok
    }


def encontrar_mais_recente(diretorio: str = "dados") -> str | None:
    """Retorna o CSV mais recente no diretório."""
    padrao = os.path.join(diretorio, "dados_aceleracao_giro-*.csv")
    arquivos = glob.glob(padrao)
    if not arquivos:
        return None
    return max(arquivos, key=os.path.getmtime)


def main():
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
        if not os.path.exists(arquivo):
            print(f"Arquivo não encontrado: {arquivo}")
            sys.exit(1)
    else:
        arquivo = encontrar_mais_recente()
        if not arquivo:
            print("Nenhum arquivo encontrado em dados/")
            sys.exit(1)
        print(f"Usando arquivo mais recente: {arquivo}")

    resultado = testar_arquivo(arquivo)

    if "erro" in resultado:
        print(f"ERRO: {resultado['erro']}")
        sys.exit(1)

    sys.exit(0 if resultado["ok"] else 1)


if __name__ == "__main__":
    main()