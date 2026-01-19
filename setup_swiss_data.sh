#!/bin/bash
# Swiss Data Setup - One-Command Data Loading

echo "🇨🇭 Swiss Trading Bot - Data Setup"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "fetch_swiss_data.py" ]; then
    echo "❌ Error: Run from /workspaces/Trading_Bot01"
    exit 1
fi

# Step 1: Load data
echo "Step 1️⃣  Loading Swiss stock data..."
python fetch_swiss_data.py

if [ $? -ne 0 ]; then
    echo "❌ Data loading failed"
    exit 1
fi

# Step 2: Verify
echo ""
echo "Step 2️⃣  Verifying setup..."
python verify_production_setup.py

if [ $? -ne 0 ]; then
    echo "⚠️  Setup verification had issues"
fi

# Step 3: Info
echo ""
echo "✅ Swiss data setup complete!"
echo ""
echo "📊 Next steps:"
echo "   streamlit run dashboard/app.py"
echo ""
echo "Dashboard will be available at:"
echo "   http://localhost:8501"
echo ""
