"""
Bucle de reproduccion de la animacion.

Corre enteramente en el hilo principal con `after()`; no crea hilos de
trabajo (la cinematica ya se precalculo por completo antes de reproducir, asi
que aqui solo se dibuja). Avanza segun el reloj real (`time.perf_counter`),
no por numero de cuadros, para que la velocidad no cambie si el equipo se
atrasa dibujando.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

import numpy as np

from core.kinematics_fast import FastFrameSequence


class Animator:
    TICK_MS = 20  # ~50 Hz de sondeo; el avance real lo marca el reloj, no este numero

    def __init__(
        self,
        widget,
        on_frame: Callable[[FastFrameSequence, int], None],
        on_finished: Callable[[], None],
    ) -> None:
        self._widget = widget  # cualquier widget de Tk con .after / .after_cancel
        self._on_frame = on_frame
        self._on_finished = on_finished

        self._sequence: Optional[FastFrameSequence] = None
        self._after_id: Optional[str] = None
        self._start_clock = 0.0
        self._elapsed_at_pause = 0.0
        self._playing = False
        self._finished = False
        self._current_index = 0

    # ------------------------------------------------------------------ #
    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def is_loaded(self) -> bool:
        return self._sequence is not None

    @property
    def is_finished(self) -> bool:
        return self._finished

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def sequence(self) -> Optional[FastFrameSequence]:
        return self._sequence

    # ------------------------------------------------------------------ #
    def load(self, sequence: FastFrameSequence) -> None:
        self.stop()
        self._sequence = sequence
        self._elapsed_at_pause = 0.0
        self._current_index = 0
        self._finished = False

    def play(self) -> None:
        if self._sequence is None or self._playing:
            return
        self._playing = True
        self._start_clock = time.perf_counter() - self._elapsed_at_pause
        self._tick()

    def pause(self) -> None:
        if not self._playing:
            return
        self._playing = False
        self._elapsed_at_pause = time.perf_counter() - self._start_clock
        self._cancel_after()

    def reset(self) -> None:
        self.pause()
        self._elapsed_at_pause = 0.0
        self._current_index = 0
        self._finished = False
        if self._sequence is not None:
            self._on_frame(self._sequence, 0)

    def stop(self) -> None:
        self.pause()
        self._sequence = None
        self._current_index = 0
        self._elapsed_at_pause = 0.0
        self._finished = False

    def seek(self, index: int) -> None:
        """Mueve la reproduccion a un cuadro concreto (arrastrar una barra de tiempo)."""
        if self._sequence is None:
            return
        index = max(0, min(index, self._sequence.num_frames - 1))
        self._current_index = index
        self._elapsed_at_pause = float(self._sequence.times[index])
        if self._playing:
            self._start_clock = time.perf_counter() - self._elapsed_at_pause
        self._on_frame(self._sequence, index)

    def cancel(self) -> None:
        """Cancela cualquier `after` pendiente; usar al cerrar la ventana."""
        self._cancel_after()
        self._playing = False

    # ------------------------------------------------------------------ #
    def _cancel_after(self) -> None:
        if self._after_id is not None:
            self._widget.after_cancel(self._after_id)
            self._after_id = None

    def _tick(self) -> None:
        if not self._playing or self._sequence is None:
            return
        transcurrido = time.perf_counter() - self._start_clock
        indice = int(np.searchsorted(self._sequence.times, transcurrido, side="right") - 1)
        indice = max(0, min(indice, self._sequence.num_frames - 1))
        self._current_index = indice
        self._on_frame(self._sequence, indice)

        if transcurrido >= self._sequence.times[-1]:
            self._playing = False
            self._finished = True
            self._after_id = None
            self._on_finished()
            return

        self._after_id = self._widget.after(self.TICK_MS, self._tick)
