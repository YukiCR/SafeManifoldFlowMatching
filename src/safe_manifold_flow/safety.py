"""Generation-time minimum-change control in round-sphere tangent fibers."""

import math

import torch

from .geometry import SphereGeometry


class SphereCapFilter:
    """A single forbidden cap, represented intrinsically on the round sphere."""

    SUCCESS = 0
    INFEASIBLE = 1
    ILL_CONDITIONED = 2
    OVERSIZED_STEP = 3
    INVALID_FIELD = 4

    def __init__(self, center, angle=math.radians(6), margin=math.radians(1), gain=0.05, activation=0.5):
        self.center = center.to(torch.float64)
        if self.center.shape != (3,) or not torch.isfinite(self.center).all() or abs(float(self.center.norm()) - 1) > 2e-5:
            raise ValueError("unit sphere: expected a finite unit cap center")
        self.angle = angle
        self.margin = margin
        self.gain = gain
        self.activation = activation

    def steer(self, time, point, nominal):
        if point.shape[-1] != 3 or not torch.isfinite(point).all() or torch.any((point.norm(dim=-1) - 1).abs() > 2e-5):
            raise ValueError("unit sphere: expected finite unit states")
        if not torch.isfinite(nominal).all() or torch.any((point * nominal).sum(-1).abs() > 2e-5):
            raise ValueError("tangent: expected a finite nominal velocity in the current tangent fiber")
        if time < self.activation:
            return {"velocity": nominal.clone(), "correction": torch.zeros_like(nominal),
                    "failure_code": torch.zeros(point.shape[:-1], dtype=torch.int64),
                    "active": torch.zeros(point.shape[:-1], dtype=torch.bool),
                    "residual": torch.full(point.shape[:-1], math.nan, dtype=point.dtype)}
        dot = (point * self.center).sum(-1)
        barrier = math.cos(self.angle + self.margin) - dot
        gradient = dot[..., None] * point - self.center
        phi = self.gain / (1 - time) ** 2
        violation = (-(gradient * nominal).sum(-1) - phi * barrier).clamp_min(0)
        norm_square = gradient.square().sum(-1)
        # A feasible zero differential needs no correction; no constraint is relaxed.
        multiplier = torch.where(violation == 0, torch.zeros_like(violation), violation / norm_square)
        correction = multiplier[..., None] * gradient
        failure = torch.where((violation > 0) & (norm_square == 0), self.INFEASIBLE, self.SUCCESS)
        failure = torch.where((violation > 0) & (norm_square > 0) & (norm_square <= 1e-14),
                              self.ILL_CONDITIONED, failure)
        correction = torch.where((failure != 0)[..., None], torch.full_like(correction, math.nan), correction)
        velocity = nominal + correction
        return {"velocity": velocity, "correction": correction, "failure_code": failure,
                "active": (violation > 0) & (failure == 0),
                "residual": (gradient * velocity).sum(-1) + phi * barrier}

    def integrate(self, field, source, step=0.001, end=0.99, snapshot_times=(), guided=True, time_grid=None):
        if time_grid is None:
            if (not 0 < end < 1 or step <= 0 or abs(round(end / step) * step - end) > 1e-12
                    or any(t < 0 or t > end or abs(round(t / step) * step - t) > 1e-12 for t in snapshot_times)):
                raise ValueError("grid: require a finite preterminal endpoint and aligned step/snapshot times")
            times = [index * step for index in range(round(end / step))]
            deltas = [step] * len(times)
            requested = {round(t / step): t for t in snapshot_times}
            protocol = {"step": step, "end": end, "steps": len(times),
                        "state_precision": "float64", "network_precision": "float32"}
        else:
            grid = torch.as_tensor(time_grid, dtype=torch.float64)
            if (grid.ndim != 1 or len(grid) < 2 or not torch.isfinite(grid).all()
                    or float(grid[0]) != 0 or float(grid[-1]) > 1 or not bool((grid.diff() > 0).all())):
                raise ValueError("grid: require strictly increasing finite times from zero to at most one")
            times, deltas = grid[:-1].tolist(), grid.diff().tolist()
            requested = {}
            for t in snapshot_times:
                index = int((grid - t).abs().argmin())
                if abs(float(grid[index]) - t) > 1e-12:
                    raise ValueError("grid: snapshot time is not a grid node")
                requested[index] = t
            protocol = {"step": None, "end": float(grid[-1]), "steps": len(times),
                        "state_precision": "float64", "network_precision": "float32", "time_grid": grid.tolist()}
        point = source.to(torch.float64).clone()
        geometry = SphereGeometry()
        snapshots = {requested[0]: point.clone()} if 0 in requested else {}
        failure = torch.zeros(len(point), dtype=torch.int64)
        diagnostics = {
            "min_qp_residual": torch.full((len(point),), math.inf, dtype=point.dtype),
            "max_unit_norm_error": (point.norm(dim=-1) - 1).abs().amax(-1),
            "max_tangent_error": torch.zeros(len(point), dtype=point.dtype),
            "correction_energy": torch.zeros(len(point), dtype=point.dtype),
            "max_correction_norm": torch.zeros(len(point), dtype=point.dtype),
            "intervention_count": torch.zeros(len(point), dtype=torch.int64),
            "controlled_factor_steps": torch.zeros(len(point), dtype=torch.int64),
        }
        for index, (time, delta) in enumerate(zip(times, deltas)):
            nominal = field(time, point)
            invalid = (~torch.isfinite(nominal).all(-1) | ((point * nominal).sum(-1).abs() > 2e-5)).any(-1)
            failure = torch.where((failure == 0) & invalid, self.INVALID_FIELD, failure)
            nominal = torch.where((failure == 0)[:, None, None], nominal, torch.zeros_like(nominal))
            result = (self.steer(time, point, nominal) if guided else
                      {"velocity": nominal, "failure_code": torch.zeros(point.shape[:-1], dtype=torch.int64),
                       "correction": torch.zeros_like(nominal), "active": torch.zeros(point.shape[:-1], dtype=torch.bool),
                       "residual": torch.full(point.shape[:-1], math.nan, dtype=point.dtype)})
            velocity = result["velocity"]
            failure = torch.where(failure == 0, result["failure_code"].amax(-1), failure)
            oversized = (velocity.norm(dim=-1) * delta > 0.1).any(-1)
            failure = torch.where((failure == 0) & oversized, self.OVERSIZED_STEP, failure)
            healthy = failure == 0
            residual = torch.nan_to_num(result["residual"], nan=math.inf)
            residual = torch.where(healthy[:, None], residual, math.inf).amin(-1)
            diagnostics["min_qp_residual"] = torch.minimum(diagnostics["min_qp_residual"], residual)
            correction = torch.where(healthy[:, None, None], result["correction"], 0.)
            energy = correction.square().sum((-1, -2))
            diagnostics["correction_energy"] += energy * delta
            diagnostics["max_correction_norm"] = torch.maximum(diagnostics["max_correction_norm"], energy.sqrt())
            diagnostics["intervention_count"] += (result["active"] & healthy[:, None]).sum(-1)
            if guided and time >= self.activation:
                diagnostics["controlled_factor_steps"] += healthy.to(torch.int64) * point.shape[1]
            # Failed rows hold their last finite generation state for diagnostics.
            # Their nonzero failure status prevents any physical advancement.
            velocity = torch.where((failure == 0)[:, None, None], velocity, torch.zeros_like(velocity))
            diagnostics["max_tangent_error"] = torch.maximum(diagnostics["max_tangent_error"],
                                                               (point * velocity).sum(-1).abs().amax(-1))
            point = geometry.exp(point, delta * velocity)
            diagnostics["max_unit_norm_error"] = torch.maximum(diagnostics["max_unit_norm_error"],
                                                                 (point.norm(dim=-1) - 1).abs().amax(-1))
            if index + 1 in requested:
                snapshots[requested[index + 1]] = point.clone()
        distance = geometry.distance(point, self.center)
        return {"positions": point, "snapshots": snapshots, "failure_code": failure,
                "actual_clearance": distance - self.angle,
                "internal_clearance": distance - self.angle - self.margin,
                "diagnostics": diagnostics,
                "protocol": protocol}
