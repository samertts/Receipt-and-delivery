# Contributing - نظام إدارة الاستلام المختبري

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (for web backend)

### Desktop App

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python main.py
```

### Backend API

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend API tests
cd backend
pytest -v

# Desktop tests
pytest tests/ -v

# With coverage
pytest --cov=app --cov-report=term-missing
```

## Code Style

- **Python**: Follow PEP 8, use type hints
- **Vue 3**: Use Composition API with `<script setup>`
- **Arabic text**: Use Arabic for all user-facing strings
- **Error messages**: Always provide Arabic error messages

## Commit Guidelines

- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Include Arabic description for user-facing changes
- Reference issue numbers when applicable

## Pull Request Process

1. Create feature branch from `main`
2. Add tests for new functionality
3. Ensure all tests pass
4. Update documentation if needed
5. Submit PR with clear description
