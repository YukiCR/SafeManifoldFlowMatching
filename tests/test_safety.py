import math

import torch
import pytest

from safe_manifold_flow.safety import SphereCapFilter


def test_boundary_projection_keeps_the_tangential_detour_and_removes_only_inward_motion():
    q = math.sqrt(3) / 2
    point = torch.tensor([0.5, 0.0, q], dtype=torch.float64)
    nominal = torch.tensor([-q / 2, 1.0, 0.25], dtype=torch.float64)
    cap = SphereCapFilter(torch.tensor([0.0, 0.0, 1.0]), angle=math.pi / 6, margin=0)

    result = cap.steer(0.75, point, nominal)

    torch.testing.assert_close(result['velocity'], torch.tensor([0.0, 1.0, 0.0], dtype=torch.float64), atol=1e-12, rtol=0)
    torch.testing.assert_close(result['correction'], torch.tensor([q / 2, 0.0, -0.25], dtype=torch.float64), atol=1e-12, rtol=0)


def test_before_activation_the_nominal_field_is_bypassed_even_when_inward():
    q = math.sqrt(3) / 2
    point = torch.tensor([0.5, 0.0, q], dtype=torch.float64)
    nominal = torch.tensor([-q / 2, 0.0, 0.25], dtype=torch.float64)
    cap = SphereCapFilter(torch.tensor([0.0, 0.0, 1.0]), angle=math.pi / 6, margin=0)

    result = cap.steer(0.25, point, nominal)

    torch.testing.assert_close(result['velocity'], nominal, atol=0, rtol=0)


def test_safe_antipode_keeps_a_feasible_velocity_without_dividing_by_zero():
    point = torch.tensor([0.0, 0.0, -1.0], dtype=torch.float64)
    nominal = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    result = SphereCapFilter(-point).steer(0.75, point, nominal)
    torch.testing.assert_close(result['velocity'], nominal, atol=0, rtol=0)


def test_unsafe_zero_gradient_reports_infeasibility_instead_of_a_valid_correction():
    point = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
    cap = SphereCapFilter(point)
    result = cap.steer(0.75, point, torch.zeros_like(point))
    assert int(result['failure_code']) == cap.INFEASIBLE
    assert bool(torch.isnan(result['velocity']).all())


def test_active_near_center_recovery_is_reported_as_ill_conditioned():
    point = torch.tensor([1e-9, 0.0, 1.0], dtype=torch.float64)
    cap = SphereCapFilter(torch.tensor([0.0, 0.0, 1.0]))
    result = cap.steer(0.75, point, torch.zeros_like(point))
    assert int(result['failure_code']) == 2
    assert bool(torch.isnan(result['velocity']).all())


def test_radial_fields_are_rejected_even_during_bypass():
    point = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    cap = SphereCapFilter(torch.tensor([0.0, 0.0, 1.0]))
    with pytest.raises(ValueError, match="tangent"):
        cap.steer(0.25, point, 0.001 * point)


def test_generation_recovers_an_unsafe_source_by_the_finite_cutoff_on_the_sphere():
    angle = math.radians(10)
    source = torch.tensor([math.sin(angle), 0.0, math.cos(angle)], dtype=torch.float64).expand(1, 8, 3).clone()
    cap = SphereCapFilter(torch.tensor([0.0, 0.0, 1.0]), angle=math.radians(15), margin=math.radians(5))

    result = cap.integrate(lambda time, point: torch.zeros_like(point), source, snapshot_times=(0.0, 0.5, 0.99))

    torch.testing.assert_close(result['snapshots'][0.5], source, atol=1e-12, rtol=0)
    final_angle = math.degrees(math.acos(float(result['positions'][0, 0, 2])))
    # Continuous scalar-barrier solution gives approximately 19.94 degrees.
    assert 19.8 < final_angle < 20.1
    torch.testing.assert_close(result['positions'].norm(dim=-1), torch.ones(1, 8, dtype=torch.float64), atol=1e-12, rtol=0)


def test_oversized_generation_step_fails_only_its_own_attempt_without_clipping():
    source = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64).expand(2, 8, 3).clone()
    omega = torch.tensor([[0.0, 0.0, 1.0], [0.0, 0.0, 1000.0]], dtype=torch.float64)[:, None]
    cap = SphereCapFilter(torch.tensor([0.0, 0.0, 1.0]))
    result = cap.integrate(lambda time, point: torch.linalg.cross(omega.expand_as(point), point), source, end=0.001)
    assert result['failure_code'].tolist() == [0, 3]
    expected = torch.tensor([math.cos(0.001), math.sin(0.001), 0.0], dtype=torch.float64).expand(8, 3)
    torch.testing.assert_close(result['positions'][0], expected, atol=1e-12, rtol=0)
    torch.testing.assert_close(result['positions'][1], source[1], atol=0, rtol=0)


@pytest.mark.parametrize('center,point', [([0.,0.,2.],[1.,0.,0.]), ([0.,0.,1.],[2.,0.,0.])])
def test_filter_requires_a_unit_sphere_center_and_state(center, point):
    with pytest.raises(ValueError, match='unit'):
        cap = SphereCapFilter(torch.tensor(center, dtype=torch.float64))
        x = torch.tensor(point, dtype=torch.float64)
        cap.steer(0.25, x, torch.zeros_like(x))


@pytest.mark.parametrize('guided', [True, False])
def test_numerical_field_failure_is_isolated_and_not_hidden_by_the_small_step(guided):
    source = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64).expand(2,8,3).clone()
    def field(time, point):
        result = torch.zeros_like(point)
        result[0,:,1] = 1.0
        result[1] = .001 * point[1]
        return result
    result = SphereCapFilter(torch.tensor([0.,0.,1.])).integrate(field, source, end=.001, guided=guided)
    assert result['failure_code'].tolist() == [0,4]
    expected = torch.tensor([math.cos(.001),math.sin(.001),0.],dtype=torch.float64).expand(8,3)
    torch.testing.assert_close(result['positions'][0], expected, atol=1e-12, rtol=0)


@pytest.mark.parametrize('options', [dict(end=1.), dict(step=.003,end=.01), dict(end=.01,snapshot_times=(.0015,))])
def test_generation_refuses_a_singular_or_mislabelled_time_grid(options):
    source = torch.tensor([1.,0.,0.],dtype=torch.float64).expand(1,8,3).clone()
    with pytest.raises(ValueError, match='grid'):
        SphereCapFilter(torch.tensor([0.,0.,1.])).integrate(lambda time,point: torch.zeros_like(point),source,**options)


def test_explicit_terminal_grid_returns_at_one_without_evaluating_the_singular_time():
    source = torch.tensor([1.,0.,0.],dtype=torch.float64).expand(1,8,3).clone()
    grid = torch.tensor([0.,.3,.6,.9,.99,.999,1.],dtype=torch.float64)
    omega = torch.tensor([0.,0.,.1],dtype=torch.float64)
    def field(time,point):
        assert time < 1, 'The generation field must only be evaluated at left endpoints'
        return torch.linalg.cross(omega.expand_as(point),point)
    result = SphereCapFilter(torch.tensor([0.,0.,1.])).integrate(field,source,time_grid=grid,snapshot_times=(0.,.99,1.))
    expected = torch.tensor([math.cos(.1),math.sin(.1),0.],dtype=torch.float64).expand_as(source)
    torch.testing.assert_close(result['positions'],expected,atol=1e-12,rtol=0)
    torch.testing.assert_close(result['snapshots'][1.],expected,atol=1e-12,rtol=0)
    assert result['protocol']['end'] == 1. and result['protocol']['steps'] == 6
    assert result['failure_code'].tolist() == [0]
