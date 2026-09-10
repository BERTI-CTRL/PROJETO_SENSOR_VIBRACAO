"""Dados da captura e hipótese mecânica usados exclusivamente pela animação.

O CSV permanece em ``dados/`` na raiz. A leitura não altera os valores em g,
não filtra, não reamostra e não estima parâmetros a partir do experimento.
"""

from dataclasses import dataclass
from pathlib import Path
import csv

import numpy as np


DEFAULT_CSV = (
    Path(__file__).resolve().parent.parent
    / "dados"
    / "dados_aceleracao_giro-2026-09-07_16-57-08.csv"
)
GRAVITY = 9.80665  # m/s² por g; usado apenas ao comparar unidades no vídeo.


@dataclass(frozen=True)
class SignalData:
    """Recorte de aceleração; ``t`` começa no primeiro ponto selecionado.

    ``start_seconds`` é o instante desse ponto em relação ao início da captura.
    As estatísticas descrevem os valores brutos, inclusive seu nível médio.
    """

    t: np.ndarray
    values: np.ndarray
    axis: str
    source: Path | None
    source_label: str
    synthetic: bool
    start_seconds: float

    @property
    def sample_count(self) -> int:
        return int(self.values.size)

    @property
    def rms(self) -> float:
        return float(np.sqrt(np.mean(self.values**2)))

    @property
    def mean(self) -> float:
        return float(np.mean(self.values))

    @property
    def std(self) -> float:
        return float(np.std(self.values, ddof=0))


def load_signal(
    csv_path: str | Path | None = None,
    axis: str = "az",
    start: float = 8.0,
    duration: float = 10.0,
) -> SignalData:
    """Leia um recorte inclusivo ``[start, start + duration]`` de um CSV.

    O relógio físico é ``tempo_arduino_us``. Todos os pontos do intervalo são
    mantidos. Arquivo explícito ausente/inválido gera erro; somente a ausência
    do arquivo padrão permite a demonstração sintética identificada.
    """
    if axis not in ("ax", "ay", "az"):
        raise ValueError("Escolha um eixo de aceleração: ax, ay ou az.")
    if not np.isfinite(start) or start < 0:
        raise ValueError("start deve ser finito e não negativo.")
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("duration deve ser finita e positiva.")

    path = Path(csv_path).expanduser().resolve() if csv_path is not None else DEFAULT_CSV
    if csv_path is None and not path.exists():
        return _synthetic_signal(axis, float(start), float(duration))

    timestamps, values = [], []
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"tempo_arduino_us", axis}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV precisa das colunas tempo_arduino_us e {axis}.")
        for line, row in enumerate(reader, start=2):
            try:
                timestamps.append(float(row["tempo_arduino_us"]))
                values.append(float(row[axis]))
            except (ValueError, TypeError) as error:
                raise ValueError(f"Valor numérico inválido na linha {line} de {path.name}.") from error

    time_us = np.asarray(timestamps, dtype=float)
    acceleration_g = np.asarray(values, dtype=float)
    if time_us.size < 2:
        raise ValueError("O CSV deve conter pelo menos duas amostras.")
    if not np.all(np.isfinite(time_us)) or not np.all(np.isfinite(acceleration_g)):
        raise ValueError("O CSV contém tempo ou aceleração não finitos.")
    if not np.all(np.diff(time_us) > 0):
        raise ValueError("O tempo do Arduino deve ser estritamente crescente.")

    session_t = (time_us - time_us[0]) / 1_000_000.0
    selected = (session_t >= start) & (session_t <= start + duration)
    if np.count_nonzero(selected) < 2:
        raise ValueError("O recorte escolhido deve conter pelo menos duas amostras.")
    crop_t = session_t[selected]
    crop_values = acceleration_g[selected]
    first_time = float(crop_t[0])
    crop_t = crop_t - first_time
    crop_t.setflags(write=False)
    crop_values.setflags(write=False)

    date = path.stem.removeprefix("dados_aceleracao_giro-")[:10]
    label = f"CSV REAL · {date[8:10]}/{date[5:7]}/{date[:4]}" if len(date) == 10 and date[4] == "-" else "CSV REAL"
    return SignalData(crop_t, crop_values, axis, path, label, False, first_time)


def illustrative_response(
    t,
    mass: float = 1.0,
    damping: float = 0.7,
    stiffness: float = 16.0,
    amplitude: float = 0.018,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solução livre ilustrativa subamortecida; retorna x, v e a em SI.

    x(t) = A exp(-α t) cos(ωd t), α=c/(2m), ωd=sqrt(k/m-α²).
    Portanto x(0)=A e v(0)=-αA. Os parâmetros são escolhidos para divulgação,
    nunca ajustados ao CSV. Para comparar com g, use ``a / GRAVITY``.
    """
    parameters = np.asarray([mass, damping, stiffness, amplitude], dtype=float)
    if not np.all(np.isfinite(parameters)):
        raise ValueError("Os parâmetros do modelo devem ser finitos.")
    if mass <= 0 or stiffness <= 0 or damping < 0:
        raise ValueError("Massa e rigidez devem ser positivas; amortecimento não negativo.")
    alpha = damping / (2 * mass)
    wd_squared = stiffness / mass - alpha**2
    if wd_squared <= 0:
        raise ValueError("Esta solução requer regime subamortecido: c² < 4mk.")
    t = np.asarray(t, dtype=float)
    if not np.all(np.isfinite(t)):
        raise ValueError("Os instantes da solução devem ser finitos.")
    wd = np.sqrt(wd_squared)
    envelope = amplitude * np.exp(-alpha * t)
    sine, cosine = np.sin(wd * t), np.cos(wd * t)
    displacement = envelope * cosine
    velocity = envelope * (-alpha * cosine - wd * sine)
    acceleration = envelope * ((alpha**2 - wd_squared) * cosine + 2 * alpha * wd * sine)
    return displacement, velocity, acceleration


def _synthetic_signal(axis: str, start: float, duration: float) -> SignalData:
    """Demonstração determinística, sem se passar por captura do MPU6050."""
    t = np.linspace(0.0, duration, max(2, int(duration * 220) + 1))
    rng = np.random.default_rng(6050)
    values = 0.11 * np.exp(-0.3 * t) * np.sin(2 * np.pi * 2.2 * t)
    values += 0.007 * rng.standard_normal(t.size)
    t.setflags(write=False)
    values.setflags(write=False)
    return SignalData(t, values, axis, None, "DADOS SINTÉTICOS", True, start)
