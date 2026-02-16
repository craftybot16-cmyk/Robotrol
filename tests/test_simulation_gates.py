import os

from simulation.gates import run_fast, run_regression, run_stress


def test_sim_fast():
    ok, _ = run_fast(cycles=3)
    assert ok


def test_sim_regression():
    ok, msgs = run_regression()
    assert ok, "\n".join(msgs)


def test_sim_stress_short():
    ok, _ = run_stress(cycles=20, seed=7, pos_jitter_mm=1.5)
    assert ok
