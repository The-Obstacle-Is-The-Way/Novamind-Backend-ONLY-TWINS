#!/bin/bash
echo "RESTORING ALL DELETED TEST FILES..."
git show --name-status b87866c | grep "^D.*test_.*\.py" | sed "s/^D\s*//" | while read file; do
  echo "Restoring $file"
  dir=$(dirname "$file")
  mkdir -p "$dir"
  git checkout b87866c~1 -- "$file"
done
echo "RESTORATION COMPLETE"
