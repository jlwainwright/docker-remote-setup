#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${YELLOW}Running API tests only (skipping SQLAlchemy-dependent tests)...${NC}"
cd /Users/jacques/DevFolder/Cyber_Zapvend
python -m pytest -vx tests/ -k "not db and not database" 

echo -e "\n${YELLOW}Note: Some tests were skipped due to SQLAlchemy compatibility issues with Python 3.13.${NC}"
echo -e "${YELLOW}Consider using Python 3.11 or 3.12 for full test compatibility.${NC}"
