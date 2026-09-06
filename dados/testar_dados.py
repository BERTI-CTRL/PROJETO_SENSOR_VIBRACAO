#!/usr/bin/env python3
"""Teste de consistência dos dados CSV do sensor MPU6050.
Uso: python dados\testar_dados.py [caminho_do_arquivo]
Se nenhum arquivo informado, pega o mais recente em dados/.


"""

import sys
import glob
import os
from pathlib import Path

# NumPy dá suporte aos cálculos vetorizados de continuidade, taxa e faixas.
try:
    import numpy as np
except ImportError:
    print("Erro: numpy não instalado. pip install numpy")
    sys.exit(1)


def testar_arquivo(caminho: str) -> dict:
    """Executa todos os testes de consistência em um arquivo CSV.
    Retorna dict com resultados.
    """
    # Delimita visualmente o relatório do arquivo analisado no terminal.
    print(f"\n{'='*60}")
    print(f"TESTANDO: {caminho}")
    print(f"{'='*60}")

    # Lê manualmente o arquivo para validar cada linha antes de convertê-lo.
    with open(caminho, 'r') as f:
        linhas = f.readlines()

    # Um arquivo sem cabeçalho e sem amostras não pode ser validado.
    if not linhas:
        return {"erro": "Arquivo vazio"}

    # Separa o cabeçalho CSV para compará-lo ao contrato rígido de persistência.
    header = linhas[0].strip().split(',')
    # Esta ordem deve coincidir exatamente com o contrato descrito em esquema-csv.
    esperados = ['tempo_arduino_us', 'tempo_relogio_pc', 'contador',
                 'ax', 'ay', 'az', 'gx', 'gy', 'gz']

    # Rejeita arquivos com coluna ausente, extra ou reordenada para evitar análise errada.
    if header != esperados:
        return {"erro": f"Header inesperado: {header}"}

    # Acumula somente as linhas que obedecem à forma numérica esperada.
    dados = []
    # Percorre as amostras mantendo o número de linha útil para mensagens de erro.
    for i, linha in enumerate(linhas[1:], 1):
        # Remove a quebra de linha e espaços sem alterar os valores internos.
        linha = linha.strip()
        # Ignora linhas em branco, que não representam amostras do sensor.
        if not linha:
            continue
        # Divide a amostra nos nove campos gravados pelo pipeline de aquisição.
        partes = linha.split(',')
        # Impede índices incorretos e diagnósticos com dados estruturalmente inválidos.
        if len(partes) != 9:
            return {"erro": f"Linha {i}: {len(partes)} colunas (esperado 9)"}
        try:
            # Converte todos os campos para float para os cálculos numéricos seguintes.
            dados.append([float(x) for x in partes])
        except ValueError:
            return {"erro": f"Linha {i}: valor não numérico"}

    # Sem ao menos uma linha válida não há estatística de consistência possível.
    if not dados:
        return {"erro": "Nenhum dado válido"}

    # Transforma a lista em matriz NumPy para selecionar colunas e calcular diferenças.
    arr = np.array(dados)
    # Separa tempos, contador e os seis eixos na mesma ordem do CSV.
    t_arduino = arr[:, 0]
    t_pc = arr[:, 1]
    contador = arr[:, 2]
    sensores = arr[:, 3:]

    # Guarda a quantidade de amostras para o relatório e a taxa média.
    n = len(arr)
    print(f"Total de amostras: {n}")

    # 1. Contador sequencial: diferenças acima de um indicam lacunas de transmissão.
    diffs = np.diff(contador)
    # Localiza o índice imediatamente anterior a cada salto de contador.
    saltos = np.where(diffs > 1)[0]
    # Conta eventos de salto, distintos da quantidade total de amostras perdidas.
    n_saltos = len(saltos)
    # Soma o tamanho de cada lacuna descontando o contador consecutivo esperado.
    total_perdidas = int(np.sum(diffs[saltos] - 1)) if n_saltos > 0 else 0
    print(f"\n1. CONTADOR:")
    print(f"   Início: {contador[0]:.0f} | Fim: {contador[-1]:.0f}")
    print(f"   Saltos: {n_saltos} | Amostras perdidas: {total_perdidas}")
    if n_saltos > 0:
        for idx in saltos[:5]:
            print(f"   - Salto {idx}: {contador[idx]:.0f} -> {contador[idx+1]:.0f} (perdidas: {int(diffs[idx]-1)})")
        if n_saltos > 5:
            print(f"   ... e mais {n_saltos-5} saltos")

    # 2. Taxa de amostragem (Hz): usa o relógio do Arduino, não a recepção no PC.
    dt_arduino = np.diff(t_arduino) / 1_000_000  # segundos
    # Descarta intervalos não positivos, que não têm frequência física definida.
    dt_arduino = dt_arduino[dt_arduino > 0]
    # Converte cada intervalo positivo em frequência instantânea.
    hz_inst = 1.0 / dt_arduino
    # Calcula a taxa da sessão inteira usando primeira/última amostra e n - 1 intervalos.
    hz_medio = (n - 1) / ((t_arduino[-1] - t_arduino[0]) / 1_000_000)
    print(f"\n2. TAXA (Hz):")
    print(f"   Média: {hz_medio:.2f}")
    print(f"   Inst. média: {np.mean(hz_inst):.2f} | std: {np.std(hz_inst):.2f}")
    print(f"   Min: {np.min(hz_inst):.2f} | Max: {np.max(hz_inst):.2f}")

    # 3. Valores dos sensores: as faixas refletem as escalas atuais do firmware.
    nomes = ['ax', 'ay', 'az', 'gx', 'gy', 'gz']
    # Define os limites físicos aceitos para aceleração em g e giro em graus por segundo.
    limites = {
        'ax': (-16, 16), 'ay': (-16, 16), 'az': (-16, 16),  # g (±16g)
        'gx': (-2000, 2000), 'gy': (-2000, 2000), 'gz': (-2000, 2000)  # °/s (±2000)
    }
    print(f"\n3. SENSORES (range físico):")
    # Resume extremos e dispersão de cada eixo e contabiliza violações da faixa configurada.
    for i, nome in enumerate(nomes):
        col = sensores[:, i]
        mn, mx = np.min(col), np.max(col)
        media, std = np.mean(col), np.std(col)
        rms = np.sqrt(np.mean(col**2))
        lim_min, lim_max = limites[nome]
        fora = np.sum((col < lim_min) | (col > lim_max))
        status = "⚠ FORA" if fora > 0 else "OK"
        print(f"   {nome:3s}: [{mn:8.3f}, {mx:8.3f}] media={media:7.3f} std={std:7.3f} rms={rms:7.3f} {status}")

    # 4. Tempo PC: o relógio de recepção não deve retroceder dentro de uma sessão.
    dt_pc = np.diff(t_pc)
    # Conta apenas deltas negativos; intervalos zero não são classificados como regressão.
    negativos = np.sum(dt_pc < 0)
    print(f"\n4. TEMPO PC:")
    print(f"   Deltas negativos: {negativos} (esperado 0)")
    print(f"   Duração total: {t_pc[-1] - t_pc[0]:.1f}s")

    # 5. NaN/Inf: qualquer elemento não finito inviabiliza métricas confiáveis.
    nan_count = np.sum(~np.isfinite(arr))
    print(f"\n5. VALORES INVÁLIDOS:")
    print(f"   NaN/Inf: {nan_count} (esperado 0)")

    # Combina continuidade, monotonicidade, finitude e faixas para o resultado final.
    ok = (n_saltos == 0 and negativos == 0 and nan_count == 0 and
          all(np.sum((sensores[:, i] < limites[n][0]) | (sensores[:, i] > limites[n][1])) == 0
              for i, n in enumerate(nomes)))

    print(f"\n{'='*60}")
    print(f"RESULTADO: {'PASSOU' if ok else 'FALHOU'}")
    print(f"{'='*60}\n")

    # Retorna números nativos para permitir serialização ou uso por outros scripts.
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
    # Limita a busca ao padrão de nome produzido pelo gravador do projeto.
    padrao = os.path.join(diretorio, "dados_aceleracao_giro-*.csv")
    # Expande o padrão sem abrir nem modificar os arquivos candidatos.
    arquivos = glob.glob(padrao)
    # Sinaliza ao chamador que não existe captura a testar.
    if not arquivos:
        return None
    # Seleciona o arquivo com a modificação mais recente para o modo sem argumento.
    return max(arquivos, key=os.path.getmtime)


def main():
    # Um argumento seleciona explicitamente a captura; sem ele usa-se a mais recente.
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

    # Executa a validação completa após resolver o caminho de entrada.
    resultado = testar_arquivo(arquivo)

    # Erros estruturais impedem o relatório de sucesso e retornam erro ao shell.
    if "erro" in resultado:
        print(f"ERRO: {resultado['erro']}")
        sys.exit(1)

    # Retorna zero somente se todas as verificações de consistência passarem.
    sys.exit(0 if resultado["ok"] else 1)


if __name__ == "__main__":
    # Executa a interface de linha de comando somente na execução direta.
    main()
