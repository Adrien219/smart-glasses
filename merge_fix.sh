#!/bin/bash
echo "🔄 Fusion propre des changements..."

# 1. Sauvegarder le commit local dans une branche temporaire
git branch temp-branch

# 2. Revenir au dépôt distant
git reset --hard origin/main

# 3. Créer un patch avec vos changements
git checkout temp-branch
git format-patch origin/main --stdout > my_changes.patch

# 4. Revenir à main et appliquer le patch
git checkout main
git apply my_changes.patch

# 5. Nettoyer
rm my_changes.patch
git branch -d temp-branch

# 6. Ajouter et commiter
git add .
git commit -m "Merge local changes with remote repository

- Arduino navigation system
- Sensor integration
- Test suite
- Updated configuration"

# 7. Pousser
git push origin main
