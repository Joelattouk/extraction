import streamlit as st
import os
import pandas as pd
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configuration de la page
st.set_page_config(page_title="OFP Scraper", page_icon=":robot:", layout="wide")

# Style CSS personnalisé
st.markdown("""
    <style>
    .main { background-color: #F5F5F5; }
    h1 { color: #2F5496; }
    .stProgress > div > div > div > div { background-color: #2F5496; }
    .st-bb { background-color: white; }
    .st-at { background-color: #DAA520; }
    </style>
""", unsafe_allow_html=True)

def init_driver(headless=True):
    """Initialise le driver Chrome"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_bc_articles(driver, save_path):
    """Scraping des BC et articles"""
    data_bc = []
    data_articles = []
    
    try:
        # Navigation vers le menu
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="kt_aside_menu"]/ul/li[2]/a/span[2]'))).click()
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="kt_aside_menu"]/ul/li[2]/div/ul/li[2]/a/span'))).click()
        
        # Sélectionner "100" éléments par page
        select = Select(WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="m_table_1_length"]/label/select'))))
        select.select_by_visible_text("100")
        time.sleep(3)

        with st.status("Scraping des BC et articles...", expanded=True) as status:
            while True:
                WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="m_table_1"]/tbody/tr')))
                lignes = driver.find_elements(By.XPATH, '//*[@id="m_table_1"]/tbody/tr')
                
                for row_index in range(1, len(lignes) + 1):
                    try:
                        # Extraction des données principales
                        bc_num = driver.find_element(By.XPATH, 
                            f'//*[@id="m_table_1"]/tbody/tr[{row_index}]/td[4]').text.strip()
                        bci_num = driver.find_element(By.XPATH, 
                            f'//*[@id="m_table_1"]/tbody/tr[{row_index}]/td[3]').text.strip()
                        status_bc = driver.find_element(By.XPATH, 
                            f'//*[@id="m_table_1"]/tbody/tr[{row_index}]/td[8]/span').text.strip()
                        
                        # Accès aux détails
                        button_detail = driver.find_element(By.XPATH, 
                            f'//*[@id="m_table_1"]/tbody/tr[{row_index}]/td[11]/a/i')
                        driver.execute_script("arguments[0].click();", button_detail)
                        time.sleep(3)
                        
                        # Extraction des détails BC
                        auteur = driver.find_element(By.XPATH, 
                            '//*[@id="kt_content"]/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/div/div[2]/div[1]/div[1]/div/a[2]').text.strip()
                        code_garage = driver.find_element(By.XPATH, 
                            '//*[@id="kt_content"]/div[2]/div/div[1]/div[1]/div[1]/div/div[2]/div/div[2]/div[1]/div[1]/div/a[3]').text.strip()
                        
                        data_bc.append({
                            "BC": bc_num,
                            "BCI": bci_num,
                            "Statut": status_bc,
                            "Auteur": auteur,
                            "Code Garage": code_garage
                        })
                        
                        # Extraction des articles
                        articles_rows = driver.find_elements(By.XPATH, 
                            '//*[@id="kt_content"]/div[2]/div/div[1]/div[2]/div/div/div[2]/div/table/tbody/tr')
                        for row in articles_rows:
                            tds = row.find_elements(By.TAG_NAME, 'td')
                            data_articles.append({
                                "BC": bc_num,
                                "BCI": bci_num,
                                "Statut": status_bc,
                                "Article": tds[0].text.strip(),
                                "Code analytique": tds[1].text.strip(),
                                "Date de livraison desiree": tds[2].text.strip(),
                                "Quantité": tds[3].text.strip(),
                                "Quantité livrée": tds[4].text.strip(),
                                "Fournisseur": tds[5].text.strip(),
                                "Prix unitaire estimé": tds[6].text.strip(),
                                "Prix unitaire HT": tds[7].text.strip(),
                                "Commentaire": tds[8].text.strip(),
                                "Délais": tds[9].text.strip()
                            })
                        
                        driver.back()
                        time.sleep(3)
                        
                    except Exception as e:
                        st.warning(f"Erreur ligne {row_index}: {str(e)}")
                        continue
                
                # Pagination
                next_button = driver.find_elements(By.XPATH, '//*[@id="m_table_1_next"]')
                if next_button and "disabled" not in next_button[0].get_attribute("class"):
                    driver.execute_script("arguments[0].click();", next_button[0])
                    time.sleep(3)
                else:
                    break

            # Sauvegarde
            bc_path = os.path.join(save_path, "Base_BC_Materiel_VF.xlsx")
            articles_path = os.path.join(save_path, "Base_Articles_VF.xlsx")
            pd.DataFrame(data_bc).to_excel(bc_path, index=False)
            pd.DataFrame(data_articles).to_excel(articles_path, index=False)
            
            status.update(label="Scraping terminé!", state="complete", expanded=False)
            return bc_path, articles_path
            
    except Exception as e:
        st.error(f"Erreur majeure: {str(e)}")
        return None, None

######################

def scrape_historique(driver, save_path):
    """Scraping de l'historique"""
    data_historique = []
    
    try:
        # Navigation vers le menu
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="kt_aside_menu"]/ul/li[2]/a/span[2]'))).click()
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="kt_aside_menu"]/ul/li[2]/div/ul/li[2]/a/span'))).click()
        
        # Sélectionner "100" éléments par page
        select = Select(WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="m_table_1_length"]/label/select'))))
        select.select_by_visible_text("100")
        time.sleep(3)

        with st.status("Scraping de l'historique...", expanded=True) as status:
            while True:
                WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="m_table_1"]/tbody/tr')))
                lignes = driver.find_elements(By.XPATH, '//*[@id="m_table_1"]/tbody/tr')
                
                for row_index in range(1, len(lignes) + 1):
                    try:
                        bc_num = driver.find_element(By.XPATH, 
                            f'//*[@id="m_table_1"]/tbody/tr[{row_index}]/td[4]').text.strip()
                        bci_num = driver.find_element(By.XPATH, 
                            f'//*[@id="m_table_1"]/tbody/tr[{row_index}]/td[3]').text.strip()
                        status_bc = driver.find_element(By.XPATH, 
                            f'//*[@id="m_table_1"]/tbody/tr[{row_index}]/td[8]/span').text.strip()

                        # Accès aux détails
                        button_detail = driver.find_element(By.XPATH, 
                            f'//*[@id="m_table_1"]/tbody/tr[{row_index}]/td[11]/a/i')
                        driver.execute_script("arguments[0].click();", button_detail)
                        time.sleep(3)

                        # Extraction de l'historique
                        historique_rows = driver.find_elements(By.XPATH, 
                            '//*[@id="kt_content"]/div[2]/div/div[1]/div[3]/div[2]/div/div[2]/div')
                        
                        historique_text = "\n".join([row.text for row in historique_rows])
                        data_historique.append({
                            "BC": bc_num,
                            "BCI": bci_num,
                            "Statut": status_bc,
                            "Historique": historique_text
                        })

                        driver.back()
                        time.sleep(3)
                        
                    except Exception as e:
                        st.warning(f"Erreur ligne {row_index}: {str(e)}")
                        continue
                
                # Pagination
                next_button = driver.find_elements(By.XPATH, '//*[@id="m_table_1_next"]')
                if next_button and "disabled" not in next_button[0].get_attribute("class"):
                    driver.execute_script("arguments[0].click();", next_button[0])
                    time.sleep(3)
                else:
                    break

            # Structuration des données
            historique_structuré = []
            pattern = r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\n(.+)"
            
            for entry in data_historique:
                matches = re.findall(pattern, entry["Historique"])
                for date, action in matches:
                    historique_structuré.append({
                        "BC": entry["BC"],
                        "BCI": entry["BCI"],
                        "Statut": entry["Statut"],
                        "Date": date,
                        "Action": action
                    })

            # Sauvegarde
            hist_path = os.path.join(save_path, "Base_Historique_Complet.xlsx")
            pd.DataFrame(historique_structuré).to_excel(hist_path, index=False)
            
            status.update(label="Scraping terminé!", state="complete", expanded=False)
            return hist_path
            
    except Exception as e:
        st.error(f"Erreur majeure: {str(e)}")
        return None

# Interface utilisateur
st.title("📦 Extraction de données")
st.markdown("---")

# Sidebar pour les paramètres
with st.sidebar:
    st.header("⚙️ Paramètres")
    save_dir = st.text_input("Dossier de sauvegarde", value=os.getcwd())
    headless = st.checkbox("Mode Masqué", value=True)
    
    st.markdown("---")
    st.info("ℹ️ Entrez vos identifiants OFP ci-dessous:")

# Formulaire de connexion
with st.form("login_form"):
    cols = st.columns(2)
    username = cols[0].text_input("Identifiant", value="MXXXXXXX")
    password = cols[1].text_input("Mot de passe", type="password", value="11111111")
    
    st.markdown("---")
    tab1, tab2 = st.tabs(["📄 BC & Articles", "🕒 Historique"])
    
    with tab1:
        bc_submit = st.form_submit_button("Lancer le scraping BC/Articles")
        
    with tab2:
        hist_submit = st.form_submit_button("Lancer le scraping Historique")

# Gestion des actions
if bc_submit or hist_submit:
    driver = init_driver(headless)
    
    try:
        # Connexion
        driver.get("https://ofp.company/login")
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="kt_login_signin_form"]/div[1]/input'))).send_keys(username)
        driver.find_element(By.XPATH, '//*[@id="kt_login_signin_form"]/div[2]/input[1]').send_keys(password)
        driver.find_element(By.XPATH, '//*[@id="kt_login_signin_submit"]').click()
        time.sleep(2)
        
        if bc_submit:
            bc_path, articles_path = scrape_bc_articles(driver, save_dir)
            if bc_path:
                st.success(f"Fichiers sauvegardés:\n- {bc_path}\n- {articles_path}")
                
        if hist_submit:
            hist_path = scrape_historique(driver, save_dir)
            if hist_path:
                st.success(f"Fichier sauvegardé:\n- {hist_path}")
                
    except Exception as e:
        st.error(f"Erreur lors de l'exécution: {str(e)}")
    finally:
        driver.quit()
        st.rerun()

# Section d'aide
with st.expander("❓ Aide"):
    st.markdown("""
    **Instructions d'utilisation:**
    1. Entrez vos identifiants OFP
    2. Sélectionnez le dossier de sauvegarde
    3. Choisissez le type de collecte -> BC & Articles ou Historique
    4. Cliquez sur le bouton d'exécution
    
    **Fonctionnalités:**
    - Mode Masqué (pas d'interface navigateur visible pendant l'opération)
    - Choix du dossier de sortie
    - Interface utilisateur intuitive
    - Suivi en temps réel
    """)