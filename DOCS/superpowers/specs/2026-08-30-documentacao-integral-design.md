# Documentação integral do projeto - desenho

## Objetivo

Atualizar a documentação para o estado atual do working tree e permitir que uma pessoa sem conhecimento prévio compreenda, execute, diagnostique e modifique o projeto com segurança. A entrega cobre os scripts Python, o firmware Arduino, a configuração do projeto, o protocolo de dados, os artefatos gerados e os fluxos visuais relevantes.

## Fonte de verdade

- O código presente no working tree em 30 de agosto de 2026 é a fonte primária, inclusive as alterações locais ainda não commitadas em `sensor/coletor.py` e `sensor/serial_reader.py`.
- Os PDFs locais da InvenSense são a fonte primária para registradores, escalas, sensibilidades, sequência de leitura e considerações do MPU-6050.
- O histórico em `ERROS/` serve como contexto de decisões e regressões já encontradas; ele não prevalece sobre o código atual.
- A tarefa não altera comportamento, interfaces, constantes ou algoritmos. Inconsistências encontradas serão documentadas como alertas.

## Estrutura da documentação

### Entradas principais

- `README.md` continuará sendo a introdução prática para instalação, hardware e primeira execução.
- `DOCS/INDEX.md` será o índice completo da base de conhecimento.
- `DOCS/ARQUITETURA.md` descreverá os componentes e o fluxo de ponta a ponta.
- Uma página de estrutura do repositório explicará diretórios, arquivos de configuração, PDFs, CSVs e arquivos gerados.

### Referência dos scripts

Cada arquivo `.py` e `.ino` terá uma página própria ou uma referência inequivocamente identificada. Cada página explicará:

1. responsabilidade e momento de uso;
2. consumidores e dependências;
3. entradas, saídas e efeitos colaterais;
4. fluxo interno por função ou método;
5. concorrência e ciclo de vida, quando aplicável;
6. erros, limites e decisões importantes;
7. pontos seguros de modificação;
8. formas de execução e verificação;
9. relações com outros módulos usando wikilinks.

Notas com nomes ambíguos serão diferenciadas. Em especial, o teste interativo de `sensor/teste_manager.py` não será confundido com o analisador de CSV `dados/testar_dados.py`.

### Comentários no código

Todos os scripts receberão comentários didáticos no próprio arquivo. Cada instrução significativa será explicada antes ou ao lado da linha correspondente, incluindo imports, constantes, criação de objetos, decisões condicionais, laços, cálculos, operações de I/O, sincronização, chamadas entre módulos e pontos de entrada.

Não serão adicionados comentários vazios para:

- linhas em branco;
- delimitadores e fechamentos puramente sintáticos;
- repetições cujo significado já esteja declarado imediatamente antes;
- código legado já desativado, que será identificado como histórico quando mantido.

Os comentários no código usarão caminhos e nomes de símbolos, pois wikilinks não são interpretados por Python ou Arduino. Wikilinks serão usados em todo o texto Markdown sempre que houver uma relação entre notas.

### Tópicos transversais

A base terá documentação específica para:

- protocolo serial de oito campos enviado pelo firmware;
- esquema CSV de nove colunas, unidades e origem de cada campo;
- tempo do Arduino versus relógio monotônico do computador;
- contador, detecção de saltos e perda de amostras;
- buffer circular, snapshots e wrap-around;
- threads, fila assíncrona, sentinela e encerramento;
- interface PyQt/PyQtGraph e seus dois timers;
- análise posterior com Plotly;
- validação dos CSVs e calibração por referência RMS;
- dependências declaradas em `pyproject.toml`;
- diagnóstico e guia de modificação segura.

### Nota da InvenSense

`DOCS/invensense-pontos-utilizados.md` será uma síntese conceitual apenas das partes dos documentos da InvenSense efetivamente usadas ou necessárias para interpretar o projeto:

- endereço I2C e papel de `AD0`;
- gerenciamento de energia e registrador `PWR_MGMT_1` (`0x6B`);
- configuração de fundo de escala do acelerômetro em `ACCEL_CONFIG` (`0x1C`);
- configuração de fundo de escala do giroscópio em `GYRO_CONFIG` (`0x1B`);
- sensibilidades correspondentes a ±16 g e ±2000 graus/s;
- mapa contínuo de registradores de `ACCEL_XOUT_H` (`0x3B`) a `GYRO_ZOUT_L` (`0x48`);
- composição de valores assinados de 16 bits e ordem high byte/low byte;
- leitura em bloco de 14 bytes e presença da temperatura no bloco;
- taxa de amostragem, `CONFIG`, DLPF e `SMPLRT_DIV` como considerações não configuradas explicitamente pelo firmware atual;
- limitações de medição e implicações para calibração e interpretação.

A nota explicará a relação de cada conceito com `[[arduino_mpu6050]]`, `[[protocolo-serial]]`, `[[esquema-csv]]` e `[[calibrar_vibracao]]`, sem tentar resumir capítulos que não influenciam o projeto.

## Wikilinks

- As relações serão escritas no corpo do texto, e não somente em seções finais de referências.
- O formato preferencial será `[[nome-da-nota]]` ou `[[nome-da-nota|texto legível]]`.
- Cada alvo deverá corresponder a um nome de nota único na base.
- O índice listará todas as notas e todos os canvases.
- Documentos históricos em `ERROS/` também serão ligados às páginas técnicas atuais.

## Canvases

Será criada a pasta `CANVASES/` com arquivos no formato JSON Canvas do Obsidian:

1. `visao-geral-projeto.canvas`: hardware, firmware, aquisição, buffer, gravação, interface e análise;
2. `fluxo-aquisicao-dados.canvas`: transformação de registradores do MPU-6050 até os campos exibidos e salvos;
3. `threads-e-encerramento.canvas`: thread da interface, thread serial, fila, thread de gravação e protocolo de parada;
4. `analise-e-calibracao.canvas`: CSV, teste de consistência, Plotly, calibração RMS e resultado JSON.

Os nós de arquivo apontarão para notas Markdown existentes. As arestas terão rótulos objetivos, direção coerente e cores usadas apenas para distinguir hardware, aquisição, persistência, interface e pós-processamento.

## Preservação e riscos

- Alterações locais do usuário não serão revertidas ou normalizadas.
- Comentários poderão aumentar bastante o tamanho dos scripts, mas não mudarão sua execução.
- Referências a baud rate e outras configurações divergentes serão descritas no contexto em que aparecem, sem escolher silenciosamente um novo valor.
- CSVs existentes não serão alterados e não receberão páginas individuais.
- PDFs originais não serão modificados.

## Verificação

1. Compilar todos os arquivos Python com `compileall`, sem executar acesso serial ou abrir a interface.
2. Validar cada `.canvas` como JSON e verificar IDs, nós, arestas e caminhos de arquivos.
3. Inventariar os `.py` e `.ino` e confirmar cobertura documental de todos eles.
4. Extrair todos os wikilinks, verificar que cada alvo possui nota ou canvas correspondente e listar links intencionalmente externos, se existirem.
5. Comparar o código antes e depois ignorando comentários e docstrings sempre que possível, além de revisar o diff, para confirmar ausência de mudança funcional.
6. Conferir as afirmações da nota InvenSense diretamente nos PDFs locais e registrar as páginas ou seções relevantes na própria nota.
7. Executar verificações sem hardware que já existam ou possam ser feitas por importação segura, sem iniciar a serial, a GUI ou o navegador.

## Critérios de conclusão

- Todo script está comentado de forma didática e possui referência documental.
- A navegação por wikilinks não possui alvos quebrados internos.
- Os quatro canvases abrem como JSON Canvas válido e representam os fluxos atuais.
- A documentação diferencia claramente aquisição em tempo real, persistência, validação, visualização e calibração.
- A síntese da InvenSense contém somente assuntos usados ou relevantes ao projeto e está fundamentada nos PDFs fornecidos.
- Nenhuma mudança funcional foi introduzida.
