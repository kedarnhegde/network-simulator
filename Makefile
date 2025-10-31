# --- Backend (FastAPI) ---

# Start FastAPI backend (with live reload)
run-backend:
	cd backend/server && python -m uvicorn app.main:app --reload --port 8000

# Install backend dependencies
install-backend:
	pip install -r backend/server/requirements.txt

# --- Frontend (React/Vite) ---

# Start React dev server
run-frontend:
	cd frontend && npm run dev

# Install frontend dependencies
install-frontend:
	cd frontend && npm install

# --- Utilities ---

# Remove caches and temp files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf node_modules
	rm -rf dist
	rm -rf build

# Default target: show help
help:
	@echo "Available commands:"
	@echo "  make run-backend        - Start FastAPI backend (reload on change)"
	@echo "  make install-backend    - Install backend dependencies"
	@echo "  make test-backend       - Run backend tests"
	@echo "  make run-frontend       - Start React frontend"
	@echo "  make install-frontend   - Install frontend dependencies"
	@echo "  make clean              - Remove caches, build, and node_modules"
