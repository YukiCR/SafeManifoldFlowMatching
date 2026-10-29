import math

import numpy as np
import torch
from scipy.io import savemat

from safe_manifold_flow.study import Phase1Study


def write_fixture(path):
    # A MAT-format test fixture, never project training/evaluation evidence.
    position = np.array([[-1.0, -1.0, -1.0, -0.5, 0.0], [1.0, 0.5, 0.0, 0.0, 0.0]])
    savemat(path, {"demos": [{"pos": position, "t": np.arange(5.0)} for _ in range(7)], "dt": 1.0})


def test_preparation_preserves_records_and_embeds_the_declared_goal(tmp_path):
    path = tmp_path / "fixture.mat"
    write_fixture(path)
    study = Phase1Study.from_mat(path)

    assert study.points.shape == (7, 200, 3)
    torch.testing.assert_close(study.points.norm(dim=-1), torch.ones(7, 200, dtype=torch.float64))
    torch.testing.assert_close(study.points[:, -1], torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64).expand(7, 3))
    torch.testing.assert_close(study.points[:, 0, 2], torch.full((7,), math.cos(math.pi / 3), dtype=torch.float64))


def test_training_batch_uses_past_context_and_terminal_padding(tmp_path):
    path = tmp_path / "fixture.mat"
    write_fixture(path)
    study = Phase1Study.from_mat(path)
    batch = study.prepare_batch("train", seed=9, pairs=torch.tensor([[0, 198]]))

    assert int(batch["context_indices"][0]) < 198
    torch.testing.assert_close(batch["target"], torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64).expand(1, 8, 3))
    angle = 2 * (math.pi / (3 * math.sqrt(2))) / 199
    torch.testing.assert_close(batch["condition"][0, :3], torch.tensor([-math.sin(angle), 0.0, math.cos(angle)], dtype=torch.float64))
    assert float(batch["condition"][0, -1]) == (199 - int(batch["context_indices"][0])) / 200


def test_rfmp_prior_repeats_one_sphere_draw_per_chunk_reproducibly(tmp_path):
    path = tmp_path / "fixture.mat"
    write_fixture(path)
    study = Phase1Study.from_mat(path)
    first = study.prepare_batch("validation", seed=17, count=10)
    second = study.prepare_batch("validation", seed=17, count=10)
    torch.testing.assert_close(first["noise"], second["noise"])
    torch.testing.assert_close(first["noise"], first["noise"][:, :1].expand(10, 8, 3))
    torch.testing.assert_close(first["noise"].norm(dim=-1), torch.ones(10, 8, dtype=torch.float64))


def test_bounded_fit_improves_its_fixed_validation_bank_and_generates(tmp_path):
    path = tmp_path / "fixture.mat"
    write_fixture(path)
    study = Phase1Study.from_mat(path)
    report = study.fit(tmp_path / "run", epochs=20, context_mode="window")
    assert report["best_validation"] < report["initial_validation"]
    batch = study.prepare_batch("test", seed=21, count=3)
    generated = study.generate(batch["condition"], source=batch["noise"])
    assert generated.shape == (3, 8, 3)
    torch.testing.assert_close(generated.norm(dim=-1), torch.ones(3, 8), atol=2e-5, rtol=0)


def test_checkpoint_reload_reproduces_the_same_seeded_generation(tmp_path):
    path = tmp_path / "fixture.mat"
    write_fixture(path)
    study = Phase1Study.from_mat(path)
    study.fit(tmp_path / "run", epochs=2, context_mode="window")
    batch = study.prepare_batch("test", seed=31, count=2)
    original = study.generate(batch["condition"], source=batch["noise"])

    restored = Phase1Study.from_mat(path).load_checkpoint(tmp_path / "run" / "best.pt")
    actual = restored.generate(batch["condition"], source=batch["noise"])
    torch.testing.assert_close(actual, original, atol=0, rtol=0)


def test_rollout_conditions_on_generated_history_and_uses_a_final_partial_chunk(tmp_path):
    path = tmp_path / "fixture.mat"
    write_fixture(path)
    study = Phase1Study.from_mat(path)
    study.fit(tmp_path / "run", epochs=2, context_mode="window")
    bootstrap = study.points[:2, :2]
    result = study.rollout(bootstrap, seeds=[3, 4], length=11)
    positions = result["positions"]

    assert positions.shape == (2, 11, 3)
    torch.testing.assert_close(positions[:, :2], bootstrap.float())
    assert [step["reference_index"] for step in result["trace"]] == [1, 5, 9]
    for step in result["trace"]:
        reference, context = step["reference_index"], step["context_indices"]
        assert bool((context < reference).all())
        torch.testing.assert_close(step["condition"][:, :3], positions[:, reference])
        torch.testing.assert_close(step["condition"][:, 3:6], positions[torch.arange(2), context])


def test_transport_snapshots_include_the_actual_prior_and_returned_chunk(tmp_path):
    path = tmp_path / "fixture.mat"
    write_fixture(path)
    study = Phase1Study.from_mat(path)
    study.fit(tmp_path / "run", epochs=2, context_mode="window")
    batch = study.prepare_batch("test", seed=5, count=2)
    flow = study.generate(batch["condition"], source=batch["noise"], snapshot_times=(0.0, 0.5, 1.0))
    torch.testing.assert_close(flow["snapshots"][0.0], batch["noise"].float())
    torch.testing.assert_close(flow["snapshots"][1.0], flow["positions"])
    torch.testing.assert_close(flow["snapshots"][0.5].norm(dim=-1), torch.ones(2, 8), atol=2e-5, rtol=0)


def test_evaluation_retains_failed_motions_in_the_success_denominator(tmp_path):
    path = tmp_path / "fixture.mat"
    write_fixture(path)
    study = Phase1Study.from_mat(path)
    positions = torch.stack([study.points[0], -study.points[1]]).float()
    report = study.evaluate_rollouts(positions, demo_ids=[0, 1], seeds=[0, 0])
    assert report["attempts"] == 2
    assert report["success_count"] == 1
    assert report["success_fraction"] == 0.5
    assert not report["freeze_gate_passed"]
    assert report["rollouts"][0]["dtw_deg"] < 1e-5
    assert abs(report["rollouts"][1]["goal_deg"] - 180.0) < 1e-4


def test_epoch_covers_every_valid_context_of_each_training_window(tmp_path):
    path = tmp_path / "fixture.mat"
    write_fixture(path)
    study = Phase1Study.from_mat(path)
    report = study.fit(tmp_path / "run", epochs=1, context_mode="all")
    expected = int(study.pairs[study.splits["train"], 1].sum())
    assert report["examples_per_epoch"] == expected
    assert report["optimizer_steps"] == math.ceil(expected / 128)
    demo, reference = study.pairs[study.splits["train"]][0].tolist()
    rows = study.training_pairs
    contexts = rows[(rows[:, 0] == demo) & (rows[:, 1] == reference), 2].sort().values
    torch.testing.assert_close(contexts, torch.arange(reference))
