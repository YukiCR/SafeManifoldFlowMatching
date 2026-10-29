import math

import pytest
import torch

from safe_manifold_flow.geometry import SphereGeometry


def test_training_path_matches_a_known_quarter_great_circle():
    sphere = SphereGeometry()
    source = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    target = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

    point, velocity = sphere.path(source, target, torch.tensor(0.5, dtype=torch.float64))

    q = math.sqrt(0.5)
    torch.testing.assert_close(point, torch.tensor([q, 0.0, q], dtype=torch.float64), atol=1e-8, rtol=0)
    torch.testing.assert_close(
        velocity,
        torch.tensor([math.pi * q / 2, 0.0, -math.pi * q / 2], dtype=torch.float64),
        atol=1e-8,
        rtol=0,
    )


def test_coincident_training_points_have_a_constant_path_and_zero_velocity():
    point = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    middle, velocity = SphereGeometry().path(point, point, torch.tensor(0.5, dtype=torch.float64))
    torch.testing.assert_close(middle, point)
    torch.testing.assert_close(velocity, torch.zeros(3, dtype=torch.float64))


def test_antipodal_training_path_reports_its_nonunique_logarithm():
    north = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    with pytest.raises(ValueError, match="cut_locus"):
        SphereGeometry().path(north, -north, torch.tensor(0.5, dtype=torch.float64))


def test_factorwise_flow_generates_a_known_chunk_on_the_product_sphere():
    source = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64).expand(2, 8, 3).clone()
    generator = torch.tensor([0.0, math.pi / 2, 0.0], dtype=torch.float64)

    def field(time, points):
        return torch.linalg.cross(generator.expand_as(points), points)

    result = SphereGeometry().integrate(field, source, steps=16)

    target = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64).expand_as(result)
    torch.testing.assert_close(result, target, atol=1e-8, rtol=0)
    torch.testing.assert_close(result.norm(dim=-1), torch.ones(2, 8, dtype=torch.float64), atol=1e-8, rtol=0)


def test_generation_rejects_a_radial_field_instead_of_calling_it_manifold_motion():
    north = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    with pytest.raises(ValueError, match="tangent"):
        SphereGeometry().integrate(lambda time, point: point, north, steps=2)


def test_small_steps_do_not_hide_an_invalid_radial_velocity():
    north = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    with pytest.raises(ValueError, match="tangent"):
        SphereGeometry().integrate(lambda time, point: 0.001 * point, north, steps=100)
