# Kimagent — commandes utiles
.PHONY: install auth fetch demo run report list test cron

install:            ## Installe les dépendances (venv)
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

auth:               ## Connecte votre compte Chariow (OAuth, une seule fois)
	.venv/bin/python -m kimagent auth

fetch:              ## Récupère les données de la boutique via MCP
	.venv/bin/python -m kimagent fetch

demo:               ## Essaye Kimagent avec une boutique de démonstration
	.venv/bin/python -m kimagent run marketing --demo --no-brain
	@echo "\n📂 Livrables dans outputs/marketing/"

run:                ## Lance un persona (ex: make run P=marketing)
	.venv/bin/python -m kimagent run $(P)

report:             ## Rapport de synthèse de la boutique
	.venv/bin/python -m kimagent report

list:               ## Liste les personas et leurs tâches
	.venv/bin/python -m kimagent list

cron:               ## Affiche la ligne crontab d'automatisation
	.venv/bin/python -m kimagent cron

test:               ## Tests rapides (mode démo)
	.venv/bin/python -m unittest discover -s tests -v
