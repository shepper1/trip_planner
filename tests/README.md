# 🤖 Trip Planner - Tests Automatisés

Ce dossier contient les scripts Python pour tester l'expérience utilisateur (UX) et la robustesse du site **Trip Planner**.

## 📂 Scripts Disponibles

### 1. `test_human_behavior.py` (Test Unitaire)
Simule **un seul utilisateur** parcourant le site.
*   **Objectif** : Vérifier que le parcours "happy path" fonctionnel.
*   **Fonctionnalités** :
    *   Lance automatiquement un serveur local (port 5500) si nécessaire.
    *   Remplit le formulaire avec des données réalistes (Faker).
    *   Simule un comportement humain (délais, hésitations).
    *   Vérifie la popup de succès.

### 2. `qa_campaign.py` (Campagne QA de Masse)
Lance une batterie de **15 tests (ou plus)** à la suite.
*   **Objectif** : Tests de charge / Robustesse / Détection de flocons (flaky tests).
*   **Fonctionnalités** :
    *   Exécution rapide en mode "headless" (invisible).
    *   Rapport de fin de campagne dans la console.
    *   **Alerting Email** : Envoie un email récapitulatif en cas d'échec.
    *   Captures d'écran automatiques des erreurs dans le dossier `error_capture/`.

---

## 🛠 Pré-requis

*   Python 3.8 ou supérieur
*   Pip (gestionnaire de paquets)

## 🚀 Installation

Il est recommandé d'utiliser l'environnement virtuel local.

1.  **Créer l'environnement virtuel (si absent) :**
    ```bash
    python3 -m venv venv
    ```

2.  **Activer l'environnement :**
    ```bash
    # Mac / Linux
    source venv/bin/activate

    # Windows
    venv\Scripts\activate
    ```

3.  **Installer les dépendances :**
    ```bash
    pip install playwright faker python-dotenv
    ```

4.  **Installer les navigateurs Playwright :**
    ```bash
    playwright install chromium
    ```

## ⚙️ Configuration (.env)

Pour le script `qa_campaign.py`, vous devez créer un fichier `.env` dans le dossier `tests/` (ou à la racine) avec les informations suivantes :

```ini
# --- URL CIBLE ---
TARGET_URL="http://127.0.0.1:5500/index.html"

# --- EMAIL DE TEST (celui saisi dans le formulaire) ---
TEST_EMAIL="testeur@example.com"

# --- CONFIGURATION ALERTING (Pour envoi de rapport) ---
MY_EMAIL="votre_email_gmail@gmail.com"
MY_APP_PASSWORD="votre_mot_de_passe_application"
ALERT_RECIPIENT="destinataire_alerte@example.com"
SEND_MAIL_ON_FAIL=True
```

> **Note :** `MY_APP_PASSWORD` doit être un "Mot de passe d'application" généré depuis votre compte Google (Sécurité > Validation en deux étapes > Mots de passe des applications).

---

## ▶️ Utilisation

### Lancer un Test Unitaire (avec visionnage)
Idéal pour le développement ou le débogage visuel.

```bash
python3 test_human_behavior.py
```
*Le navigateur s'ouvrira et vous verrez le bot agir.*

### Lancer une Campagne QA (rapide)
Idéal avant une mise en production (utilisé par le `pre-push` hook).

```bash
python3 qa_campaign.py
```
*L'exécution est silencieuse (headless). Un rapport s'affiche à la fin.*

---

## 🐛 Dépannage

**Erreur : `ModuleNotFoundError: No module named 'dotenv'`**
> Vous n'avez pas installé `python-dotenv`. Exécutez `pip install python-dotenv`.

**Erreur : `Connection refused`**
> Le serveur local n'est pas démarré.
> *   `test_human_behavior.py` le lance automatiquement.
> *   Pour `qa_campaign.py`, assurez-vous que votre site est accessible à l'URL définie dans `TARGET_URL`.

**Erreur d'envoi d'email**
> Vérifiez que `MY_APP_PASSWORD` est correct et ne contient pas d'espaces. Assurez-vous que le compte Gmail autorise l'envoi SMTP.