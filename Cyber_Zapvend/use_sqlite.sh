#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Configuring application to use SQLite database...${NC}"

# Check if the database.py file exists
if [ ! -f backend/database.py ]; then
    echo -e "${RED}Error: backend/database.py file not found!${NC}"
    exit 1
fi

# Create a backup of the original database.py file
echo -e "${YELLOW}Creating backup of database.py to database.py.bak${NC}"
cp backend/database.py backend/database.py.bak

# Update the database.py file to use SQLite instead of PostgreSQL
echo -e "${YELLOW}Updating database.py to use SQLite${NC}"
cat > backend/database.py << 'EOF'
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Use SQLite as a fallback
SQLITE_DATABASE_URL = "sqlite+aiosqlite:///./cyberzapvend.db"
DATABASE_URL = os.environ.get("DATABASE_URL", SQLITE_DATABASE_URL)

# Create the SQLAlchemy async engine
async_engine = create_async_engine(
    DATABASE_URL, 
    echo=True,  # echo=True for dev, consider False for prod
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create a configured "AsyncSession" class
AsyncSessionLocal = sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False  # Common practice for async sessions
)

# Create a Base class for declarative models
Base = declarative_base()

# Async function to create database tables
async def create_db_tables():
    """Creates database tables if they don't exist."""
    async with async_engine.begin() as conn:
        # In SQLAlchemy 2.x, run_sync is used to run synchronous DDL operations
        await conn.run_sync(Base.metadata.create_all)
    # Note: For production, Alembic is recommended for migrations.

# Async dependency to get the database session
async def get_async_db() -> AsyncSession:  # Type hint for clarity
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Commits are handled explicitly in endpoints where changes are made
        except Exception:
            await session.rollback()  # Rollback on error
            raise
        finally:
            await session.close()  # Ensure session is closed
EOF

# Make sure we have the required SQLite dependencies
echo -e "${YELLOW}Installing aiosqlite dependency...${NC}"
source .venv/bin/activate
python -m pip install aiosqlite

# Update or create .env file to use SQLite
if [ -f .env ]; then
    echo -e "${YELLOW}Creating backup of existing .env file to .env.pg.backup${NC}"
    cp .env .env.pg.backup
    
    if grep -q "DATABASE_URL=" .env; then
        sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=sqlite+aiosqlite:///./cyberzapvend.db|g" .env
        echo -e "${GREEN}Updated DATABASE_URL in .env file to use SQLite${NC}"
    else
        echo "DATABASE_URL=sqlite+aiosqlite:///./cyberzapvend.db" >> .env
        echo -e "${GREEN}Added DATABASE_URL to .env file to use SQLite${NC}"
    fi
else
    echo "DATABASE_URL=sqlite+aiosqlite:///./cyberzapvend.db" > .env
    echo -e "${GREEN}Created .env file with SQLite DATABASE_URL${NC}"
fi

echo -e "\n${GREEN}Configuration completed! The application is now set to use SQLite.${NC}"
echo -e "${YELLOW}Would you like to restart the application now? (y/n)${NC}"
read -n 1 -p "" answer
echo ""

if [ "$answer" == "y" ] || [ "$answer" == "Y" ]; then
    echo -e "${YELLOW}Stopping any running servers...${NC}"
    pkill -f "uvicorn backend.main:app"
    pkill -f "npm run dev"
    sleep 2
    echo -e "${YELLOW}Starting the application...${NC}"
    ./start_app.sh &
    echo -e "${GREEN}Application is starting with SQLite database...${NC}"
else
    echo -e "${YELLOW}Exiting without restarting. You can restart the application manually with:${NC}"
    echo -e "  ./start_app.sh"
fi
