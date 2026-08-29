#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Kimagent — installation du cron d'automatisation
#
# Fait tourner les agents automatiquement chaque matin (ou à l'heure choisie)
# pour générer les livrables de la journée dans outputs/<persona>/<date>/.
#
# Usage :  ./scripts/install_cron.sh [personas] [heure] [-y]
# Exemple : ./scripts/install_cron.sh marketing,ventes,finance 7 -y
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PERSONAS="${1:-marketing,ventes,finance,objectif}"
HEURE="${2:-7}"
AUTO="${3:-}"

PYTHON="$REPO_DIR/.venv/bin/python"
LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR"

LINE="0 $HEURE * * * cd $REPO_DIR && $PYTHON -m kimagent run $PERSONAS --force >> $LOG_DIR/kimagent.log 2>&1"

echo "Kimagent — automatisation quotidienne"
echo "  Personas : $PERSONAS"
echo "  Heure    : ${HEURE}h00"
echo "  Logs     : $LOG_DIR/kimagent.log"
echo
echo "Ligne à ajouter au crontab :"
echo "  $LINE"
echo

if [[ "$AUTO" != "-y" ]]; then
  read -r -p "L'ajouter à votre crontab maintenant ? [y/N] " REP
  [[ "$REP" =~ ^[yYoO]$ ]] || { echo "Annulé. Ajoutez la ligne manuellement avec : crontab -e"; exit 0; }
fi

# Ajout sans doublon
( crontab -l 2>/dev/null | grep -v "kimagent run" || true; echo "$LINE" ) | crontab -
echo "✔ Cron installé. Vérification : crontab -l"
