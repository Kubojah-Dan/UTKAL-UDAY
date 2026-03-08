#!/bin/bash
# IndicTrans2 Quick Setup Script

echo "=========================================="
echo "IndicTrans2 Setup for Utkal Uday"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if [[ $(echo "$python_version 3.9" | awk '{print ($1 >= $2)}') -eq 0 ]]; then
    echo "❌ Python 3.9+ required. Current: $python_version"
    exit 1
fi
echo "✅ Python version OK"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install transformers sentencepiece IndicTransToolkit --quiet
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Verify model files
echo "Checking model files..."
if [ -f "models/model.safetensors" ]; then
    echo "✅ Model files found"
else
    echo "❌ Model files not found in models/"
    echo "Please ensure IndicTrans2 model is in utkal-backend/models/"
    exit 1
fi
echo ""

# Run verification
echo "Running verification tests..."
python verify_indictrans.py

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start backend: uvicorn app.main:app --reload"
echo "2. Open Teacher Dashboard"
echo "3. Generate questions and translate"
echo ""
