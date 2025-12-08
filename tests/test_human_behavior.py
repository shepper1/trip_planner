import random
import time
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

def type_and_select_autocomplete(page, selector, text_to_type):
    """
    Simule un humain qui tape le début d'une ville et clique sur le premier résultat.
    """
    # Pour les pays/villes courts (ex: Japon), on tape tout. Sinon on tape 4 lettres.
    # Cela assure que l'autocomplétion a assez de matière.
    prefix_length = 4 if len(text_to_type) > 4 else len(text_to_type)
    prefix = text_to_type[:prefix_length]
    
    print(f"   ⌨️  Frappe simulée : '{prefix}' (pour '{text_to_type}')")
    
    # Simulation frappe lente (humain)
    page.type(selector, prefix, delay=random.randint(50, 150))
    
    # Pause cruciale pour laisser l'API Photon répondre
    time.sleep(1.5) 
    
    # On vérifie si une suggestion est apparue
    suggestion = page.locator("ul:not(.hidden) > li:first-child")
    
    if suggestion.count() > 0:
        suggestion_text = suggestion.inner_text().split('\n')[0]
        print(f"   👇 Clic suggestion : {suggestion_text}")
        suggestion.click()
        return True
    else:
        print(f"   ⚠️ Pas de suggestion trouvée pour '{text_to_type}'.")
        # On vide le champ pour retenter proprement si c'était une boucle, 
        # ou pour laisser l'erreur se produire si c'est un one-shot.
        page.fill(selector, "")
        return False

def flaner_sur_le_site(page):
    print("👀 Exploration aléatoire...")
    page.mouse.wheel(0, random.randint(300, 1000))
    time.sleep(random.uniform(0.5, 2))
    page.mouse.wheel(0, -random.randint(100, 500))

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        print("🌍 Connexion au site...")
        page.goto("http://127.0.0.1:5500/website/index.html") 
        
        flaner_sur_le_site(page)

        print("📝 Génération des données de voyage...")
        
        # --- 1. ORIGINE (Géré par FAKER -> Totalement aléatoire) ---
        found_origin = False
        while not found_origin:
            # Faker invente une ville (ex: "Detroit", "Lyon", "Munich")
            city_origin = fake.city() 
            found_origin = type_and_select_autocomplete(page, "#free_origin", city_origin)

        time.sleep(0.5)

        # --- 2. DESTINATION (Géré par LISTE -> Europe + Japon uniquement) ---
        # Ici on ne boucle pas "while" car les noms de pays sont corrects et connus.
        # On pioche au hasard dans la liste définie au début.
        pays_choisi = random.choice(LISTE_DESTINATIONS)
        
        # On s'assure juste que le départ n'est pas le même que l'arrivée (ex: France -> France)
        # Si c'est le cas, on relance le dé jusqu'à ce que ce soit différent.
        while pays_choisi in city_origin: 
            pays_choisi = random.choice(LISTE_DESTINATIONS)

        type_and_select_autocomplete(page, "#free_destination", pays_choisi)

        time.sleep(0.5)

        # --- 3. DATES ou DURÉE (Aléatoire complet) ---
        if random.choice([True, False]):
            print("   ⏱️  Mode : Durée")
            page.click("input[value='duree']")
            duree = str(random.randint(2, 21)) 
            page.fill("#free_input_duree", duree)
        else:
            print("   📅 Mode : Dates Fixes")
            page.click("input[value='dates']")
            
            # 1. On définit une date de début (entre 10 et 60 jours dans le futur)
            start_date = fake.date_between(start_date='+10d', end_date='+60d')
            
            # 2. On définit la date de fin en ajoutant une durée aléatoire (ex: 3 à 15 jours)
            # C'est la méthode sûre pour garantir que end > start
            end_date = start_date + timedelta(days=random.randint(3, 15))
            
            page.fill("#free_input_date_debut", start_date.strftime("%Y-%m-%d"))
            page.fill("#free_input_date_fin", end_date.strftime("%Y-%m-%d"))

        # --- 4. EMAIL (Faker) ---
        fake_email = fake.email()
        print(f"   📧 Email : {fake_email}")
        page.fill("input[name='email']", fake_email)
        
        # --- 5. VALIDATION ---
        print("🚀 Envoi du formulaire...")
        
        # CORRECTION : On cible spécifiquement le bouton DU formulaire gratuit (#freeForm)
        submit_btn = page.locator("#freeForm button[type='submit']")
        submit_btn.click()

        # --- 6. VERIFICATION ---
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