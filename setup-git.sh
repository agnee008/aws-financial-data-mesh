#!/bin/bash

# Git Setup Script for AWS Financial Data Mesh
# This script initializes the repository and prepares it for GitHub

echo "🚀 AWS Financial Data Mesh - Git Setup"
echo "======================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

echo "✅ Git is installed"
echo ""

# Initialize git repository
echo "📦 Initializing Git repository..."
git init
git add .
git commit -m "Initial commit: AWS Financial Data Mesh architecture

- Event-driven data pipeline with EventBridge
- Serverless processing with Lambda and Glue
- Data Mesh principles implementation
- Production-ready infrastructure as code
- Comprehensive testing and documentation"

echo "✅ Repository initialized"
echo ""

# Create main branch
echo "🌿 Creating main branch..."
git branch -M main

echo "✅ Main branch created"
echo ""

# Display next steps
echo "📝 Next Steps:"
echo "=============="
echo ""
echo "1. Create a GitHub repository:"
echo "   - Go to https://github.com/new"
echo "   - Repository name: aws-financial-data-mesh"
echo "   - Description: Production-ready event-driven data architecture for FinTech"
echo "   - Make it Public"
echo "   - Do NOT initialize with README (we already have one)"
echo ""
echo "2. Add GitHub as remote:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/aws-financial-data-mesh.git"
echo ""
echo "3. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "4. Add repository topics on GitHub:"
echo "   - aws"
echo "   - eventbridge"
echo "   - data-mesh"
echo "   - fintech"
echo "   - data-engineering"
echo "   - serverless"
echo "   - python"
echo ""
echo "5. Enable GitHub Actions (optional):"
echo "   - Go to Settings > Actions > General"
echo "   - Allow all actions and reusable workflows"
echo ""
echo "✅ Setup complete!"
echo ""
echo "Your repository is ready to be pushed to GitHub! 🎉"
