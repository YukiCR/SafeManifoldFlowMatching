"""Canonical unit-round-sphere operations on embedded tangent vectors."""

import math

import torch


class SphereGeometry:
    """Factorwise geometry; final dimension is the three ambient coordinates."""

    def _check_point(self, point: torch.Tensor):
        if point.shape[-1] != 3 or not torch.isfinite(point).all():
            raise ValueError("geometry: expected finite three-coordinate sphere points")
        if torch.any((point.norm(dim=-1) - 1).abs() > 2e-5):
            raise ValueError("geometry: point is not on the unit sphere")

    def exp(self, point: torch.Tensor, tangent: torch.Tensor) -> torch.Tensor:
        point, tangent = torch.broadcast_tensors(point, tangent)
        self._check_point(point)
        if not torch.isfinite(tangent).all() or torch.any((point * tangent).sum(-1).abs() > 2e-5):
            raise ValueError("tangent: expected finite velocity based at the sphere point")
        radius = torch.linalg.vector_norm(tangent, dim=-1, keepdim=True)
        result = torch.cos(radius) * point + torch.sinc(radius / math.pi) * tangent
        # Correct only floating-point drift after the exponential, not an Euler retraction.
        return result / result.norm(dim=-1, keepdim=True)

    def log(self, point: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        self._check_point(point)
        self._check_point(target)
        dot = (point * target).sum(dim=-1, keepdim=True)
        direction = target - dot * point
        length = torch.linalg.vector_norm(direction, dim=-1, keepdim=True)
        if torch.any((dot < 0) & (length < 1e-7)):
            raise ValueError("cut_locus: antipodal logarithm is not uniquely defined")
        angle = torch.atan2(length, dot)
        return angle * direction / length.clamp_min(torch.finfo(point.dtype).eps)

    def path(self, source: torch.Tensor, target: torch.Tensor, time: torch.Tensor):
        shooting = self.log(source, target)

        def curve(t):
            while t.ndim < source.ndim - 1:
                t = t.unsqueeze(-1)
            return self.exp(source, t.unsqueeze(-1) * shooting)

        return torch.func.jvp(curve, (time,), (torch.ones_like(time),))

    def integrate(self, field, source: torch.Tensor, steps: int = 100) -> torch.Tensor:
        if steps < 1:
            raise ValueError("integration: steps must be positive")
        self._check_point(source)
        point = source.clone()
        for index in range(steps):
            time = torch.tensor(index / steps, dtype=point.dtype, device=point.device)
            velocity = field(time, point)
            if not torch.isfinite(velocity).all() or torch.any((point * velocity).sum(-1).abs() > 2e-5):
                raise ValueError("tangent: generation field is not a finite tangent velocity")
            point = self.exp(point, velocity / steps)
        return point
