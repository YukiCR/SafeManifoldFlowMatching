import hashlib
import math

import numpy as np
import pytest
import torch
from scipy.io import savemat

from safe_manifold_flow.safety import SphereCapFilter
from safe_manifold_flow.safety_study import Phase2Study
from safe_manifold_flow.study import Phase1Study


@pytest.fixture(scope='module')
def baseline_fixture(tmp_path_factory):
    # A tiny checkpoint fixture, never a refit of the actual project model.
    folder = tmp_path_factory.mktemp('frozen-interface-fixture')
    path = folder / 'fixture.mat'
    pos = np.array([[-1.,-1.,-1.,-.5,0.],[1.,.5,0.,0.,0.]])
    savemat(path, {'demos':[{'pos':pos,'t':np.arange(5.)} for _ in range(7)]})
    baseline = Phase1Study.from_mat(path)
    baseline.fit(folder / 'checkpoint', epochs=2, context_mode='window')
    return path, folder / 'checkpoint' / 'best.pt', baseline


def test_paired_frozen_sampler_bypasses_steering_for_nominal_and_retains_failures(baseline_fixture):
    path, checkpoint, baseline = baseline_fixture
    bank = baseline.prepare_batch('test', seed=41, count=1)
    cap = SphereCapFilter(bank['noise'][0,0], activation=0)
    study = Phase2Study.from_checkpoint(path, checkpoint, cap, step=0.001, end=0.001)
    nominal = study.generate(bank['condition'], source=bank['noise'], guided=False)
    guided = study.generate(bank['condition'], source=bank['noise'], guided=True)

    assert nominal['failure_code'].tolist() == [0]
    assert int(guided['failure_code'][0]) != 0
    assert nominal['positions'].dtype == torch.float64
    torch.testing.assert_close(nominal['positions'].norm(dim=-1), torch.ones(1,8,dtype=torch.float64), atol=1e-12, rtol=0)
    assert study.checkpoint_sha256 == hashlib.sha256(checkpoint.read_bytes()).hexdigest()


def test_generation_records_the_matched_protocol_sources_and_geometric_diagnostics(baseline_fixture):
    path, checkpoint, baseline = baseline_fixture
    bank = baseline.prepare_batch('test', seed=51, count=2)
    cap = SphereCapFilter(torch.tensor([0.,0.,-1.]))
    study = Phase2Study.from_checkpoint(path, checkpoint, cap, step=.01, end=.6)
    result = study.generate(bank['condition'], bank['noise'], guided=True, snapshot_times=(0.,.5,.6))
    assert result['protocol'] == {'step':.01, 'end':.6, 'steps':60, 'state_precision':'float64', 'network_precision':'float32'}
    torch.testing.assert_close(result['source'], bank['noise'], atol=0, rtol=0)
    torch.testing.assert_close(result['condition'], bank['condition'].float(), atol=0, rtol=0)
    assert result['actual_clearance'].shape == (2,8)
    assert bool((result['actual_clearance'] > 0).all())
    assert bool((result['diagnostics']['min_qp_residual'] >= -1e-5).all())
    assert bool((result['diagnostics']['max_unit_norm_error'] < 1e-12).all())


def test_complete_portion_rejection_and_unused_tail_are_distinct(baseline_fixture):
    path, checkpoint, _ = baseline_fixture
    study = Phase2Study.from_checkpoint(path, checkpoint, SphereCapFilter(torch.tensor([0.,0.,1.])))
    chunk = torch.tensor([1.,0.,0.],dtype=torch.float64).expand(2,8,3).clone()
    chunk[0,2] = torch.tensor([0.,0.,1.])
    chunk[1,6] = torch.tensor([0.,0.,1.])
    decision = study.assess(chunk, use=4)
    assert decision['accepted'].tolist() == [False,True]
    assert decision['advance_count'].tolist() == [0,4]
    assert decision['whole_chunk_violation'].tolist() == [True,True]
    assert decision['unused_tail_violation'].tolist() == [False,True]


def test_rollout_stops_before_unsafe_portion_and_other_attempt_uses_own_history(baseline_fixture):
    path, checkpoint, _ = baseline_fixture
    cap = SphereCapFilter(torch.tensor([0.,0.,1.]),angle=.3,margin=.02)
    study = Phase2Study.from_checkpoint(path, checkpoint, cap, step=.001, end=.001)
    bootstrap = torch.tensor([1.,0.,0.],dtype=torch.float64).expand(2,2,3).clone()
    sources = torch.tensor([1.,0.,0.],dtype=torch.float64).expand(3,2,8,3).clone()
    sources[:,0] = torch.tensor([0.,0.,1.])
    result = study.rollout(bootstrap,seeds=[7,8],guided=False,length=11,source_bank=sources)
    assert [len(curve) for curve in result['positions']] == [2,11]
    assert result['stop_reasons'] == ['unsafe_execution_portion',None]
    assert [entry['reference_index'] for entry in result['trace']] == [1,5,9]
    assert result['trace'][0]['advance_count'].tolist() == [0,4]
    assert result['trace'][-1]['advance_count'].tolist() == [1]
    for entry in result['trace']:
        for row,attempt in enumerate(entry['attempt_indices']):
            c = int(entry['context_indices'][row]);r = entry['reference_index']
            assert c < r
            torch.testing.assert_close(entry['condition'][row,:3],result['positions'][attempt][r].float())
            torch.testing.assert_close(entry['condition'][row,3:6],result['positions'][attempt][c].float())


def test_evaluation_requires_completion_and_keeps_stopped_attempts_in_denominator(baseline_fixture):
    path, checkpoint, baseline = baseline_fixture
    study = Phase2Study.from_checkpoint(path, checkpoint, SphereCapFilter(torch.tensor([0.,0.,-1.])))
    result = {'positions':[baseline.points[0].clone(),baseline.points[1,:50].clone()],
              'stop_reasons':[None,'unsafe_execution_portion'],'seeds':[0,1],'length':200,'trace':[]}
    report = study.evaluate(result,demo_ids=[0,1])
    assert report['attempts'] == 2 and report['success_count'] == 1
    assert report['success_fraction'] == .5 and report['horizon_finished_count'] == 1
    assert report['rollouts'][0]['outside_mean_deg'] < 1e-10
    assert report['rollouts'][1]['failure'] == 'unsafe_execution_portion'
    assert report['rollouts'][1]['retained_count'] == 50
    assert report['rollouts'][1]['goal_deg'] > 5
