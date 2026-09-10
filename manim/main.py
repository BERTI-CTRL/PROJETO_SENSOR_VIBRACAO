"""Sensor de Vibração: uma narrativa contínua em oito passagens.

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
    structure, mechanical, spring, edo_equation, solution_equation,
    plot_frame, signal_curve,
)
from signal_data import load_signal, illustrative_response

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
            os.getenv("VIBRATION_CSV"), os.getenv("VIBRATION_AXIS", "az"),
            float(os.getenv("VIBRATION_START", "8")),
            float(os.getenv("VIBRATION_DURATION", "10")),
        )
        # Scene.duration pertence ao Manim e muda a cada self.play().
        self.signal_duration = float(self.data.t[-1])
        self.ymax = max(0.1, np.ceil(np.max(np.abs(self.data.values)) * 12) / 10)
        self.header = None
        self.caption = None
        self.carry = None
        scenes = [self.vibration, self.sensor, self.samples, self.python,
                  self.model, self.prediction, self.comparison, self.closing]
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
            self.play(FadeOut(self.header, shift=UP * 0.08), FadeIn(group, shift=UP * 0.12), run_time=0.6)
        else:
            self.play(FadeIn(group, shift=UP * 0.12), run_time=0.65)
        self.header = group

    def say(self, message, color=WHITE):
        label = text(message, 23 if self.portrait else 24, color, width=self.safe)
        label.move_to([0, -self.h / 2 + 0.62, 0])
        if self.caption:
            self.play(FadeOut(self.caption, shift=DOWN * 0.05), FadeIn(label, shift=UP * 0.08), run_time=0.45)
        else:
            self.play(FadeIn(label, shift=UP * 0.08), run_time=0.5)
        self.caption = label

    def transition(self, keep=None):
        """Preserva um motivo visual para fazer a ponte ao capítulo seguinte."""
        keep = [] if keep is None else keep
        retained = [self.header, self.caption, *keep]
        others = [m for m in self.mobjects if not any(m is r for r in retained)]
        for mob in others:
            mob.clear_updaters(recursive=True)
        if others:
            self.play(*[FadeOut(m, shift=DOWN * 0.12) for m in others], run_time=0.65)
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
        packet = text("contador, tempo, ax, ay, az, gx, gy, gz", 22, CYAN,
                      width=self.safe, font="Consolas").move_to([0, -1.5, 0])
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
                      f"{self.data.source_label} · recorte {self.data.start_seconds:.1f}–{self.data.start_seconds + self.signal_duration:.1f} s",
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
        coil = spring([-2.1, 0, 0], [2.1, 0, 0])
        if self.carry:
            self.play(ReplacementTransform(self.carry, coil), run_time=1.1)
        else:
            self.play(Create(coil), run_time=1)
        self.transition(keep=[coil])

    def model(self):
        self.heading(5, "Uma hipótese física", ("MODELO CONCEITUAL · ETAPA FUTURA", AMBER))
        q = ValueTracker(0)
        machine, bodies, labels = mechanical(q)
        # Os updaters trabalham no espaço local; mover o conjunto requer congelá-los.
        machine.clear_updaters(recursive=True)
        machine.move_to([0, 0.1 if not self.portrait else 1.0, 0])
        mass, coil, damper = bodies
        if self.carry:
            self.play(ReplacementTransform(self.carry, coil), run_time=0.8)
            self.add(machine)
            self.play(FadeIn(VGroup(*[m for m in machine if m is not coil])), run_time=1)
        else:
            self.play(Create(machine), run_time=1.3)
        self.say("Massa, elasticidade e perdas: uma aproximação do sistema.")
        self.wait(0.8)
        eq = edo_equation(self.safe - 0.1).move_to([0, -1.9 if not self.portrait else -1.5, 0])
        self.play(TransformFromCopy(labels[0], eq[0]), Indicate(mass, color=CYAN), run_time=1.1)
        self.play(FadeIn(eq[1]), TransformFromCopy(labels[1], eq[2]), Indicate(damper, color=VIOLET), run_time=1.1)
        self.play(FadeIn(eq[3]), TransformFromCopy(labels[2], eq[4]), Indicate(coil, color=AMBER), run_time=1.1)
        self.play(FadeIn(eq[5:]), run_time=0.8)
        self.add(eq)
        meanings = VGroup(text("inércia", 17, CYAN), text("dissipação", 17, VIOLET), text("restauração", 17, AMBER))
        meanings.arrange(RIGHT, buff=0.55).next_to(eq, DOWN, buff=0.3)
        self.play(FadeIn(meanings), run_time=0.6)
        self.say("A EDO relaciona forças e prevê o deslocamento x(t).")
        self.wait(2)
        origin = text("modelo descrito na documentação do projeto", 15, MUTED, width=self.safe)
        origin.next_to(meanings, DOWN, buff=0.4)
        self.play(FadeIn(origin), run_time=0.5)
        self.wait(1)
        self.transition(keep=[eq])

    def prediction(self):
        self.heading(6, "A matemática ganha movimento", ("SIMULAÇÃO · PARÂMETROS ILUSTRATIVOS", AMBER))
        solution = solution_equation(self.safe - 0.1).move_to([0, 1.6 if not self.portrait else 3.8, 0])
        if self.carry:
            self.play(ReplacementTransform(self.carry, solution), run_time=1.2)
        else:
            self.play(FadeIn(solution), run_time=0.8)
        definitions = text("F(t) = 0    ·    α = c / 2m    ·    ω² = k/m − α²", 19, MUTED, width=self.safe)
        definitions.next_to(solution, DOWN, buff=0.23)
        self.play(FadeIn(definitions), run_time=0.6)
        self.say("Depois de soltar, a amplitude diminui com a dissipação.")
        time, q = ValueTracker(0), ValueTracker(0)
        machine, _, _ = mechanical(q)
        # Layout responsivo por atualização da posição dos componentes, sem câmera 3D.
        scale = 0.56 if not self.portrait else 0.83
        machine.clear_updaters(recursive=True)
        machine.scale(scale).move_to([-3.8, -0.45, 0] if not self.portrait else [0, 1.3, 0])
        # Uma cópia reconstruída mantém as coordenadas físicas e o mesmo fator de escala.
        center = machine.get_center().copy()
        def moving_machine():
            obj, _, _ = mechanical(ValueTracker(float(illustrative_response(time.get_value())[0]) * 38))
            obj.clear_updaters(recursive=True)
            # Alinhar por um ponto fixo mantém a base imóvel durante a oscilação.
            obj.scale(scale, about_point=ORIGIN)
            obj.shift(center - np.array([-0.075 * scale, 0.05 * scale, 0]))
            return obj
        animated = always_redraw(moving_machine)
        axes, frame = plot_frame(10, 22, width=5.5 if not self.portrait else 5.8,
                                  height=2.25 if not self.portrait else 2.7,
                                  center=[3.15, -0.8, 0] if not self.portrait else [0.3, -2.1, 0],
                                  ylabel="deslocamento previsto · mm")
        ts = np.linspace(0, 10, 1000)
        xs = illustrative_response(ts)[0] * 1000
        curve = signal_curve(axes, ts, xs, AMBER)
        dot = Dot(axes.c2p(0, float(xs[0])), radius=0.055, color=AMBER)
        dot.add_updater(lambda d: d.move_to(axes.c2p(time.get_value(), float(illustrative_response(time.get_value())[0]) * 1000)))
        self.play(FadeIn(animated), Create(frame), run_time=1.1)
        self.add(dot)
        self.play(time.animate.set_value(10), Create(curve), run_time=6, rate_func=linear)
        animated.clear_updaters(recursive=True); dot.clear_updaters()
        params = text("m = 1 kg   ·   c = 0,7 N·s/m   ·   k = 16 N/m", 16, MUTED, width=self.safe)
        params.move_to([0, -2.8 if not self.portrait else -4.55, 0])
        self.play(FadeIn(params), run_time=0.6)
        self.say("Para comparar com o sensor, calculamos a aceleração.")
        acceleration = text("x(t)  →  d²x/dt²  →  aceleração em g", 29, AMBER,
                            width=self.safe, font="Cambria Math").move_to([0, -0.5 if not self.portrait else -1.7, 0])
        self.play(FadeOut(animated), FadeOut(frame), FadeOut(dot), FadeOut(params),
                  FadeOut(definitions), ReplacementTransform(curve, acceleration), run_time=1.2)
        self.wait(1.2)
        self.transition(keep=[acceleration])

    def comparison(self):
        self.heading(7, "Teoria encontra medição", ("COMPARAÇÃO CONCEITUAL · SEM AJUSTE", AMBER))
        if self.carry:
            self.play(FadeOut(self.carry), run_time=0.5)
        ymax = max(self.ymax, 0.15)
        axes, frame = plot_frame(self.signal_duration, ymax, self.safe - 0.8,
                                  2.9 if not self.portrait else 4.1,
                                  [0.22, -0.1 if not self.portrait else 0.0, 0],
                                  "aceleração · g")
        real = signal_curve(axes, self.data.t, self.data.values)
        predicted_a = illustrative_response(self.data.t)[2] / 9.80665
        theory = signal_curve(axes, self.data.t, predicted_a, AMBER, 3)
        top_y = 1.85 if not self.portrait else 3.15
        sensor = sensor_icon(0.42).move_to([-2, top_y, 0])
        eq = text("d²x/dt²", 23, AMBER, font="Cambria Math").move_to([2, top_y, 0])
        measurement_name = text(("sintético · " if self.data.synthetic else "sensor · ") + self.data.axis, 20, CYAN)
        theory_name = text("modelo", 20, AMBER)
        VGroup(sensor, measurement_name).arrange(RIGHT, buff=0.18).move_to([-1.9, top_y, 0])
        VGroup(eq, theory_name).arrange(RIGHT, buff=0.18).move_to([1.8, top_y, 0])
        legends = VGroup(measurement_name, theory_name)
        self.play(Create(frame), FadeIn(sensor), FadeIn(eq), FadeIn(legends), run_time=1)
        self.say("Duas origens. A mesma grandeza física.")
        measured_seed = Dot(sensor.get_center(), radius=0.065, color=CYAN)
        theoretical_seed = Dot(eq.get_center(), radius=0.065, color=AMBER)
        self.play(MoveAlongPath(measured_seed, Line(sensor.get_center(), real.get_start())), run_time=0.65)
        self.play(Create(real), FadeOut(measured_seed), run_time=2, rate_func=linear)
        self.play(MoveAlongPath(theoretical_seed, Line(eq.get_center(), theory.get_start())), run_time=0.65)
        self.play(Create(theory), FadeOut(theoretical_seed), run_time=2, rate_func=linear)
        self.wait(0.5)
        # Não calcular erro de ajuste: parâmetros e condição inicial não foram identificados.
        peak = int(np.argmax(np.abs(self.data.values)))
        p_real, p_theory = axes.c2p(self.data.t[peak], self.data.values[peak]), axes.c2p(self.data.t[peak], predicted_a[peak])
        gap = DashedLine(p_theory, p_real, color=CORAL, stroke_width=2, dash_length=0.055)
        ring = Circle(radius=0.16, color=CORAL, stroke_width=1.8).move_to(p_real)
        gap_label = text("diferença observada", 18, CORAL).move_to([1.4, -2.15 if not self.portrait else -3.1, 0])
        self.play(Create(gap), Create(ring), FadeIn(gap_label), run_time=0.8)
        self.say("As diferenças levantam perguntas; ainda não validam o modelo.")
        self.wait(1.7)
        next_steps = text("montagem + calibração + parâmetros + ensaio controlado", 19, MUTED, width=self.safe)
        next_steps.move_to([0, -2.8 if not self.portrait else -4.25, 0])
        self.play(FadeIn(next_steps, shift=UP * 0.1), run_time=0.75)
        self.say("É preciso conhecer a montagem e separar gravidade de movimento.")
        self.wait(2)
        self.play(FadeOut(gap), FadeOut(ring), FadeOut(gap_label), run_time=0.5)
        both = VGroup(real, theory)
        self.add(both)
        self.transition(keep=[both])

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
        icons = VGroup(sensor_icon(0.5), csv_icon(0.5), python_icon(0.5), text("x(t)", 26, AMBER, font="Cambria Math"))
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
        words = VGroup(*[text(word, 27, color) for word, color in
                          [("Medir.", CYAN), ("Modelar.", AMBER), ("Comparar.", VIOLET), ("Entender.", WHITE)]])
        words.arrange(DOWN if self.portrait else RIGHT, buff=0.24 if self.portrait else 0.38)
        words.next_to(title, DOWN, buff=0.5)
        self.play(LaggedStart(*[FadeIn(word, shift=UP * 0.12) for word in words], lag_ratio=0.25), run_time=1.8)
        note = text(("dados sintéticos" if self.data.synthetic else "medição real") +
                    " · modelo conceitual · investigação em evolução", 15, MUTED, width=self.safe)
        note.move_to([0, -self.h / 2 + 0.65, 0])
        self.play(FadeIn(note), run_time=0.6)
        self.wait(2.5)
