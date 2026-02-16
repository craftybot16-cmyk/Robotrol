.PHONY: venv install test

venv:
	python3 -m venv .venv

install:
	. .venv/bin/activate && pip install -U pip && pip install -r requirements-dev.txt

test:
	. .venv/bin/activate && pytest -q
