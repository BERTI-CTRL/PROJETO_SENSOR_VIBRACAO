"""Leitura serial assíncrona do protocolo atual do MPU6050."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Event, Lock, Thread
from typing import Any

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
        return SensorSample(
            counter=int(float(fields[0])),
            ax=float(fields[2]),
            ay=float(fields[3]),
            az=float(fields[4]),
        )
    except ValueError:
        return None


class SensorReader:
    """Lê a serial em background e expõe sempre a amostra mais recente."""

    def __init__(self, port: str, baudrate: int) -> None:
        self.port = port
        self.baudrate = baudrate
        self.status = "Sensor ainda não iniciado."
        self.is_connected = False
        self._latest: SensorSample | None = None
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
        """Solicita parada e solta a porta para outros programas do projeto."""
        self._stop_event.set()
        serial_port = self._serial
        if serial_port is not None:
            try:
                serial_port.close()
            except serial.SerialException:
                pass

        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def latest_sample(self) -> SensorSample | None:
        """Retorna uma cópia imutável da última leitura válida."""
        with self._lock:
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
        except (serial.SerialException, OSError) as error:
            if not self._stop_event.is_set():
                self.status = f"Sem sensor: {error}"
        finally:
            self.is_connected = False
            self._serial = None
