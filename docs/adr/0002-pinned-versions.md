# ADR-0002: Pinned Toolchain and Core Dependency Baseline

## Status
Accepted (2026-09-28)

## Context
To prevent drift, build breakage across environments, and CI flakiness, all primary development tools and runtime libraries must have minimum pinned versions defined at project inception.

## Decision
The project adopts the following toolchain baseline:

### Tooling & Runtime
| Tool | Minimum Version | Purpose |
|---|---|---|
| Python | `>=3.12` | Core language runtime (tested on 3.12 and 3.13) |
| uv | `>=0.5.0` | Ultra-fast package installer and virtual environment manager |
| Hatchling | `>=1.26.0` | Modern, standard PEP-621 build backend |
| Ruff | `>=0.9.0` | Unified linter and formatter |
| Pre-commit | `>=4.0.0` | Git hook automation |

### Core Runtime Dependencies (Zero DB Drivers)
| Package | Version Range | Purpose |
|---|---|---|
| `httpx` | `>=0.28.0,<1.0.0` | Async/sync HTTP client with connection pooling for Crossref |
| `typer` | `>=0.15.0,<1.0.0` | Modern CLI framework with type hints |
| `rich` | `>=13.9.0,<14.0.0` | Terminal formatting, tables, trees, progress bars |
| `pydantic` | `>=2.10.0,<3.0.0` | Schema validation and serialization |

### Optional Server Dependencies
| Package | Version Range | Purpose |
|---|---|---|
| `fastapi` | `>=0.115.0,<1.0.0` | Web API framework |
| `asyncpg` | `>=0.30.0,<1.0.0` | High-performance PostgreSQL driver |
| `alembic` | `>=1.14.0,<2.0.0` | Database schema migrations |
| `sqlalchemy` | `>=2.0.35,<3.0.0` | Server relational modeling |

### Testing & Verification
| Package | Version Range | Purpose |
|---|---|---|
| `pytest` | `>=8.3.0` | Test runner |
| `pytest-asyncio` | `>=0.25.0` | Async fixture support |
| `respx` | `>=0.22.0` | HTTP request mocking for external scholarly APIs |
| `hypothesis` | `>=6.120.0` | Property-based testing for DOI normalizer |
| `pytest-cov` | `>=6.0.0` | Coverage reporting (minimum 85% target) |

## Consequences
- Guaranteed reproducible environments across macOS, Linux, and GitHub Actions CI.
- Fast dependency resolution through `uv.lock`.
