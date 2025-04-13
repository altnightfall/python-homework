.PHONY: lint
lint:
	. .venv/bin/activate; \
	pre-commit run --all-files

.PHONY: test
test:
	. .venv/bin/activate; \
	uv sync --group test; \
	pytest tests

.PHONY: install
install:
	python -m venv .venv; \
	. .venv/bin/activate; \
	uv sync
