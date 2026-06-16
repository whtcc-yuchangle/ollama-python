# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Official Python client library for the [Ollama](https://github.com/ollama/ollama) REST API. Wraps the Ollama HTTP endpoints in a typed, idiomatic Python interface with both sync (`Client`) and async (`AsyncClient`) support. See the [Ollama API docs](https://github.com/ollama/ollama/blob/main/docs/api.md) for endpoint semantics.

## Commands

Tests use `pytest-httpserver` (mock HTTP server) — no running Ollama instance needed.

```bash
# Run full test suite (hatch)
uvx hatch test -acp

# Run tests directly with pytest
uv run pytest

# Run a single test file
uv run pytest tests/test_client.py

# Run a single test by name
uv run pytest tests/test_client.py -k test_client_chat

# Format code (ruff)
uvx hatch fmt -f

# Lint code (ruff)
uvx hatch fmt -l

# Build distribution
uv build

# Run an example
uv run examples/chat.py
```

Hatch is the test runner configured in `pyproject.toml` (`[tool.hatch.envs.hatch-test]`). Ruff is the formatter/linter (`[tool.ruff]`). `uv` is the package manager — `uv.lock` is the canonical lockfile; `requirements.txt` is a generated export.

## Architecture

```
ollama/
  __init__.py   # Public API surface + module-level convenience functions
  _client.py    # BaseClient, Client (sync), AsyncClient
  _types.py     # Pydantic models for all request/response types
  _utils.py     # convert_function_to_tool (Python fn → Ollama Tool schema)
```

### Key design decisions

- **Module-level functions** (`ollama.chat`, `ollama.generate`, etc.) are convenience wrappers bound from a default `Client()` singleton created at import time. For custom host/auth/timeout, users instantiate `Client` or `AsyncClient` directly.
- **`SubscriptableBaseModel`** is the Pydantic base class that makes all response/request models support dict-style access (`response['message']`) and dict-style `get()`. This is the primary API for consuming responses — users do `response['message']['content']` or access fields directly via `response.message.content`.
- **Streaming** is controlled by `stream=True` on the API method. Sync returns a generator of response objects; async returns an async generator. Each yielded item is the same Pydantic model type as the non-streaming return, with `done` indicating completion.
- **`_request` / `_request_raw`** are the internal HTTP dispatch methods. `_request_raw` returns the raw `httpx.Response`; `_request` deserializes JSON into the given Pydantic model (or yields models in streaming mode). Both translate `httpx.HTTPStatusError` → `ResponseError` and `httpx.ConnectError` → `ConnectionError`.
- **Client → Sync vs Async mirrors**: `Client` and `AsyncClient` have identical method surfaces. Both extend `BaseClient` which handles host resolution, header assembly (User-Agent, Content-Type, optional Bearer token from `OLLAMA_API_KEY`), and httpx client construction.
- **Host resolution** (`_parse_host`): defaults to `http://127.0.0.1:11434`. Supports short forms like `:11434`, `example.com:1234`, IPv6, and preserves paths.
- **`convert_function_to_tool`** in `_utils.py` dynamically creates a Pydantic model from a Python function's signature and Google-style docstring, then generates a JSON Schema. This is how `chat(tools=[my_function])` works without manually writing schemas.
- **Request models** use `model_dump(exclude_none=True)` before sending, so optional fields not set by the user are omitted from the JSON payload.

### Type system (`_types.py`)

- **Request models**: `GenerateRequest`, `ChatRequest`, `EmbedRequest`, `PullRequest`, `PushRequest`, `CreateRequest`, `DeleteRequest`, `CopyRequest`, `ShowRequest`, `WebSearchRequest`, `WebFetchRequest`
- **Response models**: `GenerateResponse`, `ChatResponse`, `EmbedResponse`, `ListResponse`, `ProgressResponse`, `ShowResponse`, `ProcessResponse`, `StatusResponse`, `WebSearchResponse`, `WebFetchResponse`
- **Nested types**: `Message` (with `ToolCall`/`Function` sub-models), `Options`, `Image`, `Tool`, `Logprob`/`TokenLogprob`
- **Error types**: `ResponseError` (HTTP errors, streaming errors), `RequestError` (invalid requests)
- **`Image.value`** accepts `bytes`, file path (`str`/`Path`), or base64 string; serializes to base64 for the API.

## Testing

Tests live in `tests/` and use `pytest` with `pytest-httpserver` to mock the Ollama HTTP API. No Ollama server is needed. The `pytest-anyio` plugin provides async support (marked at module level with `pytestmark = pytest.mark.anyio`).

Three test files:
- `test_client.py` — comprehensive integration tests for `Client` and `AsyncClient` against a mock HTTP server
- `test_utils.py` — unit tests for `convert_function_to_tool`
- `test_type_serialization.py` — unit tests for Pydantic model serialization (especially `Image` and `CreateRequest.from_` → `from` field rename)
