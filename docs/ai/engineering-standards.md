# Engineering Standards (Shared)

Canonical coding and quality standards for this repository.

## Implementation Principles

- Prefer simple, incremental changes over broad refactors.
- Preserve established FastAPI router and template patterns.
- Keep behavior-compatible changes unless a behavior change is explicitly requested.

## Python Conventions

- Use `uv` for dependency and run commands.
- Prefer explicit errors and structured responses for API endpoints.
- Reuse shared services in `app/services/` rather than duplicating logic.

## Routing and Templates

- Router files belong in `app/routes/`.
- Register new routers in `app/__init__.py`.
- Use route names matching current convention (`router.endpoint`) so template `url_for()` resolution remains stable.
- Prefer Win98 template chain for new user-facing pages unless extending legacy tools.

## Security and External Calls

- Keep session and security middleware expectations intact.
- Use shared `request.app.state.http_client` for outbound HTTP where applicable.
- Keep external links with `target="_blank"` paired with `rel="noopener noreferrer"`.

## Testing

Before finalizing meaningful code changes:

```bash
uv run pytest -v
npm test
```

If full tests are not feasible, run targeted tests and call out the gap.

## Documentation

- Update docs when behavior, architecture, deployment, or workflow changes.
- Shared docs in `docs/ai/` are canonical cross-tool context.
