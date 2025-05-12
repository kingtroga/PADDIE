# manual_migration.py
# Place this file in your project root and run it with:
# python manual_migration.py

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'askpaddie.settings')  # Replace with your actual project name
django.setup()

# Now you can import your Django models
from django.db import connection, DatabaseError, transaction
from django.conf import settings

def run_migration():
    """
    Manually creates a database table for ChatAnalyticsDashboardModel
    Note: This is unusual since the model has managed=False
    """
    with connection.cursor() as cursor:
        # Check if the table already exists
        table_name = 'chatbot_chatanalyticsdashboardmodel'
        
        # Different SQL for different database engines
        if connection.vendor == 'sqlite':
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=%s;",
                [table_name]
            )
            if cursor.fetchone():
                print(f"Table {table_name} already exists. No action taken.")
                return
                
            # Create the table
            print(f"Creating table {table_name}...")
            cursor.execute(f'''
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT
                );
            ''')
            
        elif connection.vendor == 'postgresql':
            cursor.execute(
                "SELECT to_regclass(%s);",
                [table_name]
            )
            if cursor.fetchone()[0]:
                print(f"Table {table_name} already exists. No action taken.")
                return
                
            # Create the table
            print(f"Creating table {table_name}...")
            cursor.execute(f'''
                CREATE TABLE {table_name} (
                    id SERIAL PRIMARY KEY
                );
            ''')
            
        elif connection.vendor == 'mysql':
            cursor.execute(
                "SHOW TABLES LIKE %s;",
                [table_name]
            )
            if cursor.fetchone():
                print(f"Table {table_name} already exists. No action taken.")
                return
                
            # Create the table
            print(f"Creating table {table_name}...")
            cursor.execute(f'''
                CREATE TABLE {table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY
                );
            ''')
        
        # Add a dummy record
        cursor.execute(f"INSERT INTO {table_name} (id) VALUES (1);")
        
        print(f"Table {table_name} created successfully.")

if __name__ == "__main__":
    try:
        with transaction.atomic():
            run_migration()
        print("Migration completed successfully.")
    except DatabaseError as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")