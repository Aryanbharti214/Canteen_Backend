# CanteenAI Backend

This is the backend for the AI-powered college canteen recommendation system. It processes user natural-language queries (using a local Ollama model) and deterministically filters and scores food combinations based on constraints (budget, diet, spice, preparation time, availability).

## Requirements
- Python 3.11+
- PostgreSQL (or SQLite for development)
- Ollama (running locally with the `qwen3:8b` model)

## Setup Instructions

### 1. Python Environment

Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```
Edit `.env` to configure your database (`DATABASE_URL`). If not set, SQLite will be used.

### 4. Database Setup

Run the migrations to create the database tables:
```bash
python manage.py migrate
```

### 5. Seed Initial Data

Seed the database with the predefined canteen menu:
```bash
python manage.py seed_menu
```

### 6. Run the Server

Start the Django development server:
```bash
python manage.py runserver
```
The API will be available at `http://127.0.0.1:8000/api/`.

## Ollama Setup

The AI features require Ollama to be running locally.

1. Install Ollama from [ollama.com](https://ollama.com/)
2. Pull the required model:
```bash
ollama pull qwen3:8b
```
3. Start the Ollama server:
```bash
ollama serve
```

## API Examples

### Get Foods Menu
```bash
curl http://127.0.0.1:8000/api/foods/
```

### Get Recommendations
```bash
curl -X POST http://127.0.0.1:8000/api/recommendations/ \
-H "Content-Type: application/json" \
-d '{"query": "I have ₹80, I am hungry, want something spicy and only have 15 minutes."}'
```

### Authenticate
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ -H "Content-Type: application/json" -d '{"username": "student", "password": "password123"}'
```

## React Frontend Integration

The backend has `django-cors-headers` enabled. The frontend can safely communicate with it.
- Development frontend allowed origins are set to allow all (`*`) for development.
- Authentication uses Django REST Framework Token authentication (`rest_framework.authtoken`). Ensure your React app saves the `token` in `localStorage` or `sessionStorage` and attaches it as `Authorization: Token <your-token>` on authenticated endpoints like favorites and history.
