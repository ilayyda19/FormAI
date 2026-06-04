from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class Phase(Enum):
    REST = "rest"
    ACTIVE = "active"
    PEAK = "peak"
    RETURN = "return"


@dataclass
class RepResult:
    counted: bool
    phase: Phase
    rep_count: int
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def feedback_lines(self):
        return self.errors + self.warnings

    @property
    def worst_severity(self):
        if self.errors:
            return "error"
        if self.warnings:
            return "warning"
        return "ok"


class BaseExercise(ABC):
    def __init__(self):
        self._count = 0
        self._phase = Phase.REST
        self._at_peak = False
        self._good_peak = True

    @abstractmethod
    def _detect_phase(self, angles: dict) -> Phase:
        pass

    @abstractmethod
    def _check_form(self, angles: dict, phase: Phase) -> tuple[list[str], list[str]]:
        pass

    def analyze(self, angles: dict) -> RepResult:
        if not angles:
            return RepResult(False, self._phase, self._count)

        new_phase = self._detect_phase(angles)
        warnings, errors = self._check_form(angles, new_phase)

        counted = self._tick_counter(new_phase, bool(errors))

        self._phase = new_phase

        return RepResult(
            counted=counted,
            phase=new_phase,
            rep_count=self._count,
            warnings=warnings,
            errors=errors,
        )

    def _tick_counter(self, new_phase: Phase, has_error: bool) -> bool:
        counted = False

        if new_phase == Phase.PEAK:
            self._at_peak = True
            self._good_peak = not has_error

        if (
            self._at_peak
            and self._phase != Phase.REST
            and new_phase == Phase.REST
        ):
            if self._good_peak:
                self._count += 1
                counted = True

            self._at_peak = False
            self._good_peak = True

        return counted

    def reset(self):
        self._count = 0
        self._phase = Phase.REST
        self._at_peak = False
        self._good_peak = True

    @property
    def rep_count(self) -> int:
        return self._count

    @property
    def phase(self) -> Phase:
        return self._phase

    @staticmethod
    def avg(a: float, b: float) -> float:
        return (a + b) / 2.0