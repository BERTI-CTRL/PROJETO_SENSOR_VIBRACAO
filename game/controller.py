"""Transforma a inclinação medida no MPU6050 em direção de movimento."""

from collections.abc import Iterable


class TiltController:
    """Mantém a calibração e filtra o eixo de inclinação escolhido."""

    def __init__(self, dead_zone_g: float, full_tilt_g: float, smoothing: float) -> None:
        if full_tilt_g <= 0:
            raise ValueError("full_tilt_g precisa ser maior que zero.")
        if not 0 < smoothing <= 1:
            raise ValueError("smoothing precisa estar entre 0 e 1.")

        self.dead_zone_g = dead_zone_g
        self.full_tilt_g = full_tilt_g
        self.smoothing = smoothing
        self.neutral_ay = 0.0
        self.inverted = False
        self._filtered = 0.0

    def calibrate(self, samples: Iterable[float]) -> float:
        """Define a média da posição parada como novo ponto neutro."""
        values = list(samples)
        if not values:
            raise ValueError("A calibração precisa de ao menos uma amostra.")

        self.neutral_ay = sum(values) / len(values)
        self._filtered = 0.0
        return self.neutral_ay

    def update(self, ay: float | None) -> float:
        """Devolve direção suavizada entre -1 (esquerda) e 1 (direita)."""
        if ay is None:
            self._filtered = 0.0
            return 0.0

        deviation = ay - self.neutral_ay
        raw = 0.0 if abs(deviation) <= self.dead_zone_g else deviation / self.full_tilt_g
        raw = max(-1.0, min(1.0, raw))
        if self.inverted:
            raw = -raw

        self._filtered += self.smoothing * (raw - self._filtered)
        return self._filtered

    def toggle_inversion(self) -> bool:
        """Inverte esquerda/direita e limpa o filtro para resposta imediata."""
        self.inverted = not self.inverted
        self._filtered = 0.0
        return self.inverted
