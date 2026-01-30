# 804 data analysis repo

This repo contains R and Python analysis code with reproducible, well-tracked data steps.

## Quick start (non-technical)
- Install R + RStudio, and install `uv` for Python work.
- Open the project folder in RStudio or your file browser.
- In RStudio, run `renv::restore()` once to install the required R packages.
- Run R scripts from `R/` or Python scripts from `src/` (example: `uv run src/main.py`).
- Put raw data in `data/raw`, intermediate outputs in `data/steps`, and final outputs in `data/out`.
- Add data source links to `data/sources.md` so anyone can re-download data.

## Technical setup
- **R with renv**: Use the guide below; it manages a project-specific library and records versions in `renv.lock`.
- **Python with uv**: Use uv-managed environments and dependencies defined in `pyproject.toml` + `uv.lock`.

## R with renv guide
Open the project in RStudio or an R console and run:

```r
install.packages("renv")
renv::restore()
```

Daily workflow:
- Install or update packages with `renv::install()` or `renv::update()`.
- After your code runs, record versions with `renv::snapshot()`.
- Check for mismatches with `renv::status()`.
- `renv::init()` is only for creating a new renv project; this repo is already initialized.

## Python workflow (uv)
Sync dependencies and create the project environment:

```bash
uv sync
```

Uv automatically creates an environment for python.

Add or remove dependencies (updates `pyproject.toml` and `uv.lock`):

```bash
uv add <package>
uv add --dev <package>
uv remove <package>
```

Run scripts from `src/`:

```bash
uv run src/main.py
```

## Reproducible data workflow
- Track data sources in `data/sources.md`.
- Keep raw inputs in `data/raw` and do not edit them in place.
- Save intermediate steps to `data/steps` with clear, descriptive names.
- Write final outputs to `data/out`.
- Use `data/temp` for scratch work you do not need to keep.

## Project layout
- `R/` R analysis scripts.
- `src/` Python analysis scripts.
- `data/raw` raw inputs (not committed).
- `data/steps` intermediate artifacts (not committed).
- `data/out` final outputs (not committed).
- `data/sources.md` source links.
- `get_data.sh` optional data download script.
- `renv.lock` R package lockfile.
