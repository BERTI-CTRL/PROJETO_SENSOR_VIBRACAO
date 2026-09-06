"""Entidades e geometria independentes da biblioteca gráfica."""

from dataclasses import dataclass


def circle_hits_rect(
    circle_x: float,
    circle_y: float,
    radius: float,
    rect: tuple[float, float, float, float],
) -> bool:
    """Informa se um círculo toca ou entra no retângulo informado."""
    x, y, width, height = rect
    nearest_x = max(x, min(circle_x, x + width))
    nearest_y = max(y, min(circle_y, y + height))
    return (circle_x - nearest_x) ** 2 + (circle_y - nearest_y) ** 2 <= radius**2


@dataclass
class Ship:
    x: float
    y: float
    width: int
    height: int
    speed: float

    @property
    def rect(self) -> tuple[float, float, float, float]:
        return (self.x, self.y, self.width, self.height)

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    def move(self, direction: float, dt: float, screen_width: int) -> None:
        """Move horizontalmente sem permitir que a nave saia da tela."""
        self.x += direction * self.speed * dt
        self.x = max(0, min(self.x, screen_width - self.width))


@dataclass
class Meteor:
    x: float
    y: float
    radius: float
    speed: float
    spin: float = 0.0

    def move(self, dt: float) -> None:
        """Desce o meteoro e avança a rotação usada apenas no desenho."""
        self.y += self.speed * dt
        self.spin = (self.spin + dt * 150) % 360
