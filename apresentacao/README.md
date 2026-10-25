# Apresentação pública — vibração no pórtico

Aplicação Streamlit independente para o pôster do XII SIEPE. Tudo o que ela usa está nesta pasta; removê-la não afeta a aquisição, os dados originais nem as demais partes do projeto.

## Executar localmente

Com o ambiente virtual já existente ativado, entre nesta pasta e execute somente:

```powershell
streamlit run app.py
```

Ou, a partir da raiz do projeto:

```powershell
streamlit run apresentacao/app.py
```

Caso falte alguma biblioteca desta aplicação no ambiente existente, instale sem criar outro ambiente:

```powershell
python -m pip install -r requirements.txt
```

## Publicar no Streamlit Community Cloud

1. Envie o repositório ao GitHub.
2. Em `share.streamlit.io`, crie um app e escolha o arquivo de entrada `apresentacao/app.py`.
3. O `requirements.txt` ao lado do `app.py` será usado na implantação.
4. Depois de publicada, gere o QR code com a URL real:

```powershell
python apresentacao/gerar_qr.py --url "https://sua-url-real.streamlit.app"
```

O PNG será salvo em `assets/qrcode_apresentacao.png`. Opcionalmente, defina `PUBLIC_APP_URL` no ambiente publicado; se o PNG existir, ele aparece na página. Não há QR code com endereço fictício.

## Dados e limites

O manifesto inclui apenas quatro CSVs que correspondem explicitamente à tabela de ensaios: sem massa, uma, duas e três massas. O arquivo `dados_aceleracao_giro-2026-09-21_14-50-19.csv` foi deixado de fora porque não há correspondência explícita na tabela fornecida. O ensaio com três massas usa o eixo transversal `AY` e reproduz pico próximo de **2,02 Hz**.

A aplicação destaca frequências; a quantificação de amplitudes pequenas ainda requer validação. Frequência isolada não é diagnóstico de saúde estrutural.
