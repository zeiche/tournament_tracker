# ⚠️ CRITICAL WARNING FOR ALL CLAUDE INSTANCES ⚠️

## 🛑 ABSOLUTELY NO INDEPENDENT DEBUG/TEST SCRIPTS! 🛑

### THIS IS A HARD RULE - NO EXCEPTIONS!

---

## ❌ FORBIDDEN ACTIONS:

1. **DO NOT CREATE** standalone debug scripts (debug_*.py)
2. **DO NOT CREATE** standalone test scripts (test_*.py) 
3. **DO NOT CREATE** demo scripts outside of go.py
4. **DO NOT CREATE** one-off utility scripts
5. **DO NOT CREATE** temporary testing files

---

## ✅ CORRECT APPROACH:

### ALL functionality MUST be integrated into `go.py`

If you need to debug, test, or demonstrate something:

1. **ADD IT TO go.py** as a proper command
2. Use the existing command structure:
   ```python
   elif args.command == "your-new-command":
       # Your code here
   ```
3. Make it reusable and documented
4. Ensure it follows the existing patterns

---

## 📋 ACCEPTABLE COMMANDS IN go.py:

- `--sync`: Sync with start.gg
- `--stats`: Show database statistics
- `--service-status`: Check service status
- `--restart-services`: Restart services
- `--discord-bot`: Run Discord bot
- `--claude-service`: Run Claude service
- `--visualize`: Generate visualizations
- `--test-feature`: Test specific features (ADD NEW TESTS HERE!)
- `--debug-feature`: Debug functionality (ADD DEBUG CODE HERE!)

---

## 🚨 WHY THIS MATTERS:

1. **Maintainability**: Scattered scripts create chaos
2. **Discoverability**: Everything should be in one place
3. **Consistency**: One entry point for all operations
4. **Cleanliness**: No file pollution in the directory
5. **Professional Standards**: This is production code

---

## 💡 EXAMPLES OF WHAT TO DO:

### ❌ WRONG:
```bash
# Creating a new file
python test_discord_feature.py
```

### ✅ RIGHT:
```bash
# Adding to go.py and running
python go.py --test-discord-feature
```

### ❌ WRONG:
```python
# Creating debug_database.py
def debug_database():
    # debug code
```

### ✅ RIGHT:
```python
# In go.py
elif args.command == "debug-database":
    from database_service import debug_database
    debug_database()
```

---

## 🎯 ENFORCEMENT:

**Any Claude instance that creates independent debug/test scripts will be considered to be violating core architectural principles.**

**The directory has been cleaned. Keep it that way.**

---

## 📝 FINAL WORDS:

If you're reading this and thinking "but I just need a quick test script..." - **STOP!**

Add it to `go.py`. No exceptions. This is the way.

---

*Last cleaned: 2025-09-06*
*Scripts removed: 60+ independent debug/test/demo files*
*Maintainer: The Claude who had to clean up this mess*