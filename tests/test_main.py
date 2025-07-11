import pytest
from fastapi.testclient import TestClient
from main import app
import os
import tempfile
import sqlite3

# Create a test client
client = TestClient(app)

@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # Set the database path for testing
    os.environ["DATABASE_PATH"] = db_path
    
    # Initialize the test database
    conn = sqlite3.connect(db_path)
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
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

def test_home_page():
    """Test the home page loads correctly"""
    response = client.get("/")
    assert response.status_code == 200
    assert "SysRef" in response.text

def test_add_entry_page():
    """Test the add entry page loads correctly"""
    response = client.get("/add")
    assert response.status_code == 200
    assert "Add New Entry" in response.text

def test_create_entry():
    """Test creating a new entry"""
    entry_data = {
        "title": "Test Entry",
        "content": "This is a test entry",
        "category": "Test",
        "tags": "test,example"
    }
    
    response = client.post("/entries", json=entry_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Test Entry"
    assert data["content"] == "This is a test entry"
    assert data["category"] == "Test"
    assert data["tags"] == "test,example"

def test_get_entries():
    """Test retrieving entries"""
    # First create an entry
    entry_data = {
        "title": "Test Entry",
        "content": "This is a test entry",
        "category": "Test",
        "tags": "test,example"
    }
    client.post("/entries", json=entry_data)
    
    # Then retrieve entries
    response = client.get("/entries")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Test Entry"

def test_search_entries():
    """Test searching entries"""
    # First create an entry
    entry_data = {
        "title": "Search Test Entry",
        "content": "This is a searchable test entry",
        "category": "Test",
        "tags": "search,test"
    }
    client.post("/entries", json=entry_data)
    
    # Search for the entry
    response = client.get("/search?q=searchable")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    assert "searchable" in data[0]["content"].lower()

def test_get_categories():
    """Test retrieving categories"""
    # First create entries with different categories
    entry1 = {
        "title": "Test Entry 1",
        "content": "Content 1",
        "category": "Category A",
        "tags": ""
    }
    entry2 = {
        "title": "Test Entry 2",
        "content": "Content 2",
        "category": "Category B",
        "tags": ""
    }
    
    client.post("/entries", json=entry1)
    client.post("/entries", json=entry2)
    
    # Get categories
    response = client.get("/categories")
    assert response.status_code == 200
    
    data = response.json()
    assert "Category A" in data
    assert "Category B" in data

def test_get_tags():
    """Test retrieving tags"""
    # First create entries with tags
    entry = {
        "title": "Tagged Entry",
        "content": "Content with tags",
        "category": "Test",
        "tags": "tag1,tag2,tag3"
    }
    
    client.post("/entries", json=entry)
    
    # Get tags
    response = client.get("/tags")
    assert response.status_code == 200
    
    data = response.json()
    assert "tag1" in data
    assert "tag2" in data
    assert "tag3" in data

def test_export_entries():
    """Test exporting entries"""
    # Create an entry first
    entry_data = {
        "title": "Export Test",
        "content": "Export content",
        "category": "Test",
        "tags": "export"
    }
    client.post("/entries", json=entry_data)
    
    # Export entries
    response = client.get("/export")
    assert response.status_code == 200
    
    data = response.json()
    assert "entries" in data
    assert "exported_at" in data
    assert len(data["entries"]) >= 1

def test_invalid_entry_creation():
    """Test creating an entry with invalid data"""
    invalid_entry = {
        "title": "",  # Empty title should be invalid
        "content": "Some content",
        "category": "Test",
        "tags": ""
    }
    
    response = client.post("/entries", json=invalid_entry)
    assert response.status_code == 422  # Validation error

def test_nonexistent_entry():
    """Test retrieving a non-existent entry"""
    response = client.get("/entries/99999")
    assert response.status_code == 404

def test_update_entry():
    """Test updating an entry"""
    # Create an entry first
    entry_data = {
        "title": "Original Title",
        "content": "Original content",
        "category": "Test",
        "tags": "original"
    }
    
    create_response = client.post("/entries", json=entry_data)
    entry_id = create_response.json()["id"]
    
    # Update the entry
    updated_data = {
        "title": "Updated Title",
        "content": "Updated content",
        "category": "Updated Category",
        "tags": "updated"
    }
    
    update_response = client.put(f"/entries/{entry_id}", json=updated_data)
    assert update_response.status_code == 200
    
    updated_entry = update_response.json()
    assert updated_entry["title"] == "Updated Title"
    assert updated_entry["content"] == "Updated content"
    assert updated_entry["category"] == "Updated Category"
    assert updated_entry["tags"] == "updated"

def test_delete_entry():
    """Test deleting an entry"""
    # Create an entry first
    entry_data = {
        "title": "To Delete",
        "content": "This will be deleted",
        "category": "Test",
        "tags": "delete"
    }
    
    create_response = client.post("/entries", json=entry_data)
    entry_id = create_response.json()["id"]
    
    # Delete the entry
    delete_response = client.delete(f"/entries/{entry_id}")
    assert delete_response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f"/entries/{entry_id}")
    assert get_response.status_code == 404