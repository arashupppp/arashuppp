#!/bin/bash
# HOVI auto-backup: commit + push
cd /root/hovi || exit 1
git add -A
if git diff --cached --quiet; then
  echo "no changes"
else
  git commit -m "HOVI auto-backup $(date +%Y-%m-%d\ %H:%M)" >/dev/null
fi
PUSH_OUT=$(git push origin main 2>&1)
if echo "$PUSH_OUT" | grep -q "403\|denied"; then
  echo "PUSH FAILED (token perms): $PUSH_OUT" | head -2
else
  echo "pushed: $(git log --oneline -1)"
fi
