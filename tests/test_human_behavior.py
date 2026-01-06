import random
import time
import socket
import threading
import http.server
import socketserver
from playwright.sync_api import sync_playwright
from datetime import timedelta
from faker import Faker

# 1. On garde Faker pour générer des villes de départ et des emails aléatoires
fake = Faker(['fr_FR', 'en_US', 'es_ES', 'it_IT', 'de_DE'])

# 2. On définit STRICTEMENT la liste de destination (Europe + Japon)
LISTE_DESTINATIONS = [
    "Albanie", "Allemagne", "Andorre", "Autriche", "Belgique", "Biélorussie",
    "Bosnie-Herzégovine", "Bulgarie", "Chypre", "Croatie", "Danemark", "Espagne",
    "Estonie", "Finlande", "France", "Grèce", "Hongrie", "Irlande", "Islande",
    "Italie", "Japon", "Kosovo", "Lettonie", "Liechtenstein", "Lituanie", 
    "Luxembourg", "Macédoine du Nord", "Malte", "Moldavie", "Monaco", "Monténégro", 
    "Norvège", "Pays-Bas", "Pologne", "Portugal", "République tchèque", "Roumanie", 
    "Royaume-Uni", "Russie", "Saint-Marin", "Serbie", "Slovaquie", "Slovénie", 
    "Suède", "Suisse", "Ukraine", "Vatican"
]

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

class ReuseAddressTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def start_server(port):
    # Démarrage d'un serveur HTTP simple servant le dossier courant
    handler = http.server.SimpleHTTPRequestHandler
    # Utilisation de la classe personnalisée pour éviter les erreurs "Address already in use"
    with ReuseAddressTCPServer(("", port), handler) as httpd:
        print(f"   🚀 Serveur démarré sur le port {port}")
        httpd.serve_forever()

def type_and_select_autocomplete(page, selector, text_to_type):
    prefix_length = 4 if len(text_to_type) > 4 else len(text_to_type)
    prefix = text_to_type[:prefix_length]
    print(f"   ⌨️  Frappe simulée : '{prefix}' (pour '{text_to_type}')")
    page.type(selector, prefix, delay=random.randint(50, 150))
    time.sleep(1.5) 
    suggestion = page.locator("ul:not(.hidden) > li:first-child")
    if suggestion.count() > 0:
        suggestion_text = suggestion.inner_text().split('\n')[0]
        print(f"   👇 Clic suggestion : {suggestion_text}")
        suggestion.click()
        return True
    else:
        print(f"   ⚠️ Pas de suggestion trouvée pour '{text_to_type}'.")
        page.fill(selector, "")
        return False

def flaner_sur_le_site(page):
    print("👀 Exploration aléatoire...")
    page.mouse.wheel(0, random.randint(300, 1000))
    time.sleep(random.uniform(0.5, 2))
    page.mouse.wheel(0, -random.randint(100, 500))

def run():
    # --- AUTO-SERVER ---
    port = 5500
    if not is_port_in_use(port):
        print(f"   ℹ️  Port {port} libre. Lancement du serveur en arrière-plan...")
        # Lancement du serveur dans un thread séparé
        server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
        server_thread.start()
        time.sleep(3) # Attente démarrage (augmenté pour stabilité)
    else:
        print(f"   ℹ️  Port {port} déjà occupé. Utilisation du serveur existant.")

    with sync_playwright() as p:
        # Mode HEADLESS activé pour exécution invisible (pre-push)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        print("🌍 Connexion au site...")
        # NOTE: On suppose que le serveur est lancé à la racine du projet ou dans 'website'
        # Si lancé dans 'website' (via notre script), l'URL est /index.html
        page.goto(f"http://127.0.0.1:{port}/index.html") 
        
        flaner_sur_le_site(page)

        print("📝 Génération des données de voyage...")
        found_origin = False
        while not found_origin:
            city_origin = fake.city() 
            found_origin = type_and_select_autocomplete(page, "#free_origin", city_origin)

        time.sleep(0.5)
        pays_choisi = random.choice(LISTE_DESTINATIONS)
        while pays_choisi in city_origin: 
            pays_choisi = random.choice(LISTE_DESTINATIONS)

        type_and_select_autocomplete(page, "#free_destination", pays_choisi)
        time.sleep(0.5)

        if random.choice([True, False]):
            print("   ⏱️  Mode : Durée")
            page.click("input[value='duree']")
            duree = str(random.randint(2, 21)) 
            page.fill("#free_input_duree", duree)
        else:
            print("   📅 Mode : Dates Fixes")
            page.click("input[value='dates']")
            start_date = fake.date_between(start_date='+10d', end_date='+60d')
            end_date = start_date + timedelta(days=random.randint(3, 15))
            page.fill("#free_input_date_debut", start_date.strftime("%Y-%m-%d"))
            page.fill("#free_input_date_fin", end_date.strftime("%Y-%m-%d"))

        fake_email = fake.email()
        print(f"   📧 Email : {fake_email}")
        page.fill("input[name='email']", fake_email)
        
        print("🚀 Envoi du formulaire...")
        submit_btn = page.locator("#freeForm button[type='submit']")
        submit_btn.click()

        try:
            popup = page.locator(".swal2-modal")
            popup.wait_for(state="visible", timeout=20000)
            title = page.locator(".swal2-title").inner_text()
            if "Décollage" in title or "Succès" in title or "imminent" in title:
                print(f"✅ SUCCÈS CONFIRMÉ : {title}")
            else:
                print(f"⚠️ POPUP DÉTECTÉE (Contenu incertain) : {title}")
        except Exception as e:
            print("❌ ÉCHEC : Pas de confirmation visuelle.")
            page.screenshot(path="echec_timeout.png")

        time.sleep(3) 
        browser.close()

if __name__ == "__main__":
    run()