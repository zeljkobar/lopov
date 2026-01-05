#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io
import os

# Force unbuffered output for real-time console display
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

import time
import argparse
import re
import os
import subprocess
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
try:
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    USE_WEBDRIVER_MANAGER = True
except:
    USE_WEBDRIVER_MANAGER = False

BASE_URL = "https://www.companywall.me/pretraga"
NORDVPN_PATH = r"C:\Program Files\NordVPN\NordVPN.exe"
VPN_STATE_FILE = "vpn_state.json"

VPN_SERVERS = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia",
    "Adelaide", "Brisbane", "Melbourne", "Perth", "Sydney", "Austria", "Azerbaijan",
    "Bahamas", "Bahrain", "Bangladesh", "Belgium", "Belize", "Bermuda", "Bhutan", "Bolivia",
    "Bosnia and Herzegovina", "Brazil", "Brunei Darussalam", "Bulgaria", "Cambodia",
    "Montreal", "Toronto", "Vancouver", "Cayman Islands", "Chile", "Colombia", "Comoros",
    "Costa Rica", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Dominican Republic",
    "Ecuador", "Egypt", "El Salvador", "Estonia", "Ethiopia", "Finland", "Paris", "Georgia",
    "Berlin", "Frankfurt", "Ghana", "Greece", "Greenland", "Guam", "Guatemala", "Honduras",
    "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Iraq", "Ireland", "Isle of Man",
    "Israel", "Italy", "Jamaica", "Japan", "Jersey", "Jordan", "Kazakhstan", "Kenya", "Kuwait",
    "Lao People's Democratic Republic", "Latvia", "Lebanon", "Libyan Arab Jamahiriya",
    "Liechtenstein", "Lithuania", "Luxembourg", "Malaysia", "Malta", "Mauritania", "Mexico",
    "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Nepal",
    "Amsterdam", "Auckland", "Nigeria", "North Macedonia", "Norway", "Pakistan", "Panama",
    "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Puerto Rico",
    "Qatar", "Romania", "Rwanda", "Senegal", "Serbia", "Singapore", "Slovakia", "Slovenia",
    "Somalia", "South Africa", "South Korea", "Spain", "Sri Lanka", "Sweden", "Switzerland",
    "Taiwan", "Thailand", "Trinidad and Tobago", "Tunisia", "Turkey", "Ukraine",
    "United Arab Emirates", "London", "Manchester", "Ashburn", "Atlanta", "Boston", "Buffalo",
    "Charlotte", "Chicago", "Dallas", "Denver", "Kansas City", "Las Vegas", "Los Angeles",
    "Miami", "New York", "Phoenix", "Salt Lake City", "San Francisco", "Seattle", "St. Louis",
    "Tampa", "Uruguay", "Uzbekistan", "Venezuela", "Vietnam"
]

def connect_to_vpn_server(server_name, max_retries=3):
    """Konektuj se na NordVPN server sa retry logikom"""
    for attempt in range(max_retries):
        try:
            print(f"Konektujem se na NordVPN server: {server_name} (pokušaj {attempt + 1}/{max_retries})")
            
            # Prvo se diskonektuj (sa dužim timeout-om)
            try:
                disconnect_cmd = [NORDVPN_PATH, "-d"]
                subprocess.run(disconnect_cmd, capture_output=True, text=True, timeout=45, shell=True)
                time.sleep(2)
            except subprocess.TimeoutExpired:
                print(f"  Timeout pri diskonektovanju, nastavljam...")
            except Exception:
                pass
            
            # Konektuj se na novi server (povećan timeout) - koristi -c za connect
            connect_cmd = [NORDVPN_PATH, "-c", "-g", server_name]
            result = subprocess.run(connect_cmd, capture_output=True, text=True, timeout=90, shell=True)
            
            if result.returncode == 0 or "connected" in result.stdout.lower():
                print(f"  ✓ Uspešno konektovan na {server_name}")
                time.sleep(5)  # Čekaj da se konekcija stabilizuje
                return True
            else:
                print(f"  ✗ Greška pri konekciji: {result.stderr}")
                if attempt < max_retries - 1:
                    print(f"  Pokušavam ponovo...")
                    time.sleep(5)
                    
        except subprocess.TimeoutExpired:
            print(f"  ⏱ Timeout pri konekciji na {server_name}")
            if attempt < max_retries - 1:
                print(f"  Pokušavam ponovo...")
                time.sleep(5)
        except Exception as e:
            print(f"  ⚠ Greška pri VPN konekciji: {e}")
            if attempt < max_retries - 1:
                print(f"  Pokušavam ponovo...")
                time.sleep(5)
    
    print(f"  ✗ Svi pokušaji neuspešni za {server_name}")
    return False

def disconnect_vpn():
    """Diskonektuj se od VPN-a"""
    try:
        print("Diskonektujem se od VPN-a...")
        disconnect_cmd = [NORDVPN_PATH, "-d"]
        result = subprocess.run(disconnect_cmd, capture_output=True, text=True, timeout=45, shell=True)
        if result.returncode == 0 or "disconnected" in result.stdout.lower():
            print("  ✓ VPN diskonektovan")
        time.sleep(2)
    except subprocess.TimeoutExpired:
        print("  ⏱ Timeout pri diskonektovanju (možda je već diskonektovan)")
        time.sleep(1)
    except Exception as e:
        print(f"  ⚠ Greška pri VPN diskonektovanju: {e}")

def save_vpn_state(current_server_index, used_servers):
    """Čuva trenutno stanje VPN servera u JSON fajl"""
    try:
        state = {
            "current_server_index": current_server_index,
            "used_servers": used_servers,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_servers": len(VPN_SERVERS)
        }
        
        with open(VPN_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        print(f"  Stanje VPN servera sačuvano: server #{current_server_index}, korišćeno {len(used_servers)}/{len(VPN_SERVERS)}")
        
    except Exception as e:
        print(f"  Greška pri čuvanju VPN stanja: {e}")

def load_vpn_state():
    """Učitava poslednje stanje VPN servera iz JSON fajla"""
    try:
        if not os.path.exists(VPN_STATE_FILE):
            print("  Nema sačuvanog VPN stanja, počinjem od početka")
            return 0, []
        
        with open(VPN_STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        current_server_index = state.get("current_server_index", 0)
        used_servers = state.get("used_servers", [])
        last_updated = state.get("last_updated", "nepoznato")
        
        # Ako su svi serveri korišćeni, počni ponovo
        if len(used_servers) >= len(VPN_SERVERS):
            print("  Svi VPN serveri su korišćeni, početak novog ciklusa")
            return 0, []
        
        print(f"  Učitano VPN stanje: server #{current_server_index}, korišćeno {len(used_servers)}/{len(VPN_SERVERS)}")
        print(f"  Poslednja izmena: {last_updated}")
        
        return current_server_index, used_servers
        
    except Exception as e:
        print(f"  Greška pri učitavanju VPN stanja: {e}")
        return 0, []

def get_next_unused_server(current_index, used_servers):
    """Pronađi sledeći nekorišćeni VPN server"""
    for i in range(len(VPN_SERVERS)):
        next_index = (current_index + i) % len(VPN_SERVERS)
        server_name = VPN_SERVERS[next_index]
        
        if server_name not in used_servers:
            return next_index, server_name
    
    # Ako su svi serveri korišćeni, počni ponovo
    print("  Svi serveri su korišćeni u ovom ciklusu, počinjem ponovo")
    return 0, VPN_SERVERS[0]

def force_vpn_change(current_server_index, used_servers, reason="blokada"):
    """Prinudno menja VPN server zbog blokade ili drugih razloga"""
    print(f"\n{'🔄'*20}")
    print(f"PRINUDNA PROMENA VPN SERVERA! Razlog: {reason}")
    print(f"{'🔄'*20}")
    
    # Pronađi sledeći nekorišćeni server
    new_server_index, new_server = get_next_unused_server(current_server_index + 1, used_servers)
    print(f"Menjam sa servera #{current_server_index} na #{new_server_index}: {new_server}")
    
    # Konektuj se na novi server
    if connect_to_vpn_server(new_server):
        # Dodaj u korišćene servere
        if new_server not in used_servers:
            used_servers.append(new_server)
            save_vpn_state(new_server_index, used_servers)
        
        print(f"✅ Uspešno promenjen VPN na: {new_server}")
        time.sleep(3)  # Kratka pauza
        return new_server_index, new_server
    else:
        print(f"❌ Greška pri promeni VPN servera na: {new_server}")
        return current_server_index, VPN_SERVERS[current_server_index]

def create_chrome_driver(headless=True):
    """Kreira Chrome WebDriver"""
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        if USE_WEBDRIVER_MANAGER:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        return driver
    except Exception as e:
        print(f"✗ Greška pri pokretanju Chrome: {e}")
        return None

def check_if_blocked(driver):
    """Proveri da li je sajt blokirao pristup"""
    try:
        current_url = driver.current_url
        if "/registracija" in current_url or "registracija" in current_url:
            print("  🚫 SAJT JE BLOKIRAO PRISTUP!")
            return True
        return False
    except:
        return False

def get_profile_link(driver, pib):
    """Pronađi profil link"""
    try:
        driver.get(f"{BASE_URL}?n={pib}")
        time.sleep(3)
        
        profile_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/firma/']")
        if not profile_links:
            return None
        
        return profile_links[0].get_attribute("href")
    except:
        return None

def extract_data_from_profile(driver, profile_url):
    """Ekstraktuj podatke sa profil stranice"""
    try:
        driver.get(profile_url)
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page_text = soup.get_text()
        
        data = {'naziv': '', 'email': '', 'telefon': '', 'kd': '', 'prihod': '', 'broj_zaposlenih': '', 'grad': ''}
        
        # ===== IZVUCI PODATKE IZ FAQ SEKCIJE (div.qanda-body) =====
        qanda_bodies = soup.find_all('div', class_='qanda-body')
        
        for qanda in qanda_bodies:
            text = qanda.get_text()
            
            # Prihod
            if 'prihod' in text.lower() and not data['prihod']:
                # Traži broj u <span class="text-bold"> ili bilo gde u tekstu
                bold_span = qanda.find('span', class_='text-bold')
                if bold_span:
                    prihod_match = re.search(r'([\d.,]+)', bold_span.get_text())
                    if prihod_match:
                        data['prihod'] = prihod_match.group(1).replace('.', '').replace(',', '.')
                        print(f"    Prihod (FAQ): {data['prihod']}")
            
            # Broj zaposlenih
            if 'zaposlenih' in text.lower() and not data['broj_zaposlenih']:
                bold_span = qanda.find('span', class_='text-bold')
                if bold_span:
                    broj_match = re.search(r'(\d+)', bold_span.get_text())
                    if broj_match and len(broj_match.group(1)) < 6:
                        data['broj_zaposlenih'] = broj_match.group(1)
                        print(f"    Broj zaposlenih (FAQ): {data['broj_zaposlenih']}")
            
            # Grad/Adresa
            if 'adresa' in text.lower() and not data['grad']:
                cities = ['BAR', 'PODGORICA', 'CETINJE', 'BUDVA', 'ULCINJ', 'HERCEG NOVI', 'KOTOR', 'TIVAT', 'NIKŠIĆ', 'PLJEVLJA']
                for city in cities:
                    if city in text.upper():
                        data['grad'] = city
                        print(f"    Grad (FAQ): {city}")
                        break
        
        # ===== NAZIV =====
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            text = tag.get_text().strip()
            if text and len(text) > 3 and 'rezultati' not in text.lower():
                data['naziv'] = text
                break
        
        # ===== EMAIL =====
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)
        if emails:
            filtered = [e for e in emails if not any(skip in e.lower() for skip in ['companywall', 'example', 'test', 'noreply'])]
            if filtered:
                data['email'] = filtered[0]
        
        # ===== TELEFON =====
        phone_patterns = [
            r'\+382[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{3}',
            r'0\d{2}[\s\-]?\d{3}[\s\-]?\d{3}',
            r'\d{3}[\s\-]?\d{3}[\s\-]?\d{3}',
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, page_text))
        
        if phones:
            valid = []
            for phone in phones:
                clean = re.sub(r'[\s\-]', '', phone)
                if re.match(r'^\+?\d{8,15}$', clean):
                    valid.append(phone.strip())
            if valid:
                data['telefon'] = valid[0]
        
        # ===== KD =====
        kd_patterns = [r'KD[:\s]*(\d{4})', r'(\d{4})']
        for pattern in kd_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if len(str(match)) == 4:
                        data['kd'] = str(match)
                        break
                if data['kd']:
                    break
        
        return data
    except:
        return None

def save_to_csv(pib, data, output_file):
    """Čuva rezultat u CSV"""
    try:
        import csv
        file_exists = os.path.isfile(output_file)
        
        with open(output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['pib', 'naziv', 'email', 'telefon', 'kd', 'prihod', 'broj_zaposlenih', 'grad'])
            writer.writerow([pib, data.get('naziv', ''), data.get('email', ''), 
                           data.get('telefon', ''), data.get('kd', ''), 
                           data.get('prihod', ''), data.get('broj_zaposlenih', ''), 
                           data.get('grad', '')])
    except Exception as e:
        print(f"  ✗ Greška pri čuvanju: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='input_pibs.txt')
    parser.add_argument('--output', default='rezultati.csv')
    parser.add_argument('--pibs-per-server', type=int, default=12)
    args = parser.parse_args()
    
    # Učitaj PIBove
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            pibs = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"✗ Greška pri učitavanju PIBova: {e}")
        return
    
    print(f"Učitano {len(pibs)} PIBova")
    print(f"VPN rotacija svakih {args.pibs_per_server} PIBova\n")
    
    # Učitaj VPN stanje
    current_server_index, used_servers = load_vpn_state()
    
    # Konektuj na početni VPN
    if current_server_index >= len(VPN_SERVERS):
        current_server_index = 0
    
    current_server = VPN_SERVERS[current_server_index]
    print(f"Konektujem na početni VPN server: {current_server}")
    
    if not connect_to_vpn_server(current_server):
        print("✗ Nisam mogao da se konektujem ni na jedan VPN server!")
        return
    
    used_servers.append(current_server)
    save_vpn_state(current_server_index, used_servers)
    
    # Kreiraj driver
    driver = create_chrome_driver(headless=True)
    if not driver:
        return
    
    try:
        success_count = 0
        
        for i, pib in enumerate(pibs, 1):
            print(f"\n[{i}/{len(pibs)}] PIB: {pib}")
            print(f"  VPN: {VPN_SERVERS[current_server_index]}")
            
            # Rotacija VPN-a svakih N PIBova
            if i > 1 and (i - 1) % args.pibs_per_server == 0:
                print(f"\n{'='*50}")
                print(f"  VPN ROTACIJA nakon {args.pibs_per_server} PIBova")
                print(f"{'='*50}")
                
                current_server_index, current_server = get_next_unused_server(current_server_index + 1, used_servers)
                
                if connect_to_vpn_server(current_server):
                    used_servers.append(current_server)
                    save_vpn_state(current_server_index, used_servers)
                    time.sleep(3)
            
            # Pronađi profil
            profile_url = get_profile_link(driver, pib)
            if not profile_url:
                print(f"  ✗ Nisam pronašao profil")
                continue
            
            print(f"  ✓ Link: {profile_url}")
            
            # Ekstraktuj podatke
            data = extract_data_from_profile(driver, profile_url)
            if not data:
                print(f"  ✗ Greška pri ekstraktovanju")
                continue
            
            # Prikaži podatke
            if data.get('naziv'):
                print(f"  → Naziv: {data['naziv']}")
            if data.get('email'):
                print(f"  → Email: {data['email']}")
            if data.get('telefon'):
                print(f"  → Telefon: {data['telefon']}")
            if data.get('kd'):
                print(f"  → KD: {data['kd']}")
            
            # Sačuvaj
            save_to_csv(pib, data, args.output)
            success_count += 1
            print(f"  ✓ Sačuvano ({success_count}/{i})")
            
            time.sleep(2)
    
    finally:
        driver.quit()
        disconnect_vpn()
        print(f"\n✓ Gotovo! Obrađeno {success_count}/{len(pibs)} PIBova")

if __name__ == "__main__":
    main()
