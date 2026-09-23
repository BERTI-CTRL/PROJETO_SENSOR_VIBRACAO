"""Sensor de Vibração: uma narrativa contínua em seis passagens.

Renderize com ``python render.py``. Cada passagem também funciona isolada
por ``--section N``; formatos e recorte são recebidos por variáveis de ambiente.
As curvas reais nunca são ajustadas à resposta ilustrativa para parecerem iguais.
"""

import os
from pathlib import Path

import numpy as np
from manim import *

from visuals import (
    BG, PANEL, GRID, WHITE, MUTED, CYAN, AMBER, VIOLET, CORAL,
    text, badge, sensor_icon, arduino_icon, python_icon, csv_icon,
    structure, portal_frame, portal_equation, plot_frame, signal_curve,
)
from signal_data import load_signal

HERE = Path(__file__).resolve().parent
VERTICAL = os.getenv("VIBRATION_FORMAT", "horizontal") == "vertical"
config.background_color = BG
config.frame_width = 8 if VERTICAL else 128 / 9
config.frame_height = 128 / 9 if VERTICAL else 8
config.media_dir = str(HERE / "media" / ("vertical" if VERTICAL else "horizontal"))
config.video_dir = str(HERE)
config.partial_movie_dir = str(Path(config.media_dir) / "partial_movie_files")
config.max_files_cached = 200
if os.getenv("VIBRATION_OUTPUT"):
    config.output_file = os.environ["VIBRATION_OUTPUT"]


class SensorVibracao(MovingCameraScene):
    """Uma cena mantém a linguagem visual e transporta motivos entre capítulos."""

    def construct(self):
        self.portrait = VERTICAL
        self.w, self.h = config.frame_width, config.frame_height
        self.safe = self.w - 1.1
        self.data = load_signal(
            os.getenv("VIBRATION_CSV"), os.getenv("VIBRATION_AXIS", "ay"),
            float(os.getenv("VIBRATION_START", "0")),
            float(os.getenv("VIBRATION_DURATION", "15")),
        )
        # Scene.duration pertence ao Manim e muda a cada self.play().
        self.signal_duration = float(self.data.t[-1])
        self.ymax = max(0.1, np.ceil(np.max(np.abs(self.data.values)) * 12) / 10)
        self.header = None
        self.caption = None
        self.carry = None
        scenes = [self.vibration, self.sensor, self.samples, self.python,
                  self.experiment, self.closing]
        section = os.getenv("VIBRATION_SECTION")
        for index, scene in enumerate(scenes, 1):
            if section and int(section) != index:
                continue
            self.next_section(f"{index:02d}_{scene.__name__}")
            scene()
        self.wait(0.5)

    def heading(self, number, title, status=None):
        eyebrow = text(f"SENSOR DE VIBRAÇÃO   /   {number:02d}", 14, MUTED)
        name = text(title, 37 if self.portrait else 36, width=self.safe, weight="SEMIBOLD")
        group = VGroup(eyebrow, name).arrange(DOWN, aligned_edge=LEFT, buff=0.20)
        group.move_to([0, self.h / 2 - 0.85, 0]).to_edge(LEFT, buff=0.58)
        if status:
            tag = badge(status[0], status[1], 13)
            tag.next_to(group, DOWN, aligned_edge=LEFT, buff=0.22)
            group.add(tag)
        if self.header:
            self.play(FadeOut(self.header, shift=UP * 0.08), FadeIn(group, shift=UP * 0.12),
                      run_time=0.85, rate_func=smooth)
        else:
            self.play(FadeIn(group, shift=UP * 0.12), run_time=0.75, rate_func=smooth)
        self.header = group

    def say(self, message, color=WHITE):
        label = text(message, 23 if self.portrait else 24, color, width=self.safe)
        label.move_to([0, -self.h / 2 + 0.62, 0])
        if self.caption:
            self.play(FadeOut(self.caption, shift=DOWN * 0.05), FadeIn(label, shift=UP * 0.08),
                      run_time=0.6, rate_func=smooth)
        else:
            self.play(FadeIn(label, shift=UP * 0.08), run_time=0.6, rate_func=smooth)
        self.caption = label

    def transition(self, keep=None):
        """Preserva um motivo visual para fazer a ponte ao capítulo seguinte."""
        keep = [] if keep is None else keep
        retained = [self.header, self.caption, *keep]
        others = [m for m in self.mobjects if not any(m is r for r in retained)]
        for mob in others:
            mob.clear_updaters(recursive=True)
        if others:
            self.play(*[FadeOut(m, shift=DOWN * 0.10, scale=0.97) for m in others],
                      run_time=0.9, rate_func=smooth)
        self.carry = keep[0] if keep else None

    def vibration(self):
        q, time = ValueTracker(0), ValueTracker(0)
        rig, chip = structure(q)
        intro = text("O INVISÍVEL\nTEM MOVIMENTO.", 49 if self.portrait else 52,
                     width=self.safe, weight="SEMIBOLD")
        intro.move_to([0, 2.5 if not self.portrait else 4.3, 0])
        micro = text("uma investigação sobre vibração", 20, MUTED).next_to(intro, DOWN, buff=0.25)
        self.play(FadeIn(intro, shift=UP * 0.18), FadeIn(micro), Create(rig), run_time=1.8)
        self.wait(0.6)
        force = Arrow([-3, 0.45, 0], [-1.3, 0.45, 0], color=AMBER, buff=0, stroke_width=5)
        impulse = text("perturbação", 18, AMBER).next_to(force, UP)
        self.play(GrowArrow(force), FadeIn(impulse), run_time=0.55)
        self.play(q.animate.set_value(0.48), run_time=0.35, rate_func=rush_into)
        self.play(FadeOut(force), FadeOut(impulse), FadeOut(intro), FadeOut(micro), run_time=0.55)
        q.add_updater(lambda m: m.set_value(0.48 * np.exp(-0.13 * time.get_value()) * np.cos(6 * time.get_value())))
        trail = TracedPath(chip.get_center, dissipating_time=1.4, stroke_color=CYAN,
                           stroke_width=4, stroke_opacity=[0, 0.6])
        self.add(q, trail)
        self.say("Uma estrutura vibra.")
        self.play(time.animate.set_value(4.3), run_time=4.3, rate_func=linear)
        self.say("Como transformar esse movimento em informação?")
        self.play(time.animate.set_value(6.4), run_time=2.1, rate_func=linear)
        q.clear_updaters()
        rig.clear_updaters(recursive=True)
        trail.clear_updaters()
        self.play(FadeOut(self.caption), FadeOut(trail),
                  self.camera.frame.animate.scale(0.44).move_to(chip), run_time=1.6)
        self.caption = None
        hero = sensor_icon(1.2).move_to(chip)
        self.play(ReplacementTransform(chip.copy(), hero), run_time=0.65)
        self.remove(rig, q)
        self.play(self.camera.frame.animate.set(width=self.w).move_to(ORIGIN),
                  hero.animate.move_to([0, 0.6, 0]).scale(1.4), run_time=1.35)
        self.carry = hero

    def sensor(self):
        self.heading(2, "Sentir o movimento")
        hero = self.carry or sensor_icon(1.68).move_to([0, 0.6, 0])
        if hero not in self.mobjects:
            self.add(hero)
        name = text("MPU6050", 28, CYAN).next_to(hero, UP + LEFT, buff=0.35)
        vector_x = Arrow(hero.get_center(), hero.get_center() + RIGHT * 2.1, color=CYAN, buff=0.08)
        vector_y = Arrow(hero.get_center(), hero.get_center() + UP * 1.5, color=VIOLET, buff=0.08)
        self.play(FadeIn(name), GrowArrow(vector_x), GrowArrow(vector_y), run_time=1)
        reading = VGroup(text("ax · ay · az", 26, CYAN), text("aceleração específica · g", 18, MUTED),
                         text("gx · gy · gz", 23, VIOLET), text("velocidade angular · °/s", 18, MUTED))
        reading.arrange(DOWN, buff=0.18).move_to([0, -1.25 if not self.portrait else -1.8, 0])
        self.play(LaggedStart(*[FadeIn(x, shift=UP * 0.1) for x in reading], lag_ratio=0.2), run_time=1.4)
        self.say("O sensor mede aceleração e giro em três eixos.")
        self.play(Wiggle(hero, scale_value=1.02, rotation_angle=0.04), run_time=1.8)
        self.play(FadeOut(reading), FadeOut(name), FadeOut(vector_x), FadeOut(vector_y), run_time=0.65)
        positions = ([[-2.5, 1.3, 0], [0, 1.3, 0], [2.5, 1.3, 0]] if self.portrait
                     else [[-4.5, 0.4, 0], [0, 0.4, 0], [4.5, 0.4, 0]])
        arduino, python = arduino_icon(), python_icon()
        arduino.move_to(positions[1]); python.move_to(positions[2])
        self.play(hero.animate.scale_to_fit_width(1.3).move_to(positions[0]),
                  FadeIn(arduino), FadeIn(python), run_time=1)
        nodes = [hero, arduino, python]
        names = VGroup(*[text(s, 20, color).next_to(n, DOWN, buff=0.3)
                         for n, s, color in zip(nodes, ["MPU6050", "Arduino", "Python"], [CYAN, VIOLET, CYAN])])
        wires = VGroup(*[Line(nodes[i].get_right(), nodes[i + 1].get_left(), color=GRID, stroke_width=3)
                         for i in range(2)])
        transport = VGroup(text("I²C", 16, MUTED).next_to(wires[0], UP, buff=0.2),
                           text("USB / serial", 16, MUTED).next_to(wires[1], UP, buff=0.2))
        self.play(Create(wires), FadeIn(names), FadeIn(transport), run_time=0.8)
        self.say("O Arduino lê, marca o tempo e transmite cada amostra.")
        particles = VGroup(*[Dot(radius=0.045, color=CYAN) for _ in range(8)])
        for p in particles:
            p.move_to(wires[0].get_start())
        route = VMobject().set_points_as_corners([wires[0].get_start(), positions[1], wires[1].get_end()])
        self.play(LaggedStart(*[MoveAlongPath(p, route, rate_func=linear) for p in particles], lag_ratio=0.14), run_time=3)
        self.remove(particles)
        packet = VGroup(
            text("tempo_arduino_us, tempo_relogio_pc, contador", 18, CYAN,
                 width=self.safe, font="Consolas"),
            text("ax, ay, az, gx, gy, gz", 18, CYAN,
                 width=self.safe, font="Consolas"),
        ).arrange(DOWN, buff=0.12).move_to([0, -1.5, 0])
        self.play(TransformFromCopy(python, packet), run_time=1)
        self.wait(0.8)
        self.transition(keep=[packet])

    def samples(self):
        status = ("DADOS SINTÉTICOS", AMBER) if self.data.synthetic else ("DADOS REAIS · CSV DO PROJETO", CYAN)
        self.heading(3, "O sinal nasce dos dados", status)
        center = [0.22, -0.2 if not self.portrait else 0.2, 0]
        axes, frame = plot_frame(self.signal_duration, self.ymax, self.safe - 0.8,
                                  3.0 if not self.portrait else 4.2, center,
                                  f"{self.data.axis} · aceleração específica · g")
        if self.carry:
            axis_seed = Line(axes.c2p(0, 0), axes.c2p(self.signal_duration, 0), color=CYAN)
            self.play(ReplacementTransform(self.carry, axis_seed), run_time=1)
            self.play(FadeOut(axis_seed), Create(frame), run_time=1)
        else:
            self.play(Create(frame), run_time=1)
        selected = np.linspace(0, len(self.data.t) - 1, 36, dtype=int)
        dots = VGroup(*[Dot(axes.c2p(self.data.t[i], self.data.values[i]), radius=0.037, color=CYAN)
                        for i in selected])
        cursor = Line(axes.c2p(0, -self.ymax), axes.c2p(0, self.ymax), color=CYAN, stroke_width=1, stroke_opacity=0.5)
        curve = signal_curve(axes, self.data.t, self.data.values)
        self.say("Cada ponto guarda um instante e uma aceleração.")
        self.play(LaggedStart(*[FadeIn(d, scale=1.8) for d in dots], lag_ratio=0.06),
                  cursor.animate.shift(axes.c2p(self.signal_duration, 0) - axes.c2p(0, 0)), run_time=3.2)
        self.play(Create(curve), FadeOut(dots), FadeOut(cursor), run_time=3.8, rate_func=linear)
        source = text("dados sintéticos · demonstração" if self.data.synthetic else
                      f"{self.data.source.name} · {self.data.axis} · recorte {self.data.start_seconds:.1f}–{self.data.start_seconds + self.signal_duration:.1f} s",
                      16, MUTED, width=self.safe)
        source.move_to([0, -2.65 if not self.portrait else -3.2, 0])
        count = badge(f"{len(self.data.t):,}".replace(',', '.') + " amostras · sem filtro", CYAN, 15)
        if self.portrait:
            count.next_to(source, DOWN, buff=0.24)
        else:
            provenance = VGroup(source, count).arrange(RIGHT, buff=0.45)
            if provenance.width > self.safe:
                provenance.scale_to_fit_width(self.safe)
            provenance.move_to([0, -2.82, 0])
        self.play(FadeIn(source), FadeIn(count), run_time=0.7)
        self.say("O gráfico usa o tempo do Arduino, convertido de µs para s.")
        self.wait(1.5)
        # A curva original continua como motivo no capítulo sobre Python.
        self.transition(keep=[curve])

    def python(self):
        self.heading(4, "Organizar para investigar")
        py = python_icon(1.15).move_to([0, 1.15 if not self.portrait else 2.7, 0])
        if self.carry:
            self.play(self.carry.animate.scale_to_fit_width(self.safe * 0.55).move_to([0, -0.15, 0]),
                      FadeIn(py), run_time=0.9)
        else:
            self.play(FadeIn(py), run_time=0.7)
        real_code = VGroup(text('campos = dados_linha.split(",")', 18, CYAN, width=self.safe, font="Consolas"),
                           text("sensor/serial_reader.py", 15, MUTED, font="Consolas"))
        real_code.arrange(DOWN, buff=0.15).next_to(py, RIGHT if not self.portrait else UP, buff=0.5)
        if not self.portrait:
            real_code.shift(LEFT * 0.05)
        self.play(FadeIn(real_code), run_time=0.65)
        self.say("Python valida as linhas e organiza seis canais.")
        row_y = -1.35 if not self.portrait else -1.25
        memory = VGroup(*[RoundedRectangle(width=0.24, height=0.55, corner_radius=0.03,
                            color=CYAN, fill_color=CYAN, fill_opacity=0.12 + i * 0.07, stroke_width=1)
                          for i in range(8)]).arrange(RIGHT, buff=0.055).move_to([-2.6 if not self.portrait else -1.9, row_y, 0])
        csv = csv_icon(0.85).move_to([2.6 if not self.portrait else 1.9, row_y, 0])
        branch = VGroup(Arrow(py.get_bottom(), memory.get_top(), color=CYAN, stroke_width=2, buff=0.2),
                        Arrow(py.get_bottom(), csv.get_top(), color=AMBER, stroke_width=2, buff=0.2))
        self.play(Create(branch), LaggedStart(*[FadeIn(x) for x in memory], lag_ratio=0.08), FadeIn(csv), run_time=1.3)
        labels = VGroup(text("buffer → gráficos ao vivo", 18, CYAN).next_to(memory, DOWN, buff=0.25),
                        text("fila → CSV → Plotly", 18, AMBER).next_to(csv, DOWN, buff=0.25))
        if self.portrait:
            for item in labels:
                item.scale_to_fit_width(3.2)
        self.play(FadeIn(labels), run_time=0.6)
        self.say("O sinal aparece ao vivo e fica registrado para análise.")
        self.wait(1)
        stats = VGroup()
        for name, value, color in [("MÉDIA", self.data.mean, CYAN), ("DESVIO", self.data.std, VIOLET), ("RMS", self.data.rms, AMBER)]:
            stat = VGroup(text(name, 14, MUTED), text(f"{value:.3f} g", 27, color)).arrange(DOWN, buff=0.15)
            stats.add(stat)
        stats.arrange(RIGHT, buff=1.0 if not self.portrait else 0.65).move_to([0, -2.75 if not self.portrait else -3.8, 0])
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.12) for s in stats], lag_ratio=0.25), run_time=1.2)
        self.say("Média, desvio e RMS resumem este recorte bruto.")
        self.wait(1.4)
        # A curva medida segue como motivo visual até a cena do pórtico.
        self.transition(keep=[self.carry] if self.carry else [])

    def experiment(self):
        if self.carry:
            self.play(FadeOut(self.carry), run_time=0.45, rate_func=smooth)
            self.carry = None
        self.heading(5, "O movimento do pórtico", ("MODELO IDEALIZADO", AMBER))
        self.say("Uma equação idealiza o movimento do pórtico.")
        q = ValueTracker(0)
        scale = 0.88 if self.portrait else 0.98
        center = [0, 0.30 if self.portrait else 0.0, 0]
        frame, _ = portal_frame(q, scale=scale, center=center)
        self.play(Create(frame), run_time=1.2, rate_func=smooth)
        self.add(frame)
        self.play(q.animate.set_value(0.28), run_time=1.3, rate_func=there_and_back)
        equation = portal_equation(self.safe - 0.35, 30 if self.portrait else 38)
        equation.move_to([0, -1.55 if self.portrait else -1.78, 0])
        self.play(FadeIn(equation, shift=UP * 0.08), run_time=0.9, rate_func=smooth)

        definitions = [
            ("M v̈(t)", "inércia: massa ×\naceleração", CYAN),
            ("ε v̇(t)", "amortecimento:\ndissipa energia", VIOLET),
            ("K v(t)", "rigidez: tende a restaurar\na posição", AMBER),
            ("P(t)", "força aplicada que\nexcita o pórtico", CORAL),
        ]
        cards = VGroup()
        for term, explanation, color in definitions:
            term_label = text(term, 18 if self.portrait else 20, color, font="Cambria Math")
            description = text(explanation, 14 if self.portrait else 15, WHITE,
                               width=2.8 if self.portrait else 2.9)
            cards.add(VGroup(term_label, description).arrange(DOWN, buff=0.12))
        if self.portrait:
            cards.arrange_in_grid(rows=2, cols=2, buff=(0.48, 0.38))
            cards.move_to([0, -3.45, 0])
        else:
            cards.arrange(RIGHT, buff=0.3)
            cards.move_to([0, -2.75, 0])
        self.play(LaggedStart(*[FadeIn(card, shift=UP * 0.07) for card in cards],
                              lag_ratio=0.18), run_time=1.7, rate_func=smooth)
        self.say("v(t) é o deslocamento idealizado; suas derivadas são velocidade e aceleração.")
        self.wait(1.5)
        self.transition(keep=[frame])

    def closing(self):
        if self.header:
            self.play(FadeOut(self.header), run_time=0.5)
            self.header = None
        if self.caption:
            self.play(FadeOut(self.caption), run_time=0.4)
            self.caption = None
        q = ValueTracker(0)
        rig, _ = structure(q)
        rig.clear_updaters(recursive=True)
        rig.scale(0.62).move_to([0, 0.3 if not self.portrait else 1.0, 0])
        halo = Circle(radius=2.1, color=GRID, stroke_width=1)
        halo.move_to(rig.get_center())
        if self.carry:
            self.play(ReplacementTransform(self.carry, halo), FadeIn(rig), run_time=1.3)
        else:
            self.play(Create(halo), FadeIn(rig), run_time=1.2)
        icons = VGroup(sensor_icon(0.5), csv_icon(0.5), python_icon(0.5),
                       text("aᵧ(t)", 26, CYAN, font="Cambria Math"))
        center = halo.get_center()
        positions = [center + UP * 2.1, center + RIGHT * 2.1, center + DOWN * 2.1, center + LEFT * 2.1]
        for item, pos in zip(icons, positions):
            item.move_to(pos)
        self.play(LaggedStart(*[FadeIn(icon, scale=0.5) for icon in icons], lag_ratio=0.18), run_time=1.4)
        self.play(Rotate(icons, angle=-TAU / 12, about_point=center), run_time=1.5)
        # Os motivos convergem para o sensor, que se torna a assinatura final.
        mark = sensor_icon(0.85).move_to([0, 1.35 if not self.portrait else 2.0, 0])
        self.play(ReplacementTransform(VGroup(halo, rig, icons), mark), run_time=1.25)
        title = text("Sensor de\nVibração" if self.portrait else "Sensor de Vibração",
                     53, WHITE, width=self.safe, weight="SEMIBOLD").next_to(mark, DOWN, buff=0.55)
        self.play(FadeIn(title, shift=UP * 0.15), run_time=1.1)
        note = text(("dados sintéticos" if self.data.synthetic else "medição real") +
                    " · aceleração bruta em g · dados do ensaio", 15, MUTED, width=self.safe)
        note.move_to([0, -self.h / 2 + 0.65, 0])
        self.play(FadeIn(note), run_time=0.6)
        self.wait(2.5)
