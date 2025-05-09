from app import create_app, db
from app.models import Task
from sqlalchemy import text
from datetime import datetime

app = create_app()

with app.app_context():
    # Add the user_id column
    try:
        db.session.execute(text('ALTER TABLE tasks ADD COLUMN user_id INTEGER REFERENCES users(id)'))
        print("Added user_id column to tasks table")
    except Exception as e:
        print(f"Error adding user_id column: {e}")
    
    # Set default user_id to admin user (id=1)
    try:
        db.session.execute(text('UPDATE tasks SET user_id = 1 WHERE user_id IS NULL'))
        print("Updated user_id for existing tasks")
    except Exception as e:
        print(f"Error updating user_id: {e}")
    
    db.session.commit()
    print("Database schema updated successfully.")