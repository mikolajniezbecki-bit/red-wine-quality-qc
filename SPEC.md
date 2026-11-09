# SPEC — Red Wine Quality QC (ML Zoomcamp 2026 Midterm Project)

> **How to use this file with Claude Code**
> Put this file in the root of a new, empty GitHub repo as `SPEC.md`, then start with:
> *"Read SPEC.md. Implement Phase 1 only, then stop and summarize what you did and what I should check."*
> Continue phase by phase (see §13). Section 0 lists decisions that are already made; change them here before starting if needed.

**Author:** Mikołaj Niezbecki · **Course:** DataTalks.Club ML Zoomcamp 2026 · **Deadline:** Mon 16 Nov 2026, 23:00 (Europe/Warsaw)

---

## 0. Decisions (defaults — confirm or change before Phase 1)

| # | Decision | Default | Alternative |
|---|----------|---------|-------------|
| D1 | Repository name | `red-wine-quality-qc` | any descriptive name (course asks for descriptive names, not `homework3`) |
| D2 | Data scope | **Red wine only** (`winequality-red.csv`, 1,599 rows) | Red + white (≈6.5k rows, adds a `wine_type` categorical feature) — more EDA, more work |
| D3 | Target | **Binary:** `good = quality >= 7` | Regression on `quality` (3–8) or multiclass |
| D4 | Cloud deployment (bonus 2 pts) | **Azure Container Apps** (I have a personal Azure subscription) | Fly.io (the pattern used in the course's 2025/26 deployment workshop) |
| D5 | Python | 3.12, pinned in `.python-version`; Docker base image must match | 3.13 (course workshop uses `python:3.13.5-slim-bookworm`) |
| D6 | Language of all repo content | English (portfolio + international peer reviewers) | — |

---

## 1. Goal and grading

Build an end-to-end ML project that scores the maximum **16 points** on the official ML Zoomcamp rubric (source: `projects/README.md` in the course repo). Every rubric line below must be explicitly satisfied:

| Criterion | Max | What earns full points | Where in this repo |
|-----------|-----|------------------------|--------------------|
| Problem description | 2 | README describes the problem with enough context that it's clear what it is and how the solution will be used | `README.md` §Problem |
| EDA | 2 | Ranges of values, missing values, target analysis, feature importance analysis | `notebook.ipynb` §3, §10 |
| Model training | 3 | Multiple models (linear **and** tree-based) **and** tuned parameters | `notebook.ipynb` §5–§9 |
| Exporting notebook to script | 1 | Training logic in a separate script | `train.py` |
| Reproducibility | 1 | Notebook and training script re-run without errors; dataset committed or clearly downloadable | `data/`, README |
| Model deployment | 1 | Model served by a web framework | `predict.py` (FastAPI) |
| Dependency & environment management | 2 | Dependency file **and** virtual env; README says how to install and activate | `pyproject.toml`, `uv.lock`, README |
| Containerization | 2 | Dockerfile **and** README explains build + run | `Dockerfile`, README |
| Cloud deployment | 2 | Code for deployment **and** a URL or video/screenshot of testing it | `deploy/`, `images/`, README |

Course rule on plagiarism: copying other people's notebooks/projects (fully or partly) = 0 points. **Do not copy code or text from existing public projects on this dataset.** Re-using code *patterns* from the course modules (DictVectorizer pipelines, tuning loops, `parse_xgb_output`, FastAPI + Pydantic) is expected and fine.

---

## 2. Problem framing (for README and notebook §1)

**Context.** Before bottling, a winery's lab measures the physicochemical profile of each batch (acidity, sugar, SO₂, sulphates, alcohol…). The sensory panel that assigns the final quality grade is slow and expensive. 

**Problem.** Given the lab analysis of a red *Vinho Verde* batch, estimate the probability that the sensory panel will rate it **good (quality ≥ 7 on a 0–10 scale)**.

**How the model is used.** A QC technician sends the 11 lab values to a REST API and gets back `good_probability` and a yes/no flag. The winery uses it to (a) prioritise which batches go to the full tasting panel / premium line, and (b) flag batches likely to be mediocre early, when blending or adjustments are still possible.

**Who it is NOT for.** Consumers in a shop — they don't know volatile acidity or sulphates. State this explicitly in README (it pre-empts an obvious reviewer question).

**Metric.**
- Primary: **ROC AUC** (threshold-independent, the course standard).
- Secondary: **PR AUC** (average precision), because positives are only ~13.5%.
- At the chosen threshold: precision, recall, F1, confusion matrix.
- Show explicitly that **accuracy is misleading**: a model that always predicts "not good" scores ~86.5% accuracy.

---

## 3. Data

**Source.** UCI Machine Learning Repository — *Wine Quality* (P. Cortez, A. Cerdeira, F. Almeida, T. Matos, J. Reis, "Modeling wine preferences by data mining from physicochemical properties", *Decision Support Systems* 47(4):547–553, 2009). Canonical file: `https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv`. Confirm licence (UCI lists CC BY 4.0) and cite it in README.

**In this repo.** Commit the file as `data/winequality-red.csv` (≈100 KB). The provided copy is the **comma-separated** Kaggle variant (md5 `6a883fd98624e18c0b7ce251f4fab4fb`); the UCI original is **semicolon-separated**. The loader must handle both (e.g. `pd.read_csv(path, sep=None, engine="python")`). README also gives the download command for the UCI original.

**Columns** (normalise to snake_case like the course: `df.columns.str.lower().str.replace(' ', '_')`). Units per the Cortez et al. paper — verify before putting them in README:

| Feature | Unit |
|---------|------|
| `fixed_acidity` | g(tartaric acid)/dm³ |
| `volatile_acidity` | g(acetic acid)/dm³ |
| `citric_acid` | g/dm³ |
| `residual_sugar` | g/dm³ |
| `chlorides` | g(sodium chloride)/dm³ |
| `free_sulfur_dioxide` | mg/dm³ |
| `total_sulfur_dioxide` | mg/dm³ |
| `density` | g/cm³ |
| `ph` | — |
| `sulphates` | g(potassium sulphate)/dm³ |
| `alcohol` | % vol. |
| `quality` (target source) | integer score, 0–10 (observed 3–8) |

**Known facts about this file** (verified on the provided copy — use as sanity checks, but the notebook must compute them itself):
- 1,599 rows × 12 columns, all numeric, **0 missing values**.
- **240 exact duplicate rows (15%)** → 1,359 unique rows.
- Quality distribution (raw): 3→10, 4→53, 5→681, 6→638, 7→199, 8→18. After dedup, 184 of 1,359 rows are `good` (13.5%).
- Strongest linear relations with `quality`: `alcohol` (+0.48), `volatile_acidity` (−0.39), `sulphates` (+0.25), `citric_acid` (+0.23).
- Notable outliers: `total_sulfur_dioxide` max 289, `sulphates` max 2.0, `chlorides` max 0.611.
- **Leakage finding:** a default RandomForest with 5-fold stratified CV gave ROC AUC ≈ 0.92 on raw data vs ≈ 0.88 after dropping duplicates — duplicates land in both train and validation folds and inflate the score. Reproduce this in the notebook (don't copy the numbers) and **drop duplicates before splitting**.

**Dataset limitations** (README §Limitations): only Portuguese red Vinho Verde; data from 2009; no grape variety, brand or price; target is a subjective panel score; very few examples at the extremes (3 and 8).

---

## 4. Repository structure

```
red-wine-quality-qc/
├── README.md
├── SPEC.md                  # this file
├── data/
│   └── winequality-red.csv
├── notebook.ipynb           # data prep, EDA, model selection (outputs saved!)
├── train.py                 # trains the final model, saves model.bin
├── predict.py               # FastAPI service (uvicorn predict:app)
├── test.py                  # sends example requests to local or cloud service
├── tests/
│   └── test_api.py          # pytest + FastAPI TestClient
├── model.bin                # committed, so Docker builds without retraining
├── pyproject.toml
├── uv.lock
├── .python-version
├── Dockerfile
├── .dockerignore
├── deploy/
│   └── azure.md (or fly.toml + fly.md, depending on D4)
├── images/                  # EDA plots + deployment screenshots used in README
└── .gitignore
```

---

## 5. Environment

- Use **uv** (the course replaced Pipenv with uv in the 2025/26 deployment workshop). Dev environment: GitHub Codespaces (Docker is available there).
- `pyproject.toml` with:
  - **main dependencies** (only what serving needs): `fastapi`, `uvicorn`, `scikit-learn`, `xgboost`, `pydantic`.
  - **dependency group `dev`**: `pandas`, `numpy`, `matplotlib`, `seaborn`, `jupyter`, `requests`, `pytest`, `httpx`.
- `uv.lock` committed. The Docker image uses `uv sync --locked --no-dev`, so the pickled model is loaded with the **same scikit-learn/xgboost versions** it was trained with.
- README: `pip install uv` → `uv sync` → `source .venv/bin/activate` (or `uv run …`).

---

## 6. `notebook.ipynb` — structure and visualisations

Style: follow the course notebooks (numbered sections, short markdown explanation before each step, plain pandas/sklearn/matplotlib/seaborn, `random_state=1` everywhere). Each section ends with a 1–3 sentence **"Takeaway"** markdown cell. Save key figures to `images/` with `plt.savefig` for the README.

1. **Problem description.** Short version of §2.
2. **Data loading and preparation.**
   - Load, normalise column names, check dtypes.
   - Duplicates: count, show examples, **demonstrate the leakage effect** (RF CV AUC on raw vs dedup), then drop.
   - Create `good = (quality >= 7).astype(int)`; keep `quality` only for EDA, never as a feature.
3. **EDA.**
   - `df.describe()` (ranges), missing values, value counts.
   - Target: bar chart of `quality` counts + bar chart of `good` share (show the imbalance).
   - Distributions: histogram/KDE grid for all 11 features, coloured by `good`; comment on skew (`residual_sugar`, `chlorides`, SO₂ features, `sulphates`).
   - Box plots of the top features vs `quality` (alcohol, volatile_acidity, sulphates, citric_acid).
   - Correlation heatmap (features + `quality`) and sorted bar chart of correlation with `quality`; note collinear pairs (fixed_acidity–citric_acid–density–ph, free vs total SO₂).
   - Mutual information with `good` (`sklearn.feature_selection.mutual_info_classif`), bar chart, compare with correlation ranking.
   - Outliers: IQR count per feature; decide (and justify) whether to keep them — default: keep (trees are robust; LR uses scaling/log).
4. **Validation framework.** Stratified split 60/20/20 like the course (`train_test_split` twice: full_train/test 80/20, then train/val 75/25, `stratify=y`, `random_state=1`). Print class balance of each split.
5. **Baselines.** (a) Majority-class "always not good": accuracy + AUC 0.5 — the accuracy trap. (b) Logistic regression with default params.
6. **Logistic regression.** Pipeline `StandardScaler → LogisticRegression`. Tune `C` ∈ {0.001, 0.01, 0.1, 1, 10, 100} and `class_weight` ∈ {None, "balanced"}. Optional: `log1p` on skewed features — compare. Plot val AUC vs C. Show coefficients (bar chart).
7. **Decision tree.** Tune `max_depth` ∈ {1, 2, 3, 4, 5, 6, 10, 15, 20, None} and `min_samples_leaf` ∈ {1, 5, 10, 15, 20, 50, 100}. Pivot table + **seaborn heatmap** of val AUC (course pattern). Print a shallow tree with `export_text`.
8. **Random forest.** Tune `n_estimators` 10→200 (step 10), `max_depth` ∈ {5, 10, 15}, `min_samples_leaf` ∈ {1, 3, 5, 10, 50}; line plots of val AUC vs n_estimators per setting (course pattern). Try `class_weight="balanced"`.
9. **XGBoost.** `xgb.train` with a train/val watchlist and `eval_metric="auc"`; capture output and plot train vs val AUC per iteration with a `parse_xgb_output` helper (course pattern). Tune in order: `eta` ∈ {0.3, 0.1, 0.05, 0.01} → `max_depth` ∈ {3, 4, 6, 10} → `min_child_weight` ∈ {1, 10, 30}; also try `scale_pos_weight` ≈ neg/pos. Choose `num_boost_round` from the val curve.
10. **Model comparison and feature importance.**
    - Table: best params + val ROC AUC + val PR AUC per model.
    - 5-fold stratified CV on full_train for the tuned models (mean ± std) — confirms the ranking isn't split luck.
    - Feature importance: RF `feature_importances_`, XGB gain, and permutation importance on val (bar charts). Compare with the EDA correlation/MI ranking.
11. **Threshold selection.** On val: precision, recall and F1 vs threshold (course module 4 plot) + PR curve. Default: pick the F1-optimal threshold; discuss the business trade-off (false "good" = reputational risk → precision matters).
12. **Final model.** Retrain the winner on full_train, evaluate **once** on test: ROC AUC, PR AUC, ROC curve, PR curve, confusion matrix at the chosen threshold. Compare test vs val (overfitting check).
13. **Summary.** Final model, parameters, threshold, test metrics, top features, limitations.

Selection rule: best val ROC AUC; if within ~0.005, prefer the simpler model. **The winner is decided by the results — do not assume XGBoost.**

---

## 7. `train.py`

- Plain script (course style), no notebook dependency: load → clean (snake_case, drop duplicates) → target → split full_train/test with the same seed → fit final pipeline on full_train → print test ROC AUC / PR AUC → save.
- Final pipeline: `make_pipeline(DictVectorizer(sparse=False), <winner>)` so the API can pass `[sample.model_dump()]` directly (course pattern). If the winner is XGBoost, use `XGBClassifier` (sklearn API) with parameters translated from the notebook (`eta`→`learning_rate`, `num_boost_round`→`n_estimators`) and check val AUC matches the notebook.
- Hyperparameters and threshold hard-coded as constants at the top, with a comment pointing to the notebook section where they were chosen.
- Save `model.bin` with pickle as a dict: `{"pipeline", "threshold", "features", "model_name", "trained_at", "sklearn_version", "xgboost_version"}`.
- Print library versions at start (course pattern).
- Runtime target: < 1 minute.

---

## 8. `predict.py` (FastAPI)

- `app = FastAPI(title="red-wine-quality-qc")`; loads `model.bin` once at startup.
- Request model `WineSample` (Pydantic): 11 float fields named exactly like the training columns, each with `Field(..., ge=…, le=…, description="<unit>")`. Bounds = plausible physical ranges, a bit wider than the observed min/max, e.g. `alcohol` 7–16, `ph` 2.5–4.5, `density` 0.98–1.01, `total_sulfur_dioxide` 0–350. Document them in README.
- Response model `PredictResponse`: `good_probability: float`, `is_good: bool`, `threshold: float`.
- Endpoints: `POST /predict`, `GET /health` → `{"status": "ok"}`. FastAPI's `/docs` page is a bonus for reviewers (screenshot in README).
- Port **9696** (course convention); `if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=9696)`.

**Example payloads** (taken from the dataset; use in README, `test.py` and tests):

```json
// quality 8 in the data → expected high probability
{"fixed_acidity": 7.9, "volatile_acidity": 0.35, "citric_acid": 0.46, "residual_sugar": 3.6,
 "chlorides": 0.078, "free_sulfur_dioxide": 15.0, "total_sulfur_dioxide": 37.0,
 "density": 0.9973, "ph": 3.35, "sulphates": 0.86, "alcohol": 12.8}

// quality 5 in the data → expected low probability
{"fixed_acidity": 7.4, "volatile_acidity": 0.70, "citric_acid": 0.0, "residual_sugar": 1.9,
 "chlorides": 0.076, "free_sulfur_dioxide": 11.0, "total_sulfur_dioxide": 34.0,
 "density": 0.9978, "ph": 3.51, "sulphates": 0.56, "alcohol": 9.4}
```

## 9. `test.py` and `tests/`

- `test.py` (course style): URL from a CLI argument or env var `SERVICE_URL`, default `http://localhost:9696/predict`; sends both example payloads; prints a human-readable decision ("→ send to premium tasting panel" / "→ standard line").
- `tests/test_api.py` (pytest + `fastapi.testclient.TestClient`): `/health` is 200; valid payload returns a probability in [0, 1]; out-of-range payload (e.g. `alcohol: -1`) returns 422.

---

## 10. Docker

Follow the course workshop Dockerfile pattern:

```dockerfile
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /code
ENV PATH="/code/.venv/bin:$PATH"
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev
COPY predict.py model.bin ./
EXPOSE 9696
ENTRYPOINT ["uvicorn", "predict:app", "--host", "0.0.0.0", "--port", "9696"]
```

- `.dockerignore`: `.venv`, `data/`, `notebook.ipynb`, `images/`, `.git`, `tests/`.
- README: `docker build -t red-wine-quality-qc .` → `docker run -it --rm -p 9696:9696 red-wine-quality-qc` → `uv run python test.py`.

## 11. Cloud deployment (D4)

**Azure Container Apps (default):** `deploy/azure.md` with exact commands — resource group in `westeurope`, `az containerapp up` building from the Dockerfile, external ingress on port 9696, how to get the URL, how to call it with `test.py`, and **teardown** (`az group delete`). Check the current CLI syntax with `az containerapp up --help` before writing; don't guess flags. I run the commands myself (my credentials).

**Fly.io (alternative):** `fly.toml` (internal_port 9696) + `deploy/fly.md` with `fly launch` / `fly deploy` / teardown, as in the course workshop.

Evidence for reviewers (the URL may be shut down later): screenshots in `images/` of `test.py` hitting the cloud URL and of the `/docs` page, embedded in README.

---

## 12. README.md

Order (based on the course's project tips):
1. Title + one-sentence summary; small diagram `lab data → model → FastAPI → decision` (Mermaid is fine).
2. **Problem description** (§2), including who uses it and how.
3. **Dataset:** source, citation, licence, feature table with units, target definition, the duplicates finding, limitations.
4. **EDA highlights:** 3–4 embedded plots (target imbalance, correlation with quality, top-feature box plots, MI) with one-line takeaways.
5. **Modeling:** models tried, tuning ranges, comparison table, CV results, final model + threshold, test metrics, top features. All numbers copied from executed notebook output — never invented.
6. **Project structure** tree.
7. **How to run locally:** install uv, `uv sync`, activate venv, `uv run python train.py`, `uv run jupyter notebook`, `uv run uvicorn predict:app --port 9696`, `uv run python test.py`, `uv run pytest`.
8. **Docker:** build, run, test.
9. **Cloud deployment:** URL, screenshots, link to `deploy/…md`.
10. **API reference:** request/response JSON, curl example.
11. **Limitations and next steps** (e.g. add white wines, regression on the full score, monitoring).
12. **Acknowledgements:** ML Zoomcamp, dataset citation.

---

## 13. Working rules for Claude Code

- **Work in phases and stop after each one** with a short summary + what I should check. Don't start the next phase without my OK.
  1. Scaffold: repo structure, `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, data file in place.
  2. Notebook §1–§4 (prep + EDA + validation framework).
  3. Notebook §5–§13 (models, tuning, selection, threshold, final evaluation).
  4. `train.py`, `predict.py`, `test.py`, `tests/`.
  5. Docker.
  6. Cloud deployment docs/config.
  7. README + final reproducibility check.
- I'm learning: explain non-obvious choices in markdown cells and in your summaries (why stratify, why dedup before split, why AUC not accuracy, etc.).
- Keep it simple: no MLflow, no config frameworks, no class hierarchies. Readable, course-style code.
- Fixed seeds (`random_state=1`, XGBoost `seed=1`).
- Never fabricate results. Re-execute the notebook top-to-bottom before finishing (`uv run jupyter nbconvert --to notebook --execute --inplace notebook.ipynb`) and keep outputs saved, so GitHub renders them for reviewers.
- Don't copy from other public projects on this dataset (see §1).
- Commit after each phase with a descriptive message.

## 14. Definition of done

On a fresh clone in Codespaces:
- [ ] `uv sync` succeeds.
- [ ] `nbconvert --execute` runs the notebook without errors.
- [ ] `uv run python train.py` creates `model.bin` and prints test metrics matching the notebook.
- [ ] `uv run pytest` passes.
- [ ] `docker build` + `docker run` work, and `python test.py` returns a high probability for the quality-8 example and a low one for the quality-5 example.
- [ ] Cloud URL answers `test.py`; screenshots are in `images/` and embedded in README.
- [ ] README covers every rubric line in §1; all metrics in it match the notebook.
- [ ] Final commit hash noted for the submission form.

## 15. Suggested schedule (evenings)

| Day | Phases |
|-----|--------|
| Tue 10 Nov | 1–2 |
| Wed 11 Nov | 3 |
| Thu 12 Nov | 4–5 |
| Fri 13 Nov | 6 |
| Sat 14 Nov | 7 + fresh-clone test |
| Sun 15 Nov | buffer |
| Mon 16 Nov | submit commit hash (form closes 23:00) |
