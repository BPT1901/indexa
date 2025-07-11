import pytest
import sqlite3
import tempfile
import os
from main import get_db, init_db

@pytest.fixture
def temp_database():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # Set the database path for testing
    os.environ["DATABASE_PATH"] = db_path
    
    # Initialize the database
    init_db()
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

def test_database_initialization(temp_database):
    """Test that the database is properly initialized"""
    with get_db() as conn:
        # Check that the entries table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entries'")
        assert cursor.fetchone() is not None
        
        # Check that the FTS table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entries_fts'")
        assert cursor.fetchone() is not None

def test_database_schema(temp_database):
    """Test that the database schema is correct"""
    with get_db() as conn:
        # Get the schema for the entries table
        cursor = conn.execute("PRAGMA table_info(entries)")
        columns = cursor.fetchall()
        
        # Check that all required columns exist
        column_names = [col[1] for col in columns]
        expected_columns = ['id', 'title', 'content', 'category', 'tags', 'created_at', 'updated_at']
        
        for col in expected_columns:
            assert col in column_names

def test_database_insert_and_retrieve(temp_database):
    """Test inserting and retrieving data"""
    with get_db() as conn:
        # Insert a test entry
        cursor = conn.execute("""
            INSERT INTO entries (title, content, category, tags)
            VALUES (?, ?, ?, ?)
        """, ("Test Title", "Test Content", "Test Category", "test,tags"))
        entry_id = cursor.lastrowid
        conn.commit()
        
        # Retrieve the entry
        cursor = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        entry = cursor.fetchone()
        
        assert entry is not None
        assert entry[1] == "Test Title"  # title
        assert entry[2] == "Test Content"  # content
        assert entry[3] == "Test Category"  # category
        assert entry[4] == "test,tags"  # tags

def test_fts_search(temp_database):
    """Test that FTS search works correctly"""
    with get_db() as conn:
        # Insert test entries
        test_entries = [
            ("Docker Setup", "How to install Docker on Ubuntu", "Server Setup", "docker,ubuntu"),
            ("Nginx Configuration", "Configure Nginx reverse proxy", "Network Config", "nginx,proxy"),
            ("Git Workflows", "Common Git commands and workflows", "Git Workflows", "git,version-control")
        ]
        
        for title, content, category, tags in test_entries:
            conn.execute("""
                INSERT INTO entries (title, content, category, tags)
                VALUES (?, ?, ?, ?)
            """, (title, content, category, tags))
        
        conn.commit()
        
        # Test FTS search
        cursor = conn.execute("""
            SELECT e.title, e.content
            FROM entries_fts 
            JOIN entries e ON entries_fts.rowid = e.id
            WHERE entries_fts MATCH ?
        """, ("docker",))
        
        results = cursor.fetchall()
        assert len(results) == 1
        assert "Docker" in results[0][0]

def test_fts_triggers(temp_database):
    """Test that FTS triggers work correctly"""
    with get_db() as conn:
        # Insert an entry
        cursor = conn.execute("""
            INSERT INTO entries (title, content, category, tags)
            VALUES (?, ?, ?, ?)
        """, ("Test Entry", "Test content for FTS", "Test", "test"))
        entry_id = cursor.lastrowid
        conn.commit()
        
        # Check that the entry is in the FTS table
        cursor = conn.execute("SELECT rowid FROM entries_fts WHERE rowid = ?", (entry_id,))
        assert cursor.fetchone() is not None
        
        # Update the entry
        conn.execute("""
            UPDATE entries SET content = ? WHERE id = ?
        """, ("Updated content for FTS", entry_id))
        conn.commit()
        
        # Search for the updated content
        cursor = conn.execute("""
            SELECT e.content
            FROM entries_fts 
            JOIN entries e ON entries_fts.rowid = e.id
            WHERE entries_fts MATCH ?
        """, ("Updated",))
        
        results = cursor.fetchall()
        assert len(results) == 1
        assert "Updated content" in results[0][0]
        
        # Delete the entry
        conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()
        
        # Check that it's removed from FTS
        cursor = conn.execute("SELECT rowid FROM entries_fts WHERE rowid = ?", (entry_id,))
        assert cursor.fetchone() is None

def test_database_context_manager(temp_database):
    """Test that the database context manager works correctly"""
    # Test successful connection
    with get_db() as conn:
        cursor = conn.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
    
    # Test that connection is closed after context
    # This is implicit in the context manager implementation

def test_database_constraints(temp_database):
    """Test database constraints and validation"""
    with get_db() as conn:
        # Test that NOT NULL constraints work
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO entries (title, content, category, tags)
                VALUES (NULL, 'Content', 'Category', 'tags')
            """)
        
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO entries (title, content, category, tags)
                VALUES ('Title', NULL, 'Category', 'tags')
            """)
        
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO entries (title, content, category, tags)
                VALUES ('Title', 'Content', NULL, 'tags')
            """)

def test_database_timestamps(temp_database):
    """Test that timestamps are handled correctly"""
    with get_db() as conn:
        # Insert an entry
        cursor = conn.execute("""
            INSERT INTO entries (title, content, category, tags)
            VALUES (?, ?, ?, ?)
        """, ("Timestamp Test", "Content", "Test", ""))
        entry_id = cursor.lastrowid
        conn.commit()
        
        # Check that timestamps are set
        cursor = conn.execute("SELECT created_at, updated_at FROM entries WHERE id = ?", (entry_id,))
        timestamps = cursor.fetchone()
        
        assert timestamps[0] is not None  # created_at
        assert timestamps[1] is not None  # updated_at
        
        # Update the entry and check that updated_at changes
        import time
        time.sleep(1)  # Ensure different timestamp
        
        conn.execute("""
            UPDATE entries SET content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, ("Updated Content", entry_id))
        conn.commit()
        
        cursor = conn.execute("SELECT created_at, updated_at FROM entries WHERE id = ?", (entry_id,))
        new_timestamps = cursor.fetchone()
        
        assert new_timestamps[0] == timestamps[0]  # created_at should be unchanged
        assert new_timestamps[1] != timestamps[1]  # updated_at should be different