"""Vocabulário visual da animação: objetos vetoriais, sem assets externos/LaTeX."""

import numpy as np
from manim import (
    VGroup, VMobject, Text, RoundedRectangle, Rectangle, Circle, Dot,
    Line, DashedLine, Arrow, Axes, ValueTracker, always_redraw,
    UP, DOWN, LEFT, RIGHT, ORIGIN,
)

BG = "#080F1B"
PANEL = "#101E30"
GRID = "#203248"
WHITE = "#EDF5FA"
MUTED = "#8AA2BA"
CYAN = "#48E1E8"
AMBER = "#FFCA78"
VIOLET = "#AF9CFF"
CORAL = "#FF828E"


def text(content, size=24, color=WHITE, width=None, font="Segoe UI", weight="NORMAL"):
    """Texto com limite de largura para manter a composição nos dois formatos."""
    obj = Text(content, font=font, font_size=size, color=color, weight=weight)
    if width and obj.width > width:
        obj.scale_to_fit_width(width)
    return obj


def badge(content, color=CYAN, size=15):
    title = text(content, size, color)
    frame = RoundedRectangle(
        width=title.width + 0.40, height=title.height + 0.28,
        corner_radius=0.12, stroke_color=color, stroke_width=1,
        fill_color=BG, fill_opacity=0.94,
    ).move_to(title)
    return VGroup(frame, title)


def sensor_icon(scale=1):
    """Módulo estilizado: nenhuma pinagem elétrica fictícia é especificada."""
    board = RoundedRectangle(width=1.28, height=0.86, corner_radius=0.10,
                             color=CYAN, fill_color="#12383E", fill_opacity=1,
                             stroke_width=2)
    ic = RoundedRectangle(width=0.45, height=0.44, corner_radius=0.03,
                          color=MUTED, fill_color=BG, fill_opacity=1)
    holes = VGroup(*[Circle(radius=0.045, color=AMBER, stroke_width=1.5)
                    .move_to([x, y, 0]) for x in [-0.48, 0.48] for y in [-0.28, 0.28]])
    traces = VGroup(*[Line([x, 0, 0], [x * 1.5, 0, 0], color=CYAN, stroke_width=1)
                     for x in [-0.24, 0.24]])
    return VGroup(board, traces, ic, holes).scale(scale)


def arduino_icon(scale=1):
    board = RoundedRectangle(width=1.70, height=1.05, corner_radius=0.12,
                             color=VIOLET, fill_color="#24263F", fill_opacity=1)
    cpu = Rectangle(width=0.56, height=0.42, color=MUTED, fill_color=BG, fill_opacity=1)
    port = Rectangle(width=0.26, height=0.4, color=WHITE, fill_color=GRID, fill_opacity=1)
    port.move_to([-0.81, 0, 0])
    pins = VGroup(*[Dot([x, y, 0], radius=0.025, color=AMBER)
                    for x in np.linspace(-0.6, 0.6, 9) for y in [-0.4, 0.4]])
    return VGroup(board, cpu, port, pins).scale(scale)


def python_icon(scale=1):
    ring = Circle(radius=0.63, color=CYAN, stroke_width=1.4,
                  fill_color=PANEL, fill_opacity=1)
    letters = text("Py", 34, CYAN, font="Consolas")
    return VGroup(ring, letters).scale(scale)


def csv_icon(scale=1):
    page = RoundedRectangle(width=0.95, height=1.10, corner_radius=0.08,
                            color=AMBER, fill_color=PANEL, fill_opacity=1)
    rows = VGroup(*[Line([-0.3, y, 0], [0.3, y, 0], color=MUTED, stroke_width=1)
                    for y in [-0.25, 0, 0.25]])
    cols = VGroup(*[Line([x, -0.35, 0], [x, 0.35, 0], color=AMBER, stroke_width=1)
                    for x in [-0.11, 0.11]])
    return VGroup(page, rows, cols).scale(scale)


def spring(start, end, color=AMBER, turns=9, amplitude=0.14):
    start, end = np.array(start, dtype=float), np.array(end, dtype=float)
    delta = end - start
    normal = np.array([-delta[1], delta[0], 0]) / max(np.linalg.norm(delta), 1e-8)
    points = [start, start + 0.12 * delta]
    for i, s in enumerate(np.linspace(0.17, 0.83, turns * 2)):
        points.append(start + s * delta + normal * amplitude * (-1) ** i)
    points.extend([start + 0.88 * delta, end])
    return VMobject(stroke_color=color, stroke_width=2.5).set_points_as_corners(points)


def damper(start, end):
    """Amortecedor telescópico; corpo preso à parede, haste presa à massa."""
    start, end = np.array(start), np.array(end)
    body_center = start + np.array([1.15, 0, 0])
    body = Rectangle(width=0.85, height=0.38, color=VIOLET,
                     fill_color=BG, fill_opacity=1, stroke_width=2).move_to(body_center)
    piston_x = np.clip(end[0] - 1.05, body_center[0] - 0.32, body_center[0] + 0.32)
    return VGroup(
        Line(start, body_center - [0.42, 0, 0], color=VIOLET, stroke_width=2), body,
        Line([piston_x, start[1] - 0.14, 0], [piston_x, start[1] + 0.14, 0], color=VIOLET),
        Line([piston_x, start[1], 0], end, color=VIOLET, stroke_width=2),
    )


def mechanical(q: ValueTracker):
    wall = Line([-2.9, -1.05, 0], [-2.9, 1.1, 0], color=MUTED, stroke_width=4)
    hatches = VGroup(*[Line([-3.15, y - 0.2, 0], [-2.9, y, 0], color=GRID)
                       for y in np.arange(-0.9, 1.1, 0.3)])
    floor = Line([-3.1, -1, 0], [3.0, -1, 0], color=GRID)
    mass = always_redraw(lambda: RoundedRectangle(
        width=1.35, height=1.45, corner_radius=0.12, color=CYAN,
        fill_color="#12313E", fill_opacity=1, stroke_width=2.5,
    ).move_to([0.6 + q.get_value(), 0, 0]))
    coil = always_redraw(lambda: spring([-2.9, 0.43, 0],
                                        [-0.075 + q.get_value(), 0.43, 0]))
    dashpot = always_redraw(lambda: damper([-2.9, -0.43, 0],
                                          [-0.075 + q.get_value(), -0.43, 0]))
    m = text("m", 32, CYAN, font="Cambria Math").move_to(mass.get_center())
    m.add_updater(lambda mob: mob.move_to(mass.get_center()))
    k = text("k", 28, AMBER, font="Cambria Math").move_to([-1.55, 0.92, 0])
    c = text("c", 28, VIOLET, font="Cambria Math").move_to([-1.65, -0.87, 0])
    return VGroup(wall, hatches, floor, coil, dashpot, mass, m, k, c), (mass, coil, dashpot), (m, c, k)


def structure(q: ValueTracker):
    """Estrutura ilustrativa flexível; q expressa apenas movimento visual."""
    base = RoundedRectangle(width=5.8, height=0.25, corner_radius=0.05,
                            color=GRID, fill_color=PANEL, fill_opacity=1).shift(DOWN * 1.25)
    legs = always_redraw(lambda: VGroup(*[
        VMobject(stroke_color=MUTED, stroke_width=3).set_points_smoothly([
            [x, -1.1, 0], [x + q.get_value() * 0.3, -0.6, 0],
            [x + q.get_value(), 0.05, 0],
        ]) for x in [-1.7, 1.7]
    ]))
    plate = always_redraw(lambda: RoundedRectangle(
        width=4.8, height=0.28, corner_radius=0.05, color=WHITE,
        fill_color="#22374A", fill_opacity=1, stroke_width=2,
    ).move_to([q.get_value(), 0.18, 0]))
    sensor = sensor_icon(0.60)
    sensor.add_updater(lambda mob: mob.move_to([q.get_value() + 0.95, 0.59, 0]))
    return VGroup(base, legs, plate, sensor), sensor


def dotted_x(order=1, color=WHITE, size=42):
    x = text("x", size, color, font="Cambria Math")
    dots = VGroup(*[Dot(radius=0.026, color=color).move_to([i * 0.11, 0, 0])
                    for i in range(order)]).next_to(x, UP, buff=0.055)
    return VGroup(x, dots)


def edo_equation(width=10):
    """Termos independentes permitem transformar cada componente físico na EDO."""
    inertia = VGroup(text("m", 42, CYAN, font="Cambria Math"), dotted_x(2, CYAN)).arrange(RIGHT, buff=0.06)
    damping = VGroup(text("c", 42, VIOLET, font="Cambria Math"), dotted_x(1, VIOLET)).arrange(RIGHT, buff=0.06)
    elastic = text("kx", 42, AMBER, font="Cambria Math")
    terms = VGroup(inertia, text("+", 34), damping, text("+", 34),
                   elastic, text("=", 34), text("F(t)", 42, WHITE, font="Cambria Math"))
    terms.arrange(RIGHT, buff=0.26, aligned_edge=DOWN)
    if terms.width > width:
        terms.scale_to_fit_width(width)
    return terms


def solution_equation(width=10):
    lhs = text("x(t) = A", 36, AMBER, font="Cambria Math")
    e = text("e", 36, AMBER, font="Cambria Math")
    exponent = text("−αt", 20, AMBER, font="Cambria Math").next_to(e, UP + RIGHT, buff=0.015)
    exponential = VGroup(e, exponent)
    cosine = text("cos(ωt)", 36, AMBER, font="Cambria Math")
    eq = VGroup(lhs, exponential, cosine).arrange(RIGHT, buff=0.16, aligned_edge=DOWN)
    if eq.width > width:
        eq.scale_to_fit_width(width)
    return eq


def plot_frame(duration, ymax, width=10, height=3, center=ORIGIN, ylabel="aceleração · g"):
    """Eixos numéricos feitos com Text para dispensar LaTeX."""
    axes = Axes(x_range=[0, duration, duration / 5], y_range=[-ymax, ymax, ymax],
                x_length=width, y_length=height,
                axis_config={"color": MUTED, "stroke_width": 1.4,
                             "include_tip": False, "include_ticks": False})
    axes.move_to(center)
    grid = VGroup(*[Line(axes.c2p(0, y), axes.c2p(duration, y),
                          color=GRID, stroke_width=0.8)
                     for y in np.linspace(-ymax, ymax, 5)])
    labels = VGroup()
    for t in np.linspace(0, duration, 6):
        labels.add(text(f"{t:.1f}".removesuffix('.0'), 15, MUTED).next_to(axes.c2p(t, -ymax), DOWN, buff=0.12))
    for y in [-ymax, ymax]:
        labels.add(text(f"{y:.2f}".rstrip('0').rstrip('.'), 14, MUTED)
                   .next_to(axes.c2p(0, y), LEFT, buff=0.12))
    axis_title = text(ylabel, 18, MUTED).next_to(axes, UP, buff=0.18).align_to(axes, LEFT)
    time_title = text("tempo · s", 16, MUTED).next_to(axes, DOWN, buff=0.48).align_to(axes, RIGHT)
    return axes, VGroup(grid, axes, labels, axis_title, time_title)


def signal_curve(axes, times, values, color=CYAN, stroke_width=2.3):
    points = [axes.c2p(float(t), float(v)) for t, v in zip(times, values)]
    return VMobject(stroke_color=color, stroke_width=stroke_width).set_points_as_corners(points)
