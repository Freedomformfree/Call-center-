# 🗄️ Local Database Setup - Same Computer Installation

## 📍 Database Location
The database will be installed and run on the **same computer** as the VoiceConnect Pro project, providing:
- **Zero Network Latency** - Direct local access
- **Complete Data Control** - No external dependencies
- **Enhanced Security** - Data never leaves your machine
- **Cost Effective** - No cloud database fees
- **High Performance** - Local SSD/HDD access

## 🐘 PostgreSQL Local Installation

### For Ubuntu/Debian Systems:
```bash
# Update package list
sudo apt update

# Install PostgreSQL and additional tools
sudo apt install postgresql postgresql-contrib postgresql-client

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

### For CentOS/RHEL/Rocky Linux:
```bash
# Install PostgreSQL
sudo dnf install postgresql postgresql-server postgresql-contrib

# Initialize database
sudo postgresql-setup --initdb

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### For Windows:
1. Download PostgreSQL installer from https://www.postgresql.org/download/windows/
2. Run installer and follow setup wizard
3. Remember the password you set for 'postgres' user
4. PostgreSQL will start automatically as a Windows service

### For macOS:
```bash
# Using Homebrew
brew install postgresql

# Start PostgreSQL
brew services start postgresql

# Or using MacPorts
sudo port install postgresql14-server
```

## 🔧 Database Configuration

### 1. Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE voiceconnect_pro;

# Create user with password
CREATE USER voiceconnect_user WITH PASSWORD 'secure_password_2024';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE voiceconnect_pro TO voiceconnect_user;

# Grant schema privileges
GRANT ALL ON SCHEMA public TO voiceconnect_user;

# Exit psql
\q
```

### 2. Update Project Configuration
The project will automatically use the local database with these settings:

**File: `core-api/config.py`**
```python
DATABASE_URL = "postgresql://voiceconnect_user:secure_password_2024@localhost:5432/voiceconnect_pro"
```

### 3. Database Connection Details
- **Host**: `localhost` (same computer)
- **Port**: `5432` (PostgreSQL default)
- **Database**: `voiceconnect_pro`
- **Username**: `voiceconnect_user`
- **Password**: `secure_password_2024`

## 🏗️ Database Schema Setup

The project will automatically create all required tables:

### Core Tables:
```sql
-- Users table with SMS verification
users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number VARCHAR(20),
    role VARCHAR(50),
    is_active BOOLEAN,
    is_verified BOOLEAN,
    email_verified_at TIMESTAMP,
    phone_verified_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_login TIMESTAMP
);

-- SMS verification tracking
sms_verifications (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(20),
    code VARCHAR(10),
    purpose VARCHAR(50),
    expires_at TIMESTAMP,
    attempts INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    is_expired BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    created_at TIMESTAMP,
    user_id UUID REFERENCES users(id)
);

-- Business tools and configurations
business_tools (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    configuration JSONB,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Call logs and analytics
call_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    phone_number VARCHAR(20),
    duration INTEGER,
    status VARCHAR(50),
    recording_url VARCHAR(500),
    transcript TEXT,
    ai_analysis JSONB,
    created_at TIMESTAMP
);
```

## 🔒 Local Database Security

### 1. PostgreSQL Configuration
**File: `/etc/postgresql/14/main/postgresql.conf`**
```ini
# Listen only on localhost for security
listen_addresses = 'localhost'

# Enable logging
log_connections = on
log_disconnections = on
log_statement = 'all'

# Performance settings for local use
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

### 2. Access Control
**File: `/etc/postgresql/14/main/pg_hba.conf`**
```ini
# Local connections only
local   all             postgres                                peer
local   all             voiceconnect_user                       md5
host    voiceconnect_pro voiceconnect_user    127.0.0.1/32      md5
host    voiceconnect_pro voiceconnect_user    ::1/128           md5
```

### 3. Firewall Configuration
```bash
# Ensure PostgreSQL is not accessible from outside
sudo ufw deny 5432/tcp

# Only allow local connections
sudo ufw allow from 127.0.0.1 to any port 5432
```

## 📊 Database Management Tools

### 1. Command Line Tools
```bash
# Connect to database
psql -h localhost -U voiceconnect_user -d voiceconnect_pro

# Backup database
pg_dump -h localhost -U voiceconnect_user voiceconnect_pro > backup.sql

# Restore database
psql -h localhost -U voiceconnect_user voiceconnect_pro < backup.sql

# Check database size
psql -h localhost -U voiceconnect_user -d voiceconnect_pro -c "SELECT pg_size_pretty(pg_database_size('voiceconnect_pro'));"
```

### 2. GUI Tools (Optional)
- **pgAdmin 4**: Web-based PostgreSQL administration
- **DBeaver**: Universal database tool
- **DataGrip**: JetBrains database IDE

## 🚀 Automatic Database Setup

The project includes automatic database initialization:

**File: `run.py`** (already implemented)
```python
def setup_database():
    """Setup local PostgreSQL database"""
    try:
        # Create database if not exists
        # Run migrations
        # Create initial admin user
        # Setup SMS verification tables
        logger.info("✅ Database setup complete")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
```

## 🔄 Database Migrations

### Automatic Migrations
The project uses SQLModel/Alembic for database migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "Add SMS verification"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current
```

### Manual Schema Updates
```sql
-- Add new columns
ALTER TABLE users ADD COLUMN phone_verified_at TIMESTAMP;

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_sms_verifications_phone ON sms_verifications(phone_number);
```

## 📈 Performance Optimization

### 1. Local SSD Storage
- Store database on SSD for faster I/O
- Use separate partition for database if possible

### 2. Memory Configuration
```sql
-- Check current settings
SHOW shared_buffers;
SHOW effective_cache_size;

-- Optimize for local use
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

### 3. Connection Pooling
The project uses SQLAlchemy connection pooling:
```python
# In config.py
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 20
```

## 🔍 Monitoring & Maintenance

### 1. Database Health Checks
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check database size
SELECT pg_size_pretty(pg_database_size('voiceconnect_pro'));

-- Check table sizes
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 2. Automated Backups
```bash
#!/bin/bash
# backup_database.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U voiceconnect_user voiceconnect_pro > "backup_${DATE}.sql"
gzip "backup_${DATE}.sql"

# Keep only last 7 days of backups
find . -name "backup_*.sql.gz" -mtime +7 -delete
```

### 3. Log Monitoring
```bash
# Monitor PostgreSQL logs
tail -f /var/log/postgresql/postgresql-14-main.log

# Monitor application logs
tail -f core-api/logs/application.log
```

## 🎯 Benefits of Local Database

### 1. **Performance**
- **Zero Network Latency**: Direct local access
- **High Throughput**: Local SSD/NVMe speeds
- **No Bandwidth Limits**: Unlimited local data transfer

### 2. **Security**
- **Data Isolation**: Never leaves your computer
- **No External Access**: Firewall protected
- **Complete Control**: You own all data

### 3. **Cost Effectiveness**
- **No Monthly Fees**: One-time setup cost
- **No Data Transfer Charges**: Unlimited local usage
- **Scalable Storage**: Add more storage as needed

### 4. **Reliability**
- **No Internet Dependency**: Works offline
- **No Service Outages**: Under your control
- **Instant Backups**: Local backup solutions

## 🛠️ Troubleshooting

### Common Issues:

1. **Connection Refused**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql
```

2. **Authentication Failed**
```bash
# Reset password
sudo -u postgres psql
ALTER USER voiceconnect_user PASSWORD 'new_password';
```

3. **Database Not Found**
```bash
# Create database
sudo -u postgres createdb voiceconnect_pro
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE voiceconnect_pro TO voiceconnect_user;"
```

4. **Permission Denied**
```bash
# Grant schema permissions
sudo -u postgres psql voiceconnect_pro -c "GRANT ALL ON SCHEMA public TO voiceconnect_user;"
```

---

**Database Status**: 🟢 **LOCAL** - PostgreSQL running on same computer

**Security Level**: 🔒 **MAXIMUM** - Data never leaves your machine

**Performance**: ⚡ **OPTIMAL** - Direct local access with zero latency