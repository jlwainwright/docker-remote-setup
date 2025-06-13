#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Configuring Docker PostgreSQL connection...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker Desktop first.${NC}"
    exit 1
fi

# Find PostgreSQL container
POSTGRES_CONTAINER=$(docker ps | grep postgres | awk '{print $1}')

if [ -z "$POSTGRES_CONTAINER" ]; then
    echo -e "${RED}No PostgreSQL container found running.${NC}"
    
    # Show all containers for reference
    echo -e "${YELLOW}Here are all your containers:${NC}"
    docker ps -a
    
    echo -e "\n${YELLOW}Enter the ID of your PostgreSQL container:${NC}"
    read -p "" POSTGRES_CONTAINER
    
    if [ -z "$POSTGRES_CONTAINER" ]; then
        echo -e "${RED}No container ID provided. Exiting.${NC}"
        exit 1
    fi
    
    # Try to start the container
    echo -e "${YELLOW}Trying to start container $POSTGRES_CONTAINER...${NC}"
    docker start $POSTGRES_CONTAINER
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to start container. Please check the container ID and try again.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Using PostgreSQL container: $POSTGRES_CONTAINER${NC}"

# Get DB connection info from user
echo -e "${YELLOW}Enter PostgreSQL username (default: postgres):${NC}"
read -p "" DB_USER
DB_USER=${DB_USER:-postgres}

echo -e "${YELLOW}Enter PostgreSQL password:${NC}"
read -s -p "" DB_PASSWORD
echo ""

echo -e "${YELLOW}Enter PostgreSQL database name (default: cyberzapvend):${NC}"
read -p "" DB_NAME
DB_NAME=${DB_NAME:-cyberzapvend}

# Try to connect to database to validate credentials
echo -e "${YELLOW}Testing database connection...${NC}"
if docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}Successfully connected to database $DB_NAME${NC}"
else
    echo -e "${YELLOW}Could not connect to database $DB_NAME. It might not exist yet.${NC}"
    
    # Check if user exists and has permission to create database
    if docker exec $POSTGRES_CONTAINER psql -U $DB_USER -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${YELLOW}User $DB_USER exists but database $DB_NAME doesn't exist. Trying to create it...${NC}"
        if docker exec $POSTGRES_CONTAINER psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;" > /dev/null 2>&1; then
            echo -e "${GREEN}Created database $DB_NAME successfully.${NC}"
        else
            echo -e "${RED}Failed to create database $DB_NAME. You might not have sufficient permissions.${NC}"
            echo -e "${YELLOW}Please create the database manually or use an existing database.${NC}"
            
            echo -e "${YELLOW}Enter an existing PostgreSQL database name:${NC}"
            read -p "" DB_NAME
            
            if [ -z "$DB_NAME" ]; then
                echo -e "${RED}No database name provided. Exiting.${NC}"
                exit 1
            fi
            
            if ! docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
                echo -e "${RED}Still cannot connect to database $DB_NAME. Please check your credentials.${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${RED}Cannot connect with user $DB_USER. Please check your credentials.${NC}"
        exit 1
    fi
fi

# Get the port mapping
POSTGRES_PORT=$(docker port $POSTGRES_CONTAINER | grep 5432 | awk '{split($3, a, ":"); print a[2]}')
POSTGRES_PORT=${POSTGRES_PORT:-5432}
echo -e "${YELLOW}PostgreSQL port mapping: $POSTGRES_PORT${NC}"

# Construct the database URL
DB_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@localhost:${POSTGRES_PORT}/${DB_NAME}"
echo -e "${GREEN}Constructed database URL${NC}"

# Update or create .env file
if [ -f .env ]; then
    echo -e "${YELLOW}Creating backup of existing .env file to .env.backup${NC}"
    cp .env .env.backup
    
    if grep -q "DATABASE_URL=" .env; then
        sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=${DB_URL}|g" .env
        echo -e "${GREEN}Updated DATABASE_URL in .env file${NC}"
    else
        echo "DATABASE_URL=${DB_URL}" >> .env
        echo -e "${GREEN}Added DATABASE_URL to .env file${NC}"
    fi
else
    echo "DATABASE_URL=${DB_URL}" > .env
    echo -e "${GREEN}Created new .env file with DATABASE_URL${NC}"
fi

echo -e "\n${YELLOW}Database connection configured. Would you like to restart the application now? (y/n)${NC}"
read -n 1 -p "" answer
echo ""

if [ "$answer" == "y" ] || [ "$answer" == "Y" ]; then
    echo -e "${YELLOW}Stopping any running servers...${NC}"
    pkill -f "uvicorn backend.main:app"
    pkill -f "npm run dev"
    sleep 2
    echo -e "${YELLOW}Starting the application...${NC}"
    ./start_app.sh &
    echo -e "${GREEN}Application is starting...${NC}"
else
    echo -e "${YELLOW}Exiting without restarting. You can restart the application manually with:${NC}"
    echo -e "  ./start_app.sh"
fi
