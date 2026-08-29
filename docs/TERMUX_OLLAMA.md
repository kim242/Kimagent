# 📱 Kimagent sur Android avec Termux + Ollama

Ce guide vous permet de faire tourner **Kimagent entièrement sur Android**,
sans serveur distant, sans clé API payante — 100 % local grâce à
[Termux](https://termux.dev) et [Ollama](https://ollama.com).

---

## Pré-requis

| Élément | Version minimale |
|---|---|
| Android | 10+ (recommandé 12+) |
| RAM | 4 Go (8 Go conseillé pour les grands modèles) |
| Stockage libre | 5 Go (pour le modèle `qwen2.5:1.5b` ou `qwen2.5:3b`) |
| Termux | F-Droid 0.118+ (⚠️ **NE PAS** utiliser la version Play Store) |
| Ollama pour Android | `tinygrad/ollama-termux` ou via `pkg install ollama` |

> **Conseil** : installez Termux depuis [F-Droid](https://f-droid.org/packages/com.termux/)
> — la version Play Store est obsolète et ne reçoit plus de mises à jour.

---

## 1 — Installer Termux et les dépendances système

```bash
# Mettre à jour les paquets
pkg update && pkg upgrade -y

# Dépendances essentielles
pkg install -y python git curl wget openssl-dev libffi-dev clang make
```

---

## 2 — Installer Ollama dans Termux

```bash
# Méthode recommandée (script officiel adapté Termux)
curl -fsSL https://ollama.com/install.sh | sh

# Vérifier que l'installation s'est bien passée
ollama --version
```

> Si la méthode ci-dessus échoue sur votre appareil, essayez :
> ```bash
> pkg install ollama   # disponible sur certaines distributions Termux
> ```

---

## 3 — Télécharger un modèle léger

```bash
# Démarrer le serveur Ollama en arrière-plan
ollama serve &

# Attendre quelques secondes, puis télécharger un modèle adapté Android
ollama pull qwen2.5:1.5b     # ~1 Go — rapide, idéal pour 4 Go RAM
# ou
ollama pull qwen2.5:3b       # ~2 Go — meilleure qualité, recommandé 6 Go+ RAM
# ou
ollama pull gemma3:1b         # ~800 Mo — très léger
```

---

## 4 — Cloner et installer Kimagent

```bash
# Cloner le dépôt
git clone https://github.com/kim242/Kimagent.git
cd Kimagent

# Utiliser le script d'installation Termux (recommandé)
bash scripts/install_termux.sh
```

Ou manuellement :

```bash
# Créer l'environnement virtuel Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copier la configuration
cp .env.example .env
```

---

## 5 — Configurer Kimagent pour Ollama

Éditez le fichier `.env` (avec `nano .env`) :

```dotenv
# Activer Ollama comme cerveau IA
KIMAGENT_BRAIN=ollama

# URL du serveur Ollama local (ne pas modifier sur Termux standard)
OLLAMA_URL=http://localhost:11434

# Modèle téléchargé à l'étape 3
OLLAMA_MODEL=qwen2.5:1.5b
```

---

## 6 — Lancer Kimagent

```bash
# S'assurer que Ollama tourne toujours
ollama serve &

# Tester avec la démo (sans boutique Chariow)
python3 -m kimagent run marketing --demo

# Avec votre vraie boutique
python3 -m kimagent auth
python3 -m kimagent fetch
python3 -m kimagent run marketing
python3 -m kimagent report
```

---

## 7 — Démarrage automatique avec Termux:Boot

Pour que Ollama démarre automatiquement à l'allumage de l'appareil :

```bash
# Installer Termux:Boot depuis F-Droid
# Puis créer le script de démarrage automatique
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-ollama.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
ollama serve &
EOF
chmod +x ~/.termux/boot/start-ollama.sh
```

---

## Commandes utiles sur Termux

```bash
# Lister les modèles installés
ollama list

# Vérifier que le serveur répond
curl http://localhost:11434/api/tags

# Voir les logs Kimagent en temps réel
tail -f outputs/*/$(date +%F)/*.md

# Libérer de la RAM (arrêter Ollama)
pkill ollama
```

---

## Modèles recommandés selon votre appareil

| RAM disponible | Modèle conseillé | Taille | Qualité |
|---|---|---|---|
| 3-4 Go | `qwen2.5:1.5b` | ~1 Go | ✅ Suffisant |
| 4-6 Go | `qwen2.5:3b` | ~2 Go | ✅✅ Bonne |
| 6-8 Go | `qwen2.5:7b` | ~4,5 Go | ✅✅✅ Excellente |
| 8 Go+ | `llama3.2:3b` ou `mistral` | ~2-4 Go | ✅✅✅ Excellente |

---

## Dépannage

### `ollama: command not found`
```bash
pkg update && pkg install ollama
# ou redémarrez Termux après l'installation via curl
```

### `Connection refused` sur le port 11434
```bash
# Ollama n'est pas démarré — lancez-le
ollama serve &
# Attendez 5 secondes puis réessayez
```

### `pip install` échoue (erreur de compilation)
```bash
pkg install -y clang python-dev make libffi-dev openssl-dev
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

### Génération très lente
- Utilisez un modèle plus petit (`qwen2.5:1.5b` ou `gemma3:1b`).
- Fermez les autres applications Android.
- Branchez votre téléphone sur secteur.

### `ModuleNotFoundError: No module named 'kimagent'`
```bash
# Assurez-vous d'être dans le bon dossier
cd ~/Kimagent
python3 -m kimagent run marketing --demo
```

---

> 💡 **Astuce** : utilisez l'application **Termux:Widget** pour créer un
> raccourci sur votre écran d'accueil qui lance Kimagent en un tap.
