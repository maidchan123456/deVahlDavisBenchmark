"""Offline preregistered policy/evidence checks. Never launches OpenFOAM."""
import bisect
import math
import sys

TEMPORAL_TARGET = 0.005
ITERATIVE_BUDGET = TEMPORAL_TARGET / 100
OUTER_CHANGE_LIMIT = ITERATIVE_BUDGET / 500
ARRIVAL_RANGE_LIMIT = TEMPORAL_TARGET / 100
ARRIVAL_TREND_LIMIT = ARRIVAL_RANGE_LIMIT / 2
N_OUTER = 24
N_PRESSURE = 2
MIN_T_STAR = 0.5
MAX_T_STAR = 2.0
WINDOW_T_STAR = 0.1
CONFIRMATIONS = 3
T_CHAR = 710.0
CELL_THERMAL_TIME = T_CHAR / 160**2
FIRST_PHYSICAL_DT = CELL_THERMAL_TIME / 1000
CONTROL_DICT_DT = FIRST_PHYSICAL_DT / 1.2
MAX_DT = CELL_THERMAL_TIME
MAX_STEPS = 2_000_000


def controller_step(old_h, control_co, target):
    """Static/source-free native foamRun controller; not a recovery controller."""
    if not all(math.isfinite(v) for v in (old_h, control_co, target)):
        raise ValueError("NONFINITE_CONTROLLER")
    if old_h <= 0 or control_co < 0 or target not in (0.5, 0.25, 0.125):
        raise ValueError("WRONG_CONTROLLER")
    # Foundation v13 DP doubleScalarSmall equals numeric_limits<double>::epsilon().
    cap = min(MAX_DT, target / control_co * old_h) if control_co > sys.float_info.epsilon else MAX_DT
    return min(1.2 * old_h, cap)


def minimum_dt(time):
    """64 representable increments at the larger physical-time scale."""
    return 64 * math.ulp(max(abs(time), T_CHAR))


def certify_outer(changes, floors):
    """Four terminal transitions, monitored individually; conditional tail bound.

    Contraction or representational-floor plateau is required. This is a local
    engineering certificate, not a rigorous global trajectory-error theorem.
    """
    required = {"U", "T", "p_rgh", "rho_s", "rho_T",
                "Nu_bar_cavity", "Umax", "Wmax"}
    if set(changes) != required or set(floors) != required:
        raise ValueError("OUTER_OBSERVABLES_MISSING")
    estimates = {}
    for name in sorted(required):
        values = changes[name]
        floor = floors[name]
        if len(values) != 4 or not math.isfinite(floor) or not 0 <= floor <= OUTER_CHANGE_LIMIT:
            raise ValueError("OUTER_FLOOR_NOT_RESOLVABLE")
        if any(not math.isfinite(v) or v < 0 or v > OUTER_CHANGE_LIMIT for v in values):
            raise ValueError("NONLINEAR_CONVERGENCE_FAILURE")
        if max(values) <= floor:
            tail = 4 * floor
        else:
            if any(values[i] > 0.5 * values[i - 1] for i in range(1, 4)):
                raise ValueError("NONLINEAR_CONTRACTION_NOT_ESTABLISHED")
            tail = 2 * values[-1]  # deliberately exceeds q/(1-q) Δ at q<=1/2
        if tail > ITERATIVE_BUDGET:
            raise ValueError("ITERATIVE_BUDGET_EXCEEDED")
        estimates[name] = tail
    return estimates


def validate_linear(records):
    seen = set()
    for field, initial, final, iterations in records:
        if field not in {"Ux", "Uy", "e", "p_rgh", "rho"}:
            raise ValueError("WRONG_LINEAR_FIELD")
        limit = 1e-14 if field == "rho" else 1e-12
        cap = 4000 if field == "p_rgh" else 1 if field == "rho" else 2000
        if (not math.isfinite(initial) or not math.isfinite(final)
            or initial < 0 or final < 0 or final > limit
            or not isinstance(iterations, int) or not 0 <= iterations <= cap):
            raise ValueError("LINEAR_CONVERGENCE_FAILURE")
        seen.add(field)
    if seen != {"Ux", "Uy", "e", "p_rgh", "rho"}:
        raise ValueError("LINEAR_EVIDENCE_MISSING")


def interpolate(times, values, x):
    if len(times) != len(values) or len(times) < 2:
        raise ValueError("HISTORY_SIZE")
    if any(not math.isfinite(v) for v in times + values):
        raise ValueError("HISTORY_NONFINITE")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("HISTORY_DUPLICATE_OR_REVERSED")
    if x < times[0] or x > times[-1]:
        raise ValueError("HISTORY_EXTRAPOLATION")
    i = bisect.bisect_right(times, x) - 1
    if i == len(times) - 1:
        return values[-1]
    fraction = (x - times[i]) / (times[i + 1] - times[i])
    return values[i] + fraction * (values[i + 1] - values[i])


def integral(times, values, left, right):
    points = [left] + [x for x in times if left < x < right] + [right]
    y = [interpolate(times, values, x) for x in points]
    return math.fsum((b-a)*(u+v)/2 for a,b,u,v in zip(points,points[1:],y,y[1:]))


def window_stats(times, values, right, scale=1.0, width=WINDOW_T_STAR):
    left = right - width
    if scale <= 0 or width <= 0:
        raise ValueError("WINDOW_SCALE")
    points = [left] + [x for x in times if left < x < right] + [right]
    y = [interpolate(times, values, x) for x in points]
    mean = integral(times, values, left, right) / width
    first = integral(times, values, left, left+width/2)/(width/2)
    second = integral(times, values, left+width/2, right)/(width/2)
    # Exact continuous OLS of piecewise-linear data, using centred t to avoid
    # cancellation from a large absolute time origin.
    centre = (left+right)/2
    tq = math.fsum((b-a)*((2*(a-centre)+(b-centre))*u
                    +((a-centre)+2*(b-centre))*v)/6
                  for a,b,u,v in zip(points,points[1:],y,y[1:]))
    slope = tq / (width**3/12)
    denom = max(abs(mean), scale)
    return {"left": left, "right": right, "mean": mean,
            "endpoint": y[-1], "range": (max(y)-min(y))/denom,
            "half_mean_drift": abs(second-first)/denom,
            "normalized_slope_span": abs(slope)*width/denom,
            "slope": slope}


def arrival_candidate(times, histories, endpoint, support_scales, evaluator_valid):
    """QoI and state stationarity, never conservation accuracy PASS."""
    primary = {"Nu_bar_cavity", "Umax", "Wmax"}
    support = {"rho_min", "rho_max", "rho_mean", "total_mass", "energy_storage"}
    if set(histories) != primary | support or set(support_scales) != support:
        raise ValueError("ARRIVAL_HISTORY_MISSING")
    if endpoint < MIN_T_STAR or endpoint > MAX_T_STAR or not evaluator_valid:
        return False, []
    if abs(endpoint/WINDOW_T_STAR-round(endpoint/WINDOW_T_STAR)) > 64*math.ulp(max(1.,abs(endpoint/WINDOW_T_STAR))):
        return False, []
    windows = []
    for i in range(CONFIRMATIONS):
        right = endpoint - (CONFIRMATIONS-1-i)*WINDOW_T_STAR
        stats = {}
        for name, values in histories.items():
            # Primary denominator follows v1.0. Supporting STATE deviations
            # use fixed physical perturbation scales, not large rho/e means.
            if name in primary:
                result = window_stats(times, values, right, 1.0)
            else:
                # Centre around its initial value only for stationarity scale;
                # raw conserved-functional evidence is never recentered.
                centred = [v-values[0] for v in values]
                result = window_stats(times, centred, right, support_scales[name])
                result["mean"] += values[0]
                result["endpoint"] += values[0]
            stats[name] = result
            if (result["range"] > ARRIVAL_RANGE_LIMIT
                or result["half_mean_drift"] > ARRIVAL_TREND_LIMIT
                or result["normalized_slope_span"] > ARRIVAL_RANGE_LIMIT):
                return False, windows
        windows.append(stats)
    return True, windows


class StageLedger:
    """Evidence ordering verifier; does not insert native solver hooks."""
    def __init__(self):
        self.seen = set()
        self.sequence = []

    def accept(self, packet):
        required = {"time_index", "time", "outer", "pressure", "energy_solve",
                    "stage", "oldTime_ids", "dt", "dt_previous"}
        if not required <= packet.keys() or not packet["oldTime_ids"]:
            raise ValueError("STAGE_METADATA_MISSING")
        if (any(type(packet[k]) is not int or packet[k] < 0
                for k in ("time_index","outer","pressure","energy_solve"))
            or not isinstance(packet["stage"], str) or not packet["stage"]
            or not isinstance(packet["oldTime_ids"], list)
            or any(not isinstance(s, str) or not s for s in packet["oldTime_ids"])):
            raise ValueError("STAGE_METADATA_INVALID")
        if (not all(math.isfinite(packet[k]) for k in ("time","dt","dt_previous"))
            or packet["dt"] <= 0 or packet["dt_previous"] <= 0):
            raise ValueError("STAGE_TIME_INVALID")
        key = tuple(packet[k] for k in ("time_index","outer","pressure","energy_solve","stage"))
        if key in self.seen:
            raise ValueError("STAGE_DUPLICATE")
        self.seen.add(key)
        self.sequence.append(key)

    def expect(self, sequence):
        if self.sequence != sequence:
            raise ValueError("STAGE_MISSING_OR_REORDERED")
