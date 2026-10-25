"""Gera o QR code da apresentação somente para uma URL pública válida."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse


DESTINO = Path(__file__).resolve().parent / "assets" / "qrcode_apresentacao.png"


def validar_url(url: str) -> str:
    """Recusa endereços incompletos e o placeholder da instrução de publicação."""
    url = url.strip()
    partes = urlparse(url)
    marcadores_ficticios = ("SEU-APP", "SUA-URL-REAL", "EXAMPLE.COM", "PLACEHOLDER")
    if any(marcador in url.upper() for marcador in marcadores_ficticios) or partes.scheme not in {"http", "https"} or not partes.netloc:
        raise ValueError("Informe uma URL pública real; URLs fictícias não geram QR code.")
    return url


def gerar_qr(url: str, destino: Path = DESTINO) -> Path:
    """Gera PNG grande, com correção de erro, após validar a URL publicada."""
    url = validar_url(url)
    try:
        import qrcode
    except ImportError as erro:
        raise RuntimeError("Instale as dependências de apresentacao/requirements.txt para gerar o QR code.") from erro
    imagem = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=16, border=4)
    imagem.add_data(url)
    imagem.make(fit=True)
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagem.make_image(fill_color="#54247E", back_color="white").save(destino)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o QR code da aplicação Streamlit publicada.")
    parser.add_argument("--url", required=True, help="URL pública real da aplicação")
    args = parser.parse_args()
    print(f"QR code salvo em: {gerar_qr(args.url)}")


if __name__ == "__main__":
    main()
