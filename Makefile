.PHONY: dev test lint up down
dev:   ; uvicorn app.main:app --reload
test:  ; pytest -q
lint:  ; ruff check .
up:    ; docker compose up -d --build
down:  ; docker compose down
