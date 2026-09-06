"""Meteor Dash: jogo de nave controlado por inclinação do MPU6050."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from .config import (
    CONTROL_DEAD_ZONE_G,
    CONTROL_FULL_TILT_G,
    CONTROL_SMOOTHING,
    FPS,
    SERIAL_BAUDRATE,
    SERIAL_PORT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .controller import TiltController
from .entities import Meteor, Ship, circle_hits_rect
from .sensor_input import SensorReader, SensorSample


BACKGROUND = (7, 12, 33)
CYAN = (72, 222, 255)
PINK = (255, 87, 184)
TEXT = (230, 240, 255)
MUTED = (150, 171, 204)
ORANGE = (255, 150, 74)


@dataclass
class Particle:
    x: float
    y: float
    life: float
    size: float
    color: tuple[int, int, int]


def combine_direction(sensor_direction: float, keyboard_direction: int) -> float:
    """Combina os dois controles em um único valor seguro para a nave."""
    return max(-1.0, min(1.0, sensor_direction + keyboard_direction))


def add_new_calibration_sample(
    samples: list[float],
    last_counter: int | None,
    sample: SensorSample | None,
) -> int | None:
    """Inclui somente uma amostra recebida após a referência de calibração."""
    if sample is None or (last_counter is not None and sample.counter <= last_counter):
        return last_counter

    samples.append(sample.ay)
    return sample.counter


def _new_ship() -> Ship:
    return Ship(
        x=(WINDOW_WIDTH - 64) / 2,
        y=WINDOW_HEIGHT - 112,
        width=64,
        height=54,
        speed=570,
    )


def _make_stars() -> list[tuple[int, int, int, float]]:
    return [
        (
            random.randrange(WINDOW_WIDTH),
            random.randrange(80, WINDOW_HEIGHT - 48),
            random.choice((1, 1, 2, 2, 3)),
            random.uniform(18, 65),
        )
        for _ in range(110)
    ]


def _draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    center: tuple[int, int],
) -> None:
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=center))


def _draw_background(surface: pygame.Surface, stars: list[tuple[int, int, int, float]], elapsed: float) -> None:
    for y in range(0, WINDOW_HEIGHT, 32):
        intensity = min(36, 15 + y // 24)
        pygame.draw.rect(surface, (5, 9, intensity), (0, y, WINDOW_WIDTH, 32))

    for x, y, size, speed in stars:
        star_y = (y + elapsed * speed) % WINDOW_HEIGHT
        alpha = 155 + int(70 * math.sin(elapsed * speed / 30 + x))
        pygame.draw.circle(surface, (alpha, alpha, 255), (x, int(star_y)), size)

    pygame.draw.circle(surface, (23, 29, 72), (WINDOW_WIDTH - 90, 112), 100)
    pygame.draw.circle(surface, (42, 48, 104), (WINDOW_WIDTH - 112, 89), 68)


def _draw_ship(surface: pygame.Surface, ship: Ship, direction: float) -> None:
    x = int(ship.x)
    y = int(ship.y)
    tilt = int(direction * 8)
    flame_length = 16 + int(abs(direction) * 7)
    pygame.draw.polygon(
        surface,
        (32, 63, 116),
        [(x + 8, y + 44), (x + 25, y + 20 + tilt), (x + 32, y + 50), (x + 39, y + 20 + tilt), (x + 56, y + 44)],
    )
    pygame.draw.polygon(surface, CYAN, [(x + 32, y + 1 + tilt), (x + 57, y + 48), (x + 32, y + 41), (x + 7, y + 48)])
    pygame.draw.polygon(surface, (220, 248, 255), [(x + 32, y + 10 + tilt), (x + 41, y + 31), (x + 32, y + 27), (x + 23, y + 31)])
    pygame.draw.rect(surface, PINK, (x + 10, y + 38, 12, 6), border_radius=3)
    pygame.draw.rect(surface, PINK, (x + 42, y + 38, 12, 6), border_radius=3)
    pygame.draw.polygon(surface, ORANGE, [(x + 27, y + 46), (x + 37, y + 46), (x + 32, y + 46 + flame_length)])


def _draw_meteor(surface: pygame.Surface, meteor: Meteor) -> None:
    x, y, radius = int(meteor.x), int(meteor.y), int(meteor.radius)
    pygame.draw.circle(surface, (73, 43, 68), (x + 4, y + 5), radius)
    pygame.draw.circle(surface, (186, 83, 83), (x, y), radius)
    pygame.draw.circle(surface, (247, 133, 84), (x - radius // 3, y - radius // 3), max(3, radius // 3))
    angle = math.radians(meteor.spin)
    for distance, crater_radius in ((0.48, 3), (0.7, 2)):
        crater_x = x + math.cos(angle + distance * 5) * radius * distance
        crater_y = y + math.sin(angle + distance * 5) * radius * distance
        pygame.draw.circle(surface, (121, 55, 61), (int(crater_x), int(crater_y)), crater_radius)


def _draw_particles(surface: pygame.Surface, particles: list[Particle]) -> None:
    for particle in particles:
        alpha = max(0, min(255, int(255 * particle.life)))
        color = tuple(channel * alpha // 255 for channel in particle.color)
        pygame.draw.circle(surface, color, (int(particle.x), int(particle.y)), max(1, int(particle.size * particle.life)))


def _status_text(reader: SensorReader) -> tuple[str, tuple[int, int, int]]:
    if reader.is_connected:
        return reader.status, (120, 255, 177)
    return reader.status, (255, 184, 104)


def run() -> None:
    """Abre e executa uma partida até o usuário fechar a janela."""
    pygame.init()
    pygame.display.set_caption("Meteor Dash — controle por MPU6050")
    surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 52)
    hud_font = pygame.font.Font(None, 30)
    small_font = pygame.font.Font(None, 22)

    reader = SensorReader(SERIAL_PORT, SERIAL_BAUDRATE)
    controller = TiltController(CONTROL_DEAD_ZONE_G, CONTROL_FULL_TILT_G, CONTROL_SMOOTHING)
    stars = _make_stars()
    ship = _new_ship()
    meteors: list[Meteor] = []
    particles: list[Particle] = []
    elapsed = 0.0
    score = 0.0
    record = 0.0
    spawn_elapsed = 0.0
    state = "calibration"
    calibration_started_at: float | None = None
    calibration_samples: list[float] = []
    calibration_last_counter: int | None = None
    message = "Pressione C e deixe o sensor parado para calibrar."
    running = True

    reader.start()
    try:
        while running:
            dt = min(clock.tick(FPS) / 1000, 0.05)
            elapsed += dt
            sample = reader.latest_sample() if reader.is_connected else None

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_i:
                        inverted = controller.toggle_inversion()
                        message = "Direção invertida." if inverted else "Direção normal restaurada."
                    elif event.key == pygame.K_c and state == "calibration":
                        if reader.is_connected:
                            calibration_started_at = elapsed
                            calibration_samples.clear()
                            calibration_last_counter = sample.counter if sample is not None else None
                            message = "Calibrando: mantenha o conjunto parado..."
                        else:
                            controller.calibrate([0.0])
                            state = "playing"
                            message = "Modo teclado ativado. Desvie dos meteoros!"
                    elif event.key == pygame.K_r:
                        ship = _new_ship()
                        meteors.clear()
                        particles.clear()
                        score = 0.0
                        spawn_elapsed = 0.0
                        calibration_started_at = None
                        calibration_samples.clear()
                        calibration_last_counter = None
                        state = "calibration"
                        message = "Nova partida. Pressione C para calibrar."

            if state == "calibration" and calibration_started_at is not None:
                calibration_last_counter = add_new_calibration_sample(
                    calibration_samples,
                    calibration_last_counter,
                    sample,
                )
                if elapsed - calibration_started_at >= 1.5:
                    if calibration_samples:
                        controller.calibrate(calibration_samples)
                        state = "playing"
                        message = "Calibrado! Desvie dos meteoros."
                    else:
                        calibration_started_at = None
                        message = "Nenhuma amostra chegou. Aguarde o sensor e pressione C novamente."

            keys = pygame.key.get_pressed()
            keyboard_direction = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            sensor_direction = controller.update(sample.ay if sample is not None else None)
            direction = combine_direction(sensor_direction, keyboard_direction)

            if state == "playing":
                ship.move(direction, dt, WINDOW_WIDTH)
                score += dt * 10
                spawn_elapsed += dt
                spawn_interval = max(0.26, 0.80 - score / 680)
                if spawn_elapsed >= spawn_interval:
                    spawn_elapsed = 0.0
                    radius = random.uniform(17, 37)
                    meteors.append(
                        Meteor(
                            x=random.uniform(radius, WINDOW_WIDTH - radius),
                            y=-radius,
                            radius=radius,
                            speed=210 + min(260, score * 0.75),
                        )
                    )

                survivors: list[Meteor] = []
                for meteor in meteors:
                    meteor.move(dt)
                    if circle_hits_rect(meteor.x, meteor.y, meteor.radius, ship.rect):
                        state = "game_over"
                        record = max(record, score)
                        message = "Impacto! Pressione R para tentar de novo."
                        for _ in range(45):
                            particles.append(
                                Particle(
                                    x=ship.center_x + random.uniform(-26, 26),
                                    y=ship.y + random.uniform(4, ship.height),
                                    life=random.uniform(0.45, 1.0),
                                    size=random.uniform(3, 8),
                                    color=random.choice((CYAN, PINK, ORANGE)),
                                )
                            )
                    elif meteor.y - meteor.radius > WINDOW_HEIGHT:
                        score += 8
                    else:
                        survivors.append(meteor)
                meteors = survivors

                if random.random() < 0.65:
                    particles.append(
                        Particle(
                            x=ship.center_x + random.uniform(-4, 4),
                            y=ship.y + ship.height,
                            life=random.uniform(0.22, 0.45),
                            size=random.uniform(2, 5),
                            color=random.choice((ORANGE, PINK)),
                        )
                    )

            for particle in particles:
                particle.y += 100 * dt
                particle.life -= dt * 1.9
            particles = [particle for particle in particles if particle.life > 0]

            _draw_background(surface, stars, elapsed)
            for meteor in meteors:
                _draw_meteor(surface, meteor)
            _draw_particles(surface, particles)
            if state != "game_over":
                _draw_ship(surface, ship, direction)

            pygame.draw.rect(surface, (9, 16, 42), (0, 0, WINDOW_WIDTH, 68))
            _draw_text(surface, hud_font, f"PONTOS  {int(score):05d}", TEXT, (126, 25))
            _draw_text(surface, hud_font, f"RECORDE  {int(record):05d}", MUTED, (WINDOW_WIDTH - 135, 25))

            if state == "calibration":
                _draw_text(surface, title_font, "METEOR DASH", CYAN, (WINDOW_WIDTH // 2, 160))
                _draw_text(surface, hud_font, "CONTROLE SUA NAVE COM O MPU6050", TEXT, (WINDOW_WIDTH // 2, 205))
                if calibration_started_at is not None:
                    progress = min(1.0, (elapsed - calibration_started_at) / 1.5)
                    pygame.draw.rect(surface, (25, 39, 74), (250, 255, 460, 18), border_radius=9)
                    pygame.draw.rect(surface, PINK, (250, 255, int(460 * progress), 18), border_radius=9)
                _draw_text(surface, hud_font, message, PINK, (WINDOW_WIDTH // 2, 310))
                _draw_text(surface, small_font, "C = calibrar  •  I = inverter direção", MUTED, (WINDOW_WIDTH // 2, 352))
                _draw_text(surface, small_font, "Setas ← → sempre funcionam como controle reserva", MUTED, (WINDOW_WIDTH // 2, 382))
            elif state == "game_over":
                _draw_text(surface, title_font, "NAVE DESTRUÍDA", PINK, (WINDOW_WIDTH // 2, 245))
                _draw_text(surface, hud_font, message, TEXT, (WINDOW_WIDTH // 2, 292))
                _draw_text(surface, small_font, "R = nova partida  •  Esc = sair", MUTED, (WINDOW_WIDTH // 2, 332))

            status, status_color = _status_text(reader)
            pygame.draw.rect(surface, (9, 16, 42), (0, WINDOW_HEIGHT - 46, WINDOW_WIDTH, 46))
            _draw_text(surface, small_font, status, status_color, (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30))
            pygame.display.flip()
    finally:
        reader.stop()
        pygame.quit()


if __name__ == "__main__":
    run()
