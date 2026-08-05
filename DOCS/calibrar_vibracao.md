# `calibração/calibrar_vibracao.py`

**Responsabilidade:** calcular um offset e um ganho para um eixo do acelerômetro a partir de uma vibração RMS conhecida.

## Cenário correto

Use quando o MPU6050 está preso rigidamente ao mesmo corpo da referência e apenas um eixo é excitado. A referência deve informar aceleração em **g RMS**.

Não use para calibrar giroscópio, impactos sem referência RMS, sensor solto ou dados em que vários eixos foram excitados sem uma referência para cada um.

## Uso

```powershell
# Vibração conhecida de 0,50 g RMS no eixo Z; usa o último CSV.
python calibração\calibrar_vibracao.py 0.50

# Mesmo ensaio em X, com CSV escolhido e 5 s iniciais descartados.
python calibração\calibrar_vibracao.py 0.50 dados\teste.csv --eixo ax --descartar-inicio 5
```

## Cálculo

O script lê o CSV, descarta o início escolhido e calcula:

```text
offset = média do eixo
sinal de vibração = valor medido - offset
ganho = RMS conhecido / RMS medido
valor corrigido = ganho × (valor medido - offset)
```

Ele salva um JSON como `calibração/calibracao_vibracao_ax.json`. O CSV original não é alterado e os coeficientes ainda não são aplicados automaticamente ao projeto.

## Próximo passo obrigatório

Faça uma segunda captura, que não foi usada no cálculo, na mesma referência conhecida. Aplique a fórmula manualmente ou em análise posterior e confirme se o RMS corrigido se aproxima do RMS de referência. Só depois considere integrar o JSON no `sensor/coletor.py`.

## Relação com os demais scripts

```text
sensor/gravador.py → dados/teste.csv → calibrar_vibracao.py → JSON
```

No estado atual, esta é uma análise posterior. `realtime/janela.py` e `grafico/plotar_csv.py` ainda mostram os valores não corrigidos do CSV.

## Referências

- [[plotar_csv]] — inspeção visual do ensaio.
- [[coletor]] — futuro ponto de integração dos coeficientes.
- `calibração/guia_calibracao_mpu6050.md` — procedimento completo e cuidados de bancada.
