# Contributing to AI Dataset Governance

Thank you for your interest in contributing to **AI Dataset Governance**!

## Development Workflow

1. Fork and clone the repository.
2. Set up the Python virtual environment:
   ```bash
   uv venv
   uv sync
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Run backend tests:
   ```bash
   uv run pytest
   ```
5. Commit with conventional commit messages (`feat: ...`, `fix: ...`, `docs: ...`).
6. Submit a Pull Request.
