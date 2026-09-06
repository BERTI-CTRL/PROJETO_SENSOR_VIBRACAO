# `sensor/gravador.py`

`GravadorCSV` é a camada de escrita do histórico de uma sessão. O nome do arquivo Python é histórico e genérico, mas sua única responsabilidade atual é produzir o CSV consumido por [[plotar_csv]] e [[testar_dados]]. A thread [[gravador_worker]] é sua única usuária no fluxo normal.

## Destino e cabeçalho

O construtor recebe `arquivo="dados/dados_aceleracao_giro.csv"`, porém esse parâmetro **não é usado** para decidir o caminho. O destino efetivo é sempre `dados/dados_aceleracao_giro-YYYY-MM-DD_HH-MM-SS.csv`, criado a partir de `datetime.now()`. Abrir em modo `"a"` preserva conteúdo se o caminho já existir; o cabeçalho é escrito somente quando ele não existia.

Essa discrepância deve ser tratada como consideração de uma modificação futura: usar de fato `arquivo` exigiria definir se ele é caminho final, prefixo ou diretório e manter compatibilidade com os chamadores. Esta tarefa apenas a documenta, sem alterar a interface ou o comportamento.

O escritor `csv.writer` usa o delimitador padrão, vírgula, e o cabeçalho estável de nove posições descrito em [[esquema-csv]]. `newline=""` evita linhas em branco extras no Windows e `encoding="utf-8"` define a codificação do arquivo.

## Buffer e fechamento

`salvar(linha)` primeiro acrescenta a linha recebida ao `buffer` em memória. Quando `len(buffer) >= tamanho_buffer`, `writerows` grava o lote e `clear` libera a lista para reutilização. Portanto, a gravação não é uma operação de disco para cada amostra: a fila e o buffer desacoplam a aquisição descrita em [[coletor]] do I/O.

`fechar()` grava também o lote parcial que não atingiu `tamanho_buffer`, limpa o buffer e fecha o arquivo. [[gravador_worker]] chama esse método no seu `finally`; no encerramento normal coordenado por [[manager]], isso ocorre depois de consumir a sentinela `None`.

## Interface

```python
GravadorCSV(arquivo="dados/dados_aceleracao_giro.csv", tamanho_buffer=10000)
salvar(linha)
fechar()
```

`linha` deve manter a ordem de nove valores produzida por [[coletor]]. A classe não é compartilhada entre threads: o acesso ao arquivo pertence ao único [[gravador_worker]].
