#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import time
import random
import argparse
import sys
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WEBDRIVER_MANAGER = True
except:
    USE_WEBDRIVER_MANAGER = False

try:
    import chromedriver_binary
    USE_CHROMEDRIVER_BINARY = True
except:
    USE_CHROMEDRIVER_BINARY = False

# Constants
BASE_URL = "https://www.companywall.me/pretraga"

def polite_sleep(min_seconds=2, max_seconds=4):
    """Educano cekanje izmedju zahteva"""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)

def create_chrome_driver(headless=True):
    """Kreira Chrome WebDriver sa optimizovanim podesavanjima"""
    try:
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
            print("Chrome driver - headless mode")
        else:
            print("Chrome driver - visible mode")
            
        # Basic settings
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Disable logging
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Pokusaj razlicite nacine za Chrome driver
        driver = None
        
        # Metod 1: chromedriver-binary (lokalni)
        if USE_CHROMEDRIVER_BINARY and not driver:
            try:
                print("Pokusavam chromedriver-binary...")
                driver = webdriver.Chrome(options=chrome_options)
                print("Uspesno - chromedriver-binary")
            except Exception as e:
                print(f"chromedriver-binary failed: {e}")
                driver = None
        
        # Metod 2: webdriver-manager (download)
        if USE_WEBDRIVER_MANAGER and not driver:
            try:
                print("Pokusavam webdriver-manager...")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("Uspesno - webdriver-manager")
            except Exception as e:
                print(f"webdriver-manager failed: {e}")
                driver = None
        
        # Metod 3: sistemski PATH
        if not driver:
            try:
                print("Pokusavam sistemski chromedriver...")
                driver = webdriver.Chrome(options=chrome_options)
                print("Uspesno - sistemski chromedriver")
            except Exception as e:
                print(f"sistemski chromedriver failed: {e}")
                driver = None
        
        if driver:
            print("Chrome driver uspesno pokrenut!")
            return driver
        else:
            print("Svi pokusaji neuspesni!")
            return None
        
    except Exception as e:
        print(f"Greska pri pokretanju Chrome driver-a: {e}")
        return None

def search_companywall_by_pib(driver, pib):
    """Pretrazi CompanyWall po PIB-u"""
    try:
        print(f"  Idem na {BASE_URL}")
        driver.get(BASE_URL)
        polite_sleep()
        
        # Pronadji search input
        search_inputs = driver.find_elements(By.CSS_SELECTOR, "input[placeholder*='PIB'], input[name='n']")
        
        search_input = None
        for inp in search_inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            name = inp.get_attribute("name") or ""
            if "PIB" in placeholder or name == "n":
                search_input = inp
                print(f"  Nasao search input: {inp.tag_name}")
                break
        
        if not search_input:
            print("  Nisam nasao search polje!")
            return None
        
        # Unesi PIB i posalji
        search_input.clear()
        search_input.send_keys(pib)
        search_input.send_keys(Keys.RETURN)
        print(f"  Poslao Enter za PIB: {pib}")
        
        polite_sleep(3, 5)
        
        current_url = driver.current_url
        print(f"  URL nakon search-a: {current_url}")
        
        # Proveri da li ima rezultata
        if "pretraga?n=" not in current_url:
            print("  Search nije prosao")
            return None
            
        # Pokusaj da nadjes link ka profilu firme
        try:
            profile_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/firma/']")
            
            if not profile_links:
                print("  Nema linkova ka profilu firme")
                return None
                
            profile_url = profile_links[0].get_attribute("href")
            print(f"  Nasao profil firme: {profile_url}")
            return profile_url
            
        except Exception as e:
            print(f"  Greska pri trazenju profila: {e}")
            return None
            
    except Exception as e:
        print(f"  Greska pri search-u: {e}")
        return None

def parse_company_profile(driver, profile_url, pib):
    """Parsira profil firme i izvlaci podatke"""
    try:
        print(f"  Otvoram profil: {profile_url}")
        driver.get(profile_url)
        polite_sleep(2, 4)
        
        # Osnovni podaci
        company_data = {
            'naziv': '',
            'pib': pib.zfill(8),  # Formatuj PIB na 8 cifara
            'grad': '',
            'email': '',
            'telefon': '',
            'web': '',
            'kd': ''
        }
        
        # Izvuci HTML sadrzaj za parsiranje
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Pokusaj da nadjes naziv firme
        title_selectors = [
            'h1',
            '.company-name',
            '.firm-name', 
            '[class*="title"]',
            '[class*="name"]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                company_data['naziv'] = title_elem.get_text().strip()
                break
        
        # Trazi email adrese i telefone u HTML-u
        page_text = soup.get_text()
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)
        if emails:
            # Filtriraj nezeljene email-ove
            filtered_emails = [e for e in emails if not any(skip in e.lower() for skip in ['companywall', 'example', 'test', 'noreply'])]
            if filtered_emails:
                company_data['email'] = filtered_emails[0]  # Uzmi prvi validni
        
        # Telefon patterns za crnogorske i medjunarodne brojeve
        phone_patterns = [
            r'\+382[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{3}',  # +382 XX XXX XXX
            r'382[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{3}',   # 382 XX XXX XXX
            r'0\d{2}[\s\-]?\d{3}[\s\-]?\d{3}',            # 0XX XXX XXX
            r'\d{3}[\s\-]?\d{3}[\s\-]?\d{3}',             # XXX XXX XXX
            r'\+\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}',  # Medjunarodni
            r'\d{2}[\s\-]?\d{3}[\s\-]?\d{3}',             # XX XXX XXX
        ]
        
        phones = []
        for pattern in phone_patterns:
            found_phones = re.findall(pattern, page_text)
            phones.extend(found_phones)
        
        if phones:
            # Pocisti i validuj telefone
            valid_phones = []
            for phone in phones:
                # Ukloni razmake i crtice
                clean_phone = re.sub(r'[\s\-]', '', phone)
                # Proveri da li je validan broj (minimum 8, maksimum 15 cifara)
                if re.match(r'^\+?\d{8,15}$', clean_phone):
                    valid_phones.append(phone.strip())
            
            if valid_phones:
                company_data['telefon'] = valid_phones[0]  # Uzmi prvi validni
        
        # Trazi web sajt
        web_links = soup.find_all('a', href=True)
        for link in web_links:
            href = link.get('href', '')
            if href.startswith('http') and 'companywall' not in href:
                # Osnovne provere za web sajt
                if any(domain in href for domain in ['.com', '.me', '.rs', '.net', '.org']):
                    company_data['web'] = href
                    break
        
        # Trazi KD (klasifikacija delatnosti)
        kd_patterns = [
            r'KD[:\s]*(\d{2}\.?\d{2}\.?\d{0,2})',
            r'(\d{2}\.\d{2}\.\d{2})',
            r'(\d{2}\.\d{2})',
            r'Delatnost[:\s]*(\d{2}\.?\d{2}\.?\d{0,2})'
        ]
        
        for pattern in kd_patterns:
            kd_matches = re.findall(pattern, page_text, re.IGNORECASE)
            if kd_matches:
                company_data['kd'] = kd_matches[0]
                break
        
        print(f"  Izvukao podatke za {company_data['naziv'] or 'N/A'}")
        return company_data
        
    except Exception as e:
        print(f"  Greska pri parsiranju profila: {e}")
        return None

def save_to_csv_incremental(company_data, output_file):
    """Cuva jedan red u CSV fajl (append mode)"""
    try:
        import os
        
        # Proverava da li fajl postoji
        file_exists = os.path.isfile(output_file)
        
        # Kreira DataFrame sa jednim redom
        df = pd.DataFrame([company_data])
        
        # Cuva u CSV
        if file_exists:
            # Append mode - dodaje na kraj bez header-a
            df.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8')
            print(f"  + Dodat u {output_file}")
        else:
            # Prvi put - kreira fajl sa header-om
            df.to_csv(output_file, mode='w', header=True, index=False, encoding='utf-8')
            print(f"  + Kreiran {output_file} sa prvim rezultatom")
        
        return True
    except Exception as e:
        print(f"Greska pri cuvanju: {e}")
        return False

def save_to_csv(results, output_file):
    """Sacuvaj rezultate u CSV fajl (backup funkcija)"""
    try:
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Rezultati sacuvani u: {output_file}")
        return True
    except Exception as e:
        print(f"Greska pri cuvanju CSV fajla: {e}")
        return False

def load_pibs_from_file(file_path):
    """Ucitaj PIB brojeve iz fajla"""
    pibs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and line.isdigit():
                    pibs.append(line)
        
        print(f"Ucitao {len(pibs)} PIB brojeva iz {file_path}")
        return pibs
        
    except Exception as e:
        print(f"Greska pri ucitavanju fajla: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='CompanyWall Montenegro Scraper')
    parser.add_argument('--input', required=True, help='Fajl sa PIB brojevima')
    parser.add_argument('--output', default='rezultati.csv', help='Izlazni CSV fajl')
    parser.add_argument('--headless', action='store_true', help='Pokreni u headless modu')
    
    args = parser.parse_args()
    
    # Ucitaj PIB brojeve
    pibs = load_pibs_from_file(args.input) 
    if not pibs:
        print("Nema PIB brojeva za obradu!")
        return
    
    # Kreiraj Chrome driver
    driver = create_chrome_driver(headless=args.headless)
    if not driver:
        print("Neuspesno kreiranje Chrome driver-a!")
        return
    
    success_count = 0
    
    try:
        print(f"Pocinje obrada {len(pibs)} PIB brojeva...")
        
        for i, pib in enumerate(pibs, 1):
            print(f"\n[{i}/{len(pibs)}] Obradjujem PIB: {pib}")
            
            # VPN upozorenje svakih 15 PIB-ova
            if i > 1 and i % 15 == 1:
                print("\n" + "="*50)
                print("VPN UPOZORENJE!")
                print("Promeni VPN lokaciju u Bitdefender VPN-u")
                print("Pritisni Enter kad zavrsis...")
                print("="*50)
                input()
            
            # Pretrazi po PIB-u
            profile_url = search_companywall_by_pib(driver, pib)
            
            if profile_url:
                # Parsiranje profila
                company_data = parse_company_profile(driver, profile_url, pib)
                
                if company_data:
                    # ODMAH cuva rezultat inkrementalno
                    save_to_csv_incremental(company_data, args.output)
                    success_count += 1
                    print(f"  Uspesno! ({success_count}/{i})")
                else:
                    # Cuva prazan red ako nema podataka
                    empty_data = {
                        'naziv': '',
                        'pib': pib.zfill(8),
                        'grad': '',
                        'email': '',
                        'telefon': '',
                        'web': '',
                        'kd': ''
                    }
                    save_to_csv_incremental(empty_data, args.output)
                    print(f"  Nema podataka za PIB {pib}")
            else:
                # Cuva prazan red ako nema profila
                empty_data = {
                    'naziv': '',
                    'pib': pib.zfill(8),
                    'grad': '',
                    'email': '',
                    'telefon': '',  
                    'web': '',
                    'kd': ''
                }
                save_to_csv_incremental(empty_data, args.output)
                print(f"  Profil nije nadjen za PIB {pib}")
        
        print(f"\nZAVRSENO!")
        print(f"Ukupno obradjeno: {len(pibs)} PIB brojeva")
        print(f"Uspesno: {success_count}")
        print(f"Svi rezultati su vec sacuvani u: {args.output}")
        
    except KeyboardInterrupt:
        print("\nPrekid od strane korisnika!")
        print(f"Rezultati su vec sacuvani inkrementalno u: {args.output}")
    
    except Exception as e:
        print(f"Neocekivana greska: {e}")
        print(f"Rezultati su vec sacuvani inkrementalno u: {args.output}")
    
    finally:
        if driver:
            driver.quit()
            print("Chrome driver zatvoren")

if __name__ == "__main__":
    main()