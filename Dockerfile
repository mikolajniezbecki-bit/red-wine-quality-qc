FROM python:3.12-slim-bookworm

# uv binary, pinned to the version that created uv.lock
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

WORKDIR /code

# use the image's Python 3.12, never download another one
ENV UV_PYTHON_DOWNLOADS=never
ENV PATH="/code/.venv/bin:$PATH"

# install dependencies first (cached layer), exactly as locked, serving deps only
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev

COPY predict.py model.bin ./

EXPOSE 9696

ENTRYPOINT ["uvicorn", "predict:app", "--host", "0.0.0.0", "--port", "9696"]
