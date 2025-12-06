# 🤖 Trip Planner - Test Automatisé (Comportement Humain)

Ce script Python simule le parcours d'un utilisateur réel sur le site **Trip Planner**. Il utilise l'automatisation de navigateur pour générer du trafic, tester le formulaire de création de voyage et vérifier le bon fonctionnement de l'infrastructure (Frontend + Webhook n8n).

## 📋 Fonctionnalités

Le script ne se contente pas de remplir des champs, il simule un comportement "humain" pour tester la robustesse de l'UX :

* **Comportement aléatoire :** Scroll, hésitations de la souris, délais de frappe variables.
* **Données dynamiques :** Utilisation de `Faker` pour générer des villes de départ et des emails différents à chaque lancement.
* **Gestion de l'autocomplétion :** Tape les premières lettres, attend la réponse de l'API (Photon), et clique sur la suggestion.
* **Logique géographique stricte :**
    * *Origine* : Aléatoire mondial (via Faker).
    * *Destination* : Liste stricte (Pays d'Europe + Japon).
    * *Sécurité* : Vérifie que l'origine n'est pas identique à la destination.
* **Modes temporels :** Alterne aléatoirement entre le mode "Durée" (ex: 7 jours) et le mode "Dates fixes" (dates futures cohérentes).
* **Validation E2E :** Vérifie la présence de la popup de succès (SweetAlert2) pour valider le test.

## 🛠 Pré-requis

* Python 3.8 ou supérieur
* Pip (gestionnaire de paquets Python)

## 🚀 Installation

Il est recommandé d'utiliser un environnement virtuel.

1. **Cloner le projet ou télécharger le script.**

2. **Créer et activer l'environnement virtuel :**
   ```bash
   # Mac / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```
3. **Installer les dépendances :**
```Bash
pip install playwright faker
```

4. **Installer les navigateurs pour Playwright :**
```Bash
playwright install
```

## ▶️ Utilisation
Pour lancer le test, exécutez simplement la commande suivante dans votre terminal :

```Bash
python test_human_behavior.py
```
Le navigateur Chromium s'ouvrira (mode headless=False) et vous verrez le bot effectuer les actions en temps réel.

## ⚙️ Configuration
Vous pouvez modifier certaines constantes directement dans le fichier test_human_behavior.py :

**Changer l'URL cible**
Ligne 66 :

```Python
page.goto("[https://www.mytripplanner.fr/](https://www.mytripplanner.fr/)")
```

**Modifier la liste des destinations**
Ligne 10 (LISTE_DESTINATIONS). Vous pouvez ajouter ou retirer des pays selon vos besoins de test.

**Mode "Sans Tête" (Invisible)**
Pour exécuter le test en arrière-plan (par exemple sur un serveur CI/CD), modifiez la ligne 61 :

```Python
# Mettre headless=True pour ne pas voir le navigateur
browser = p.chromium.launch(headless=True) 
```

## 🐛 Dépannage courant
**Erreur**: strict mode violation: locator resolved to multiple elements Cela signifie que le script trouve plusieurs boutons ou champs identiques.

**Solution** : Le script utilise désormais des sélecteurs précis (ex: #freeForm button[type='submit']) pour éviter ce conflit entre le formulaire gratuit et le formulaire de connexion.

L'autocomplétion ne sélectionne rien si la ville générée par Faker est trop obscure ou mal orthographiée dans la base de données de l'API.

**Comportement du script** : Le script détecte l'absence de suggestion, vide le champ et tente de générer une nouvelle ville automatiquement (boucle while).

**Erreur** : ModuleNotFoundError: No module named 'playwright' Vous n'avez pas activé votre environnement virtuel ou les dépendances ne sont pas installées. Relisez la section Installation.

## 📞 Support
Ce script est conçu pour tester le formulaire "Gratuit" (#freeForm). Si vous souhaitez tester le formulaire Premium (modal), il faudra adapter les sélecteurs CSS (ex: #premiumForm).