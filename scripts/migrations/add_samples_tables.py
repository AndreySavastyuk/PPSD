"""
Migration script to add samples and lab_test_samples tables
"""
from sqlalchemy import text
from database.connection import engine, Base
from models.models import Sample, LabTestSample

def run_migration():
    """Run the migration to create samples and lab_test_samples tables"""
    # Create a connection
    conn = engine.connect()
    
    # Check if tables already exist
    existing_tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    table_names = [table[0] for table in existing_tables]
    
    # Create samples table if it doesn't exist
    if 'samples' not in table_names:
        print("Creating samples table...")
        # Let SQLAlchemy create the table with proper schema
        Sample.__table__.create(bind=engine, checkfirst=True)
        print("samples table created successfully")
    else:
        print("samples table already exists")
    
    # Create lab_test_samples table if it doesn't exist
    if 'lab_test_samples' not in table_names:
        print("Creating lab_test_samples table...")
        # Let SQLAlchemy create the table with proper schema
        LabTestSample.__table__.create(bind=engine, checkfirst=True)
        print("lab_test_samples table created successfully")
    else:
        print("lab_test_samples table already exists")
    
    # Add test_samples relationship to lab_tests table if needed
    # This is handled automatically by SQLAlchemy relationships
    
    # Commit the transaction
    conn.commit()
    conn.close()
    
    return True 