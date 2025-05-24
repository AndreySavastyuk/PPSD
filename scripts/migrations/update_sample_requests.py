"""
Migration script to add sample location, cutting scheme, and manufacturing fields to SampleRequest table
"""
from sqlalchemy import text
from database.connection import engine

def run_migration():
    """Run the migration to add new fields to sample_requests table"""
    # Create a connection
    conn = engine.connect()
    
    # Check if the columns already exist
    columns = conn.execute(text("PRAGMA table_info(sample_requests)")).fetchall()
    column_names = [col[1] for col in columns]
    
    # Add sample_location column if it doesn't exist
    if 'sample_location' not in column_names:
        conn.execute(text("ALTER TABLE sample_requests ADD COLUMN sample_location VARCHAR(100)"))
    
    # Add sample_cutting_scheme column if it doesn't exist
    if 'sample_cutting_scheme' not in column_names:
        conn.execute(text("ALTER TABLE sample_requests ADD COLUMN sample_cutting_scheme VARCHAR(255)"))
    
    # Add manufactured_by_id column if it doesn't exist
    if 'manufactured_by_id' not in column_names:
        conn.execute(text("ALTER TABLE sample_requests ADD COLUMN manufactured_by_id INTEGER REFERENCES users(id)"))
    
    # Add manufacturing_notes column if it doesn't exist
    if 'manufacturing_notes' not in column_names:
        conn.execute(text("ALTER TABLE sample_requests ADD COLUMN manufacturing_notes TEXT"))
    
    # Commit the transaction
    conn.commit()
    conn.close()
    
    return True 