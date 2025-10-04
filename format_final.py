import pandas as pd
import os

def format_all_data():
    # Učitaj CSV fajl
    df = pd.read_csv('rezultati.csv')
    
    print(f"Ukupno redova: {len(df)}")
    
    # Funkcija za formatiranje PIB-a (8 cifara sa vodećim nulama)
    def format_pib(pib):
        if pd.isna(pib) or pib == '':
            return pib
        
        # Konvertuj u string i ukloni decimalne delove ako postoje
        pib_str = str(pib)
        if '.' in pib_str:
            pib_str = pib_str.split('.')[0]
        
        # Dodaj nule na početak da bude 8 cifara
        return pib_str.zfill(8)
    
    # Funkcija za formatiranje telefona
    def format_phone(phone):
        if pd.isna(phone) or phone == '':
            return phone
        
        # Konvertuj u string i ukloni .0 ako postoji
        phone_str = str(phone)
        if phone_str.endswith('.0'):
            phone_str = phone_str[:-2]
        
        # Ako počinje sa 67, 68 ili 69, dodaj 0 na početak
        if phone_str.startswith(('67', '68', '69')):
            return '0' + phone_str
        
        return phone_str
    
    # Funkcija za formatiranje KD (šifre delatnosti)
    def format_kd(kd):
        if pd.isna(kd) or kd == '':
            return kd
        
        kd_str = str(kd)
        if kd_str.endswith('.0'):
            return kd_str[:-2]
        
        return kd_str
    
    # Funkcija za zamenu dijakritika
    def replace_diacritics_text(text):
        if pd.isna(text) or text == '':
            return text
        
        # Mapa za zamenu dijakritičkih znakova
        diacritic_map = {
            'š': 's', 'Š': 'S',
            'č': 'c', 'Č': 'C', 
            'ć': 'c', 'Ć': 'C',
            'đ': 'dj', 'Đ': 'Dj',
            'ž': 'z', 'Ž': 'Z'
        }
        
        text_str = str(text)
        for old, new in diacritic_map.items():
            text_str = text_str.replace(old, new)
        
        return text_str
    
    # Prebrojimo koliko ima problema
    pib_issues = sum(1 for pib in df['pib'] if pd.notna(pib) and (len(str(pib).split('.')[0]) != 8 or '.' in str(pib)))
    phone_issues = sum(1 for phone in df['telefon'] if pd.notna(phone) and ('.0' in str(phone) or str(phone).replace('.0', '').startswith(('67', '68', '69'))))
    kd_issues = sum(1 for kd in df['kd'] if pd.notna(kd) and '.0' in str(kd))
    diacritic_issues = sum(1 for naziv in df['naziv'] if pd.notna(naziv) and any(char in str(naziv) for char in 'šščćđžŠŠČĆĐŽ'))
    
    print(f"PIB brojeva za formatiranje: {pib_issues}")
    print(f"Telefona za formatiranje: {phone_issues}")
    print(f"KD kodova za formatiranje: {kd_issues}")
    print(f"Naziva sa dijakriticima: {diacritic_issues}")
    
    # Primeni sve formatiranje
    df['pib'] = df['pib'].apply(format_pib)
    df['telefon'] = df['telefon'].apply(format_phone)
    df['kd'] = df['kd'].apply(format_kd)
    
    # Primeni zamenu dijakritika na tekstualne kolone
    text_columns = ['naziv', 'grad', 'email', 'web']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(replace_diacritics_text)
    
    print("\nFormatiranje završeno!")
    
    # Prikaži prvih nekoliko redova
    print("\nPrvih 5 redova nakon formatiranja:")
    print(df[['naziv', 'pib', 'telefon', 'kd']].head())
    
    # Sačuvaj izmenjeni fajl
    df.to_csv('rezultati.csv', index=False)
    print("\nFajl je uspešno sačuvan!")

def cleanup_scripts():
    # Lista skripti za brisanje
    scripts_to_delete = [
        'remove_duplicates.py',
        'fix_pib.py', 
        'fix_decimals.py',
        'fix_phones.py',
        'fix_complete.py'
    ]
    
    print("\nBrisanje starih skripti...")
    for script in scripts_to_delete:
        if os.path.exists(script):
            os.remove(script)
            print(f"Obrisana: {script}")
        else:
            print(f"Nije pronađena: {script}")

if __name__ == "__main__":
    format_all_data()
    cleanup_scripts()
    print("\nSve gotovo! Svi podaci su formatiri i stare skripte su obrisane.")