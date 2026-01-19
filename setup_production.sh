#!/bin/bash
# Setup Production Environment
# Initializes all components for the trading bot

set -e

echo "🚀 Setting up Trading Bot Production Environment"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Step 1: Create .env file if not exists
echo -e "${BLUE}1. Setting up environment variables${NC}"
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Financial Data
FMP_API_KEY=your_api_key_here

# Database
DUCKDB_PATH=/workspaces/Trading_Bot01/database/qsconnect.duckdb

# Feature Store
FEATURE_CACHE_DIR=/workspaces/Trading_Bot01/database/cache

# Optuna
OPTUNA_DB_PATH=sqlite:////workspaces/Trading_Bot01/database/optuna/optuna.db

# Trading
INITIAL_CAPITAL=100000
MAX_LEVERAGE=2.0
MAX_POSITION_SIZE=0.1
EOF
    echo -e "${GREEN}✅ Created .env file${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Step 2: Create directories
echo -e "${BLUE}2. Creating directory structure${NC}"
mkdir -p database/{cache,fmp,yahoo,user,optuna}
mkdir -p src/{analytics,feature_store,optimization}
mkdir -p dashboard
mkdir -p orchestration
mkdir -p logs
echo -e "${GREEN}✅ Directories created${NC}"

# Step 3: Install dependencies
echo -e "${BLUE}3. Installing dependencies${NC}"
if command -v pip &> /dev/null; then
    pip install --upgrade pip setuptools wheel -q
    pip install duckdb optuna streamlit plotly pyarrow -q
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  pip not found${NC}"
fi

# Step 4: Verify setup
echo -e "${BLUE}4. Verifying setup${NC}"
if python3 verify_production_setup.py; then
    echo -e "${GREEN}✅ Setup verification passed${NC}"
else
    echo -e "${YELLOW}⚠️  Some verification tests failed${NC}"
fi

# Step 5: Show next steps
echo ""
echo -e "${GREEN}=================================================="
echo "✅ Production Setup Complete!"
echo "==================================================${NC}"
echo ""
echo "📝 Next steps:"
echo "1. Set your FMP_API_KEY in .env:"
echo "   export FMP_API_KEY=your_key_here"
echo ""
echo "2. Run the Streamlit dashboard:"
echo "   streamlit run dashboard/app.py"
echo ""
echo "3. Start the data pipeline:"
echo "   python orchestration/prefect_flows.py"
echo ""
echo "4. Or install Prefect for scheduled runs:"
echo "   pip install prefect"
echo "   prefect serve orchestration/prefect_flows.py"
echo ""
