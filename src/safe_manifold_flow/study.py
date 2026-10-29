"""The public Phase 1 study: recorded data, conditional learning and evaluation."""

import copy
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
from scipy.io import loadmat

from .geometry import SphereGeometry


class _Swish(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.beta = torch.nn.Parameter(torch.ones(()))

    def forward(self, value):
        return value * torch.sigmoid(self.beta * value)


class _RFMP(torch.nn.Module):
    def __init__(self):
        super().__init__()
        layers = []
        width = 32  # 24 noisy coordinates + time + 7 observation/context values.
        for _ in range(5):
            layers.extend([torch.nn.Linear(width, 64), _Swish()])
            width = 64
        layers.append(torch.nn.Linear(64, 24))
        self.network = torch.nn.Sequential(*layers)

    def forward(self, time, point, condition):
        batch = len(point)
        time = time.reshape(-1, 1).expand(batch, 1)
        ambient = self.network(torch.cat([point.reshape(batch, 24), time, condition], dim=-1)).reshape(batch, 8, 3)
        return ambient - (ambient * point).sum(dim=-1, keepdim=True) * point


class Phase1Study:
    """A reproducible original-RFMP study on seven spherical LShape records."""

    @classmethod
    def from_mat(cls, path):
        path = Path(path)
        records = loadmat(path, simplify_cells=True)["demos"]
        if len(records) != 7:
            raise ValueError("data: expected seven original recordings")
        planar = []
        for record in records:
            position = np.asarray(record["pos"], dtype=float)
            if position.ndim != 2 or position.shape[0] != 2 or not np.isfinite(position).all():
                raise ValueError("data: expected finite 2-by-time positions")
            time = np.asarray(record.get("t", np.arange(position.shape[1])), dtype=float).reshape(-1)
            if len(time) != position.shape[1] or not np.isfinite(time).all() or not np.all(np.diff(time) > 0):
                raise ValueError("data: expected strictly increasing time samples")
            time = (time - time[0]) / (time[-1] - time[0])
            planar.append(np.stack([np.interp(np.linspace(0, 1, 200), time, row) for row in position], axis=-1))
        planar = np.stack(planar)
        study = cls()
        study.geometry = SphereGeometry()
        study.pairs = torch.tensor([(demo, reference) for demo in range(7) for reference in range(1, 199)])
        order = torch.randperm(len(study.pairs), generator=torch.Generator().manual_seed(0))
        n_train, n_val = int(0.8 * len(order)), int(0.1 * len(order))
        study.splits = {"train": order[:n_train], "validation": order[n_train:n_train+n_val], "test": order[n_train+n_val:]}
        radius = max(np.linalg.norm(planar[d, :min(r + 9, 200)], axis=-1).max() for d, r in study.pairs[study.splits["train"]].tolist())
        if radius <= 0:
            raise ValueError("data: training information has no nonzero angular extent")
        study.scale = float((math.pi / 3) / radius)
        tangent = torch.zeros(7, 200, 3, dtype=torch.float64)
        tangent[..., :2] = torch.from_numpy(planar * study.scale)
        study.points = study.geometry.exp(torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64), tangent)
        study.source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        study.source_path = str(path.resolve())
        return study

    def prepare_batch(self, split: str, seed: int, count=None, pairs=None):
        generator = torch.Generator().manual_seed(seed)
        if pairs is None:
            ids = self.splits[split]
            if count is not None:
                ids = ids[torch.randint(len(ids), (count,), generator=generator)]
            pairs = self.pairs[ids]
        demo, reference = pairs[:, 0], pairs[:, 1]
        context = pairs[:, 2] if pairs.shape[1] == 3 else (torch.rand(len(pairs), generator=generator) * reference).long()
        future = (reference[:, None] + torch.arange(1, 9)).clamp_max(199)
        condition = torch.cat([
            self.points[demo, reference], self.points[demo, context],
            ((reference + 1 - context).to(torch.float64) / 200)[:, None],
        ], dim=-1)
        tangent = torch.zeros(len(pairs), 3, dtype=torch.float64)
        tangent[:, :2] = math.sqrt(0.5) * torch.randn(len(pairs), 2, dtype=torch.float64, generator=generator)
        noise = self.geometry.exp(torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64), tangent)
        return {
            "target": self.points[demo[:, None], future],
            "condition": condition,
            "demo_indices": demo,
            "reference_indices": reference,
            "context_indices": context,
            "noise": noise[:, None].expand(-1, 8, -1).clone(),
            "time": torch.rand(len(pairs), dtype=torch.float64, generator=generator),
        }

    def _training_inputs(self, batch):
        point, velocity = self.geometry.path(batch["noise"], batch["target"], batch["time"])
        return point.float(), velocity.float(), batch["time"].float(), batch["condition"].float()

    @staticmethod
    def _loss(model, inputs):
        point, velocity, time_value, condition = inputs
        error = model(time_value, point, condition) - velocity
        return error.square().sum(dim=(-1, -2)).mean()

    def fit(self, output_dir, epochs=200, verbose=False, context_mode="all"):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        torch.set_num_threads(2)
        torch.manual_seed(0)
        model = _RFMP()
        ema = copy.deepcopy(model)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
        validation = self.prepare_batch("validation", seed=100_000)
        validation_inputs = self._training_inputs(validation)
        with torch.no_grad():
            initial = float(self._loss(ema, validation_inputs))
        best, best_epoch = initial, 0
        best_state = copy.deepcopy(ema.state_dict())
        history = []
        shuffle = torch.Generator().manual_seed(0)
        base = self.pairs[self.splits["train"]]
        if context_mode == "all":
            self.training_pairs = torch.tensor([(d, r, c) for d, r in base.tolist() for c in range(r)])
        elif context_mode == "window":
            self.training_pairs = base
        else:
            raise ValueError("training: context_mode must be 'all' or 'window'")
        examples = len(self.training_pairs)
        batches_per_epoch = math.ceil(examples/128)
        start = time.perf_counter()
        for epoch in range(epochs):
            order = torch.randperm(examples, generator=shuffle)
            losses = []
            for offset in range(0, len(order), 128):
                pairs = self.training_pairs[order[offset:offset+128]]
                # Preserve the first-attempt window protocol; expanded epochs use unique draw seeds.
                stride = 100 if context_mode == "window" else batches_per_epoch
                batch = self.prepare_batch("train", seed=1000+epoch*stride+offset//128, pairs=pairs)
                inputs = self._training_inputs(batch)
                optimizer.zero_grad()
                loss = self._loss(model, inputs)
                loss.backward()
                optimizer.step()
                with torch.no_grad():
                    for averaged, current in zip(ema.parameters(), model.parameters()):
                        averaged.lerp_(current, 0.001)
                losses.append(float(loss.detach()))
            with torch.no_grad():
                score = float(self._loss(ema, validation_inputs))
            history.append({"epoch": epoch+1, "train_loss": float(np.mean(losses)), "validation_loss": score})
            if score < best:
                best, best_epoch = score, epoch+1
                best_state = copy.deepcopy(ema.state_dict())
            if verbose and (epoch == 0 or (epoch+1) % 10 == 0):
                print(json.dumps(history[-1]), flush=True)
        self.model = ema
        self.model.load_state_dict(best_state)
        self.model.eval()
        with torch.no_grad():
            test = self.prepare_batch("test", seed=200_000)
            test_loss = float(self._loss(self.model, self._training_inputs(test)))
        self.training_report = {
            "epochs": epochs, "best_epoch": best_epoch, "initial_validation": initial,
            "best_validation": best, "test_loss": test_loss,
            "parameter_count": sum(p.numel() for p in model.parameters()),
            "context_mode": context_mode, "examples_per_epoch": examples,
            "optimizer_steps": epochs*batches_per_epoch,
            "seconds": time.perf_counter()-start, "history": history,
        }
        torch.save({"model": best_state, "source_hash": self.source_hash, "scale": self.scale,
                    "splits": self.splits, "pairs": self.pairs, "training": self.training_report}, output_dir / "best.pt")
        torch.save({"validation": validation, "test": test}, output_dir / "banks.pt")
        torch.save(self.training_pairs, output_dir / "training_pairs.pt")
        (output_dir / "training.json").write_text(json.dumps(self.training_report, indent=2))
        self.output_dir = output_dir
        return self.training_report

    @torch.no_grad()
    def generate(self, condition, source=None, seed=0, snapshot_times=None):
        if source is None:
            tangent = torch.zeros(len(condition), 3, dtype=torch.float64)
            tangent[:, :2] = math.sqrt(0.5)*torch.randn(len(condition), 2, dtype=torch.float64,
                                                     generator=torch.Generator().manual_seed(seed))
            point = self.geometry.exp(torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64), tangent)
            source = point[:, None].expand(-1, 8, -1).clone()
        condition = condition.float()
        return self.geometry.integrate(lambda s, point: self.model(s, point, condition), source.float(),
                                       steps=100, snapshot_times=snapshot_times)

    def load_checkpoint(self, path):
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        if checkpoint["source_hash"] != self.source_hash or checkpoint["scale"] != self.scale:
            raise ValueError("checkpoint: source data or preprocessing mismatch")
        self.model = _RFMP()
        self.model.load_state_dict(checkpoint["model"])
        self.model.eval()
        self.training_report = checkpoint["training"]
        self.output_dir = Path(path).parent
        return self

    @torch.no_grad()
    def rollout(self, bootstrap, seeds, length=200):
        if bootstrap.shape[1:] != (2, 3) or len(seeds) != len(bootstrap) or length < 2:
            raise ValueError("rollout: expected two supplied positions and one seed per attempt")
        positions = bootstrap.float().clone()
        trace = []
        while positions.shape[1] < length:
            reference = positions.shape[1] - 1
            context, tangents = [], []
            for seed in seeds:
                generator = torch.Generator().manual_seed(seed*1_000_000 + len(trace)*10_000 + 301)
                context.append(int(torch.randint(reference, (), generator=generator)))
                tangents.append(torch.cat([math.sqrt(0.5)*torch.randn(2, dtype=torch.float64, generator=generator), torch.zeros(1, dtype=torch.float64)]))
            context = torch.tensor(context)
            condition = torch.cat([
                positions[:, reference], positions[torch.arange(len(positions)), context],
                ((reference+1-context).float()/200)[:, None],
            ], dim=-1)
            noise = self.geometry.exp(torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64), torch.stack(tangents))
            source = noise[:, None].expand(-1, 8, -1).clone()
            chunk = self.generate(condition, source=source)
            trace.append({"reference_index": reference, "context_indices": context,
                          "condition": condition.clone(), "source": source})
            use = min(4, length-positions.shape[1])
            positions = torch.cat([positions, chunk[:, :use]], dim=1)
        return {"positions": positions, "trace": trace, "seeds": list(seeds)}

    def evaluate_rollouts(self, positions, demo_ids, seeds):
        if len(positions) != len(demo_ids) or len(positions) != len(seeds):
            raise ValueError("evaluation: one recording and seed required per attempt")
        rows = []
        for curve, demo, seed in zip(positions, demo_ids, seeds):
            finite = bool(torch.isfinite(curve).all())
            norm_error = float((curve.norm(dim=-1)-1).abs().max()) if finite else None
            valid = finite and norm_error <= 2e-5
            row = {"demo": int(demo), "seed": int(seed), "valid": valid,
                   "norm_error": norm_error, "success": False}
            if valid:
                target = self.points[demo].to(curve.dtype)
                costs = self.geometry.distance(curve[:, None], target[None]).numpy()
                total = np.full((len(curve)+1, len(target)+1), np.inf)
                count = np.zeros_like(total, dtype=int)
                total[0, 0] = 0
                for i in range(1, len(curve)+1):
                    for j in range(1, len(target)+1):
                        previous = min([(i-1, j-1), (i-1, j), (i, j-1)], key=lambda ij: total[ij])
                        total[i, j] = total[previous]+costs[i-1, j-1]
                        count[i, j] = count[previous]+1
                dtw = math.degrees(total[-1, -1]/count[-1, -1])
                goal = math.degrees(float(self.geometry.distance(curve[-1], target[-1])))
                jump = math.degrees(float(self.geometry.distance(curve[1:], curve[:-1]).max()))
                row.update(dtw_deg=dtw, goal_deg=goal, max_jump_deg=jump,
                           success=goal <= 5 and dtw <= 10 and jump <= 20,
                           failure=None if goal <= 5 and dtw <= 10 and jump <= 20 else "motion_quality")
            else:
                row.update(dtw_deg=None, goal_deg=None, max_jump_deg=None, failure="invalid_geometry")
            rows.append(row)
        successes = sum(row["success"] for row in rows)
        training = getattr(self, "training_report", {})
        improved = training.get("best_validation", math.inf) < training.get("initial_validation", -math.inf)
        return {"attempts": len(rows), "success_count": successes,
                "success_fraction": successes/len(rows),
                "freeze_gate_passed": all(row["valid"] for row in rows) and successes/len(rows) >= 0.8 and improved,
                "validation_improved": improved, "rollouts": rows}
