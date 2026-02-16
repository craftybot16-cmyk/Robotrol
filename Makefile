.PHONY: venv install test sim-fast sim-regression sim-stress

venv:
	python3 -m venv .venv

install:
	. .venv/bin/activate && pip install -U pip && pip install -r requirements-dev.txt

test:
	. .venv/bin/activate && pytest -q

sim-fast:
	. .venv/bin/activate && python -m simulation.gates fast --cycles 5

sim-regression:
	. .venv/bin/activate && python -m simulation.gates regression

sim-stress:
	. .venv/bin/activate && python -m simulation.gates stress --cycles 200 --seed 42 --jitter 2.0
