# ✈️ Trip Planner - Frontend (Interface Client)

Ce dépôt contient l'interface utilisateur (UI) du projet Trip Planner, hébergée sur GitHub Pages. C'est le code que le client télécharge dans son navigateur.

---

## 1. 🌐 Architecture & Fichiers

Ce projet utilise une architecture **Single Page Application (SPA)** simple en HTML, JavaScript et Tailwind CSS (via CDN).

| Fichier | Rôle |
| :--- | :--- |
| `index.html` | Contient toute la structure HTML, le style (Tailwind) et la logique JavaScript (y compris le routage et la connexion à l'API). |
| `README.md` | Ce document. |

---

## 2. ⚙️ Configuration de l'API (Lien vers le Backend)

La seule configuration requise est de pointer le Frontend vers votre **serveur Docker personnel**.

**Où configurer ?**
Vous devez éditer le fichier `index.html` et modifier l'URL de l'API dans la section `<script>` (en haut du code JS).

**Action :**
Dans le code JavaScript, mettez à jour la constante `PB_URL` (votre PocketBase) et les adresses des Webhooks :

```javascript
// --- CONFIGURATION POCKETBASE (Authentification) ---
const PB_URL = "[https://api.votre-domaine.com](https://api.votre-domaine.com)"; 

// --- CONFIGURATION DES WEBHOOKS (Logique n8n) ---
const WEBHOOK_FREE = "[https://api.votre-domaine.com/webhook/free](https://api.votre-domaine.com/webhook/free)"; 
const WEBHOOK_PRO = "[https://api.votre-domaine.com/webhook/pro](https://api.votre-domaine.com/webhook/pro)";