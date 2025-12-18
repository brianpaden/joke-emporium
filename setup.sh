#!/usr/bin/env bash
# Joke Emporium Development Setup Script
# One-command setup for Linux/macOS developers
# Usage: ./setup.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_PRE_COMMIT=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-pre-commit)
      SKIP_PRE_COMMIT=true
      shift
      ;;
    --skip-tests)
      SKIP_TESTS=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--skip-pre-commit] [--skip-tests]"
      exit 1
      ;;
  esac
done

echo -e "${CYAN}========================================"
echo "Joke Emporium Development Setup"
echo -e "========================================${NC}\n"

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Step 1: Check Python
echo -e "${YELLOW}[1/7] Checking Python...${NC}"
if command_exists python3; then
  PYTHON_VERSION=$(python3 --version)
  echo -e "${GREEN}  Found: $PYTHON_VERSION${NC}"

  # Check if version is 3.10+
  PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
  PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

  if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo -e "${RED}  ERROR: Python 3.10+ required, found $PYTHON_VERSION${NC}"
    exit 1
  fi
else
  echo -e "${RED}  ERROR: Python not found!${NC}"
  echo -e "${RED}  Please install Python 3.10+ from https://python.org${NC}"
  exit 1
fi

# Step 2: Check/Install uv
echo -e "${YELLOW}[2/7] Checking uv package manager...${NC}"
if command_exists uv; then
  UV_VERSION=$(uv --version)
  echo -e "${GREEN}  Found: $UV_VERSION${NC}"
else
  echo -e "${YELLOW}  Installing uv...${NC}"
  python3 -m pip install --upgrade uv
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}  Installed uv successfully${NC}"
  else
    echo -e "${RED}  ERROR: Failed to install uv${NC}"
    exit 1
  fi
fi

# Step 3: Install dependencies
echo -e "${YELLOW}[3/7] Installing project dependencies...${NC}"
uv sync --extra dev --dev
if [ $? -eq 0 ]; then
  echo -e "${GREEN}  Dependencies installed successfully${NC}"
else
  echo -e "${RED}  ERROR: Failed to install dependencies${NC}"
  exit 1
fi

# Step 4: Check Git LFS
echo -e "${YELLOW}[4/7] Checking Git LFS...${NC}"
if command_exists git-lfs; then
  LFS_VERSION=$(git lfs version)
  echo -e "${GREEN}  Found: $LFS_VERSION${NC}"

  # Initialize Git LFS
  git lfs install >/dev/null 2>&1
  echo -e "${GREEN}  Git LFS initialized${NC}"
else
  echo -e "${YELLOW}  WARNING: Git LFS not found${NC}"
  echo -e "${YELLOW}  Install from: https://git-lfs.github.com/${NC}"
  echo -e "${YELLOW}  (Not critical for basic development)${NC}"
fi

# Step 5: Install pre-commit hooks
if [ "$SKIP_PRE_COMMIT" = false ]; then
  echo -e "${YELLOW}[5/7] Installing pre-commit hooks...${NC}"
  if [ -f ".pre-commit-config.yaml" ]; then
    # Install pre-commit package
    uv pip install pre-commit >/dev/null 2>&1

    # Install hooks
    uv run pre-commit install >/dev/null 2>&1
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}  Pre-commit hooks installed${NC}"
    else
      echo -e "${YELLOW}  WARNING: Failed to install pre-commit hooks${NC}"
    fi
  else
    echo -e "${YELLOW}  Skipping (no .pre-commit-config.yaml found)${NC}"
  fi
else
  echo -e "${YELLOW}[5/7] Skipping pre-commit hooks (--skip-pre-commit flag)${NC}"
fi

# Step 6: Create data directory
echo -e "${YELLOW}[6/7] Setting up data directories...${NC}"
if [ ! -d "data" ]; then
  mkdir -p data
  echo -e "${GREEN}  Created data/ directory${NC}"
else
  echo -e "${GREEN}  data/ directory exists${NC}"
fi

# Step 7: Run tests
if [ "$SKIP_TESTS" = false ]; then
  echo -e "${YELLOW}[7/7] Running test suite...${NC}"
  uv run pytest tests/ -v --tb=short
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}  All tests passed!${NC}"
  else
    echo -e "${YELLOW}  WARNING: Some tests failed${NC}"
    echo -e "${YELLOW}  This may be expected if databases are not set up${NC}"
  fi
else
  echo -e "${YELLOW}[7/7] Skipping tests (--skip-tests flag)${NC}"
fi

# Success!
echo ""
echo -e "${GREEN}========================================"
echo "Setup Complete!"
echo -e "========================================${NC}\n"

echo -e "${CYAN}Next Steps:${NC}"
echo -e "  ${NC}1. Run tests:        task test${NC}"
echo -e "  ${NC}2. Format code:      task format${NC}"
echo -e "  ${NC}3. Import sample:    task import:taivop -- --max-records 100${NC}"
echo -e "  ${NC}4. View commands:    task --list${NC}\n"

echo -e "${CYAN}Documentation:${NC}"
echo -e "  ${NC}- Project overview:  CLAUDE.md${NC}"
echo -e "  ${NC}- Quick start:       README.md${NC}"
echo -e "  ${NC}- DX analysis:       DX_ANALYSIS.md${NC}\n"

echo -e "${GREEN}Happy coding!${NC}"
