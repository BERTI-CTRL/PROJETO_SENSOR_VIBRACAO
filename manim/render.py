"""Renderiza a narrativa em um MP4 diretamente nesta pasta.

Execute este arquivo com o Python do ambiente ``manim/.venv``. As opções
visuais e de dados são transmitidas à cena por variáveis de ambiente para
manter a linha de comando do Manim simples e reproduzível.
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import subprocess
import sys


MANIM_DIR = Path(__file__).resolve().parent


def nonnegative_seconds(value: str) -> float:
    """Aceita um instante finito, em segundos, a partir do início do CSV."""
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("informe um número de segundos") from exc
    if not math.isfinite(seconds) or seconds < 0:
        raise argparse.ArgumentTypeError("informe segundos finitos maiores ou iguais a zero")
    return seconds


def positive_seconds(value: str) -> float:
    seconds = nonnegative_seconds(value)
    if seconds == 0:
        raise argparse.ArgumentTypeError("a duração deve ser maior que zero")
    return seconds


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Renderiza Sensor de Vibração e salva o MP4 na pasta manim.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--format", choices=("horizontal", "vertical"), default="horizontal",
        help="orientação do vídeo: 16:9 ou 9:16",
    )
    parser.add_argument(
        "--quality", choices=("preview", "final"), default="final",
        help="preview: 540p/15 fps; final: 1080p/30 fps",
    )
    parser.add_argument("--csv", type=Path, help="CSV real; caminho relativo à pasta atual")
    parser.add_argument("--axis", choices=("ax", "ay", "az"), default="ay", help="eixo de aceleração")
    parser.add_argument("--start", type=nonnegative_seconds, default=0.0, help="início do recorte do CSV, em s")
    parser.add_argument("--duration", type=positive_seconds, default=15.0, help="duração do recorte do CSV, em s; não é a duração do vídeo")
    parser.add_argument("--section", type=int, choices=range(1, 7), help="renderiza somente uma das seis cenas")
    args = parser.parse_args(argv)
    if args.csv is not None:
        args.csv = args.csv.expanduser().resolve()
        if not args.csv.is_file():
            parser.error(f"CSV não encontrado: {args.csv}")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stem = f"sensor_vibracao_{args.format}"
    if args.quality == "preview":
        stem += "_preview"
    if args.section is not None:
        stem += f"_cena_{args.section}"
    output = MANIM_DIR / f"{stem}.mp4"

    width, height = (1920, 1080) if args.quality == "final" else (960, 540)
    if args.format == "vertical":
        width, height = height, width
    fps = 30 if args.quality == "final" else 15

    # Valores opcionais não devem vazar de um render anterior no mesmo terminal.
    environment = os.environ.copy()
    environment.pop("VIBRATION_CSV", None)
    environment.pop("VIBRATION_SECTION", None)
    environment.update({
        "VIBRATION_FORMAT": args.format,
        "VIBRATION_AXIS": args.axis,
        "VIBRATION_START": str(args.start),
        "VIBRATION_DURATION": str(args.duration),
        "VIBRATION_OUTPUT": stem,
    })
    if args.csv is not None:
        environment["VIBRATION_CSV"] = str(args.csv)
    if args.section is not None:
        environment["VIBRATION_SECTION"] = str(args.section)

    command = [
        sys.executable, "-m", "manim", "--renderer", "cairo",
        "--format", "mp4", "-r", f"{width},{height}", "--fps", str(fps),
        "--media_dir", str(MANIM_DIR / "media"),
        "-o", stem, "main.py", "SensorVibracao",
    ]
    print(f"Renderizando {width} x {height}, {fps} fps -> {output}", flush=True)
    try:
        result = subprocess.run(command, cwd=MANIM_DIR, env=environment, check=False)
    except KeyboardInterrupt:
        print("\nRenderização interrompida.", file=sys.stderr)
        return 130
    except OSError as exc:
        print(f"Não foi possível iniciar o Manim: {exc}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print("O Manim não concluiu a renderização. Consulte o erro acima.", file=sys.stderr)
        return result.returncode
    if not output.is_file() or output.stat().st_size == 0:
        print(f"O Manim terminou, mas o vídeo esperado não foi encontrado: {output}", file=sys.stderr)
        return 1
    print(f"\nVídeo renderizado: {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
