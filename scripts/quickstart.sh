#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Kimagent — démarrage rapide en un script
#   1. crée l'environnement Python et installe les dépendances
#   2. crée .env à partir de .env.example si absent
#   3. lance une démo marketing pour voir le résultat immédiatement
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "── Kimagent : installation ──"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "✔ Fichier .env créé — ouvrez-le pour choisir votre cerveau IA (KIMAGENT_BRAIN)."
fi

echo
echo "── Démo (boutique fictive) ──"
.venv/bin/python -m kimagent run marketing --demo --no-brain

echo
echo "🎉 Terminé ! Vos livrables sont dans outputs/marketing/$(date +%F)/"
echo
echo "Prochaines étapes :"
echo "  1. .venv/bin/python -m kimagent auth      # connecter votre boutique Chariow"
echo "  2. .venv/bin/python -m kimagent fetch     # importer vos vraies données"
echo "  3. .venv/bin/python -m kimagent run marketing"
