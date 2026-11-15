#!/usr/bin/env bash
# One-command sync: commit every change and push it to GitHub.
set -e
cd "$(dirname "$0")"
read -r -p "Describe the change (Enter = automatic message): " MSG
MSG=${MSG:-"Update $(TZ=Africa/Cairo date '+%Y-%m-%d %H:%M')"}
python3 tools/build_project_md.py
git add -A
git commit -m "$MSG" || echo "Nothing new to commit"
git pull --rebase origin main
git push origin main
git pull --rebase origin main
echo "Done. GitHub will refresh the project MD file within about a minute."
