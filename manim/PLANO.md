# Sensor de Vibração — narrativa e implementação

**Objetivo:** apresentar a vibração do pórtico e o registro experimental com Manim, exportando os vídeos nesta pasta.

**Arquitetura:** `main.py` contém uma cena contínua com seis passagens; `visuals.py` reúne tipografia, desenho de hardware e gráficos; `signal_data.py` lê os ensaios e calcula estatísticas; `render.py` seleciona formato, qualidade e dados. Assets gerados são vetores locais. O ambiente de renderização é isolado em `.venv/`.

**Tecnologias:** Python 3.11, Manim Community 0.20.1/Cairo, NumPy; fórmulas vetoriais desenhadas sem exigir instalação de LaTeX.

## Evidência e limites

- Firmware: `../arduino/mpu-6050/mpu-6050.ino`; sensor MPU6050, I²C, Arduino e USB/serial.
- Python: leitura validada, buffer circular, fila de gravação, CSV, gráficos em tempo real, média/desvio/RMS e análise Plotly.
- Modelo documentado em `../DOCS/arquitetura/teoria_vibração.md`: massa–mola–amortecedor, `m x'' + c x' + kx = F_ext(t)`. Ainda não há identificação de parâmetros nem validação do modelo a partir do CSV.
- Medição padrão: `../dados/dados_aceleracao_giro-2026-09-07_16-57-08.csv`, eixo `az`, intervalo 8–18 s desde a primeira amostra. Curva com valores brutos em g, sem filtro nem remoção de gravidade.
- A estrutura inicial é ilustrativa: o ensaio não identifica a montagem. Solução matemática usa parâmetros ilustrativos e não é apresentada como ajuste.
- Comparação usa aceleração nos dois lados. Sem métricas de ajuste, percentuais de erro, diagnóstico de ruído ou afirmações de concordância experimental.

## Storyboard e transições

1. **Vibração:** fundo escuro, estrutura estilizada, impulso e rastro. Aproximação da câmera revela o sensor.
2. **Medição:** o sensor acompanha a estrutura; eixos e pulsos revelam aceleração específica e giro. Os pulsos percorrem I²C → Arduino → USB/serial.
3. **Dados:** o cabo se estende como eixo temporal; pulsos viram pontos reais e a curva cresce amostra a amostra. Tempo deriva de `micros()`.
4. **Python:** a curva alimenta o buffer e o CSV, com referência aos módulos reais. Estatísticas calculadas no recorte aparecem associadas ao sinal.
5. **Idealização:** pórtico esquemático com a equação `M v''(t) + ε v'(t) + K v(t) = P(t)` e explicação dos termos; sem curva simulada ou comparação com os dados.
6. **Retorno:** o sensor e o nome do projeto concluem a narrativa.

## Execução e verificação

- [ ] Implementar e testar leitura de dados, seleção de intervalo e consistência da solução com a EDO.
- [ ] Criar elementos vetoriais e primeiras passagens; renderizar uma cena curta antes de completar a narrativa.
- [ ] Completar as seis passagens em composição adaptada a 16:9 e 9:16.
- [ ] Renderizar previews, extrair quadros de momentos-chave e corrigir cortes/sobreposições.
- [ ] Renderizar MP4 final horizontal e vertical; verificar codec, dimensões, duração e reprodução/decodificação.
- [ ] Registrar comandos, proveniência e limites no README; manter o restante do projeto intacto.
