"""Safety adaptation of a frozen Phase 1 model, with matched numerical protocols."""

import hashlib
import math
from collections import Counter
from pathlib import Path
import time

import torch

from .study import Phase1Study


class Phase2Study:
    """The public paired-generation and rollout boundary; no fitting interface."""

    @classmethod
    def from_checkpoint(cls, data, checkpoint, cap, step=0.001, end=0.99, time_grid=None):
        torch.set_num_threads(2)
        study = cls()
        study.baseline = Phase1Study.from_mat(data).load_checkpoint(checkpoint)
        study.cap = cap
        study.step = step
        study.end = end
        study.time_grid = time_grid
        study.checkpoint_sha256 = hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()
        return study

    @torch.no_grad()
    def generate(self, condition, source, guided=True, snapshot_times=()):
        condition = condition.float()

        def field(time, point):
            ambient = self.baseline.model(torch.tensor(time, dtype=torch.float32), point.float(), condition).double()
            return ambient - (ambient * point).sum(-1, keepdim=True) * point

        result = self.cap.integrate(field, source, step=self.step, end=self.end,
                                    guided=guided, snapshot_times=snapshot_times, time_grid=self.time_grid)
        result["source"] = source.clone()
        result["condition"] = condition.clone()
        return result

    def assess(self, chunk, use=4):
        """Accept a whole execution portion, while diagnosing the unused tail."""
        chunk = chunk.double()
        if not 1 <= use <= chunk.shape[1]:
            raise ValueError("acceptance: invalid execution-portion length")
        valid = torch.isfinite(chunk).all((-1, -2)) & ((chunk.norm(dim=-1) - 1).abs().amax(-1) <= 2e-5)
        clearance = torch.full(chunk.shape[:-1], torch.nan, dtype=chunk.dtype)
        if bool(valid.any()):
            clearance[valid] = self.baseline.geometry.distance(chunk[valid], self.cap.center) - self.cap.angle
        unsafe = ~(clearance >= 0)
        execution_violation = unsafe[:, :use].any(-1)
        accepted = valid & ~execution_violation
        return {"accepted": accepted, "advance_count": accepted.to(torch.int64) * use,
                "valid_geometry": valid, "execution_violation": execution_violation,
                "whole_chunk_violation": unsafe.any(-1),
                "unused_tail_violation": unsafe[:, use:].any(-1), "actual_clearance": clearance}

    @torch.no_grad()
    def rollout(self, bootstrap, seeds, guided=True, length=200, source_bank=None, snapshot_times=()):
        """Replan from generated history; reject an entire unsafe next portion."""
        if bootstrap.shape[1:] != (2, 3) or len(bootstrap) != len(seeds) or length < 2:
            raise ValueError("rollout: expected two bootstrap directions and one seed per attempt")
        start = time.perf_counter()
        histories = [curve.double().clone() for curve in bootstrap]
        stop_reasons = [None] * len(histories)
        initial = self.assess(bootstrap, use=2)
        for attempt in range(len(histories)):
            if not bool(initial["valid_geometry"][attempt]):
                stop_reasons[attempt] = "invalid_initial_geometry"
            elif not bool(initial["accepted"][attempt]):
                stop_reasons[attempt] = "unsafe_initial_history"
        trace = []
        north = torch.tensor([0., 0., 1.], dtype=torch.float64)
        labels = {1: "infeasible_cbf", 2: "ill_conditioned_cbf", 3: "oversized_generation_step", 4: "invalid_field"}
        while True:
            indices = [i for i, curve in enumerate(histories) if stop_reasons[i] is None and len(curve) < length]
            if not indices:
                break
            reference = len(histories[indices[0]]) - 1
            contexts, sources = [], []
            for attempt in indices:
                generator = torch.Generator().manual_seed(seeds[attempt] * 1_000_000 + len(trace) * 10_000 + 301)
                contexts.append(int(torch.randint(reference, (), generator=generator)))
                tangent = torch.zeros(3, dtype=torch.float64)
                tangent[:2] = math.sqrt(0.5) * torch.randn(2, dtype=torch.float64, generator=generator)
                sources.append(self.baseline.geometry.exp(north, tangent))
            context = torch.tensor(contexts)
            condition = torch.stack([
                torch.cat([histories[i][reference], histories[i][c],
                           torch.tensor([(reference + 1 - c) / 200], dtype=torch.float64)])
                for i, c in zip(indices, contexts)
            ])
            source = torch.stack(sources)[:, None].expand(-1, 8, -1).clone()
            if source_bank is not None:
                source = source_bank[len(trace), indices].double().clone()
            generation = self.generate(condition, source, guided=guided, snapshot_times=snapshot_times)
            proposal = generation["positions"]
            use = min(4, length - reference - 1)
            decision = self.assess(proposal, use=use)
            accepted = decision["accepted"] & (generation["failure_code"] == 0)
            for row, attempt in enumerate(indices):
                code = int(generation["failure_code"][row])
                if code:
                    stop_reasons[attempt] = labels.get(code, "numerical_failure")
                elif not bool(decision["valid_geometry"][row]):
                    stop_reasons[attempt] = "invalid_generated_geometry"
                elif not bool(accepted[row]):
                    stop_reasons[attempt] = "unsafe_execution_portion"
                else:
                    histories[attempt] = torch.cat([histories[attempt], proposal[row, :use]])
            entry = dict(generation)
            entry["proposal"] = entry.pop("positions")
            entry.update(decision)
            entry.update(attempt_indices=indices, reference_index=reference, context_indices=context,
                         accepted=accepted, advance_count=accepted.to(torch.int64) * use)
            trace.append(entry)
        return {"positions": histories, "trace": trace, "stop_reasons": stop_reasons,
                "seeds": list(seeds), "length": length, "guided": guided,
                "sampling_seconds": time.perf_counter() - start}

    def evaluate(self, result, demo_ids):
        """Score all attempts, retaining stopped prefixes rather than padding them."""
        start = time.perf_counter()
        if len(result["positions"]) != len(demo_ids):
            raise ValueError("evaluation: one recording per attempted rollout")
        rows = []
        for attempt, (curve, demo, seed, stopped) in enumerate(zip(
                result["positions"], demo_ids, result["seeds"], result["stop_reasons"])):
            base = self.baseline.evaluate_rollouts(curve[None], [demo], [seed])["rollouts"][0]
            row = dict(base, retained_count=len(curve), horizon_finished=len(curve) == 200,
                       stop_reason=stopped, outside_mean_deg=None, outside_max_deg=None,
                       outside_count=0, unsafe_used_directions=0, minimum_used_clearance_deg=None,
                       minimum_retained_clearance_deg=None, minimum_internal_clearance_deg=None,
                       tail_travel_deg=None, initial_history_safe=False)
            if base["valid"]:
                distance = self.baseline.geometry.distance(curve, self.cap.center)
                clearance = torch.rad2deg(distance - self.cap.angle)
                row["initial_history_safe"] = bool((clearance[:2] >= 0).all())
                row["minimum_retained_clearance_deg"] = float(clearance.min())
                row["minimum_internal_clearance_deg"] = float(clearance.min()) - math.degrees(self.cap.margin)
                if len(curve) > 2:
                    row["minimum_used_clearance_deg"] = float(clearance[2:].min())
                    row["unsafe_used_directions"] = int((clearance[2:] < 0).sum())
                    outside = curve[2:][distance[2:] >= math.radians(12)]
                    row["outside_count"] = len(outside)
                    if len(outside):
                        errors = torch.rad2deg(self.baseline.geometry.distance(
                            outside[:, None], self.baseline.points[demo][None])).amin(-1)
                        row["outside_mean_deg"] = float(errors.mean())
                        row["outside_max_deg"] = float(errors.max())
                if len(curve) >= 22:
                    row["tail_travel_deg"] = math.degrees(float(self.baseline.geometry.distance(
                        curve[-20:-1], curve[-19:]).sum()))
            row.update(generation_calls=0, valid_proposals=0, numerical_generation_failures=0,
                       unsafe_execution_proposals=0, whole_chunk_violations=0, unused_tail_violations=0,
                       minimum_proposed_clearance_deg=None, minimum_internal_proposal_clearance_deg=None,
                       correction_energy=0., max_correction_norm=0., intervention_count=0,
                       controlled_factor_steps=0, min_qp_residual=None, max_tangent_error=0.)
            for entry in result["trace"]:
                if attempt not in entry["attempt_indices"]:
                    continue
                r = entry["attempt_indices"].index(attempt)
                row["generation_calls"] += 1
                diagnostics = entry["diagnostics"]
                for key in ["correction_energy", "intervention_count", "controlled_factor_steps"]:
                    row[key] += diagnostics[key][r].item()
                for key in ["max_correction_norm", "max_tangent_error"]:
                    row[key] = max(row[key], float(diagnostics[key][r]))
                residual = float(diagnostics["min_qp_residual"][r])
                if math.isfinite(residual):
                    row["min_qp_residual"] = residual if row["min_qp_residual"] is None else min(row["min_qp_residual"], residual)
                if int(entry["failure_code"][r]):
                    row["numerical_generation_failures"] += 1
                    continue
                row["valid_proposals"] += 1
                row["unsafe_execution_proposals"] += int(entry["execution_violation"][r])
                row["whole_chunk_violations"] += int(entry["whole_chunk_violation"][r])
                row["unused_tail_violations"] += int(entry["unused_tail_violation"][r])
                for key, values in [("minimum_proposed_clearance_deg", entry["actual_clearance"]),
                                    ("minimum_internal_proposal_clearance_deg", entry["internal_clearance"])]:
                    value = math.degrees(float(values[r].min()))
                    row[key] = value if row[key] is None else min(row[key], value)
            row["intervention_fraction"] = (row["intervention_count"] / row["controlled_factor_steps"]
                                             if row["controlled_factor_steps"] else None)
            failures = [stopped] if stopped else []
            if not row["valid"]:
                failures.append("invalid_geometry")
            else:
                if not row["horizon_finished"]:
                    failures.append("incomplete_horizon")
                if not row["initial_history_safe"] or row["unsafe_used_directions"]:
                    failures.append("unsafe_retained_directions")
                if row["goal_deg"] > 5:
                    if row["horizon_finished"] and row["tail_travel_deg"] is not None and row["tail_travel_deg"] <= 1:
                        failures.append("stalled")
                    else:
                        failures.append("goal_not_reached")
                if row["dtw_deg"] > 10:
                    failures.append("shape_fidelity")
                if row["max_jump_deg"] > 20:
                    failures.append("excessive_jump")
                if row["outside_mean_deg"] is None or row["outside_mean_deg"] > 3:
                    failures.append("outside_fidelity")
            row["failure_reasons"] = list(dict.fromkeys(failures))
            row["failure"] = row["failure_reasons"][0] if failures else None
            row["success"] = not failures
            rows.append(row)
        proposals = sum(row["valid_proposals"] for row in rows)
        calls = sum(row["generation_calls"] for row in rows)
        unsafe_proposals = sum(row["unsafe_execution_proposals"] for row in rows)
        successes = sum(row["success"] for row in rows)
        return {
            "attempts": len(rows), "success_count": successes, "success_fraction": successes / len(rows),
            "horizon_finished_count": sum(row["horizon_finished"] for row in rows),
            "goal_reached_count": sum(row["valid"] and row["goal_deg"] <= 5 for row in rows),
            "failure_counts": dict(Counter(row["failure"] for row in rows if row["failure"])),
            "unsafe_used_directions": sum(row["unsafe_used_directions"] for row in rows),
            "valid_proposals": proposals, "generation_calls": calls,
            "unsafe_execution_proposals": unsafe_proposals,
            "preaccept_execution_violation_fraction": unsafe_proposals / proposals if proposals else None,
            "whole_chunk_violations": sum(row["whole_chunk_violations"] for row in rows),
            "unused_tail_violations": sum(row["unused_tail_violations"] for row in rows),
            "numerical_generation_failures": sum(row["numerical_generation_failures"] for row in rows),
            "sampling_seconds": result.get("sampling_seconds"),
            "scoring_seconds": time.perf_counter() - start, "rollouts": rows,
        }
