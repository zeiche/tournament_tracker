#!/bin/bash
# Clean git history of Discord tokens

echo "Cleaning git history of sensitive files..."

# Create a backup first
cp -r .git .git.backup

# Use git filter-repo (more reliable than filter-branch)
pip3 install git-filter-repo --break-system-packages 2>/dev/null || pip3 install git-filter-repo

# Remove the problematic files from history
git filter-repo --path dm_text_images.py --invert-paths --force
git filter-repo --path find_discord_user.py --invert-paths --force  
git filter-repo --path send_poop_dm.py --invert-paths --force
git filter-repo --path send_poop_final.py --invert-paths --force
git filter-repo --path send_poop_simple.py --invert-paths --force
git filter-repo --path send_poop_to_hank.py --invert-paths --force
git filter-repo --path send_poop_to_jedi.py --invert-paths --force
git filter-repo --path discord_backup/discord_pure_test.py --invert-paths --force

echo "History cleaned. You'll need to:"
echo "1. git remote add origin https://github.com/zeiche/tournament_tracker.git"
echo "2. git push --force origin master"
echo ""
echo "WARNING: This rewrites history. All collaborators need to re-clone."