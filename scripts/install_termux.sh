#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Kimagent — Script d'installation pour Termux (Android) + Ollama
#
# Usage : bash scripts/install_termux.sh
#
# Ce script :
#   1. Vérifie que l'environnement Termux est compatible
#   2. Installe les dépendances système manquantes
#   3. Vérifie / installe Ollama
#   4. Crée l'environnement Python et installe les dépendances Kimagent
#   5. Configure .env pour Ollama si aucun fichier .env n'existe
#   6. Lance une démo pour vérifier que tout fonctionne
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Couleurs ──────────────────────────────────────────────────────────────
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m"

info()    { echo -e "${BLUE}ℹ${NC}  $*"; }
success() { echo -e "${GREEN}✔${NC}  $*"; }
warn()    { echo -e "${YELLOW}⚠${NC}  $*"; }
error()   { echo -e "${RED}✖${NC}  $*"; exit 1; }

# ── Se placer à la racine du dépôt ────────────────────────────────────────
cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPO_ROOT="$(pwd)"
info "Dépôt Kimagent : $REPO_ROOT"

# ── 1. Vérifier l'environnement Termux ────────────────────────────────────
echo
echo -e "${BLUE}══ Étape 1/6 — Vérification de l'environnement ══${NC}"

if [[ -z "${TERMUX_VERSION:-}" && ! -d /data/data/com.termux ]]; then
    warn "Ce script est optimisé pour Termux (Android)."
    warn "Sur Linux classique, utilisez plutôt : bash scripts/quickstart.sh"
    read -r -p "Continuer quand même ? (o/N) " confirm
    [[ "$confirm" =~ ^[oOyY]$ ]] || exit 0
fi

if ! command -v python3 &>/dev/null; then
    error "Python 3 non trouvé. Lancez d'abord : pkg install python"
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
success "Python $PYTHON_VERSION détecté"

# ── 2. Installer les dépendances système manquantes ───────────────────────
echo
echo -e "${BLUE}══ Étape 2/6 — Dépendances système ══${NC}"

PKG_NEEDED=()
for pkg in git curl openssl-dev libffi-dev; do
    if ! pkg list-installed 2>/dev/null | grep -q "^${pkg}/"; then
        PKG_NEEDED+=("$pkg")
    fi
done

if [[ ${#PKG_NEEDED[@]} -gt 0 ]]; then
    info "Installation des paquets manquants : ${PKG_NEEDED[*]}"
    pkg install -y "${PKG_NEEDED[@]}"
else
    success "Toutes les dépendances système sont présentes"
fi

# ── 3. Vérifier / installer Ollama ────────────────────────────────────────
echo
echo -e "${BLUE}══ Étape 3/6 — Ollama ══${NC}"

OLLAMA_OK=false
if command -v ollama &>/dev/null; then
    OLLAMA_VER=$(ollama --version 2>&1 || echo "?")
    success "Ollama détecté : $OLLAMA_VER"
    OLLAMA_OK=true
fi

if [[ "$OLLAMA_OK" == "false" ]]; then
    info "Ollama non trouvé — tentative d'installation via pkg..."
    if pkg install -y ollama 2>/dev/null; then
        success "Ollama installé via pkg"
        OLLAMA_OK=true
    else
        warn "Installation via pkg non disponible — tentative via curl..."
        if curl -fsSL https://ollama.com/install.sh | sh; then
            success "Ollama installé via le script officiel"
            OLLAMA_OK=true
        else
            warn "Impossible d'installer Ollama automatiquement."
            warn "Installez-le manuellement, puis relancez ce script."
            warn "Voir : docs/TERMUX_OLLAMA.md → Étape 2"
        fi
    fi
fi

# Démarrer Ollama si pas déjà en cours
if [[ "$OLLAMA_OK" == "true" ]]; then
    if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
        info "Démarrage du serveur Ollama en arrière-plan..."
        ollama serve &>/tmp/ollama.log &
        sleep 4
        if curl -sf http://localhost:11434/api/tags &>/dev/null; then
            success "Serveur Ollama démarré (port 11434)"
        else
            warn "Le serveur Ollama n'a pas répondu — poursuivons sans lui."
        fi
    else
        success "Serveur Ollama déjà en cours d'exécution"
    fi

    # Choisir / télécharger un modèle par défaut si aucun n'est présent
    INSTALLED_MODELS=$(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' || true)
    if [[ -z "$INSTALLED_MODELS" ]]; then
        info "Aucun modèle Ollama installé — téléchargement de qwen2.5:1.5b (~1 Go)..."
        info "(Cela peut prendre plusieurs minutes selon votre connexion)"
        ollama pull qwen2.5:1.5b
        DEFAULT_MODEL="qwen2.5:1.5b"
        success "Modèle $DEFAULT_MODEL prêt"
    else
        DEFAULT_MODEL=$(echo "$INSTALLED_MODELS" | head -1)
        success "Modèle disponible : $DEFAULT_MODEL"
    fi
else
    DEFAULT_MODEL="qwen2.5:1.5b"
fi

# ── 4. Environnement Python + dépendances Kimagent ───────────────────────
echo
echo -e "${BLUE}══ Étape 4/6 — Environnement Python ══${NC}"

if [[ ! -d .venv ]]; then
    info "Création de l'environnement virtuel..."
    python3 -m venv .venv
fi

info "Installation des dépendances Python..."
# Sur Termux, wheel/setuptools doivent être récents
.venv/bin/pip install -q --upgrade pip wheel setuptools
.venv/bin/pip install -q -r requirements.txt
success "Dépendances Kimagent installées"

# ── 5. Configurer .env ────────────────────────────────────────────────────
echo
echo -e "${BLUE}══ Étape 5/6 — Configuration .env ══${NC}"

if [[ ! -f .env ]]; then
    cp .env.example .env
    # Activer Ollama par défaut et définir le bon modèle
    sed -i "s/^KIMAGENT_BRAIN=none/KIMAGENT_BRAIN=ollama/" .env
    sed -i "s|^# OLLAMA_URL=.*|OLLAMA_URL=http://localhost:11434|" .env
    sed -i "s|^# OLLAMA_MODEL=.*|OLLAMA_MODEL=${DEFAULT_MODEL}|" .env
    success ".env créé et configuré pour Ollama (modèle : $DEFAULT_MODEL)"
else
    warn ".env existe déjà — aucune modification (vérifiez KIMAGENT_BRAIN=ollama)"
fi

# ── 6. Démo de vérification ───────────────────────────────────────────────
echo
echo -e "${BLUE}══ Étape 6/6 — Vérification avec la démo ══${NC}"

if [[ "$OLLAMA_OK" == "true" ]]; then
    info "Lancement d'une démo marketing avec Ollama..."
    .venv/bin/python -m kimagent run marketing --demo || {
        warn "La démo a rencontré un problème — vérifiez les messages ci-dessus."
    }
else
    info "Lancement d'une démo sans cerveau IA (mode 'none')..."
    .venv/bin/python -m kimagent run marketing --demo --no-brain
fi

# ── Résumé ────────────────────────────────────────────────────────────────
echo
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🎉 Kimagent est prêt sur Termux !${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo
echo "Prochaines étapes :"
echo
echo "  1. Connecter votre boutique Chariow :"
echo "     .venv/bin/python -m kimagent auth"
echo
echo "  2. Importer vos données :"
echo "     .venv/bin/python -m kimagent fetch"
echo
echo "  3. Lancer un agent :"
echo "     .venv/bin/python -m kimagent run marketing"
echo "     .venv/bin/python -m kimagent run ventes"
echo "     .venv/bin/python -m kimagent run objectif"
echo
echo "  4. Générer un rapport :"
echo "     .venv/bin/python -m kimagent report"
echo
echo "  📖 Guide complet : docs/TERMUX_OLLAMA.md"
echo
if [[ "$OLLAMA_OK" == "true" ]]; then
    echo "  🧠 Cerveau IA actif : Ollama ($DEFAULT_MODEL)"
else
    echo "  ⚠  Ollama non disponible — installez-le et relancez le script."
fi
echo
