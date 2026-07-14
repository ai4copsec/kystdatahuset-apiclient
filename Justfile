default:
    just --list

# Install/update the dev environment
sync:
    uv sync --all-extras

# Run the test suite
test *ARGS:
    uv run pytest {{ ARGS }}

# Run pre-commit hooks (ruff, isort, ...) against all files
lint:
    uv run pre-commit run --all-files

# Build the quartodoc API reference and render the docs site
docs:
    uv run quartodoc build --config docs/_quarto.yml
    cd docs && uv run quarto render

# Live-preview the docs site
docs-preview:
    uv run quartodoc build --config docs/_quarto.yml
    cd docs && uv run quarto preview

# Remove build/test artifacts
clean:
    rm -rf .pytest_cache .coverage htmlcov dist build src/*.egg-info \
        docs/reference docs/_site docs/.quarto docs/objects.json
