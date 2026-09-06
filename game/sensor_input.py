"""Leitura serial assíncrona do protocolo atual do MPU6050."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from threading import Event, Lock, Thread
from time import monotonic
from typing import Any, Callable

import serial


@dataclass(frozen=True)
class SensorSample:
    """A parte da amostra necessária para controlar o jogo."""

    counter: int
    ax: float
    ay: float
    az: float


def parse_sensor_line(line: str) -> SensorSample | None:
    """Converte uma linha CSV do Arduino ou ignora conteúdo não compatível."""
    fields = line.strip().split(",")
    if len(fields) != 8:
        return None

    try:
        values = [float(field) for field in fields]
    except ValueError:
        return None

    if not all(isfinite(value) for value in values) or not values[0].is_integer():
        return None

    try:
        return SensorSample(
            counter=int(values[0]),
            ax=values[2],
            ay=values[3],
            az=values[4],
        )
    except OverflowError:
        return None


class SensorReader:
    """Lê a serial em background e expõe sempre a amostra mais recente."""

    def __init__(
        self,
        port: str,
        baudrate: int,
        stale_after_s: float = 0.5,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if stale_after_s <= 0:
            raise ValueError("stale_after_s precisa ser maior que zero.")

        self.port = port
        self.baudrate = baudrate
        self.stale_after_s = stale_after_s
        self._clock = clock
        self.status = "Sensor ainda não iniciado."
        self.is_connected = False
        self._latest: SensorSample | None = None
        self._latest_at: float | None = None
        self._lock = Lock()
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._serial: Any | None = None

    def start(self) -> None:
        """Inicia a thread uma única vez; uma falha fica visível em ``status``."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._read_loop, name="game-sensor-reader", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Solicita parada; a própria thread fecha a porta ao sair do ``with``."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def latest_sample(self) -> SensorSample | None:
        """Retorna a última leitura válida apenas enquanto ela estiver recente."""
        with self._lock:
            if self._latest is None or self._latest_at is None:
                return None
            if self._clock() - self._latest_at > self.stale_after_s:
                self.status = "Sensor conectado, mas dados desatualizados."
                return None
            return self._latest

    def _read_loop(self) -> None:
        try:
            with serial.Serial(self.port, self.baudrate, timeout=0.25) as serial_port:
                self._serial = serial_port
                self.is_connected = True
                self.status = f"Sensor conectado em {self.port}."

                while not self._stop_event.is_set():
                    raw_line = serial_port.readline()
                    sample = parse_sensor_line(raw_line.decode("utf-8", errors="replace"))
                    if sample is not None:
                        with self._lock:
                            self._latest = sample
                            self._latest_at = self._clock()
                        self.status = f"Sensor conectado em {self.port}."
        except (serial.SerialException, OSError) as error:
            if not self._stop_event.is_set():
                self.status = f"Sem sensor: {error}"
        finally:
            self.is_connected = False
            self._serial = None
