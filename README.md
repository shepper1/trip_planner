````markdown
# ✈️ Trip Planner - Infrastructure Backend

Documentation technique pour le déploiement et l'exploitation de l'infrastructure Backend du projet **Trip Planner**.
Ce projet est auto-hébergé (Self-Hosted) et fonctionne de pair avec un Frontend hébergé sur GitHub Pages.

---

## 📋 Sommaire
1. [Prérequis & Déploiement](#1-prérequis--déploiement)
2. [Partie Docker (Installation)](#2-partie-docker-installation)
3. [Démarrage du conteneur](#3-démarrage-du-conteneur)
4. [Exploitation & Maintenance](#4-exploitation--maintenance)

---

## 1. Prérequis & Déploiement

Pour déployer ce projet sur un serveur (ou une machine locale), l'environnement suivant est requis :

* **OS :** Linux (recommandé), Windows ou macOS.
* **Moteur de conteneurs :** Docker et Docker Compose installés.
* **Réseau :**
    * Ports **80** (HTTP) et **443** (HTTPS) ouverts et redirigés vers la machine (Port Forwarding).
    * Une adresse IP publique (fixe ou dynamique via DDNS).
* **Domaine :** Un nom de domaine (ex: `api.trip-planner.com`) configuré pour pointer vers l'IP publique.
* **Frontend :** L'URL de votre site web (ex: `https://user.github.io`) pour configurer les autorisations (CORS).

---

## 2. Partie Docker (Installation)

### A. Structure des fichiers
Créez un dossier `trip-planner` contenant l'arborescence suivante :
trip-planner/
├── 📄 .env                 # Variables d'environnement (Configuration)
├── 📄 docker-compose.yml   # Définition des services
├── 📁 caddy/
│   └── 📄 Caddyfile        # Configuration du serveur Web / Proxy
├── 📁 pb_data/             # Persistance des données PocketBase (Auto-généré)
└── 📁 n8n_data/            # Persistance des données n8n (Auto-généré)

### B. Configuration des variables (`.env`)
Créez le fichier `.env` à la racine :
```bash
# Domaine de l'API Backend (doit pointer vers votre IP)
DOMAIN_NAME=api.votre-domaine.com

# URL du Frontend (pour autoriser les requêtes CORS)
FRONTEND_URL=[https://votre-user.github.io](https://votre-user.github.io)

# Clé de chiffrement pour la base de données (Chaîne aléatoire)
PB_ENCRYPTION_KEY=ChangezMoiPourUneCleSecrete12345
```

### C. Orchestration (`docker-compose.yml`)

Créez le fichier `docker-compose.yml` à la racine :

```yaml
version: '3.8'

services:
  # --- 1. Gateway (Caddy) ---
  # Gère le HTTPS automatique et protège les services internes
  caddy:
    image: caddy:2-alpine
    container_name: caddy
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./caddy/Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    environment:
      - DOMAIN_NAME=${DOMAIN_NAME}
      - FRONTEND_URL=${FRONTEND_URL}
    networks:
      - app_network

  # --- 2. Base de données (PocketBase) ---
  # Backend NoSQL et Authentification
  pocketbase:
    image: spectado/pocketbase:latest
    container_name: pocketbase
    restart: always
    command: 
      - --encryptionEnv=PB_ENCRYPTION_KEY
    environment:
      - PB_ENCRYPTION_KEY=${PB_ENCRYPTION_KEY}
    volumes:
      - ./pb_data:/pb_data
    networks:
      - app_network

  # --- 3. Workflow Engine (n8n) ---
  # Logique métier et Agents IA
  n8n:
    image: n8n.io/n8n
    container_name: n8n
    restart: always
    environment:
      - N8N_HOST=${DOMAIN_NAME}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://${DOMAIN_NAME}/
      - GENERIC_TIMEZONE=Europe/Paris
    volumes:
      - ./n8n_data:/home/node/.n8n
    networks:
      - app_network

volumes:
  caddy_data:

networks:
  app_network:
    driver: bridge
```

### D. Configuration Proxy (`caddy/Caddyfile`)

Créez le dossier `caddy`, puis le fichier `Caddyfile` à l'intérieur :

```caddyfile
{$DOMAIN_NAME} {
    # --- Configuration CORS (Cross-Origin Resource Sharing) ---
    # Indispensable pour que le Frontend hébergé ailleurs puisse contacter l'API
    @origin header Origin {$FRONTEND_URL}
    header @origin Access-Control-Allow-Origin "{$FRONTEND_URL}"
    header Access-Control-Allow-Methods "POST, GET, OPTIONS, PUT, DELETE"
    header Access-Control-Allow-Headers "Content-Type, Authorization"

    # Réponse aux requêtes OPTIONS (Preflight)
    handle_method OPTIONS {
        respond 204
    }

    # --- Routage des Services ---
    
    # Vers PocketBase (Base de données & Auth)
    handle_path /api/* {
        reverse_proxy pocketbase:8090
    }
    handle_path /_/* {
        reverse_proxy pocketbase:8090
    }

    # Vers n8n (Webhooks)
    handle_path /webhook/* {
        reverse_proxy n8n:5678
    }

    # Optimisation
    encode gzip zstd
}
```

-----

## 3\. Démarrage du conteneur

### Lancement

Placez-vous à la racine du dossier `trip-planner` et exécutez :

```bash
docker compose up -d
```

*L'option `-d` lance les conteneurs en arrière-plan (mode détaché).*

### Vérification du statut

```bash
docker compose ps
```

Tous les services (`caddy`, `pocketbase`, `n8n`) doivent être à l'état **Up**.

### Accès aux interfaces

  * **Admin PocketBase :** `https://api.votre-domaine.com/_/`
  * **Test API :** `https://api.votre-domaine.com/webhook/test` (si configuré dans n8n)

### Arrêt

```bash
docker compose down
```

-----

## 4\. Exploitation & Maintenance

### A. Consultation des Logs

Pour surveiller l'activité ou déboguer une erreur :

```bash
# Voir les logs de tous les services en temps réel
docker compose logs -f

# Voir les logs d'un service spécifique (ex: n8n)
docker compose logs -f n8n
```

### B. Mises à jour

Pour mettre à jour les applications vers leurs dernières versions :

```bash
# 1. Télécharger les nouvelles images Docker
docker compose pull

# 2. Redémarrer l'infrastructure (recrée les conteneurs)
docker compose up -d
```

### C. Sauvegardes (Backup)

**CRITIQUE :** Les données sont stockées localement sur le serveur. Il est impératif de sauvegarder régulièrement ces deux dossiers :

1.  `pb_data/` (Comptes utilisateurs, Voyages enregistrés)
2.  `n8n_data/` (Vos workflows et identifiants IA)

**Commande type pour créer une archive :**

```bash
tar -czvf backup_tripplanner_$(date +%F).tar.gz pb_data n8n_data
```

### D. Sécurité (Git)

Si vous versionnez ce projet avec Git, assurez-vous que le fichier `.gitignore` contient bien les exclusions suivantes pour éviter de fuiter vos secrets :

```text
.env
pb_data/
n8n_data/
caddy_data/
*.tar.gz
```

```
```
````
