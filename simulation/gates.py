from __future__ import annotations

import argparse
import os
import random

from control.app import build_pipeline
from simulation.simulation_loop import SimulationRunner


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def run_fast(cycles: int = 5) -> tuple[bool, str]:
    pipeline, configs = build_pipeline(_base_dir())
    runner = SimulationRunner(pipeline, configs["perception"])
    successes = runner.run(cycles)
    ok = successes == cycles
    return ok, f"sim-fast: successes={successes}/{cycles}"


def run_regression() -> tuple[bool, list[str]]:
    messages: list[str] = []
    all_ok = True

    # 1) Nominal
    pipeline, configs = build_pipeline(_base_dir())
    runner = SimulationRunner(pipeline, configs["perception"])
    target = 20
    successes = runner.run(target)
    ok = successes == target
    all_ok &= ok
    messages.append(f"regression/nominal: {'OK' if ok else 'FAIL'} ({successes}/{target})")

    # 2) Low confidence -> perception should fail and safe-stop
    pipeline, configs = build_pipeline(_base_dir())
    runner = SimulationRunner(pipeline, configs["perception"])
    base = configs["perception"].get("mock_pose", {})
    pos = base.get("position_mm", [0.0, 0.0, 0.0])
    quat = base.get("quaternion_xyzw", [0.0, 0.0, 0.0, 1.0])
    pipeline.context.perception.set_mock_pose(pos, quat, 0.1)
    ok_cycle = pipeline.run_cycle()
    ok = (not ok_cycle) and pipeline.context.robot.stopped
    all_ok &= ok
    messages.append(f"regression/low-confidence: {'OK' if ok else 'FAIL'}")

    # 3) Grasp failure -> executor should fail and safe-stop
    pipeline, _ = build_pipeline(_base_dir())
    pipeline.context.gripper.config["mock_grasped"] = False
    ok_cycle = pipeline.run_cycle()
    ok = (not ok_cycle) and pipeline.context.robot.stopped
    all_ok &= ok
    messages.append(f"regression/grasp-failure: {'OK' if ok else 'FAIL'}")

    # 4) Invalid grid dimensions -> planning fail and safe-stop
    pipeline, _ = build_pipeline(_base_dir())
    pipeline.context.place_planner.grid_cfg["rows"] = 0
    ok_cycle = pipeline.run_cycle()
    ok = (not ok_cycle) and pipeline.context.robot.stopped
    all_ok &= ok
    messages.append(f"regression/invalid-grid: {'OK' if ok else 'FAIL'}")

    return all_ok, messages


def run_stress(cycles: int = 200, seed: int = 42, pos_jitter_mm: float = 2.0) -> tuple[bool, str]:
    rnd = random.Random(seed)
    pipeline, configs = build_pipeline(_base_dir())

    base = configs["perception"].get("mock_pose", {})
    base_pos = base.get("position_mm", [200.0, 0.0, 50.0])
    base_quat = base.get("quaternion_xyzw", [0.0, 0.0, 0.0, 1.0])

    successes = 0
    for _ in range(cycles):
        pos = [
            float(base_pos[0]) + rnd.uniform(-pos_jitter_mm, pos_jitter_mm),
            float(base_pos[1]) + rnd.uniform(-pos_jitter_mm, pos_jitter_mm),
            float(base_pos[2]) + rnd.uniform(-pos_jitter_mm, pos_jitter_mm),
        ]
        pipeline.context.perception.set_mock_pose(pos, base_quat, 0.99)
        if pipeline.run_cycle():
            successes += 1

    ok = successes == cycles
    return ok, f"sim-stress: successes={successes}/{cycles} seed={seed} jitter={pos_jitter_mm}mm"


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulation gates")
    parser.add_argument("mode", choices=["fast", "regression", "stress"])
    parser.add_argument("--cycles", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--jitter", type=float, default=2.0)
    args = parser.parse_args()

    if args.mode == "fast":
        ok, msg = run_fast(cycles=args.cycles or 5)
        print(msg)
        return 0 if ok else 2

    if args.mode == "regression":
        ok, msgs = run_regression()
        for m in msgs:
            print(m)
        return 0 if ok else 2

    ok, msg = run_stress(cycles=args.cycles or 200, seed=args.seed, pos_jitter_mm=args.jitter)
    print(msg)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
