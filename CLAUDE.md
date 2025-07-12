# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Indexa is a personal IT knowledge base application built with FastAPI and SQLite. It provides a web interface for storing, searching, and managing technical documentation and reference materials.

## Architecture

- **Backend**: FastAPI application with SQLite database
- **Frontend**: HTML templates with Jinja2 templating
- **Database**: SQLite with FTS5 full-text search capabilities
- **Deployment**: Containerized with Docker

### Key Components

- `main.py`: Main FastAPI application with all routes and business logic
- `templates/`: Jinja2 HTML templates for web interface
- `static/`: CSS, JavaScript, and static assets
- `tests/`: Test files (currently empty)
- `requirements.txt`: Python dependencies

## Development Commands

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run with Python
python main.py
```

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build

# Build Docker image
docker build -t indexa .

# Run container
docker run -p 8000:8000 -v /path/to/data:/data indexa
```

### Testing

```bash
# Run tests with pytest
pytest tests/

# Run specific test file
pytest tests/test_main.py
```

## Database Architecture

The application uses SQLite with FTS5 for full-text search:

- **entries**: Main table storing knowledge base entries
- **entries_fts**: FTS5 virtual table for full-text search
- **triggers**: Automatic sync between main table and FTS index

Database location is configurable via `DATABASE_PATH` environment variable (default: `/data/indexa.db`).

## API Endpoints

### Core CRUD Operations
- `GET /entries` - List all entries with optional category filter
- `GET /entries/{id}` - Get specific entry
- `POST /entries` - Create new entry
- `PUT /entries/{id}` - Update entry
- `DELETE /entries/{id}` - Delete entry

### Search and Metadata
- `GET /search` - Full-text search with optional category filter
- `GET /categories` - List all unique categories
- `GET /tags` - List all unique tags
- `GET /export` - Export all entries as JSON

### Web Interface
- `GET /` - Homepage with search interface
- `GET /add` - Add entry form
- `GET /edit/{id}` - Edit entry form
- `GET /view/{id}` - View entry details

## Data Model

Entries contain:
- `title`: Entry title
- `content`: Main content/documentation
- `category`: Classification category
- `tags`: Comma-separated tags
- `created_at`/`updated_at`: Timestamps

## Configuration

- `DATABASE_PATH`: Database file location
- Port 8000 for web interface
- Volume mount at `/data` for persistent storage in Docker

## Development Notes

- All database operations use context managers for proper connection handling
- FTS5 search uses prefix matching with `"query"*` pattern
- Search results include highlighted snippets
- Templates use Jinja2 with base template inheritance
- No authentication/authorization implemented (personal use application)