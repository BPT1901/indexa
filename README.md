# Indexa - Personal IT Knowledge Base

A modern web application for storing, searching, and managing technical documentation and reference materials. Built with FastAPI and SQLite with full-text search capabilities.

## Features

- **Full-Text Search**: Powered by SQLite FTS5 for fast and accurate search results
- **Markdown Support**: Rich text formatting with syntax highlighting
- **Category & Tag Organization**: Organize entries with categories and tags
- **Modern UI**: Clean, responsive interface with purple gradient theme
- **Export Functionality**: Export all data as JSON
- **Docker Support**: Easy deployment with Docker containers
- **RESTful API**: Complete API for programmatic access

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/BPT1901/indexa.git
cd indexa

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` to access the application.

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t indexa .
docker run -p 8000:8000 -v /path/to/data:/data indexa
```

## Configuration

- **Database Location**: Set via `DATABASE_PATH` environment variable (default: `/data/indexa.db`)
- **Application Name**: Configurable via `APP_NAME` environment variable
- **Debug Mode**: Enable with `DEBUG=true` environment variable

## API Endpoints

### Entries
- `GET /entries` - List all entries
- `GET /entries/{id}` - Get specific entry
- `POST /entries` - Create new entry
- `PUT /entries/{id}` - Update entry
- `DELETE /entries/{id}` - Delete entry

### Search & Metadata
- `GET /search` - Full-text search
- `GET /categories` - List all categories
- `GET /tags` - List all tags
- `GET /export` - Export all data

### Web Interface
- `GET /` - Homepage
- `GET /add` - Add entry form
- `GET /edit/{id}` - Edit entry form
- `GET /view/{id}` - View entry details

## Data Structure

Each entry contains:
- **Title**: Entry title
- **Content**: Main documentation (supports Markdown)
- **Category**: Classification category
- **Tags**: Comma-separated tags
- **Timestamps**: Created and updated dates

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite with FTS5 full-text search
- **Frontend**: HTML/CSS/JavaScript with Jinja2 templates
- **Styling**: Font Awesome icons, modern CSS with purple theme
- **Deployment**: Docker with Docker Compose support

## Development

### Project Structure

```
indexa/
├── main.py              # Main FastAPI application
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── add_entry.html
│   ├── edit_entry.html
│   └── view_entry.html
├── static/              # CSS, JavaScript, and assets
│   ├── style.css
│   └── script.js
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
└── README.md           # This file
```

### Running Tests

```bash
pytest tests/
```

### Database Schema

The application uses SQLite with the following structure:
- `entries` table for storing knowledge base entries
- `entries_fts` virtual table for full-text search
- Automatic triggers to keep FTS index synchronized

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality
5. Submit a pull request

## License

This project is for personal use. Feel free to fork and modify for your own needs.

## Support

For issues and feature requests, please use the GitHub issue tracker.