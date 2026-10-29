"""Animate actual frozen-RFMP rollouts; never fit or modify the baseline model.

Run from the repository root with PYTHONPATH=src. Rendering uses an orthographic
projection of the embedded sphere. Zooming changes only the camera scale.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch

from safe_manifold_flow.study import Phase1Study


WIDTH, HEIGHT = 1280, 800
INK = "#17263C"
MUTED = "#5A6C80"
ORANGE = "#D99822"
TEAL = "#078B80"
PURPLE = "#7055C6"
PINK = "#C54681"
GRAY = "#A9B4C1"
FONT_ROOT = Path("/usr/share/fonts/truetype/dejavu")
FONTS = {}


def font(size, bold=False):
    key = size, bold
    if key not in FONTS:
        FONTS[key] = ImageFont.truetype(
            str(FONT_ROOT / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size
        )
    return FONTS[key]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture(study, output, seeds, baseline):
    """Replay the public rollout interface, retaining every actual solver step."""
    demos = [0, 0, 0]
    rollout = study.rollout(study.points[demos, :2], seeds=seeds)
    snapshots = []
    times = tuple(i / 100 for i in range(101))
    for step in rollout["trace"]:
        flow = study.generate(step["condition"], source=step["source"], snapshot_times=times)
        r = step["reference_index"]
        use = min(4, 199 - r)
        torch.testing.assert_close(
            flow["positions"][:, :use], rollout["positions"][:, r + 1:r + 1 + use],
            atol=0, rtol=0,
        )
        snapshots.append(torch.stack([flow["snapshots"][t] for t in times]))
    chunks = torch.stack(snapshots)  # replan, generation step, rollout, waypoint, xyz
    assert len(rollout["trace"]) == 50
    assert torch.isfinite(chunks).all()
    norm_error = float((chunks.norm(dim=-1) - 1).abs().max())
    assert norm_error <= 2e-5
    sources = torch.stack([step["source"] for step in rollout["trace"]])
    assert bool((sources == sources[:, :, :1]).all())
    assert len(torch.unique(sources[:, :, 0].reshape(-1, 3), dim=0)) == 150
    torch.save({"rollout": rollout, "chunks": chunks, "generation_times": times,
                "demos": demos, "seeds": seeds}, output / "generation_records.pt")
    evaluation = study.evaluate_rollouts(rollout["positions"], demos, seeds)
    (output / "evaluation.json").write_text(json.dumps(evaluation, indent=2) + "\n")
    manifest = {
        "purpose": "Three independent stochastic rollouts of ONE frozen RFMP model",
        "checkpoint_sha256": baseline["artifacts_sha256"]["best.pt"],
        "source_sha256": study.source_hash,
        "baseline_code_commit": baseline["code_commit"],
        "model_code_sha256": baseline["code_sha256"],
        "seeds": seeds, "bootstrap_recording_zero_based": 0,
        "bootstrap_positions": 2, "rollout_positions": 200,
        "replans_per_video": 50, "prediction_horizon": 8, "execution_horizon": 4,
        "last_execution_count": 2, "integration_steps": 100,
        "snapshots_per_solve": 101,
        "solver": "Unmodified factorwise sphere-exponential Euler, ds=0.01",
        "prior": "One wrapped-Gaussian draw, tangent covariance 0.5 I, repeated 8 times",
        "generated_history_only_after_bootstrap": True,
        "exact_replayed_chunks_match_rollout": True,
        "max_all_snapshot_unit_norm_residual": norm_error,
        "distinct_source_points": 150,
        "generation_records_sha256": digest(output / "generation_records.pt"),
        "evaluation": evaluation,
    }
    (output / "capture_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Captured 3 independent rollouts, 150 FM solves, 15,150 joint snapshots; "
          f"quality gate {evaluation['success_count']}/3.", flush=True)


def arcs(points, samples=10):
    """Shortest spherical arcs, for drawing only; no rollout interpolation."""
    points = np.asarray(points, dtype=float)
    if len(points) < 2:
        return points
    a, b = points[:-1], points[1:]
    theta = np.arctan2(np.linalg.norm(np.cross(a, b), axis=-1), (a * b).sum(-1))
    t = np.linspace(0, 1, samples)[None, :, None]
    # sinc form handles coincident consecutive directions without a singularity.
    den = np.sinc(theta / np.pi)[:, None, None]
    first = (1 - t) * np.sinc((1 - t) * theta[:, None, None] / np.pi) / den
    second = t * np.sinc(t * theta[:, None, None] / np.pi) / den
    return (first * a[:, None] + second * b[:, None]).reshape(-1, 3)


def projection(points, center=(346, 398), scale=245):
    xy = np.asarray(points)[..., :2] * np.array([1, -1])
    return xy * scale + np.asarray(center)


def line(draw, coordinates, color, width=2):
    if len(coordinates) > 1:
        draw.line([tuple(p) for p in coordinates], fill=color, width=width, joint="curve")


def dot(draw, coordinate, color, radius=5, hollow=False):
    x, y = coordinate
    box = x - radius, y - radius, x + radius, y + radius
    draw.ellipse(box, fill=None if hollow else color, outline=color, width=2)


def background(study, video, seed):
    frame = Image.new("RGB", (WIDTH, HEIGHT), "#F8FAFD")
    draw = ImageDraw.Draw(frame)
    draw.text((44, 23), "Riemannian flow matching on S²", font=font(32, True), fill=INK)
    draw.text((45, 69), f"Independent rollout {video}  ·  seed {seed}  ·  one frozen RFMP model",
              font=font(19), fill=MUTED)
    draw.text((90, 120), "Spherical task and rollout history", font=font(21, True), fill=INK)
    radius = 245
    u, v = np.meshgrid(np.linspace(-1, 1, radius * 2), np.linspace(1, -1, radius * 2))
    mask = u * u + v * v <= 1
    z = np.sqrt(np.maximum(0, 1 - u * u - v * v))
    brightness = np.clip(0.64 + 0.23 * (-0.3 * u + 0.45 * v + 0.84 * z), 0, 1)
    shade = np.stack([brightness * 233 + 20] * 3, axis=-1).astype(np.uint8)
    disc = Image.fromarray(shade)
    alpha = Image.fromarray((mask * 255).astype(np.uint8))
    frame.paste(disc, (346 - radius, 398 - radius), alpha)
    draw = ImageDraw.Draw(frame, "RGBA")
    longitude = np.linspace(0, 2 * np.pi, 300)
    for angle in [np.pi / 6, np.pi / 3, np.pi / 2]:
        circle = np.stack([np.sin(angle) * np.cos(longitude),
                           np.sin(angle) * np.sin(longitude), np.full_like(longitude, np.cos(angle))], -1)
        line(draw, projection(circle), (110, 125, 145, 35), 1)
    for meridian in np.linspace(0, np.pi, 6, endpoint=False):
        line(draw, projection(np.array([[-np.cos(meridian), -np.sin(meridian), 0],
                                         [np.cos(meridian), np.sin(meridian), 0]])), (110, 125, 145, 28), 1)
    for curve in study.points.numpy():
        line(draw, projection(arcs(curve, 3)), (217, 152, 34, 145), 2)
    dot(draw, projection(np.array([0, 0, 1])), ORANGE, 5)
    draw.text((357, 406), "goal", font=font(14), fill=MUTED)
    draw.rounded_rectangle((694, 124, 1242, 470), 18, fill="white", outline="#DDE4ED", width=1)
    draw.text((719, 144), "Current eight-position chunk", font=font(22, True), fill=INK)
    draw.text((719, 180), "Magnified orthographic projection of S²", font=font(15), fill=MUTED)
    draw.text((719, 207), "Black: current direction   ·   pink on sphere: context", font=font(12), fill=MUTED)
    draw.text((719, 445), "Numbers indicate future-position order", font=font(14), fill=MUTED)
    for x, color, name in [(84, ORANGE, "LASA reference"), (279, TEAL, "Used history"), (470, PURPLE, "FM candidates")]:
        draw.line((x, 659, x + 24, 659), fill=color, width=4)
        draw.text((x + 33, 647), name, font=font(14), fill=MUTED)
    draw.text((44, 765), "Actual solver states · no retraining · Phase 1 has no safety filter",
              font=font(14), fill=MUTED)
    draw.text((860, 765), "Front hemisphere: solid · back: hollow", font=font(13), fill=MUTED)
    return frame


def draw_frame(base, history, chunk, trail, context, cycle, solver_step, stage, use, metrics=None):
    frame = base.copy()
    draw = ImageDraw.Draw(frame, "RGBA")
    line(draw, projection(arcs(history, 4)), TEAL, 4)
    for i in range(8):
        line(draw, projection(trail[:, i]), (112, 85, 198, 45), 1)
    current = history[-1]
    dot(draw, projection(context), PINK, 6, hollow=True)
    if stage in ["select", "advance", "done"]:
        line(draw, projection(arcs(chunk)), (150, 163, 179, 180), 2)
        line(draw, projection(arcs(chunk[:use])), TEAL, 3)
        if stage == "select":
            line(draw, projection(arcs(np.stack([current, chunk[0]]))), TEAL, 3)
    for i, point in enumerate(chunk):
        color = PURPLE if stage in ["sample", "flow"] else (TEAL if i < use else GRAY)
        dot(draw, projection(point), color, 4, hollow=bool(point[2] < 0))
    dot(draw, projection(current), "white", 8)
    dot(draw, projection(current), INK, 5)

    # Zoom is a display transform, never an alternative manifold computation.
    cloud = np.concatenate([current[None], chunk])
    xy = cloud[:, :2] * [1, -1]
    low, high = xy.min(0), xy.max(0)
    zoom_scale = min(420 / max(high[0] - low[0], 0.02), 196 / max(high[1] - low[1], 0.02), 4096)
    mid = (low + high) / 2

    def zoom(points):
        return ((np.asarray(points)[..., :2] * [1, -1]) - mid) * zoom_scale + [968, 323]

    # Reference axes for the magnified orthographic projection, not a tangent chart.
    draw.line((736, 323, 1200, 323), fill="#EFF2F7", width=1)
    draw.line((968, 218, 968, 428), fill="#EFF2F7", width=1)
    line(draw, zoom(arcs(chunk)), "#D8CFF0" if stage in ["sample", "flow"] else GRAY, 2)
    if stage in ["select", "advance", "done"]:
        line(draw, zoom(arcs(chunk[:use])), TEAL, 3)
        if stage == "select":
            line(draw, zoom(arcs(np.stack([current, chunk[0]]))), TEAL, 3)
    labels = []
    for i, point in enumerate(chunk):
        color = PURPLE if stage in ["sample", "flow"] else (TEAL if i < use else GRAY)
        p = zoom(point)
        dot(draw, p, color, 5, hollow=bool(point[2] < 0))
        if solver_step >= 90:
            labels.append((i, p, color))
    # Label placement is a display operation; the generated points never move.
    for side in [0, 1]:
        entries = sorted([entry for entry in labels if entry[0] % 2 == side], key=lambda entry: entry[1][1])
        ys = []
        for _, point, _ in entries:
            ys.append(max(point[1] - 7, ys[-1] + 18 if ys else 222))
        if ys and ys[-1] > 421:
            ys = [y - (ys[-1] - 421) for y in ys]
        for (index, point, color), y in zip(entries, ys):
            x = point[0] + (26 if side else -34)
            endpoint = (x - 3 if side else x + 14, y + 8)
            draw.line([tuple(point), endpoint], fill=color, width=1)
            draw.text((x, y), str(index + 1), font=font(13, True), fill=color)
    dot(draw, zoom(current), INK, 5)
    if solver_step == 0:
        p = zoom(chunk[0])
        draw.text((max(735, min(p[0] - 65, 1050)), p[1] + 12), "8 coincide", font=font(15, True), fill=PURPLE)

    titles = {"sample": "1  Sample a new source", "flow": "2  Flow on the product sphere",
              "select": f"3  Select the next {use} directions", "advance": "3  Advance, then replan",
              "done": "Trajectory generation complete"}
    lines = {
        "sample": ["One wrapped-Gaussian direction, repeated ×8.", "History is fixed during this FM solve."],
        "flow": ["A learned tangent field moves all 8 positions.", "The rollout direction has not advanced yet."],
        "select": [f"Use the first {use} of 8 predicted positions.", "Discard the tail after advancing; sample again."],
        "advance": ["Append the selected directions to the history.", "The next solve conditions on this new history."],
        "done": [f"Goal error: {metrics['goal_deg']:.2f}°" if metrics else "",
                 f"Angular DTW: {metrics['dtw_deg']:.2f}°" if metrics else ""],
    }
    draw.text((719, 490), titles[stage], font=font(23, True), fill=INK)
    for i, value in enumerate(lines[stage]):
        draw.text((719, 531 + 29 * i), value, font=font(17), fill=MUTED)
    draw.text((719, 600), f"Replan {cycle + 1:02d} / 50", font=font(20, True), fill=INK)
    draw.text((1017, 602), f"FM time s = {solver_step / 100:.2f}", font=font(18), fill=PURPLE)
    draw.rounded_rectangle((720, 636, 1230, 646), 5, fill="#E6EAF1")
    if solver_step:
        draw.rounded_rectangle((720, 636, 720 + 510 * solver_step / 100, 646), 5, fill=PURPLE)

    for i, name in enumerate(["SAMPLE", "TANGENT FLOW", "SELECT & ADVANCE"]):
        active = i == {"sample": 0, "flow": 1, "select": 2, "advance": 2, "done": 2}[stage]
        x = 46 + i * 405
        draw.rounded_rectangle((x, 693, x + 376, 732), 9, fill=INK if active else "#E7ECF3")
        draw.text((x + 17, 701), name, font=font(16, True), fill="white" if active else MUTED)
    draw.text((44, 102), f"Rollout: {len(history):03d} / 200 directions", font=font(14), fill=TEAL)
    return frame


def render(study, output, fps):
    records = torch.load(output / "generation_records.pt", weights_only=True)
    rollout, chunks = records["rollout"], records["chunks"].numpy()
    positions = rollout["positions"].numpy()
    evaluation = json.loads((output / "evaluation.json").read_text())
    rendered = []
    storyboard = []
    for video, seed in enumerate(records["seeds"]):
        path = output / f"rollout_{video + 1:02d}_seed_{seed}.mp4"
        log = output / f"rollout_{video + 1:02d}_ffmpeg.log"
        base = background(study, video + 1, seed)
        frame_count = 0
        with log.open("w") as error_log:
            encoder = subprocess.Popen([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
                "-s", f"{WIDTH}x{HEIGHT}", "-r", str(fps), "-i", "-", "-an",
                "-c:v", "libx264", "-threads", "2", "-preset", "fast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path),
            ], stdin=subprocess.PIPE, stderr=error_log)

            def emit(frame, repeat=1):
                nonlocal frame_count
                raw = frame.tobytes()
                for _ in range(repeat):
                    encoder.stdin.write(raw)
                frame_count += repeat

            try:
                for cycle, step in enumerate(rollout["trace"]):
                    r = step["reference_index"]
                    history = positions[video, :r + 1]
                    context = positions[video, int(step["context_indices"][video])]
                    flow = chunks[cycle, :, video]
                    use = min(4, 199 - r)
                    args = (base, history, flow[0], flow[:1], context, cycle, 0, "sample", use)
                    sample = draw_frame(*args)
                    emit(sample, 24 if cycle == 0 else 6)
                    if cycle == 0:
                        sample.save(output / f"rollout_{video + 1:02d}_poster.png")
                    for index in (range(101) if cycle == 0 else range(0, 101, 5)):
                        frame = draw_frame(base, history, flow[index], flow[:index + 1], context,
                                           cycle, index, "flow", use)
                        emit(frame)
                        if video == 0 and cycle == 0 and index in [0, 50, 100]:
                            storyboard.append(frame.copy())
                    selected = draw_frame(base, history, flow[-1], flow, context,
                                          cycle, 100, "select", use)
                    emit(selected, 36 if cycle == 0 else 8)
                    if video == 0 and cycle == 0:
                        storyboard.append(selected.copy())
                    for added in range(1, use + 1):
                        frame = draw_frame(base, positions[video, :r + 1 + added], flow[-1], flow,
                                           context, cycle, 100, "advance", use)
                        emit(frame, 6 if cycle == 0 else 2)
                    if (cycle + 1) % 10 == 0:
                        print(f"Video {video + 1}/3: rendered {cycle + 1}/50 replans", flush=True)
                final = draw_frame(base, positions[video], flow[-1], flow, context, 49, 100,
                                   "done", use, evaluation["rollouts"][video])
                emit(final, 72)
                final.save(output / f"rollout_{video + 1:02d}_final.png")
                encoder.stdin.close()
                if encoder.wait() != 0:
                    raise RuntimeError(f"Encoding failed; see {log}")
            finally:
                if encoder.poll() is None:
                    encoder.kill()
                    encoder.wait()
        rendered.append({"path": path.name, "seed": seed, "frames": frame_count,
                         "fps": fps, "duration_seconds": frame_count / fps,
                         "sha256": digest(path)})
        print(f"Saved {path} ({frame_count / fps:.1f} seconds)", flush=True)
    sheet = Image.new("RGB", (1280, 800), "white")
    for i, frame in enumerate(storyboard):
        sheet.paste(frame.resize((640, 400), Image.Resampling.LANCZOS), ((i % 2) * 640, (i // 2) * 400))
    sheet.save(output / "first_cycle_storyboard.png")
    metadata = {"videos": rendered, "resolution": [WIDTH, HEIGHT], "codec": "H.264 / yuv420p",
                "script_sha256": digest(__file__),
                "display": "Orthographic north-pole view; right pane magnifies that projection",
                "timing": "First cycle slowed. Later flow frames use actual solver steps 0,5,...,100.",
                "no_interpolated_FM_states": True, "sphere_arcs_are_display_only": True}
    (output / "video_manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=Path("runs/phase1-context-expanded"))
    parser.add_argument("--data", type=Path, default=Path("data/raw/LShape.mat"))
    parser.add_argument("--seeds", type=int, nargs=3, default=[101, 202, 303])
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--capture-only", action="store_true")
    parser.add_argument("--render-only", action="store_true")
    args = parser.parse_args()
    if len(set(args.seeds)) != 3 or args.fps < 1:
        parser.error("Use three distinct seeds and a positive frame rate")
    output = args.run / "viz"
    output.mkdir(parents=True, exist_ok=True)
    baseline = json.loads(Path("docs/results/phase1_baseline.json").read_text())
    assert digest(args.run / "best.pt") == baseline["artifacts_sha256"]["best.pt"]
    for name, expected in baseline["code_sha256"].items():
        assert digest(Path("src/safe_manifold_flow") / name) == expected, name
    torch.set_num_threads(2)
    study = Phase1Study.from_mat(args.data).load_checkpoint(args.run / "best.pt")
    if not args.render_only:
        if (output / "generation_records.pt").exists():
            raise FileExistsError("Capture already exists; use --render-only to preserve the draws")
        capture(study, output, args.seeds, baseline)
    if not args.capture_only:
        render(study, output, args.fps)
    for name, expected in baseline["artifacts_sha256"].items():
        assert digest(args.run / name) == expected, name
    print("Frozen baseline artifacts are unchanged.", flush=True)


if __name__ == "__main__":
    main()
