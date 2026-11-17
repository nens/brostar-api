"""Rule-based quality validation for GLD registration measurements."""

from dataclasses import dataclass
from statistics import mean, pstdev

from api.bro_upload.upload_datamodels import TimeValuePair

DEFAULT_RULES = (
    "flatline",
    "spike",
    "below_tube_top",
    "above_tube_bottom",
)
AVAILABLE_RULES = DEFAULT_RULES + ("at_or_below_sensor_height",)
FLATLINE_INTERVAL_COUNT = 5
DEFAULT_FLATLINE_SIGMA_MULTIPLIER = 0.1
DEFAULT_SPIKE_SIGMA_MULTIPLIER = 3.0
DEFAULT_PHYSICAL_TOLERANCE = 0.1


@dataclass(frozen=True)
class ValidationSettings:
    rules: tuple[str, ...] = DEFAULT_RULES
    flatline_sigma_multiplier: float = DEFAULT_FLATLINE_SIGMA_MULTIPLIER
    spike_sigma_multiplier: float = DEFAULT_SPIKE_SIGMA_MULTIPLIER
    tube_top_tolerance: float = DEFAULT_PHYSICAL_TOLERANCE
    tube_bottom_tolerance: float = DEFAULT_PHYSICAL_TOLERANCE
    sensor_height_tolerance: float = DEFAULT_PHYSICAL_TOLERANCE
    sensor_height: float | None = None


def _record(result: list[str], status: str) -> None:
    result.append(status)


def _combine_statuses(statuses: list[str]) -> str:
    if not statuses:
        return "onbeslist"
    if "afgekeurd" in statuses:
        return "afgekeurd"
    if "onbeslist" in statuses:
        return "onbeslist"
    return "goedgekeurd"


def _measurement_deltas(
    measurements: list[TimeValuePair],
) -> list[tuple[int, int, float]]:
    return [
        (index, index + 1, measurements[index + 1].value - measurements[index].value)
        for index in range(len(measurements) - 1)
        if measurements[index].value is not None
        and measurements[index + 1].value is not None
    ]


def _apply_statistical_rules(
    pairs: list[tuple[int, int, float]],
    settings: ValidationSettings,
    findings: list[list[str]],
) -> None:
    deltas = [delta for _, _, delta in pairs]
    delta_mean = mean(deltas) if deltas else 0.0
    delta_stddev = pstdev(deltas) if len(deltas) > 1 else 0.0

    if "flatline" in settings.rules and pairs:
        flatline_threshold = settings.flatline_sigma_multiplier * delta_stddev
        flatline_run: list[tuple[int, int, float]] = []
        for pair in pairs:
            is_low_change = abs(pair[2]) <= flatline_threshold
            if is_low_change and (not flatline_run or pair[0] == flatline_run[-1][1]):
                flatline_run.append(pair)
            else:
                _apply_flatline_run(flatline_run, findings)
                flatline_run = [pair] if is_low_change else []
        _apply_flatline_run(flatline_run, findings)

    if "spike" in settings.rules and delta_stddev > 0:
        spike_threshold = settings.spike_sigma_multiplier * delta_stddev
        for left_index, right_index, delta in pairs:
            if abs(delta - delta_mean) > spike_threshold:
                _record(findings[right_index], "afgekeurd")


def _apply_geometry_rules(
    index: int,
    value: float,
    settings: ValidationSettings,
    findings: list[list[str]],
    tube_top: float | None,
    tube_bottom: float | None,
) -> None:
    if "below_tube_top" in settings.rules and tube_top is not None:
        if abs(value - tube_top) <= settings.tube_top_tolerance:
            _record(findings[index], "onbeslist")
        elif value > tube_top + settings.tube_top_tolerance:
            _record(findings[index], "afgekeurd")
        else:
            _record(findings[index], "goedgekeurd")

    if "above_tube_bottom" in settings.rules and tube_bottom is not None:
        if abs(value - tube_bottom) <= settings.tube_bottom_tolerance:
            _record(findings[index], "onbeslist")
        elif value < tube_bottom - settings.tube_bottom_tolerance:
            _record(findings[index], "afgekeurd")
        else:
            _record(findings[index], "goedgekeurd")

    if (
        "at_or_below_sensor_height" in settings.rules
        and settings.sensor_height is not None
    ):
        if abs(value - settings.sensor_height) <= settings.sensor_height_tolerance:
            _record(findings[index], "onbeslist")
        elif value > settings.sensor_height + settings.sensor_height_tolerance:
            _record(findings[index], "afgekeurd")
        else:
            _record(findings[index], "goedgekeurd")


def validate_measurements(
    measurements: list[TimeValuePair],
    settings: ValidationSettings,
    tube_top: float | None = None,
    tube_bottom: float | None = None,
) -> list[TimeValuePair]:
    """Set statusQualityControl for numeric values based on selected rules."""
    findings: list[list[str]] = [[] for _ in measurements]
    pairs = _measurement_deltas(measurements)
    _apply_statistical_rules(pairs, settings, findings)

    for index, measurement in enumerate(measurements):
        if measurement.value is None:
            continue
        _apply_geometry_rules(
            index,
            measurement.value,
            settings,
            findings,
            tube_top,
            tube_bottom,
        )

    for index, measurement in enumerate(measurements):
        if measurement.value is None:
            continue
        measurement.status_quality_control = _combine_statuses(findings[index])
    return measurements


def _apply_flatline_run(
    run: list[tuple[int, int, float]],
    findings: list[list[str]],
) -> None:
    if len(run) < FLATLINE_INTERVAL_COUNT:
        return
    _record(findings[run[0][0]], "afgekeurd")
    for _, right_index, _ in run:
        _record(findings[right_index], "afgekeurd")
