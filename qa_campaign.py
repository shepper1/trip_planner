import random
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from faker import Faker

import sys
from dotenv import load_dotenv

# --- CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ---
# Cette astuce permet de trouver le .env même si lancé via Cron
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(env_path)

# --- RÉCUPÉRATION DES VARIABLES ---
# On utilise os.getenv avec une valeur par défaut (optionnel) si la variable manque
TARGET_URL = os.getenv("TARGET_URL", "https://www.mytripplanner.fr/")
TEST_EMAIL = os.getenv("TEST_EMAIL")

# Configuration Email
MY_EMAIL = os.getenv("MY_EMAIL")
MY_APP_PASSWORD = os.getenv("MY_APP_PASSWORD")
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT")

# Conversion du booléen (car tout est string dans un .env)
SEND_MAIL_ON_FAIL = os.getenv("SEND_MAIL_ON_FAIL", "True").lower() == "true"

# Vérification de sécurité (pour ne pas lancer le script si le MDP manque)
if not MY_APP_PASSWORD:
    print("❌ ERREUR : La variable MY_APP_PASSWORD est vide dans le fichier .env")
    sys.exit(1)

# --- CONFIGURATION DU TEST ---
NB_TESTS = 15
SCREENSHOT_DIR = "error_capture"
MAX_RETRIES = 10

# --- CONFIGURATION ALERTES EMAIL ---
SEND_MAIL_ON_FAIL = True
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- LISTES DE SECOURS (FALLBACK) ---
SAFE_ORIGINS = [
    "Paris", "Lyon", "Marseille", "Bordeaux", "Lille", "Toulouse", 
    "Nice", "Nantes", "Strasbourg", "Montpellier", "Rennes", "Reims"
]

SAFE_DESTINATIONS = [
    "Japon", "Italie", "Espagne", "Canada", "Grèce", "Thaïlande", 
    "New York", "Londres", "Rome", "Barcelone", "Lisbonne", "Marrakech",
    "Bali", "Australie", "Mexique", "Vienne", "Amsterdam", "Berlin"
]

fake = Faker('fr_FR')

if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# --- FONCTION D'ENVOI D'EMAIL ---
def send_alert_email(report_body, failure_count):
    if not SEND_MAIL_ON_FAIL: return

    subject = f"❌ ALERTE QA : {failure_count} tests échoués sur MyTripPlanner"
    
    msg = MIMEMultipart()
    msg['From'] = MY_EMAIL
    msg['To'] = ALERT_RECIPIENT
    msg['Subject'] = subject

    # Corps du message
    body = f"""
    Bonjour,

    La campagne de test vient de se terminer avec des erreurs.
    
    🛑 Échecs : {failure_count}
    ✅ Succès : {NB_TESTS - failure_count}
    
    Voici le rapport détaillé :
    
    {report_body}
    
    Les captures d'écran sont disponibles dans le dossier '{SCREENSHOT_DIR}'.
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(MY_EMAIL, MY_APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(MY_EMAIL, ALERT_RECIPIENT, text)
        server.quit()
        print(f"\n📧 EMAIL D'ALERTE ENVOYÉ À {ALERT_RECIPIENT}")
    except Exception as e:
        print(f"\n⚠️ Erreur lors de l'envoi du mail : {e}")

class TripReporter:
    def __init__(self):
        self.results = []

    def add_result(self, status, origin, dest, surprise, duration_info, error_file=None):
        self.results.append({
            "status": status,
            "origin": origin,
            "dest": dest,
            "surprise": surprise,
            "duration_info": duration_info,
            "error": error_file,
            "time": datetime.now().strftime("%H:%M:%S")
        })

    def get_summary_string(self):
        """Génère le rapport sous forme de texte pour l'affichage ET le mail"""
        lines = []
        lines.append("="*115)
        lines.append(f"📊 RAPPORT QA - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("="*115)
        lines.append(f"{'HEURE':<10} | {'STATUS':<8} | {'ORIGINE':<22} | {'SURPRISE':<8} | {'DESTINATION':<22} | {'DURÉE'}")
        lines.append("-" * 115)
        
        success_count = 0
        for res in self.results:
            icon = "PASS" if res['status'] else "FAIL" # Icônes simplifiées pour compatibilité mail
            if res['status']: success_count += 1
            
            surprise_txt = "OUI" if res['surprise'] else "NON"
            o_txt = (res['origin'][:20] + '..') if len(res['origin']) > 20 else res['origin']
            d_txt = (res['dest'][:20] + '..') if len(res['dest']) > 20 else res['dest']
            if res['surprise']: d_txt = "---"
            
            lines.append(f"{res['time']:<10} | {icon:<8} | {o_txt:<22} | {surprise_txt:<8} | {d_txt:<22} | {res['duration_info']}")
            
            if not res['status'] and res['error']:
                lines.append(f"{' ' * 13} ↳ Capture : {res['error']}")
        
        lines.append("-" * 115)
        score = (success_count / len(self.results)) * 100
        lines.append(f"📈 TAUX DE SUCCÈS : {score}% ({success_count}/{len(self.results)})")
        lines.append("="*115)
        
        return "\n".join(lines), (len(self.results) - success_count)

    def print_summary(self):
        text_report, failure_count = self.get_summary_string()
        print("\n" + text_report + "\n")
        return text_report, failure_count

def find_valid_location(page, selector, type_generator):
    for attempt in range(MAX_RETRIES):
        text_to_test = type_generator()
        page.fill(selector, "")
        page.type(selector, text_to_test, delay=50)
        time.sleep(1.5)
        suggestions = page.locator("ul:not(.hidden) > li")
        if suggestions.count() > 0:
            suggestions.first.click()
            return text_to_test
    return None

def force_select_location(page, selector, location_name):
    page.fill(selector, "")
    page.type(selector, location_name, delay=50)
    time.sleep(1.5)
    suggestions = page.locator("ul:not(.hidden) > li")
    if suggestions.count() > 0:
        suggestions.first.click()
        return True
    return False

def run_campaign():
    reporter = TripReporter()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        
        print(f"🚀 Démarrage de la campagne QA...\n")

        for i in range(1, NB_TESTS + 1):
            page = context.new_page()
            current_origin, current_dest, is_surprise, duration_str = "Init...", "---", False, "?"
            
            try:
                page.goto(TARGET_URL)
                is_surprise = random.choice([True, False])
                mode_date = "dates" if random.random() < 0.4 else "duree"
                
                # --- ORIGINE ---
                found_origin = find_valid_location(page, "#free_origin", fake.city)
                if found_origin:
                    current_origin = found_origin
                else:
                    fallback_origin = random.choice(SAFE_ORIGINS)
                    print(f"   ⚠️ Fallback Origine: {fallback_origin}")
                    force_select_location(page, "#free_origin", fallback_origin)
                    current_origin = f"{fallback_origin} (Fallback)"
                
                # --- DESTINATION ---
                if is_surprise:
                    page.locator("text=Mode \"Surprends-moi\"").click()
                else:
                    generator = fake.country if random.choice([True, False]) else fake.city
                    found_dest = find_valid_location(page, "#free_destination", generator)
                    if found_dest:
                        current_dest = found_dest
                    else:
                        fallback_dest = random.choice(SAFE_DESTINATIONS)
                        while fallback_dest in current_origin: fallback_dest = random.choice(SAFE_DESTINATIONS)
                        print(f"   ⚠️ Fallback Destination: {fallback_dest}")
                        force_select_location(page, "#free_destination", fallback_dest)
                        current_dest = f"{fallback_dest} (Fallback)"

                # --- DATES ---
                if mode_date == "duree":
                    page.click("input[value='duree']")
                    d = random.randint(2, 21)
                    page.fill("#free_input_duree", str(d))
                    duration_str = f"{d} jours"
                else:
                    page.click("input[value='dates']")
                    start = fake.date_between(start_date='+5d', end_date='+60d')
                    end = start + timedelta(days=random.randint(3, 15))
                    page.fill("#free_input_date_debut", start.strftime("%Y-%m-%d"))
                    page.fill("#free_input_date_fin", end.strftime("%Y-%m-%d"))
                    duration_str = f"{start.strftime('%d/%m/%Y')} au {end.strftime('%d/%m/%Y')}"

                # --- ENVOI ---
                page.fill("input[name='email']", TEST_EMAIL)
                page.locator("#freeForm button[type='submit']").click()

                # --- VALIDATION ---
                popup = page.locator(".swal2-modal")
                popup.wait_for(state="visible", timeout=15000)
                title = page.locator(".swal2-title").inner_text()
                
                if "Décollage" in title or "imminent" in title:
                    reporter.add_result(True, current_origin, current_dest, is_surprise, duration_str)
                else:
                    filename = f"{SCREENSHOT_DIR}/fail_functional_{i}.png"
                    page.screenshot(path=filename)
                    reporter.add_result(False, current_origin, current_dest, is_surprise, duration_str, filename)

            except Exception as e:
                filename = f"{SCREENSHOT_DIR}/error_crash_{i}.png"
                page.screenshot(path=filename)
                reporter.add_result(False, current_origin, current_dest, is_surprise, duration_str, filename)
            
            finally:
                page.close()

        browser.close()
        
        # --- RAPPORT ET ALERTE EMAIL ---
        report_text, failure_count = reporter.print_summary()
        
        if failure_count > 0:
            print(f"🚨 DÉTECTION D'ERREURS ({failure_count}) -> Envoi de l'alerte email...")
            send_alert_email(report_text, failure_count)
        else:
            print("✨ Tous les tests sont passés.")

if __name__ == "__main__":
    run_campaign()