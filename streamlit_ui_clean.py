#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import subprocess
import os
import sys
import threading

st.set_page_config(
    page_title="CompanyWall Scraper",
    page_icon="🏢",
    layout="wide"
)

def main():
    st.title("🏢 CompanyWall Montenegro Scraper")
    
    with st.sidebar:
        st.header("Podesavanja")
        output_file = st.text_input("Izlazni fajl:", value="rezultati.csv")
        headless_mode = st.checkbox("Headless rezim", value=True)
        
        st.markdown("---")
        st.markdown("### Izvlaceni podaci:")
        st.markdown("""
        - Naziv firme
        - PIB (8 cifara)
        - Grad (iz adrese)
        - Email
        - Telefon
        - Web sajt
        - KD sifra (delatnost)
        """)
        
        st.warning("VPN Napomena: Promeni VPN lokaciju svakih 15 PIB-ova!")
    
    tab1, tab2, tab3 = st.tabs(["Unos PIB-ova", "Pokretanje", "Rezultati"])
    
    with tab1:
        handle_pib_input()
    
    with tab2:
        handle_scraper_execution(output_file, headless_mode)
    
    with tab3:
        handle_results_display(output_file)

def handle_pib_input():
    st.header("Unos PIB brojeva")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Unesi PIB brojeve (jedan po liniji):")
        pib_text = st.text_area(
            "PIB brojevi:",
            height=300,
            placeholder="12345678\n87654321\n11223344",
            help="Svaki PIB broj u novom redu"
        )
        
        if st.button("Sacuvaj PIB brojeve", type="primary"):
            if pib_text.strip():
                result = save_pibs_from_text(pib_text, "input_pibs.txt")
                if result:
                    st.success(f"Sacuvano {result['count']} PIB brojeva u input_pibs.txt")
                    if result['invalid']:
                        st.warning(f"Preskoceno {len(result['invalid'])} nevalidnih PIB-ova: {', '.join(result['invalid'])}")
                else:
                    st.error("Greska pri cuvanju PIB brojeva!")
            else:
                st.error("Molim unesi PIB brojeve!")
    
    with col2:
        st.subheader("Ili upload fajl:")
        uploaded_file = st.file_uploader(
            "Izaberi TXT fajl sa PIB brojevima",
            type=['txt'],
            help="TXT fajl sa PIB brojevima, jedan po liniji"
        )
        
        if uploaded_file:
            try:
                content = uploaded_file.read().decode('utf-8')
                st.text_area("Sadrzaj fajla:", value=content, height=200, disabled=True)
                
                if st.button("Koristi ovaj fajl"):
                    result = save_pibs_from_text(content, "input_pibs.txt")
                    if result:
                        st.success(f"Sacuvano {result['count']} PIB brojeva iz uploadovanog fajla")
                        if result['invalid']:
                            st.warning(f"Preskoceno {len(result['invalid'])} nevalidnih PIB-ova")
                    else:
                        st.error("Greska pri obradi fajla!")
                        
            except Exception as e:
                st.error(f"Greska pri citanju fajla: {e}")

def save_pibs_from_text(text, filename):
    """Sacuvaj PIB brojeve iz teksta u fajl"""
    try:
        lines = text.strip().split('\n')
        valid_pibs = []
        invalid_pibs = []
        
        for line in lines:
            pib = line.strip()
            if pib and pib.isdigit() and len(pib) >= 7:
                valid_pibs.append(pib)
            elif pib:  # nije prazan ali nije validan
                invalid_pibs.append(pib)
        
        if valid_pibs:
            with open(filename, 'w', encoding='utf-8') as f:
                for pib in valid_pibs:
                    f.write(f"{pib}\n")
            
            return {
                'count': len(valid_pibs),
                'invalid': invalid_pibs
            }
        
        return None
        
    except Exception as e:
        st.error(f"Greska pri cuvanju: {e}")
        return None

def handle_scraper_execution(output_file, headless_mode):
    st.header("Pokretanje Scraper-a")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.metric("PIB-ova za obradu", get_pib_count())
    
    with col2:
        st.metric("Izlazni fajl", output_file)
    
    with col3:
        st.metric("Rezim", "Headless" if headless_mode else "Visible")
    
    if st.button("Pokreni Scraper", type="primary", use_container_width=True):
        if not os.path.exists("input_pibs.txt"):
            st.error("Nema PIB brojeva! Idi na tab 'Unos PIB-ova' i unesi PIB brojeve.")
            return
        
        with st.spinner("Pokretam scraper..."):
            # Pripremi komandu
            cmd = [
                sys.executable, "script_clean.py",
                "--input", "input_pibs.txt",
                "--output", output_file
            ]
            
            if headless_mode:
                cmd.append("--headless")
            
            st.info(f"Pokrecem scraper: {' '.join(cmd)}")
            
            # Pokreni proces
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minuta timeout
                    encoding='utf-8',
                    errors='replace'
                )
                
                if result.returncode == 0:
                    st.success("Scraper pokrenut u pozadini!")
                    
                    if result.stdout:
                        st.text("Output:")
                        st.code(result.stdout)
                else:
                    st.error(f"Greska pri pokretanju scraper-a (kod: {result.returncode})")
                    if result.stderr:
                        st.error("Stderr:")
                        st.code(result.stderr)
                        
            except subprocess.TimeoutExpired:
                st.warning("Scraper se izvrsava u pozadini (timeout dostignut)")
            except Exception as e:
                st.error(f"Greska: {e}")
    
    # Status i kontrole
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Proveri status"):
            # Proveri da li postoji output fajl
            if os.path.exists(output_file):
                try:
                    df = pd.read_csv(output_file)
                    st.success(f"Pronadjeno {len(df)} rezultata u {output_file}")
                    
                    # Prikazi osnovne statistike
                    email_count = df['email'].notna().sum()
                    phone_count = df['telefon'].notna().sum()
                    web_count = df['web'].notna().sum()
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Email", f"{email_count}/{len(df)}")
                    with col_b:
                        st.metric("Telefon", f"{phone_count}/{len(df)}")
                    with col_c:
                        st.metric("Web", f"{web_count}/{len(df)}")
                        
                except Exception as e:
                    st.error(f"Greska pri citanju rezultata: {e}")
            else:
                st.info("Jos nema rezultata")
    
    with col2:
        if st.button("Koristi 'Proveri status' da pratis napredak"):
            st.info("Klikni na 'Proveri status' da vidis napredak scraper-a")

def get_pib_count():
    """Vrati broj PIB-ova u input fajlu"""
    try:
        if os.path.exists("input_pibs.txt"):
            with open("input_pibs.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return len([line for line in lines if line.strip()])
        return 0
    except:
        return 0

def handle_results_display(output_file):
    st.header("Rezultati")
    
    if os.path.exists(output_file):
        try:
            df = pd.read_csv(output_file)
            
            # Osnovne statistike
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Ukupno firmi", len(df))
            
            with col2:
                email_count = df['email'].notna().sum()
                st.metric("Sa email-om", f"{email_count}/{len(df)}")
            
            with col3:
                phone_count = df['telefon'].notna().sum()
                st.metric("Sa telefonom", f"{phone_count}/{len(df)}")
            
            with col4:
                web_count = df['web'].notna().sum()
                st.metric("Sa web sajtom", f"{web_count}/{len(df)}")
            
            st.markdown("---")
            
            # Filter kontrole
            col1, col2 = st.columns(2)
            
            with col1:
                show_only_with_email = st.checkbox("Prikazi samo sa email-om")
            
            with col2:
                show_only_with_phone = st.checkbox("Prikazi samo sa telefonom")
            
            # Filtriraj podatke
            filtered_df = df.copy()
            
            if show_only_with_email:
                filtered_df = filtered_df[filtered_df['email'].notna() & (filtered_df['email'] != '')]
            
            if show_only_with_phone:
                filtered_df = filtered_df[filtered_df['telefon'].notna() & (filtered_df['telefon'] != '')]
            
            # Prikazi tabelu
            if len(filtered_df) > 0:
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=400
                )
                
                # Download dugme
                csv_data = filtered_df.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"filtered_{output_file}",
                    mime="text/csv"
                )
            else:
                st.info("Nema rezultata koji odgovaraju filter kriterijumima")
                
        except Exception as e:
            st.error(f"Greska pri citanju rezultata: {e}")
            st.code(str(e))
    else:
        st.info("Nema rezultata jos uvek...")
        st.markdown("### Kako pokrenuti scraper:")
        st.markdown("""
        1. Idi na tab **Unos PIB-ova** i unesi PIB brojeve
        2. Idi na tab **Pokretanje** i pokreni scraper
        3. Vrati se ovde da vidis rezultate
        """)

if __name__ == "__main__":
    main()