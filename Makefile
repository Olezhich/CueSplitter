all:
	poetry run ruff format . --check
	poetry eun ruff check .
	poetry run mypy .
	poetry run pytest

fix:
	poetry run ruff format .
	poetry run ruff check .
	poetry run mypy .
	poetry run pytest