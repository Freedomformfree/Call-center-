#!/usr/bin/env python3
"""
Database Migration Script
Updates the existing database schema to match the simple authentication system
"""

import sqlite3
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate the existing database to the new simple schema"""
    db_path = "ai_call_center.db"
    backup_path = f"ai_call_center_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        # Create backup
        logger.info(f"Creating backup: {backup_path}")
        if os.path.exists(db_path):
            import shutil
            shutil.copy2(db_path, backup_path)
            logger.info("Backup created successfully")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if we need to migrate
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'full_name' in columns:
            logger.info("Database already has the correct schema")
            return True
            
        logger.info("Starting database migration...")
        
        # Step 1: Create new users table with correct schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                company TEXT,
                phone TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Step 2: Migrate existing data if any
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count > 0:
            logger.info(f"Migrating {user_count} existing users...")
            
            # Copy data from old table to new table
            cursor.execute('''
                INSERT INTO users_new (full_name, email, company, phone, password_hash, created_at, last_login, is_active)
                SELECT 
                    COALESCE(first_name || ' ' || last_name, email) as full_name,
                    email,
                    NULL as company,
                    phone,
                    password_hash,
                    created_at,
                    last_login,
                    is_active
                FROM users
            ''')
            
            logger.info("Data migration completed")
        
        # Step 3: Drop old table and rename new table
        cursor.execute('DROP TABLE users')
        cursor.execute('ALTER TABLE users_new RENAME TO users')
        
        # Step 4: Create sessions table for better session management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Step 5: Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users (is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions (session_token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions (user_id)')
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info("Database migration completed successfully!")
        logger.info("New schema:")
        
        # Verify new schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for column in columns:
            logger.info(f"  {column[1]} {column[2]}")
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        
        # Restore backup if migration failed
        if os.path.exists(backup_path):
            logger.info("Restoring backup...")
            import shutil
            shutil.copy2(backup_path, db_path)
            logger.info("Backup restored")
        
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("✅ Database migration completed successfully!")
    else:
        print("❌ Database migration failed!")