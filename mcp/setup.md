# 🔌 Connecter vos outils IA à votre boutique Chariow

Le serveur MCP de Chariow est accessible à l'adresse unique :

```
https://mcp.chariow.com/public
```

Il prend en charge les transports **Streamable HTTP** et **SSE** (Server-Sent
Events), avec authentification **OAuth 2.0** en un clic (pas de clé API à
gérer pour la lecture).

---

## Claude Desktop / Claude.ai (Pro/Max)

1. Ouvrez **Paramètres → Connecteurs (Connectors)**.
2. Cliquez **Ajouter un connecteur personnalisé**.
3. **URL** : `https://mcp.chariow.com/public`
4. Cliquez **Ajouter** → vous êtes redirigé vers Chariow pour autoriser l'accès.
5. Nouvelle conversation : « *Montre-moi mes ventes récentes* ».

> Les connecteurs personnalisés nécessitent un abonnement Claude Pro, Max,
> Team ou Enterprise.

## ChatGPT

1. **Paramètres → Apps & Connectors → Paramètres avancés** → activez le mode
   développeur.
2. **Paramètres → Connectors → Créer** :
   - Nom : `Chariow`
   - Description : « Accès aux données de ma boutique Chariow »
   - URL : `https://mcp.chariow.com/public`
3. Terminez le flux OAuth.
4. Nouveau chat → cliquez **+** → **Plus** → choisissez **Chariow**.

## Cursor

**Paramètres → Features → MCP → Add new MCP server**, type **SSE**, URL :
`https://mcp.chariow.com/public` — ou créez un fichier `.cursor/mcp.json` :

```json
{
  "mcpServers": {
    "chariow": {
      "url": "https://mcp.chariow.com/public"
    }
  }
}
```

## Windsurf

**Paramètres → Extensions → MCP** → ajoutez un serveur distant :

```json
{
  "mcpServers": {
    "chariow": {
      "url": "https://mcp.chariow.com/public"
    }
  }
}
```

## Claude Code (CLI)

```bash
claude mcp add --transport http chariow https://mcp.chariow.com/public
```

L'authentification OAuth se fait au premier usage.

## Kimagent (ce dépôt)

```bash
.venv/bin/python -m kimagent auth
```

Ouvre votre navigateur, vous autorisez l'accès, et le jeton est stocké dans
`.chariow/token.json` (rafraîchi automatiquement).

---

## Vérification

Après connexion, demandez : **« Affiche les informations de ma boutique
Chariow »** — l'IA doit répondre avec le nom, l'URL et les réglages.

## Dépannage

| Problème | Solution |
|---|---|
| Connexion impossible | Vérifiez l'URL, redémarrez l'outil, supprimez/recréez le connecteur |
| Échec d'authentification | Connectez-vous à votre compte Chariow, boutique active, cookies du navigateur |
| Outils absents | Redémarrez l'outil ; vérifiez le JSON ; dans ChatGPT, cliquez **Actualiser** |
| Limite de débit | 60 requêtes/min sur le MCP — patientez quelques secondes |

## Révoquer l'accès

Tableau de bord Chariow (`app.chariow.com`) → **Paramètres → API Keys** →
trouvez la connexion MCP → **Révoquer**.
