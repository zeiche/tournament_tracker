#!/usr/bin/env python3
import os

print("Environment variables loaded by go.py:")
print(f"DISCORD_BOT_TOKEN: {os.environ.get('DISCORD_BOT_TOKEN', 'NOT SET')}")
print(f"AUTH_KEY: {os.environ.get('AUTH_KEY', 'NOT SET')}")
print(f"ANTHROPIC_API_KEY: {os.environ.get('ANTHROPIC_API_KEY', 'NOT SET')}")