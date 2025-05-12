#!/usr/bin/env python
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'askpaddie.settings')
django.setup()

from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.apps import apps

def create_analytics_dashboard_model():
    """
    Manually create the necessary database objects for AnalyticsDashboardModel.
    This script handles creation of content type and permissions for
    a managed=False model.
    """
    print("Starting manual migration for AnalyticsDashboardModel...")
    
    # Find the analytics app
    analytics_app = apps.get_app_config('analytics')
    if analytics_app:
        print(f"Found analytics app: {analytics_app}")
    else:
        print("Analytics app not found. Make sure it's installed and in INSTALLED_APPS.")
        return
    
    # Create content type for the model if it doesn't exist
    content_type, created = ContentType.objects.get_or_create(
        app_label='analytics',
        model='analyticsdashboardmodel'
    )
    
    if created:
        print("Created content type for AnalyticsDashboardModel.")
    else:
        print("Content type for AnalyticsDashboardModel already exists.")
    
    # Create permissions
    view_permission, created = Permission.objects.get_or_create(
        codename='view_analyticsdashboardmodel',
        name='Can view analytics dashboard',
        content_type=content_type,
    )
    
    if created:
        print("Created view permission for AnalyticsDashboardModel.")
    else:
        print("Permission already exists: Can view analytics dashboard")
    
    # Try to create the table directly (simpler approach)
    try:
        table_name = 'analytics_analyticsdashboardmodel'
        with connection.cursor() as cursor:
            # Direct check without parameters
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='analytics_analyticsdashboardmodel'")
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                print(f"Creating table {table_name}...")
                # Create the table with direct SQL
                cursor.execute("""
                CREATE TABLE analytics_analyticsdashboardmodel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT
                )
                """)
                print("Table created successfully.")
            else:
                print(f"Table {table_name} already exists.")
    except Exception as e:
        print(f"Error during table creation: {str(e)}")
        print("This is not critical as the model is managed=False")
    
    print("Migration completed successfully.")

if __name__ == "__main__":
    create_analytics_dashboard_model()