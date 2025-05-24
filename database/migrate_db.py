from sqlalchemy import text
from database.connection import engine, SessionLocal

def migrate_database():
    """
    Add new issue columns to qc_checks table
    """
    db = SessionLocal()
    try:
        # Add new columns to qc_checks table
        new_columns = [
            "issue_repurchase BOOLEAN DEFAULT 0",
            "issue_poor_quality BOOLEAN DEFAULT 0",
            "issue_no_stamp BOOLEAN DEFAULT 0",
            "issue_diameter_deviation BOOLEAN DEFAULT 0",
            "issue_cracks BOOLEAN DEFAULT 0",
            "issue_no_melt BOOLEAN DEFAULT 0",
            "issue_no_certificate BOOLEAN DEFAULT 0",
            "issue_copy BOOLEAN DEFAULT 0"
        ]
        
        for column in new_columns:
            try:
                # Check if column exists
                column_name = column.split()[0]
                check_sql = f"""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('qc_checks') 
                WHERE name='{column_name}'
                """
                result = db.execute(text(check_sql)).first()
                
                if result[0] == 0:
                    # Add column if it doesn't exist
                    sql = f"ALTER TABLE qc_checks ADD COLUMN {column}"
                    db.execute(text(sql))
                    print(f"Added column: {column_name}")
            except Exception as e:
                print(f"Error adding column {column_name}: {e}")
        
        # Add new columns to material_entries table for edit requests
        material_entry_columns = [
            "edit_requested BOOLEAN DEFAULT 0",
            "edit_comment VARCHAR(255)"
        ]
        
        for column in material_entry_columns:
            try:
                # Check if column exists
                column_name = column.split()[0]
                check_sql = f"""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('material_entries') 
                WHERE name='{column_name}'
                """
                result = db.execute(text(check_sql)).first()
                
                if result[0] == 0:
                    # Add column if it doesn't exist
                    sql = f"ALTER TABLE material_entries ADD COLUMN {column}"
                    db.execute(text(sql))
                    print(f"Added column: {column_name}")
            except Exception as e:
                print(f"Error adding column {column_name}: {e}")
        
        db.commit()
        print("Database migration completed successfully")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database() 