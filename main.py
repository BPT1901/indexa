from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
from contextlib import contextmanager
from typing import List, Optional
from pydantic import BaseModel
import os
from datetime import datetime
from dotenv import load_dotenv
import markdown

# Load environment variables from .env file
load_dotenv()

# Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/sysref.db")
STATIC_DIR = "static"
TEMPLATES_DIR = "templates"
APP_NAME = os.getenv("APP_NAME", "SysRef - Personal IT Knowledge Base")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=DEBUG)

# Mount static files and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Pydantic models
class Entry(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    category: str
    tags: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SearchResult(BaseModel):
    id: int
    title: str
    content: str
    category: str
    tags: str
    snippet: str
    created_at: str
    updated_at: str

# Database context manager
@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Initialize database
def init_db():
    """Initialize the database with tables and FTS index"""
    with get_db() as conn:
        # Create main entries table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create FTS virtual table for full-text search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                title, content, category, tags, content='entries', content_rowid='id'
            )
        """)
        
        # Create triggers to keep FTS table in sync
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
                INSERT INTO entries_fts(rowid, title, content, category, tags) 
                VALUES (new.id, new.title, new.content, new.category, new.tags);
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
                INSERT INTO entries_fts(entries_fts, rowid, title, content, category, tags) 
                VALUES('delete', old.id, old.title, old.content, old.category, old.tags);
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
                INSERT INTO entries_fts(entries_fts, rowid, title, content, category, tags) 
                VALUES('delete', old.id, old.title, old.content, old.category, old.tags);
                INSERT INTO entries_fts(rowid, title, content, category, tags) 
                VALUES (new.id, new.title, new.content, new.category, new.tags);
            END
        """)
        
        conn.commit()

# Initialize database on startup
init_db()

# Markdown converter
def convert_markdown(text):
    """Convert markdown text to HTML"""
    return markdown.markdown(text, extensions=['fenced_code', 'tables', 'toc'])

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Homepage with search interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/entries", response_model=List[Entry])
async def get_entries(category: Optional[str] = None, limit: int = 50):
    """Get all entries or filter by category"""
    with get_db() as conn:
        if category:
            cursor = conn.execute("""
                SELECT * FROM entries 
                WHERE category = ? 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (category, limit))
        else:
            cursor = conn.execute("""
                SELECT * FROM entries 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (limit,))
        
        entries = []
        for row in cursor.fetchall():
            entries.append(Entry(**dict(row)))
        
        return entries

@app.get("/entries/{entry_id}", response_model=Entry)
async def get_entry(entry_id: int):
    """Get a specific entry"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return Entry(**dict(row))

@app.post("/entries", response_model=Entry)
async def create_entry(entry: Entry):
    """Create a new entry"""
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO entries (title, content, category, tags)
            VALUES (?, ?, ?, ?)
        """, (entry.title, entry.content, entry.category, entry.tags))
        
        entry_id = cursor.lastrowid
        conn.commit()
        
        # Return the created entry
        cursor = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        
        return Entry(**dict(row))

@app.put("/entries/{entry_id}", response_model=Entry)
async def update_entry(entry_id: int, entry: Entry):
    """Update an existing entry"""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE entries 
            SET title = ?, content = ?, category = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (entry.title, entry.content, entry.category, entry.tags, entry_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        conn.commit()
        
        # Return the updated entry
        cursor = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        
        return Entry(**dict(row))

@app.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int):
    """Delete an entry"""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        conn.commit()
        
        return {"message": "Entry deleted successfully"}

@app.get("/search", response_model=List[SearchResult])
async def search_entries(q: str, category: Optional[str] = None, limit: int = 20):
    """Full-text search across all entries"""
    if not q.strip():
        return []
    
    with get_db() as conn:
        # Prepare search query for FTS
        search_query = f'"{q}"*'  # Prefix search
        
        if category:
            cursor = conn.execute("""
                SELECT e.*, snippet(entries_fts, 1, '<mark>', '</mark>', '...', 32) as snippet
                FROM entries_fts 
                JOIN entries e ON entries_fts.rowid = e.id
                WHERE entries_fts MATCH ? AND e.category = ?
                ORDER BY bm25(entries_fts)
                LIMIT ?
            """, (search_query, category, limit))
        else:
            cursor = conn.execute("""
                SELECT e.*, snippet(entries_fts, 1, '<mark>', '</mark>', '...', 32) as snippet
                FROM entries_fts 
                JOIN entries e ON entries_fts.rowid = e.id
                WHERE entries_fts MATCH ?
                ORDER BY bm25(entries_fts)
                LIMIT ?
            """, (search_query, limit))
        
        results = []
        for row in cursor.fetchall():
            result_dict = dict(row)
            results.append(SearchResult(**result_dict))
        
        return results

@app.get("/categories")
async def get_categories():
    """Get all unique categories"""
    with get_db() as conn:
        cursor = conn.execute("SELECT DISTINCT category FROM entries ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        return categories

@app.get("/tags")
async def get_tags():
    """Get all unique tags"""
    with get_db() as conn:
        cursor = conn.execute("SELECT DISTINCT tags FROM entries WHERE tags != ''")
        all_tags = []
        for row in cursor.fetchall():
            tags = [tag.strip() for tag in row[0].split(',') if tag.strip()]
            all_tags.extend(tags)
        
        unique_tags = sorted(set(all_tags))
        return unique_tags

@app.get("/export")
async def export_entries():
    """Export all entries as JSON"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM entries ORDER BY id")
        entries = []
        for row in cursor.fetchall():
            entries.append(dict(row))
        
        return JSONResponse(
            content={"entries": entries, "exported_at": datetime.now().isoformat()},
            headers={"Content-Disposition": "attachment; filename=sysref_export.json"}
        )

# Web interface routes
@app.get("/add", response_class=HTMLResponse)
async def add_entry_form(request: Request):
    """Form to add new entry"""
    return templates.TemplateResponse("add_entry.html", {"request": request})

@app.get("/edit/{entry_id}", response_class=HTMLResponse)
async def edit_entry_form(request: Request, entry_id: int):
    """Form to edit existing entry"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        entry = dict(row)
        return templates.TemplateResponse("edit_entry.html", {"request": request, "entry": entry})

@app.get("/view/{entry_id}", response_class=HTMLResponse)
async def view_entry(request: Request, entry_id: int):
    """View a specific entry"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        entry = dict(row)
        # Convert markdown content to HTML
        entry['content_html'] = convert_markdown(entry['content'])
        return templates.TemplateResponse("view_entry.html", {"request": request, "entry": entry})

if __name__ == "__main__":
    import uvicorn
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    WORKERS = int(os.getenv("WORKERS", "1"))
    
    if DEBUG:
        uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
    else:
        uvicorn.run(app, host=HOST, port=PORT, workers=WORKERS)