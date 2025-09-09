#!/bin/bash
# Setup script for Claude API key

echo "Claude API Key Setup"
echo "===================="
echo ""
echo "To use Claude's interactive mode, you need an Anthropic API key."
echo "Get one from: https://console.anthropic.com/account/keys"
echo ""

# Check current status
if grep -q "^ANTHROPIC_API_KEY=sk-ant-" /home/ubuntu/claude/tournament_tracker/.env 2>/dev/null; then
    echo "✅ API key is already configured in .env"
    exit 0
fi

if grep -q "^ANTHROPIC_API_KEY=sk-ant-" /home/ubuntu/claude/.env 2>/dev/null; then
    echo "✅ API key is configured in parent .env"
    exit 0
fi

echo "❌ No API key found"
echo ""
echo "To add your API key, run:"
echo ""
echo "  echo 'ANTHROPIC_API_KEY=sk-ant-api...' >> /home/ubuntu/claude/tournament_tracker/.env"
echo ""
echo "Or edit .env and uncomment the ANTHROPIC_API_KEY line with your key."
echo ""
echo "Then run: ./go.py --interactive"