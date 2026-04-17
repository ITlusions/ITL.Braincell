#!/bin/bash
# BrainCell Setup Script for Local Development

set -e

echo "🧠 BrainCell Local Setup"
echo "========================"

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"
if [[ $(echo -e "$python_version\n$required_version" | sort -V | head -n1) != "$required_version" ]]; then
    echo "⚠️  Warning: Python 3.11+ is required (found: $python_version)"
fi

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file (update with your settings)"
fi

# Create init script for database setup
cat > setup-db.sh << 'EOF'
#!/bin/bash
# Database setup (assumes PostgreSQL is running locally)

echo "Initializing database..."

# Run SQL init script
psql -U postgres -d postgres -f init.sql 2>/dev/null || echo "Note: Make sure PostgreSQL is running"

echo "✅ Database initialized"
EOF

chmod +x setup-db.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure PostgreSQL, Weaviate, and Redis are running locally"
echo "2. Update .env with your local configuration"
echo "3. Run: python3 -m src.main (if using uvicorn directly)"
echo "4. Or run: docker-compose up -d (for full Docker setup)"
echo ""
