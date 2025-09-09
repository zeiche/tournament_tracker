# Claude Setup Guide

## Quick Start

1. **Get an API Key**
   - Sign up at https://console.anthropic.com
   - Go to Account → API Keys
   - Create a new key (starts with `sk-ant-api`)

2. **Add to .env**
   ```bash
   echo 'ANTHROPIC_API_KEY=sk-ant-api-YOUR-KEY-HERE' >> .env
   ```

3. **Test Interactive Mode**
   ```bash
   ./go.py --interactive
   ```

## Troubleshooting

### "No API key configured" Error

The API key must be in one of these locations:
- `/home/ubuntu/claude/tournament_tracker/.env` (preferred)
- `/home/ubuntu/claude/.env` (parent directory)

Format in .env:
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
```

### Verify Setup

Run the setup checker:
```bash
./setup_claude_api.sh
```

Or test directly:
```bash
./go.py --test-env | grep ANTHROPIC
```

## How It Works

1. **go.py loads .env files** on startup (both parent and local)
2. **Environment variables are set** before starting services
3. **Claude services read** from `os.getenv('ANTHROPIC_API_KEY')`
4. **Interactive mode** uses the bonjour-enhanced Claude service

## Features When Working

- Natural language conversation with Claude
- Dynamic service discovery via Bonjour
- Services announce capabilities in real-time
- Claude's abilities grow as services start
- Async processing for responsive interaction

## Security Note

Never commit your API key to git! The .env file should be in .gitignore.