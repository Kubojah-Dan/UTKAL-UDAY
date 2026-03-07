#!/bin/bash

# Utkal Uday - Quick Setup Script
# This script helps set up the development environment

echo "🎓 Utkal Uday - Quick Setup Script"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Windows (Git Bash)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows environment"
    IS_WINDOWS=true
else
    IS_WINDOWS=false
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

# Check Python
if command_exists python || command_exists python3; then
    PYTHON_CMD=$(command_exists python && echo "python" || echo "python3")
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
else
    echo -e "${RED}✗${NC} Python not found. Please install Python 3.9+"
    exit 1
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION found"
else
    echo -e "${RED}✗${NC} Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓${NC} npm $NPM_VERSION found"
else
    echo -e "${RED}✗${NC} npm not found. Please install npm"
    exit 1
fi

# Check MongoDB
if command_exists mongod; then
    MONGO_VERSION=$(mongod --version | head -n 1)
    echo -e "${GREEN}✓${NC} MongoDB found"
else
    echo -e "${YELLOW}⚠${NC} MongoDB not found. You'll need to install it separately."
fi

echo ""
echo "=================================="
echo ""

# Setup backend
echo "🔧 Setting up backend..."
cd utkal-backend || exit

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠${NC} .env file not found. Creating from template..."
    cat > .env << EOF
GROQ_API_KEY=your_groq_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here
MONGODB_URL=mongodb://localhost:27017/utkal_uday
UTKAL_TEACHER_PASSWORD=teacher123
UTKAL_AUTH_SECRET=your_secret_key_here
EOF
    echo -e "${GREEN}✓${NC} .env file created. Please edit it with your API keys."
else
    echo -e "${GREEN}✓${NC} .env file exists"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if $IS_WINDOWS; then
    py -m pip install -r requirements.txt
else
    $PYTHON_CMD -m pip install -r requirements.txt
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Backend dependencies installed"
else
    echo -e "${RED}✗${NC} Failed to install backend dependencies"
    exit 1
fi

cd ..

# Setup frontend
echo ""
echo "🎨 Setting up frontend..."
cd utkal-frontend || exit

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠${NC} .env file not found. Creating from template..."
    cat > .env << EOF
VITE_API_BASE=http://127.0.0.1:8000
VITE_ANDROID_API_BASE=http://10.0.2.2:8000
EOF
    echo -e "${GREEN}✓${NC} .env file created"
else
    echo -e "${GREEN}✓${NC} .env file exists"
fi

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Frontend dependencies installed"
else
    echo -e "${RED}✗${NC} Failed to install frontend dependencies"
    exit 1
fi

cd ..

# Create uploads directory
echo ""
echo "📁 Creating necessary directories..."
mkdir -p utkal-backend/uploads
mkdir -p utkal-backend/app/data
echo -e "${GREEN}✓${NC} Directories created"

# Summary
echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Edit backend .env file with your API keys:"
echo "   - Get Groq API key: https://console.groq.com/keys"
echo "   - Get Sarvam.ai API key: https://www.sarvam.ai/"
echo ""
echo "2. Start MongoDB:"
if $IS_WINDOWS; then
    echo "   mongod --dbpath C:\\data\\db"
else
    echo "   sudo systemctl start mongod"
    echo "   OR: mongod --dbpath /path/to/data"
fi
echo ""
echo "3. Start the backend (in utkal-backend directory):"
if $IS_WINDOWS; then
    echo "   py -m uvicorn app.main:app --reload"
else
    echo "   uvicorn app.main:app --reload"
fi
echo ""
echo "4. Start the frontend (in utkal-frontend directory):"
echo "   npm run dev"
echo ""
echo "5. Access the application:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📚 Documentation:"
echo "   - COMPLETE_SUMMARY.md - Full feature overview"
echo "   - IMPLEMENTATION_GUIDE.md - Detailed setup guide"
echo "   - FEATURES_SUMMARY.md - Quick reference"
echo "   - DEPLOYMENT_CHECKLIST.md - Production deployment"
echo ""
echo "🎉 Happy coding!"
