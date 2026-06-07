import streamlit as st
import shutil
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime, timedelta
from fpdf import FPDF
import warnings

# --- NASCONDE GLI AVVISI DI STREAMLIT 2026 ---
warnings.filterwarnings("ignore")

# =========================================================
# CODICE DEL BACKUP JSON
# =========================================================

def crea_backup_automatico():
    """Crea una copia del database nella cartella 'backups'"""
    try:
        if os.path.exists("db_studio.json"):
            if not os.path.exists("backups"):
                os.makedirs("backups")
            
            data_ora = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_backup = f"backups/backup_auto_{data_ora}.json"
            shutil.copy2("db_studio.json", nome_backup)
            
            # Mantieni solo gli ultimi 30 backup per non occupare spazio
            elenco_b = sorted([os.path.join("backups", f) for f in os.listdir("backups")])
            if len(elenco_b) > 30:
                os.remove(elenco_b[0])
    except:
        pass

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Studio Ga.Ma. srl", layout="wide", page_icon="🦷")

# --- CSS PERSONALIZZATO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
    /* SFONDO CENTRALE: Rimane la sfumatura dolce celestina, che non tocca la barra */
    .stApp {
        background: linear-gradient(135deg, #e6f2ff 0%, #f4f9ff 100%) !important;
    }
    
    /* EFFETTO MODULI: Bianco Candido per i moduli dati */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stDateInput input, .stTimeInput input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }
    
    /* CONTENITORI ESPANDIBILI (st.expander) */
    div[data-testid="stExpander"] {
        background: linear-gradient(90deg, #ffffff 0%, #f8fafc 100%) !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }
    
    /* TAB / NAVIGAZIONE INTERNA */
    button[data-baseweb="tab"] {
        color: #64748b !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0056b3 !important;
        border-bottom: 3px solid #0056b3 !important;
    }
    
    /* PULSANTI CENTRALI */
    button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #0056b3 0%, #1d3557 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    
    /* SCHEDE DENTI (Odontogramma) */
    .dente-card { 
        border: 1px solid #e2e8f0; 
        padding: 6px; 
        border-radius: 8px; 
        background-color: #ffffff; 
        text-align: center; 
    }
    
    .legenda-p { font-size: 13px !important; margin-bottom: 2px !important; font-family: 'Segoe UI', sans-serif; display: flex; align-items: center; }
    .emoji-space { margin-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DI UTILITÀ ---
def format_it(valore):
    """Formatta i numeri con stile italiano: 1.250,50 €"""
    try:
        return f"{float(valore):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
    except:
        return str(valore)

def pulisci_numero_wa(numero):
    num = str(numero).replace(" ", "").replace("-", "").replace("+", "")
    if num.startswith("3") and len(num) >= 9: return "39" + num
    return num

def applica_colore(testo):
    t = testo.upper()
    if "[URG]" in t: return "🔴 " + testo
    if "[IG]" in t: return "🟢 " + testo
    if "[PRO]" in t: return "🔵 " + testo
    if "[ORT]" in t: return "🟡 " + testo
    if "[VIS]" in t: return "⚪ " + testo
    return "⚪ " + testo

def carica_dati():
    default = {"medici": [], "appuntamenti": [], "pazienti": []}
    if os.path.exists("db_studio.json"):
        try:
            with open("db_studio.json", "r") as f: 
                d = json.load(f)
                for key in default:
                    if key not in d: d[key] = []
                for p in d["pazienti"]:
                    campi_default = {
                        "Via": "", "Citta": "", "Provincia": "", "Note_Cliniche": "", 
                        "CF": "", "Tel": "", "Allergie": "", "Odontogramma": {}, 
                        "Pagamenti": [], "Diario": []
                    }
                    for k, v in campi_default.items():
                        if k not in p: p[k] = v
                return d
        except: return default
    return default

def salva_dati(d):
    with open("db_studio.json", "w") as f:
        json.dump(d, f, indent=2)
    crea_backup_automatico()

def esporta_pdf(df, data, medico):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "STUDIO GA.MA. SRL - AGENDA", 0, 1, 'C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 8, f"Data: {data} | Medico: {medico}", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 10, "ORA", 1, 0, 'C', True)
    pdf.cell(90, 10, "PAZIENTE / PRESTAZIONE", 1, 0, 'C', True)
    pdf.cell(70, 10, "MEDICO", 1, 1, 'C', True)
    pdf.set_font("Arial", '', 10)
    for index, row in df.iterrows():
        pdf.cell(30, 10, str(row['Ora']), 1, 0, 'C')
        pdf.cell(90, 10, str(row['Paziente']), 1, 0, 'L')
        pdf.cell(70, 10, str(row['Medico']), 1, 1, 'L')
    return pdf.output(dest='S').encode('latin-1')
    
def genera_ricevuta_pdf(paziente, data, importo, descrizione="Prestazione Odontoiatrica"):
    pdf = FPDF()
    pdf.add_page()
    # Intestazione
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "STUDIO ODONTOIATRICO GA.MA. SRL", 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, "- Ricevuta Interna di Pagamento-", 0, 1, 'C')
    pdf.cell(190, 5, "Sede Legale", 0, 1, 'C')
    pdf.cell(190, 5, "Via XX Settembre, 7, 84091 Battipaglia (SA)", 0, 1, 'C')
    
    pdf.ln(20)
    
    # Corpo Ricevuta
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 10, f"Data: {data}", 0, 1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, f"Ricevuto da: {paziente}", 0, 1)
    pdf.ln(10)
    # ---DESCRIZIONE PRESTAZIONE ---
    pdf.set_font("Arial", 'I', 11)
    pdf.multi_cell(190, 8, f"Per: {descrizione}", 0, 'L')
    pdf.ln(5)
        
    # Somma versata
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 10, f"Somma versata: {importo}", 1, 1, 'C')
    pdf.set_font("Arial", '', 12)
    pdf.ln(20)
    
    # Firma
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(190, 10, "STUDIO ODONTOIATRICO GA.MA. SRL", 0, 1, 'R')
    pdf.cell(190, 10, "__________________________", 0, 1, 'R')
    pdf.cell(190, 10, "dott. Stefano Pio Gammella", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

def get_richiami_igiene(db):
    richiami = []
    oggi = datetime.now().date()
    sei_mesi_fa = oggi - timedelta(days=180)
    for paz in db["pazienti"]:
        nome_paz = paz["Nome"]
        app_ig = [a for a in db["appuntamenti"] if nome_paz in a["Paziente"] and "[IG]" in a["Paziente"]]
        if app_ig:
            try:
                ult_ig_str = max([a["Data"] for a in app_ig], key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
                ult_ig_dt = datetime.strptime(ult_ig_str, "%d/%m/%Y").date()
                if ult_ig_dt < sei_mesi_fa:
                    richiami.append({"Paziente": nome_paz, "Ultima Igiene": ult_ig_str, "Telefono": paz.get("Tel", "N/D"), "Mesi": (oggi - ult_ig_dt).days // 30})
            except: continue
    return richiami

# =========================================================
# CARICAMENTO DATABASE E CONVERSIONE CON CODIFICA LATIN-1
# =========================================================
st.session_state.db = carica_dati()

# Se la chiave non esiste, o se la lista dei pazienti è completamente vuota
if "pazienti" not in st.session_state.db or len(st.session_state.db["pazienti"]) == 0:
    try:
        import pandas as pd
        import json
        import os
        
        if os.path.exists("Contatti  STUDIO GAMA.csv"):
            # AGGIUNTO encoding="latin-1" PER RISOLVERE L'ERRORE DI DECODIFICA WINDOWS
            df = pd.read_csv("Contatti  STUDIO GAMA.csv", sep=";", encoding="latin-1")
            df.columns = df.columns.str.strip() 
            
            pazienti_importati = []
            for _, row in df.iterrows():
                nome_completo = str(row.get("Nome e Cognome", "")).strip().upper()
                
                if nome_completo and nome_completo != "NAN" and nome_completo != "NOME E COGNOME":
                    pazienti_importati.append({
                        "Nome": nome_completo,  
                        "CF": str(row.get("Codice fiscale", "")).strip().upper() if pd.notna(row.get("Codice fiscale")) else "",
                        "Via": str(row.get("Indirizzo", "")).strip().upper() if pd.notna(row.get("Indirizzo")) else "",
                        "Citta": str(row.get("Citta'", "")).strip().upper() if pd.notna(row.get("Citta'")) else "",
                        "Provincia": str(row.get("Provincia", "")).strip().upper() if pd.notna(row.get("Provincia")) else "",
                        "Tel": "",  
                        "Odontogramma": {},
                        "Pagamenti": [],
                        "Diario": [],
                        "Allergie": "",
                        "Note_Cliniche": ""
                    })
            
            if pazienti_importati:
                st.session_state.db["pazienti"] = pazienti_importati
                with open("db_studio.json", "w") as f:
                    json.dump(st.session_state.db, f, indent=2)
                st.success(f"🎉 Ottimo! Importati con successo {len(pazienti_importati)} pazienti dal CSV!")
        else:
            st.error("⚠️ Il file 'Contatti  STUDIO GAMA.csv' non è stato trovato nella cartella del progetto!")
                
    except Exception as e:
        st.error(f"Errore critico nell'importazione del CSV: {e}")


# --- MENU LATERALE ---
with st.sidebar:
    st.markdown("## 🦷 STUDIO GA.MA.")
    st.markdown("### 🏷️ LEGENDA VISITA")
    st.markdown("""
        <p class="legenda-p"><span class="emoji-space">🔴</span><b>[URG]</b> Urgenza</p>
        <p class="legenda-p"><span class="emoji-space">🟢</span><b>[IG]</b> &nbsp;&nbsp;Igiene</p>
        <p class="legenda-p"><span class="emoji-space">🔵</span><b>[PRO]</b> Protesi</p>
        <p class="legenda-p"><span class="emoji-space">🟡</span><b>[ORT]</b> Ortodonzia</p>
        <p class="legenda-p"><span class="emoji-space">⚪</span><b>[VIS]</b> Visita</p>
    """, unsafe_allow_html=True)
    st.markdown("---")
    menu = st.sidebar.radio("NAVIGAZIONE:", [
    "🏠 Dashboard",  
    "👥 Anagrafica Pazienti", 
    "📅 Agenda Appuntamenti", 
    "💰 Gestione Incassi", 
    "📊 Statistiche e Richiami", 
    "🖨️ Stampa Agenda", 
    "🔍 Cronologia Appuntamenti", 
    "📝 Nuova Prenotazione", 
    "👨‍⚕️ Gestione Medici", 
    "📄 Fattura Sanitaria", 
    "📑 Piano di Cura",
    "📦 Magazzino"
    ])
    st.markdown("---")
    st.sidebar.info("💾 **Stato Database:**\nIl sistema salva i dati in automatico ad ogni operazione - Oppure click su Salva DataBase.")
    if st.button("💾 SALVA DATABASE", width="stretch"):
        salva_dati(st.session_state.db)
        st.success("Dati salvati!")
    
    st.markdown(f'''
        <div class="credits-sidebar" style="text-align: center; margin: 40px auto 10px auto; width: 100%;">
            CORE ENGINE BY<br>
            <b style="color: #5d6d7e;">SERGIO MIRRA</b><br>
            <span style="font-size: 9px;">Release 1.8.8 • 2026</span>
        </div>
''', unsafe_allow_html=True)
# =========================================================
# 1. DASHBOARD CON LOGO 
# =========================================================
if menu == "🏠 Dashboard":
    import base64
    import os

    logo_html = ""
    # Controlliamo se il file esiste nella tua cartella
    if os.path.exists("logo_studio.png"):
        with open("logo_studio.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            # Questo tag inserisce l'immagine convertita direttamente nell'HTML
            logo_html = f'<img src="data:image/png;base64,{encoded_string}" width="90" style="border-radius: 4px;">'
    else:
        # Se non trova il file, usa un'icona di sicurezza (un dente) per non rompere la grafica
        logo_html = '<span style="font-size: 40px; margin-right: 10px;">🦷</span>'

    try:
        # --- LOGO E SCRITTA AFFIANCATI (VERSIONE DEFINITIVA) ---
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 5px;">
                {logo_html}
                <div>
                    <h2 style="margin: 0; font-size: 26px; color: #1c3d5a; font-family: 'Segoe UI', system-ui, sans-serif; font-weight: 600;">
                        Studio Odontoiatrico Ga.Ma.
                    </h2>
                    <p style="margin: 0; font-size: 13px; color: #555555; font-style: italic;">
                        Gestionale Clinico Interno
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        st.title("🦷 STUDIO ODONTOIATRICO GA.MA.")
    
    st.subheader(f"Situazione al {datetime.now().strftime('%d/%m/%Y')}")
    st.divider()
    # =========================================================================
    # 🚨 INTEGRAZIONE ALERT MAGAZZINO IN DASHBOARD (Rilevazione automatica)
    # =========================================================================
    articoli_scaduti = 0
    articoli_sottoscorta = 0
    oggi_dt = datetime.now()

    if "magazzino" in st.session_state.db and st.session_state.db["magazzino"]:
        for k, v in st.session_state.db["magazzino"].items():
            # Controllo Scadenza lotti
            try:
                data_scad_dt = datetime.strptime(v["Scadenza"], "%d/%m/%Y")
                if (data_scad_dt - oggi_dt).days < 0:
                    articoli_scaduti += 1
            except:
                pass
            
            # Controllo Scorte minime
            if v["Quantità"] <= v.get("Soglia", 2):
                articoli_sottoscorta += 1

    # Mostra i banner colorati solo se ci sono anomalie reali
    if articoli_scaduti > 0:
        st.error(f"🔴 **ATTENZIONE:** Ci sono **{articoli_scaduti}** articoli scaduti in magazzino! Controllare la scheda inventario.")
    if articoli_sottoscorta > 0:
        st.warning(f"⚠️ **SOTTOSCORTA:** Ci sono **{articoli_sottoscorta}** articoli in esaurimento o sotto la soglia minima.")
    
    if articoli_scaduti > 0 or articoli_sottoscorta > 0:
        st.divider()

    # =========================================================================
    # FASE 3: PROMEMORIA APPUNTAMENTI DI DOMANI (WHATSAPP)
    # =========================================================================
    from datetime import timedelta
    data_domani = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
    # =========================================================================
    # FASE 3: PROMEMORIA APPUNTAMENTI DI DOMANI (WHATSAPP)
    # =========================================================================
    from datetime import timedelta
    data_domani = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
    
    with st.expander(f"📱 Invia Promemoria per Domani ({data_domani})"):
        # Recuperiamo tutti gli appuntamenti di domani
        appuntamenti_domani = []
        if "appuntamenti" in st.session_state.db:
            for app in st.session_state.db["appuntamenti"]:
                if app.get("Data") == data_domani:
                    appuntamenti_domani.append(app)
        
        if appuntamenti_domani:
            msg_domani_base = "Gentile paziente, le ricordiamo il suo appuntamento presso lo Studio Dentistico Ga.Ma. per domani alle ore [ORA]. La preghiamo di avvisare con anticipo in caso di impedimento. Saluti!"
            
            testo_wa_domani = st.text_area(
                "Modifica il testo base del promemoria:",
                value=msg_domani_base,
                height=100,
                key="txt_promemoria_domani"
            )
            st.divider()
            
            for app in appuntamenti_domani:
                paz_nome = app.get("Paziente", "Paziente")
                ora_app = app.get("Ora", "--:--")
                
                # Cerchiamo il numero di telefono del paziente nel database dei pazienti
                paz_tel = ""
                if "pazienti" in st.session_state.db:
                    for p in st.session_state.db["pazienti"]:
                        if p.get("Nome") == paz_nome:
                            paz_tel = p.get("Telefono", "")
                            break
                
                # Sostituiamo dinamicamente l'ora nel testo modificato dalla segretaria
                testo_con_ora = testo_wa_domani.replace("[ORA]", ora_app)
                
                # Pulizia numero
                tel_pulito = "".join(filter(str.isdigit, str(paz_tel)))
                if tel_pulito and not tel_pulito.startswith("39") and len(tel_pulito) == 10:
                    tel_pulito = "39" + tel_pulito
                
                import urllib.parse
                testo_url = urllib.parse.quote(testo_con_ora)
                link_wa = f"https://wa.me/{tel_pulito}?text={testo_url}"
                
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"⏰ Ore **{ora_app}** - 👤 **{paz_nome}** (Tel: {paz_tel if paz_tel else 'N/D'})")
                with c2:
                    if tel_pulito:
                        st.markdown(f'📱 [Invia]({link_wa})', unsafe_allow_html=True)
                    else:
                        st.caption("❌ No Tel")
        else:
            st.info("🤷‍♂️ Nessun appuntamento fissato per domani.")
    st.divider()
    # =========================================================================
    oggi = datetime.now().strftime("%d/%m/%Y")
    lista_appuntamenti = st.session_state.db.get("appuntamenti", [])
    
    # Estraiamo e contiamo gli impegni odierni
    appuntamenti_oggi = [a for a in lista_appuntamenti if a.get('Data') == oggi]
    totale_oggi = len(appuntamenti_oggi)
    
    # Monitoraggio Urgenze della giornata
    urgenze_oggi = sum(1 for a in appuntamenti_oggi if "[URG]" in a.get('Paziente', '') or "Urgenza" in a.get('Prestazione', ''))
    
    # Conteggio anagrafica generale
    tot_pazienti = len(st.session_state.db.get("pazienti", []))
    
    # Generazione dei riquadri visivi (i vecchi incassi sono spariti)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="👥 Totale Pazienti in Anagrafica", value=tot_pazienti)
    with c2:
        st.metric(label="📅 Appuntamenti Fissati Oggi", value=totale_oggi)
    with c3:
        st.metric(label="🚨 Urgenze del Giorno", value=urgenze_oggi, delta="Attenzione!" if urgenze_oggi > 0 else None)

    st.divider()
    st.subheader("📅 Appuntamenti in Agenda per Oggi")
    oggi = datetime.now().strftime("%d/%m/%Y")
    
    # LEGGE DALLA CHIAVE CORRETTA
    lista_appuntamenti = st.session_state.db.get("appuntamenti", [])
    appuntamenti_oggi = [a for a in lista_appuntamenti if a.get('Data') == oggi]
    
    if appuntamenti_oggi:
        appuntamenti_oggi.sort(key=lambda x: x.get('Ora', '00:00'))
        for a in appuntamenti_oggi:
            with st.expander(f"🕒 {a['Ora']} - {a['Paziente']}"):
                st.write(f"**Prestazione:** {a.get('Prestazione', 'Non specificata')}")
                st.write(f"**Medico:** {a.get('Medico', 'Non specificato')}")
    else:
        st.info("🤷‍♂️ Non ci sono appuntamenti fissati per la giornata di oggi.")

    st.markdown("---")
    st.markdown('<p style="color:#003366; font-size:14px; font-weight:bold;">Studio Odontoiatrico GA.MA. SRL - Via XX Settembre, 7 - Battipaglia (SA) - Direttore Sanitario Dott. Stefano Pio Gammella</p>', unsafe_allow_html=True)
    st.caption("Software CORE ENGINE BY Sergio Mirra")

# --- 2. ANAGRAFICA PAZIENTI ---
elif menu == "👥 Anagrafica Pazienti":
    st.header("Gestione Paziente Completa")
    tab1, tab2 = st.tabs(["🔍 Cerca e Modifica", "🆕 Nuovo Paziente"])
    
    with tab1:
        search = st.text_input("Cerca per Nome o Cognome:").upper()
        
        # CONTROLLO BLOCO VUOTO: Se l'utente non digita nulla, non esegue il rendering di massa
        if not search:
            st.info("💡 Digita il nome o il cognome del paziente nel campo sopra per accedere alla sua scheda clinica.")
        else:
            # RIGHE CORRETTE E POTENZIATE PER IL MATCH PERFETTO
            paz_filtrati = [p for p in st.session_state.db["pazienti"] if search.strip() in str(p['Nome']).upper().strip()]
            
            if paz_filtrati:
                scelta = st.selectbox("Seleziona:", [p['Nome'] for p in paz_filtrati])
                idx = next(i for i, p in enumerate(st.session_state.db["pazienti"]) if p['Nome'] == scelta)
                p = st.session_state.db["pazienti"][idx]
                
                if p.get('Allergie') and p['Allergie'].strip():
                    st.error(f"⚠️ **ATTENZIONE ALLERGIE/NOTE CRITICHE:** {p['Allergie'].upper()}")
                
                sub1, sub2, sub3, sub4 = st.tabs(["📝 Anagrafica", "🦷 Odontogramma", "💰 Pagamenti", "📖 Diario Clinico"])
                
                with sub1:
                    with st.form(f"edit_{idx}"):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        n_n = c1.text_input("Nome e Cognome", p['Nome']).upper()
                        n_cf = c2.text_input("Codice Fiscale", p.get('CF','')).upper()
                        n_tl = c3.text_input("Telefono", p.get('Tel',''))
                        
                        ca, cb, cc = st.columns([3, 2, 1])
                        n_v = ca.text_input("Indirizzo", p.get('Via','')).upper()
                        n_ct = cb.text_input("Città", p.get('Citta','')).upper()
                        n_pr = cc.text_input("Provincia", p.get('Provincia','')).upper()
                        
                        n_al = st.text_input("⚠️ ALLERGIE", p.get('Allergie','')).upper()
                        n_nt = st.text_area("Anamnesi Iniziale", p.get('Note_Cliniche',''))
                        
                        if st.form_submit_button("AGGIORNA DATI", width="stretch"):
                            st.session_state.db["pazienti"][idx].update({
                                "Nome": n_n, "CF": n_cf, "Tel": n_tl, 
                                "Via": n_v, "Citta": n_ct, "Provincia": n_pr, 
                                "Allergie": n_al, "Note_Cliniche": n_nt
                            })
                            salva_dati(st.session_state.db)
                            
                            # Mostra la rotellina di caricamento durante l'attesa
                            with st.spinner("Salvataggio in corso..."):
                                # Mostra il banner verde di conferma
                                st.success("✅ Dati Aggiornati con Successo!")
                                
                                # Mantiene lo schermo congelato per i tuoi 3.5 secondi
                                import time
                                time.sleep(3.5)
                            
                            # Esegue il rinfresco pulito della pagina
                            st.rerun()
                with sub2:
                    st.info("💡 **LEGENDA ODONTOGRAMMA:**")
                    cl1, cl2, cl3, cl4, cl5, cl6, cl7, cl8 = st.columns(8)
                    
                    cl1.markdown("<div style='font-size:13px;'>⬜ <b>Sano</b></div>", unsafe_allow_html=True)
                    cl2.markdown("<div style='font-size:13px;'>🔴 <b>Carie</b></div>", unsafe_allow_html=True)
                    cl3.markdown("<div style='font-size:13px;'>🟡 <b>Otturazione</b></div>", unsafe_allow_html=True)
                    cl4.markdown("<div style='font-size:13px;'>🔵 <b>Impianto</b></div>", unsafe_allow_html=True)
                    cl5.markdown("<div style='font-size:13px;'>❌ <b>Estratto</b></div>", unsafe_allow_html=True)
                    cl6.markdown("<div style='font-size:13px;'>🟢 <b>Protesi</b></div>", unsafe_allow_html=True)
                    cl7.markdown("<div style='font-size:13px;'>🟠 <b>Endodonzia</b></div>", unsafe_allow_html=True)
                    cl8.markdown("<div style='font-size:13px;'>🟣 <b>Corona</b></div>", unsafe_allow_html=True)
                    st.divider()
                    
                    st.write("") 
                    st.image("odontogramma.png", width="stretch")
                    st.write("") 
                    
                    ati = {"Sano": "⬜", "Carie": "🔴", "Otturazione": "🟡", "Impianto": "🔵", "Estratto": "❌", "Protesi": "🟢", "Endodonzia": "🟠", "Corona": "🟣"}
                    
                    def m_arc(denti, key_p):
                        p_dent = st.session_state.db["pazienti"][key_p]
                        cols = st.columns(len(denti))
                        for i, d in enumerate(denti):
                            d_s = str(d)
                            attuale = p_dent.get("Odontogramma", {}).get(d_s, "Sano")
                            with cols[i]:
                                nuovo = st.selectbox(
                                    f"{d_s}", 
                                    list(ati.keys()), 
                                    index=list(ati.keys()).index(attuale), 
                                    key=f"d_{key_p}_{d_s}", 
                                    label_visibility="visible"
                                )
                                
                                if nuovo != attuale:
                                    if "Odontogramma" not in p_dent: p_dent["Odontogramma"] = {}
                                    p_dent["Odontogramma"][d_s] = nuovo
                                    
                                    from datetime import datetime
                                    data_oggi = datetime.now().strftime("%d/%m/%Y")
                                    ora_oggi = datetime.now().strftime("%H:%M")
                                    
                                    nueva_nota = {
                                        "Data": data_oggi,
                                        "Lavoro": f"AGGIORNAMENTO ODONTOGRAMMA: DENTE {d_s}",
                                        "Note": f"Stato modificato alle ore {ora_oggi}. Da '{attuale}' a '{nuovo}'."
                                    }
                                    
                                    if "Diario" not in p_dent: 
                                        p_dent["Diario"] = []
                                    p_dent["Diario"].insert(0, nueva_nota)
                                    
                                    salva_dati(st.session_state.db)
                                    st.rerun()
                                    
                                st.markdown(f"<span style='font-size:20px'>{ati[nuovo]}</span></div>", unsafe_allow_html=True)
                                            
                    st.write("**Arcata Superiore**")
                    m_arc([18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28], idx)
                    st.write("**Arcata Inferiore**")
                    m_arc([48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38], idx)            
                
                with sub3:
                    st.subheader("Pagamenti Ricevuti")
                    with st.form(f"paga_{idx}"):
                        cp1, cp2 = st.columns(2)
                        monto = cp1.number_input("Somma Versata (€)", min_value=0.00)
                        data_p = cp2.date_input("Data Pagamento", format="DD/MM/YYYY")
                        if st.form_submit_button("REGISTRA", width="stretch"):
                            if "Pagamenti" not in st.session_state.db["pazienti"][idx]: st.session_state.db["pazienti"][idx]["Pagamenti"] = []
                            st.session_state.db["pazienti"][idx]["Pagamenti"].append({
                                "Data": data_p.strftime("%d/%m/%Y"), 
                                "Importo": f"{monto:.2f}"
                            })
                            salva_dati(st.session_state.db)
                            st.success("Pagamento registrato!")
                            st.rerun()
                    
                    if p.get("Pagamenti"):
                        st.write("---")
                        for i_pag, pag_singolo in enumerate(p["Pagamenti"]):
                            c_p1, c_p2, c_p3 = st.columns([2, 2, 2])
                            c_p1.write(f"📅 {pag_singolo['Data']}")
                            c_p2.write(f"💰 **{format_it(pag_singolo['Importo'])}**")
                            
                            desc_pag = pag_singolo.get('Descrizione', 'Acconto/Saldo prestazione odontoiatrica')
                            pdf_ricevuta = genera_ricevuta_pdf(p['Nome'], pag_singolo['Data'], pag_singolo['Importo'], desc_pag)
                            
                            if pdf_ricevuta is not None:
                                c_p3.download_button(
                                    label="📄 Ricevuta",
                                    data=pdf_ricevuta,
                                    file_name=f"Ricevuta_{p['Nome']}_{pag_singolo['Data'].replace('/','-')}.pdf",
                                    mime="application/pdf",
                                    key=f"btn_pdf_{idx}_{i_pag}",
                                    width="stretch"
                                )
                        
                        tot_v = sum(float(it['Importo']) for it in p["Pagamenti"])
                        st.info(f"**TOTALE VERSATO: {format_it(tot_v)}**")
                
                with sub4:
                    st.subheader("Registro Lavori Eseguiti")
                    
                    with st.form(f"diario_{idx}"):
                        cd1, cd2 = st.columns([1, 3])
                        data_l = cd1.date_input("Data Lavoro", format="DD/MM/YYYY")
                        lavoro = cd2.text_input("Descrizione Lavoro (es. Estrazione dente 46)").upper()
                        note_l = st.text_area("Dettagli Tecnici / Materiali Usati")
                        
                        if st.form_submit_button("AGGIUNGI AL DIARIO CLINICO", width="stretch"):
                            if "Diario" not in st.session_state.db["pazienti"][idx]: 
                                st.session_state.db["pazienti"][idx]["Diario"] = []
                            st.session_state.db["pazienti"][idx]["Diario"].insert(0, {
                                "Data": data_l.strftime("%d/%m/%Y"),
                                "Lavoro": lavoro,
                                "Note": note_l
                            })
                            salva_dati(st.session_state.db)
                            st.success("Diario aggiornato!")
                            st.rerun()
                            
                    if p.get("Diario"):
                        st.write("---")
                        for i_nota, l in enumerate(p["Diario"]):
                            with st.expander(f"📅 {l['Data']} - {l['Lavoro']}"):
                                st.write(f"**Dettagli:** {l['Note']}")
                                
                                chiave_lavoro = f"del_diario_{idx}_{l['Data']}_{l['Lavoro']}_{i_nota}".replace(" ", "_").replace("/", "_").replace(":", "_")
                                st.write("") 
                                
                                if st.button("🗑️ Elimina Voce", key=chiave_lavoro, width="stretch"):
                                    st.session_state.db["pazienti"][idx]["Diario"].remove(l)
                                    salva_dati(st.session_state.db)
                                    st.rerun()
            else:
                st.warning("❌ Nessun paziente trovato con questo nome.")

    with tab2:
        st.subheader("Registrazione Nuovo Paziente")
        with st.form("n_p", clear_on_submit=True):
            c_n1, c_n2 = st.columns([2, 1])
            nn = c_n1.text_input("NOME COMPLETO *").upper().strip()
            ncf = c_n2.text_input("CODICE FISCALE").upper().strip()
            
            c_i1, c_i2, c_i3 = st.columns([2, 1, 1])
            nvia = c_i1.text_input("INDIRIZZO").upper().strip()
            nct = c_i2.text_input("CITTÀ").upper().strip()
            npr = c_i3.text_input("PROVINCIA", max_chars=2).upper().strip()
            
            ntl = st.text_input("TELEFONO")
            
            if st.form_submit_button("REGISTRA PAZIENTE", width="stretch"):
                if nn:
                    st.session_state.db["pazienti"].append({
                        "Nome": nn,
                        "CF": ncf,
                        "Via": nvia,
                        "Citta": nct,
                        "Provincia": npr,
                        "Tel": ntl,
                        "Odontogramma": {},
                        "Pagamenti": [],
                        "Diario": [],
                        "Allergie": "",
                        "Note_Cliniche": ""
                    })
                    salva_dati(st.session_state.db)
                    
                    with st.spinner("Creazione anagrafica in corso..."):
                        st.success(f"✅ Paziente {nn} registrato correttamente!")
                        import time
                        time.sleep(3.5)
                    
                    st.rerun()
                else:
                    st.error("Il campo Nome è Cognome è obbligatorio.")
                   
# --- 3. AGENDA APPUNTAMENTI ---
elif menu == "📅 Agenda Appuntamenti":
    st.header("Agenda Giornaliera")
    d_obj = st.date_input("Seleziona Giorno:", format="DD/MM/YYYY")
    d_sel = d_obj.strftime("%d/%m/%Y")
    apps = [a for a in st.session_state.db["appuntamenti"] if a['Data'] == d_sel]
    if apps:
        for i, a in enumerate(apps):
            with st.expander(f"{a['Ora']} - {applica_colore(a['Paziente'])}"):
                c1, c2, c3 = st.columns([2,1,1])
                c1.write(f"Medico: {a['Medico']} | Importo: {format_it(a['Importo'])}")
                nome_p = a['Paziente'].split(" [")[0].strip()
                paz_obj = next((p for p in st.session_state.db['pazienti'] if p['Nome'] == nome_p), None)
                tel = paz_obj.get('Tel','') if paz_obj else ""
                allergie_p = paz_obj.get('Allergie','') if paz_obj else ""
                
                if allergie_p:
                    st.warning(f"⚠️ **NOTA CLINICA:** {allergie_p.upper()}")
                
                if tel:
                    msg = urllib.parse.quote(f"Studio Ga.Ma.: Le ricordiamo l'appuntamento del {a['Data']} alle ore {a['Ora']}")
                    c2.link_button("💬 WhatsApp", f"https://wa.me/{pulisci_numero_wa(tel)}?text={msg}", width="stretch")
                
                # Generiamo la chiave unica senza toccare la logica
                chiave_unica_del = f"del_{a['Data']}_{a['Ora']}_{a['Paziente']}".replace(" ", "_").replace("/", "_")
                
                # Pulsante di eliminazione sicuro (Alineato a c3 come nel tuo codice)
                if c3.button("🗑️ Elimina", key=chiave_unica_del, width="stretch"):
                    st.session_state.db["appuntamenti"].remove(a)
                    salva_dati(st.session_state.db)
                    st.rerun()

# --- 4. GESTIONE INCASSI ---
elif menu == "💰 Gestione Incassi":
    st.header("Resoconto Incassi e Versamenti")
    t_inc1, t_inc2 = st.tabs(["📅 Per Periodo (Appuntamenti)", "👤 Per Paziente (Storico Versamenti)"])
    
    with t_inc1:
        c1, c2 = st.columns(2)
        da = c1.date_input("Dal:", format="DD/MM/YYYY")
        af = c2.date_input("Al:", format="DD/MM/YYYY")
        v = [a for a in st.session_state.db["appuntamenti"] if da <= datetime.strptime(a['Data'], "%d/%m/%Y").date() <= af]
        if v:
            tot_p = sum(float(x.get('Importo', 0)) for x in v)
            st.metric("TOTALE PREVISTO DA APPUNTAMENTI", format_it(tot_p))
            df_v = pd.DataFrame(v)
            df_v['Importo'] = df_v['Importo'].apply(format_it)
            st.table(df_v[['Data', 'Paziente', 'Importo']])
        else:
            st.info("Nessun appuntamento nel periodo selezionato.")

    with t_inc2:
        st.subheader("Cerca storico pagamenti di un paziente")
        nome_cerca = st.text_input("Inserisci nome paziente:", key="cerca_paz_incassi").upper()
        p_tot = []
        
        # =========================================================================
        # GESTIONE PREVENTIVO E SALDO DELLA FASE 4 (ALLINEAMENTO CORRETTO)
        # =========================================================================
        paziente_trovato = None
        if nome_cerca:
            for p in st.session_state.db["pazienti"]:
                if nome_cerca in p['Nome'].upper():
                    paziente_trovato = p
                    break
            
            if paziente_trovato:
                # Recuperiamo il preventivo attuale se esiste, altrimenti impostiamo 0.0
                prev_attuale = float(paziente_trovato.get("Preventivo", 0.0))
                
                # Mostriamo il campo numerico per inserire o modificare il preventivo
                nuovo_prev = st.number_input(
                    f"💰 Preventivo Concordato per {paziente_trovato['Nome']}:", 
                    value=prev_attuale, 
                    step=50.0,
                    format="%.2f",
                    key=f"prev_{paziente_trovato['Nome']}"
                )
                
                # Se il valore cambia, lo salviamo direttamente nel database
                if nuovo_prev != prev_attuale:
                    paziente_trovato["Preventivo"] = str(nuovo_prev)  # Forza il salvataggio in formato testo pulito
                    if hasattr(st.session_state.db, "save"):
                        st.session_state.db.save()
                    st.rerun()  # Forza Streamlit a ricaricare i dati aggiornati nel widget
       
            if paziente_trovato and paziente_trovato.get("Pagamenti"):
                for pag in paziente_trovato["Pagamenti"]:
                    p_tot.append({"Paziente": paziente_trovato['Nome'], "Data": pag['Data'], "Importo": pag['Importo']})
                    
        if p_tot:
            df_storico = pd.DataFrame(p_tot)
            tot_v = sum(float(p['Importo']) for p in p_tot)
            
            # Mostriamo il totale versato che avevi già
            st.metric(f"TOTALE VERSATO", format_it(tot_v))
            
            # Mostra il saldo rimanente sotto la metrica del versato
            if paziente_trovato:
                preventivo_totale = float(paziente_trovato.get("Preventivo", 0.0))
                saldo_rimanente = preventivo_totale - tot_v
                
                if saldo_rimanente > 0:
                    st.metric("🔴 SALDO DA PAGARE", format_it(saldo_rimanente))
                elif preventivo_totale > 0 and saldo_rimanente <= 0:
                    st.success(f"🎉 Trattamento completamente Saldato! (Saldo: {format_it(saldo_rimanente)})")
            
            df_storico['Importo'] = df_storico['Importo'].apply(format_it)
            st.dataframe(df_storico.sort_values(by="Data", ascending=False), width="stretch")
        else:
            st.warning("Nessun versamento trovato.")

# --- 5. STATISTICHE E RICHIAMI ---
elif menu == "📊 Statistiche e Richiami":
    st.header("Analisi e Richiami Igiene")
    t1, t2 = st.tabs(["📈 Report Medici", "📞 Lista Richiami"])
    with t1:
        st.subheader("📊 Analisi Finanziaria")
        st.markdown("### 💰 Incassi Effettivi (Versamenti)")
        
        # 1. Recupero dei versamenti reali
        dati_p = []
        for p in st.session_state.db["pazienti"]:
            if p.get("Pagamenti"):
                for pag in p["Pagamenti"]:
                    val_p = str(pag['Importo']).replace('€', '').replace(' ', '').replace(',', '.')
                    try: imp_f = float(val_p)
                    except: imp_f = 0.0
                    dati_p.append({"Importo": imp_f, "Data": pag['Data']})
        
        if dati_p:
            df_r = pd.DataFrame(dati_p)
            tot_incassato_reale = df_r['Importo'].sum()
            
            tot_preventivi_emessi = 0.0
            pazienti_sospesi = []
            
            # 2. Calcolo preventivi e saldi reali per ciascun paziente
            for p in st.session_state.db["pazienti"]:
                raw_prev = str(p.get("Preventivo", "0.0")).replace('€', '').replace(' ', '').replace(',', '.')
                try:
                    prev_paziente = float(raw_prev)
                except:
                    prev_paziente = 0.0
                
                tot_preventivi_emessi += prev_paziente
                
                versato_singolo = 0.0
                if p.get("Pagamenti"):
                    for pag in p["Pagamenti"]:
                        val_singolo = str(pag['Importo']).replace('€', '').replace(' ', '').replace(',', '.')
                        try: versato_singolo += float(val_singolo)
                        except: pass
                
                saldo_paziente = prev_paziente - versato_singolo
                if saldo_paziente > 0:
                    pazienti_sospesi.append({
                        "Paziente": p.get("Nome", "N/D"),
                        "Preventivo": format_it(prev_paziente),
                        "Totale Versato": format_it(versato_singolo),
                        "Saldo Rimanente": format_it(saldo_paziente),
                        "_raw_saldo": saldo_paziente
                    })

            # 3. Visualizzazione metriche (3 colonne)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("TOTALE INCASSATO REALE", format_it(tot_incassato_reale))
            with c2:
                st.metric("📊 VOLUME PREVENTIVI", format_it(tot_preventivi_emessi))
            with c3:
                da_riscuotere = tot_preventivi_emessi - tot_incassato_reale
                st.metric("🔴 TOTALE DA RISCUOTERE", format_it(max(0.0, da_riscuotere)))
                
            st.divider()
            
            # Tabella delle posizioni aperte (Ora con l'allineamento perfetto)
            st.markdown("### 📋 Situazione Debiti Pazienti (Posizioni Aperte)")
            if pazienti_sospesi:
                df_sospesi = pd.DataFrame(pazienti_sospesi)
                df_sospesi = df_sospesi.sort_values(by="_raw_saldo", ascending=False).drop(columns=["_raw_saldo"])
                st.dataframe(df_sospesi, width="stretch")
            else:
                st.success("🎉 Fantastico! Tutti i pazienti hanno saldato i loro trattamenti.")
        else:
            st.info("Nessun versamento reale registrato.")
            
        st.divider()
        # =========================================================================
        st.markdown("### 📅 Previsione da Agenda")
        if st.session_state.db["appuntamenti"]:
            df_app = pd.DataFrame(st.session_state.db["appuntamenti"])
            df_app['Imp_Num'] = df_app['Importo'].apply(lambda x: str(x).replace('€','').replace(',','.')).astype(float)
            report_m = df_app.groupby('Medico')['Imp_Num'].sum()
            st.bar_chart(report_m)
            st.caption("Fatturato previsto per Medico.")

    # =========================================================================
    # RIGHE COINVOLTE: DA RIGA 604 IN POI (SOSTITUISCI IL VECCHIO "with t2:")
    # =========================================================================
    with t2:
        st.subheader("📆 Pazienti da richiamare (Oltre 6 mesi)")
        lista_r = get_richiami_igiene(st.session_state.db)
        
        # --- FASE 3: MESSAGGIO PERSONALIZZABILE PER LA SEGRETERIA ---
        st.markdown("### 📱 Personalizza Messaggio WhatsApp")
        
        msg_predefinito = "Gentile paziente, lo Studio Dentistico Ga.Ma. le ricorda che sono passati 6 mesi dall'ultima igiene orale. La invitiamo a contattarci per fissare il prossimo appuntamento di controllo. Saluti!"
        
        testo_whatsapp = st.text_area(
            "Testo del promemoria da inviare:", 
            value=msg_predefinito, 
            height=110,
            key="txt_richiamo_igiene"
        )
        st.divider()
        
        # Struttura di controllo e ciclo pazienti correttamente allineati
        if lista_r:
            for paz in lista_r:
                nome_paz = paz.get('Nome', 'Paziente')
                telefono = paz.get('Telefono', '')
                
                # Pulizia e formattazione del numero per WhatsApp
                tel_pulito = "".join(filter(str.isdigit, str(telefono)))
                if tel_pulito and not tel_pulito.startswith("39") and len(tel_pulito) == 10:
                    tel_pulito = "39" + tel_pulito
                
                import urllib.parse
                testo_url = urllib.parse.quote(testo_whatsapp)
                link_wa = f"https://wa.me/{tel_pulito}?text={testo_url}"
                
                # Layout visivo per la segretaria
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"👤 **{nome_paz}** - Tel: {telefono}")
                with col2:
                    if tel_pulito:
                        st.markdown(f'📱 [Invia WhatsApp]({link_wa})', unsafe_allow_html=True)
                    else:
                        st.caption("❌ No Tel")
        else:
            st.success("🎉 Tutti i pazienti in regola!")

# --- 6. STAMPA AGENDA ---
elif menu == "🖨️ Stampa Agenda":
    st.header("Esporta Agenda PDF")
    dt_obj = st.date_input("Scegli data:", format="DD/MM/YYYY")
    dt_stampa = dt_obj.strftime("%d/%m/%Y")
    m_list = ["TUTTI"] + [f"{m['Nome']} {m['Cognome']}" for m in st.session_state.db.get("medici", [])]
    filtro_m = st.selectbox("Seleziona Medico:", m_list)
    lista_stampa = [a for a in st.session_state.db["appuntamenti"] if a['Data'] == dt_stampa]
    if filtro_m != "TUTTI":
        lista_stampa = [a for a in lista_stampa if a['Medico'] == filtro_m]
    if lista_stampa:
        df_stampa = pd.DataFrame(lista_stampa)[['Ora', 'Paziente', 'Medico']].sort_values(by='Ora')
        st.table(df_stampa)
        try:
            pdf_data = esporta_pdf(df_stampa, dt_stampa, filtro_m)
            st.download_button("📄 SCARICA AGENDA IN PDF", pdf_data, f"Agenda_{dt_stampa}.pdf", "application/pdf", width="stretch")
        except: st.error("Errore generazione PDF")
    else: st.warning("Nessun appuntamento.")

# --- 7. CRONOLOGIA ---
elif menu == "🔍 Cronologia Appuntamenti":
    st.header("Ricerca Storico")
    q = st.text_input("Inserisci nome:").upper()
    if st.session_state.db["appuntamenti"]:
        df_h = pd.DataFrame(st.session_state.db["appuntamenti"])
        ris = df_h[df_h['Paziente'].str.contains(q, na=False, case=False)]
        if not ris.empty: st.dataframe(ris.sort_values(by='Data', ascending=False), width="stretch")
        else: st.info("Nessun riscontro.")

# --- 8. NUOVA PRENOTAZIONE ---
elif menu == "📝 Nuova Prenotazione":
    st.header("Registra Appuntamento")
    
    # Prepariamo le liste di opzioni da usare nei menu a discesa
    med_opts = [f"{m['Nome']} {m['Cognome']}" for m in st.session_state.db.get("medici", [])]
    if not med_opts:
        med_opts = ["Dott. Stefano Pio Gammella"]
        
    p_list = sorted([p['Nome'] for p in st.session_state.db["pazienti"]])
    
    # Generazione della griglia oraria di base dello studio (ogni 15 minuti)
    orari_base = []
    start_ora = datetime.strptime("08:30", "%H:%M")
    end_ora = datetime.strptime("19:30", "%H:%M")
    while start_ora <= end_ora:
        orari_base.append(start_ora.strftime("%H:%M"))
        start_ora += timedelta(minutes=15)

    # UNICO FORM: Racchiude tutte le scelte per evitare ricaricamenti fastidiosi
    with st.form("f_p_nuovo_unico"):
        p_sel = st.selectbox("Paziente", ["---"] + p_list)
        
        c_med, c_data = st.columns(2)
        with c_med:
            med_sel = st.selectbox("Seleziona Medico", med_opts)
        with c_data:
            data_app = st.date_input("Seleziona Data Appuntamento:", format="DD/MM/YYYY")
            data_str = data_app.strftime("%d/%m/%Y")
            
        c_dur, c_ora = st.columns(2)
        with c_dur:
            durata_sel = st.selectbox(
                "Durata Appuntamento", 
                ["15 Minuti", "30 Minuti", "60 Minuti (1h)", "90 Minuti (1.5h)", "120 Minuti (2h)"],
                index=1  # Default su 30 Minuti
            )
            minuti_durata = int(durata_sel.split()[0])
            
        with c_ora:
            # Inseriamo tutti gli orari base. Il controllo reale sulle sovrapposizioni 
            # e sugli slot occupati viene fatto istantaneamente al click del tasto d'invio.
            ora_sel = st.selectbox("Orario Inizio Appuntamento", orari_base)
            
        tipo = st.selectbox("Prestazione", ["Visita [VIS]", "Urgenza [URG]", "Igiene [IG]", "Protesi [PRO]", "Ortodonzia [ORT]"])
        importo = st.number_input("Importo Stimato (€)", min_value=0.0, step=10.0)
        nota_app = st.text_input("Note Aggiuntive Appuntamento")
        
        invia_btn = st.form_submit_button("REGISTRA APPUNTAMENTO", width="stretch")
        
        if invia_btn:
            if p_sel == "---":
                st.error("❌ Errore: Seleziona un paziente valido!")
            else:
                # 1. Calcoliamo la catena di slot da 15 minuti richiesti dalla NUOVA prenotazione
                slot_nuovi_richiesti = []
                try:
                    ora_scelta_dt = datetime.strptime(ora_sel, "%H:%M")
                    for m in range(0, minuti_durata, 15):
                        slot_acc = (ora_scelta_dt + timedelta(minutes=m)).strftime("%H:%M")
                        slot_nuovi_richiesti.append(slot_acc)
                except Exception as e:
                    st.error(f"Errore formato orario: {e}")
                    slot_nuovi_richiesti = [ora_sel]

                # 2. Ricostruiamo la mappa di tutti i minuti già occupati nel database per quel medico in quel giorno
                orari_occupati_dal_db = set()
                appuntamenti_salvati = st.session_state.db.get("appuntamenti", [])
                
                for a in appuntamenti_salvati:
                    if a.get("Data") == data_str and a.get("Medico") == med_sel:
                        ora_inizio_str = a.get("Ora")
                        durata_prec = int(a.get("Durata", 30)) # Default 30 min se vecchio record senza durata
                        
                        try:
                            ora_ini = datetime.strptime(ora_inizio_str, "%H:%M")
                            for m in range(0, durata_prec, 15):
                                s_occupato = (ora_ini + timedelta(minutes=m)).strftime("%H:%M")
                                orari_occupati_dal_db.add(s_occupato)
                        except:
                            orari_occupati_dal_db.add(ora_inizio_str)
                
                # 3. Controllo incrociato: vediamo se uno qualsiasi dei nuovi slot va a collidere con l'occupato
                collisione = any(slot in orari_occupati_dal_db for slot in slot_nuovi_richiesti)
                
                if collisione:
                    st.error(f"⚠️ ORARIO OCCUPATO O IN SOVRAPPOSIZIONE! Il {data_str} a partire dalle ore {ora_sel}, il {med_sel} non ha a disposizione i {durata_sel} richiesti perché occupato da un altro appuntamento.")
                else:
                    # Nessuna collisione: procediamo al salvataggio definitivo
                    tag_prestazione = tipo.split("[")[-1].replace("]", "")
                    nome_paziente_con_tag = f"{p_sel} [{tag_prestazione}]"
                    
                    nuovo_app = {
                        "Paziente": nome_paziente_con_tag,
                        "Data": data_str,
                        "Ora": ora_sel,
                        "Durata": minuti_durata,
                        "Prestazione": tipo,
                        "Medico": med_sel,
                        "Importo": str(importo),
                        "Note": nota_app
                    }
                    
                    if "appuntamenti" not in st.session_state.db:
                        st.session_state.db["appuntamenti"] = []
                        
                    st.session_state.db["appuntamenti"].append(nuovo_app)
                    salva_dati(st.session_state.db)
                    
                    # Messaggio di conferma solido e persistente a video
                    st.success(f"🎉 Appuntamento registrato correttamente per {p_sel}! Salvato il {data_str} alle ore {ora_sel} con una durata bloccata di {durata_sel}.")
# --- 9. GESTIONE MEDICI ---
elif menu == "👨‍⚕️ Gestione Medici":
    st.header("Staff Medico")
    
    # --- FORM PER AGGIUNGERE ---
    with st.form("doc", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("Nome").upper().strip()
        c = c2.text_input("Cognome").upper().strip()
        s = c3.text_input("Specializzazione").upper().strip()
        
        if st.form_submit_button("Aggiungi Medico", width="stretch"):
            if n and c:
                st.session_state.db["medici"].append({
                    "Nome": n, 
                    "Cognome": c, 
                    "Specializzazione": s if s else "ODONTOIATRA"
                })
                salva_dati(st.session_state.db)
                st.success(f"Medico {n} {c} aggiunto!")
                st.rerun()

    st.divider()

    # --- LISTA CON TASTO ELIMINA ---
    if st.session_state.db.get("medici"):
        st.subheader("Medici in organico")
        for i, m in enumerate(st.session_state.db["medici"]):
            col_info, col_del = st.columns([4, 1])
            
            # Mostra Nome, Cognome e Specializzazione
            spec = m.get('Specializzazione', 'ODONTOIATRA')
            col_info.write(f"👨‍⚕️ **{m['Nome']} {m['Cognome']}** - *{spec}*")
            
            # Tasto elimina
            if col_del.button("Elimina", key=f"del_med_{i}", width="stretch"):
                st.session_state.db["medici"].pop(i)
                salva_dati(st.session_state.db)
                st.rerun()
    else:
        st.info("Nessun medico registrato al momento.")
# =========================================================
# SCHEDA FATTURA SANITARIA - CON DETTAGLIO IVA E BOLLO
# =========================================================

# =========================================================
# SCHEDA FATTURA SANITARIA - CON DETTAGLIO IVA E BOLLO
# =========================================================

elif menu == "📄 Fattura Sanitaria":
    st.header("Emissione Fattura Sanitaria")
    
    # =========================================================================
    # AGGIUNTA: CONTATORE ED ALERT ULTIMO NUMERO FATTURA (SOLO IN AGGIUNTA)
    # =========================================================================
    lista_fatture_esistenti = st.session_state.db.get("fatture", [])
    totale_fatture_archivio = len(lista_fatture_esistenti)
    
    if totale_fatture_archivio > 0:
        ultima_fattura_num = lista_fatture_esistenti[-1].get("numero", "N/D")
        st.info(f"📁 **Archivio Fatture:** In archivio sono presenti **{totale_fatture_archivio}** fatture. | ⚠️ **Ultimo numero inserito:** `{ultima_fattura_num}`")
    else:
        st.info("📁 **Archivio Fatture:** L'archivio è attualmente vuoto. Nessuna fattura emessa.")
    # =========================================================================
    
    nomi_p = [p['Nome'] for p in st.session_state.db["pazienti"]]
    p_scelto = st.selectbox("Seleziona Paziente", ["---"] + nomi_p)
    
    if p_scelto != "---":
        p_dati = next(p for p in st.session_state.db["pazienti"] if p['Nome'] == p_scelto)
        
        if 'pdf_sanitario' not in st.session_state:
            st.session_state.pdf_sanitario = None
            st.session_state.nome_file_sanitario = ""

        with st.form("form_sanitaria_iva_tabella"):
            c1, c2 = st.columns(2)
            n_fatt = c1.text_input("Numero Fattura", "01/2026")
            d_fatt = c2.date_input("Data Fattura")
            
            st.divider()
            desc_fatt = st.text_area("Descrizione Prestazione", "Cure Odontoiatriche Specialistiche")
            
            col_imp, col_pag = st.columns(2)
            importo_base = col_imp.number_input("Importo Prestazione (€)", min_value=0.0, step=50.0)
            metodo_pagamento = col_pag.selectbox(
                "Metodo di Pagamento", 
                ["Contanti", "Carta di Credito/Debito", "Bonifico Bancario", "Assegno"]
            )
            
            st.divider()
            clicca_genera = st.form_submit_button("1. GENERA FATTURA")
            
            if clicca_genera:
                ha_bollo = importo_base > 77.47
                valore_bollo = 2.0 if ha_bollo else 0.0
                totale_complessivo = importo_base + valore_bollo
                
            # 1. Controlliamo se esiste il cassetto delle fatture nel database
                if "fatture" not in st.session_state.db:
                    st.session_state.db["fatture"] = []
                
                # 2. Impacchettiamo i dati della fattura corrente
                dati_da_salvare = {
                    "numero": n_fatt,
                    "data": str(d_fatt),
                    "paziente": p_scelto,
                    "importo": importo_base,
                    "metodo_pagamento": metodo_pagamento,
                    "totale": totale_complessivo
                }
                
                # 3. Controlliamo se la fattura esiste già per evitare doppioni
                esiste_gia = any(f["numero"] == n_fatt for f in st.session_state.db["fatture"])
                
                # 4. Se non esiste, la salviamo nel file JSON
                if not esiste_gia:
                    st.session_state.db["fatture"].append(dati_da_salvare)
                    salva_dati(st.session_state.db)  # La tua funzione originale
                    st.success(f"Fattura {n_fatt} salvata nell'archivio storico!")
                # --- FINE DEL CODICE DI SALVATAGGIO ---
                
                # Da qui in poi continua il tuo codice originale per creare il PDF...
                txt_base = format_it(importo_base).replace("€", "Euro")
                
                # ==========================================
                # NUOVO PASSO: SALVATAGGIO NEL DATABASE JSON
                # ==========================================
                
                # 1. Controlliamo se nel database esiste la chiave "fatture". Se non c'è, la creiamo.
                if "fatture" not in st.session_state.db:
                    st.session_state.db["fatture"] = []
                
                # 2. Prepariamo i dati della fattura corrente
                dati_da_salvare = {
                    "numero": n_fatt,
                    "data": str(d_fatt),
                    "paziente": p_scelto,
                    "importo": importo_base,
                    "metodo_pagamento": metodo_pagamento,
                    "totale": totale_complessivo
                }
                
                # 3. Controlliamo se questa fattura (stesso numero) è già stata salvata,
                # per evitare di duplicarla se l'utente clicca due volte sul pulsante.
                esiste_gia = any(f["numero"] == n_fatt for f in st.session_state.db["fatture"])
                
                if not esiste_gia:
                    # Aggiungiamo la nuova fattura alla lista in memoria
                    st.session_state.db["fatture"].append(dati_da_salvare)
                    # Chiamiamo la tua funzione (es. salva_db) per scrivere sul file db_studio.json
                    salva_dati(st.session_state.db) # Assicurati che il nome della tua funzione di salvataggio sia questo
                    st.success(f"Fattura {n_fatt} salvata nell'archivio storico!")
                
                # Formattazione per PDF senza caratteri speciali
                txt_base = format_it(importo_base).replace("€", "Euro")
                txt_bollo = format_it(valore_bollo).replace("€", "Euro")
                txt_iva_zero = "0,00 Euro"
                txt_totale = format_it(totale_complessivo).replace("€", "Euro")
                
                desc_fatt_pulita = desc_fatt.replace("€", "Euro")
                
                # --- QUI VIENE CREATO IL PDF ---
                f_pdf = FPDF()
                f_pdf.add_page()
                
                # INTESTAZIONE CENTRALE
                f_pdf.set_font("Arial", 'B', 16)
                f_pdf.cell(190, 10, "STUDIO ODONTOIATRICO GA.MA. SRL", 0, 1, 'C')
                
                
                # ... qui sotto continua tutto il resto del tuo codice originale ...
                
                # Riprendiamo la tua logica di generazione delle celle...
                # NOTA: Se usi stringhe personalizzate sotto questa riga, 
                # assicurati di non usare il carattere "€" ma la variabile txt_totale o la parola "Euro".
                
                # --- FINE CODICE BLINDATO ---
                f_pdf.set_font("Arial", '', 10)
                f_pdf.cell(190, 5, "Via XX Settembre, 7 - 84091 Battipaglia (SA)", 0, 1, 'C')
                f_pdf.cell(190, 5, "Tel. 0828345054 - C.F. - P.IVA 03036130650", 0, 1, 'C')
                f_pdf.cell(190, 5, "Email centromedicogamasrl@gmail.com", 0, 1, 'C')
                f_pdf.cell(190, 5, "CCIAA E NUMERO REA SA02566010 - Capitale Sociale € 10.400", 0, 1, 'C')
                f_pdf.ln(15)
                
                f_pdf.set_font("Arial", 'B', 12)
                f_pdf.cell(190, 10, f"FATTURA N. {n_fatt}", 1, 1, 'C')
                f_pdf.ln(5)
                
                # DATI PAZIENTE
                f_pdf.set_font("Arial", 'B', 10)
                f_pdf.cell(190, 7, f"Spett.le: {p_dati['Nome']}", 0, 1)
                f_pdf.set_font("Arial", '', 10)
                indirizzo_p = f"{p_dati.get('Via', '')} - {p_dati.get('Citta', '')} ({p_dati.get('Provincia', '')})"
                f_pdf.cell(190, 7, f"Indirizzo: {indirizzo_p.upper()}", 0, 1)
                f_pdf.cell(190, 7, f"Codice Fiscale: {p_dati.get('CF', 'N.D.').upper()}", 0, 1)
                f_pdf.cell(190, 7, f"Data Emissione: {d_fatt.strftime('%d/%m/%Y')}", 0, 1)
                f_pdf.ln(10)
                
                # TABELLA
                f_pdf.set_font("Arial", 'B', 10)
                f_pdf.cell(140, 10, "DESCRIZIONE", 1, 0, 'C')
                f_pdf.cell(50, 10, "IMPORTO", 1, 1, 'C')
                
                # Riga Prestazione
                f_pdf.set_font("Arial", '', 10)
                f_pdf.cell(140, 12, desc_fatt, 1)
                f_pdf.cell(50, 12, txt_base, 1, 1, 'R')
                
                # RIGA IVA ESENTE (Prima del bollo)
                f_pdf.set_font("Arial", 'I', 8) #  note Font leggermente più piccolo per la dicitura lunga
                f_pdf.cell(140, 10, "IVA Esente ai sensi dell'art. 10, comma 1, n. 18 del D.P.R. 633/72", 1, 0, 'L')
                f_pdf.set_font("Arial", '', 10)
                f_pdf.cell(50, 10, txt_iva_zero, 1, 1, 'R')
                
                # Riga Bollo
                if ha_bollo:
                    f_pdf.cell(140, 10, "Imposta di bollo", 1, 0, 'L')
                    f_pdf.cell(50, 10, txt_bollo, 1, 1, 'R')
                
                # Totale Finale
                f_pdf.set_font("Arial", 'B', 11)
                f_pdf.cell(140, 10, "TOTALE FATTURA", 1, 0, 'R')
                f_pdf.cell(50, 10, txt_totale, 1, 1, 'R')
                
                # Note a fondo tabella
                f_pdf.ln(5)
                if ha_bollo:
                    f_pdf.set_font("Arial", 'I', 10)
                    f_pdf.cell(190, 5, "Imposta di bollo da 2,00 Euro assolta sull'originale per importi superiori a 77,47 Euro ed e' a carico del paziente.", 0, 1)
                
                # >>> SPOSATA QUI: ADESSO f_pdf ESISTE E NON DARÀ PIÙ ERRORE <<<
                f_pdf.set_font("Arial", '', 11)
                f_pdf.cell(190, 10, f"Metodo di Pagamento: {metodo_pagamento}", 0, 1, 'L')
                
                # DIRETTORE SANITARIO A PIÈ DI PAGINA
                f_pdf.set_y(-30)
                f_pdf.set_font("Arial", 'I', 8)
                f_pdf.cell(190, 5, '"Direttore Sanitario - Dott. Stefano Pio Gammella "', 0, 1, 'L')
                
                if hasattr(f_pdf, 'pages'):
                    for i in range(1, len(f_pdf.pages) + 1):
                        if i in f_pdf.pages:
                            f_pdf.pages[i] = f_pdf.pages[i].replace("€", "Euro")

                st.session_state.pdf_sanitario = f_pdf.output(dest='S').encode('latin-1', errors='ignore')
                st.session_state.nome_file_sanitario = f"Fattura_{n_fatt.replace('/','_')}.pdf"
                st.success("Fattura generata correttamente!")

        lista_fatture_esistenti = st.session_state.db.get("fatture", [])
        totale_reale = len(lista_fatture_esistenti)
        
        if totale_reale > 0:
            st.write("---")
            st.write("### 📜 Gestione e Modifica Fatture in Archivio")
            
            for idx_f, f in enumerate(reversed(lista_fatture_esistenti)):
                reale_idx = totale_reale - 1 - idx_f
                
                with st.expander(f"🧾 Fattura N. {f.get('numero')} - {f.get('paziente')} ({f.get('data')})"):
                    col_info1, col_info2 = st.columns(2)
                    col_info1.write(f"**Importo Prestazione:** € {f.get('importo'):.2f}")
                    col_info1.write(f"**Metodo Pagamento:** {f.get('metodo_pagamento')}")
                    col_info2.write(f"**Totale Complessivo:** € {f.get('totale'):.2f}")
                    
                    chiave_popover = f"pop_mod_{f.get('numero')}_{reale_idx}".replace("/", "_")
                    
                    with st.popover("✏️ Modifica Dati", key=chiave_popover, use_container_width=True):
                        st.write(f"⚙️ **Modifica Fattura N. {f.get('numero')}**")
                        
                        nuovo_paziente = st.selectbox(
                            "Paziente", nomi_p, 
                            index=nomi_p.index(f.get('paziente')) if f.get('paziente') in nomi_p else 0,
                            key=f"mod_paz_{reale_idx}"
                        )
                        
                        import datetime
                        try:
                            data_corrente_f = datetime.datetime.strptime(f.get('data'), "%Y-%m-%d").date()
                        except:
                            data_corrente_f = datetime.date.today()
                            
                        nuova_data = st.date_input("Nuova Data", value=data_corrente_f, key=f"mod_data_{reale_idx}")
                        nuovo_importo = st.number_input("Nuovo Importo Prestazione (€)", min_value=0.0, value=float(f.get('importo', 0.0)), step=50.0, key=f"mod_imp_{reale_idx}")
                        
                        metodi_lista = ["Contanti", "Carta di Credito/Debito", "Bonifico Bancario", "Assegno"]
                        nuovo_metodo = st.selectbox(
                            "Nuovo Metodo Pagamento", metodi_lista,
                            index=metodi_lista.index(f.get('metodo_pagamento')) if f.get('metodo_pagamento') in metodi_lista else 0,
                            key=f"mod_met_{reale_idx}"
                        )
                        
                        # Adesso questo pulsante funzionerà perché siamo fuori dal form!
                        if st.button("💾 Salva Modifiche", key=f"btn_save_{reale_idx}", type="primary", use_container_width=True):
                            ha_bollo_mod = nuovo_importo > 77.47
                            valore_bollo_mod = 2.0 if ha_bollo_mod else 0.0
                            nuovo_totale = nuovo_importo + valore_bollo_mod
                            
                            st.session_state.db["fatture"][reale_idx]["paziente"] = nuovo_paziente
                            st.session_state.db["fatture"][reale_idx]["data"] = str(nuova_data)
                            st.session_state.db["fatture"][reale_idx]["importo"] = nuovo_importo
                            st.session_state.db["fatture"][reale_idx]["metodo_pagamento"] = nuovo_metodo
                            st.session_state.db["fatture"][reale_idx]["totale"] = nuevo_totale
                            
                            salva_dati(st.session_state.db)
                            st.success("Fattura modificata e salvata con successo!")
                            st.rerun()
        if st.session_state.get("pdf_sanitario") is not None:
            st.write("---")
            st.success(f"📄 Pronto per il download: `{st.session_state.nome_file_sanitario}`")
            
            st.download_button(
                label="📥 SCARICA / STAMPA PDF FATTURA",
                data=st.session_state.pdf_sanitario,
                file_name=st.session_state.nome_file_sanitario,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
# =========================================================
# SCHEDA: PIANO DI CURA E PREVENTIVO
# =========================================================

elif menu == "📑 Piano di Cura":
    st.header("Sviluppo Piano di Cura e Preventivo")
    
    nomi_p = [p['Nome'] for p in st.session_state.db["pazienti"]]
    p_scelto = st.selectbox("Seleziona Paziente per il Piano di Cura", ["---"] + nomi_p)
    
    if p_scelto != "---":
        p_dati = next(p for p in st.session_state.db["pazienti"] if p['Nome'] == p_scelto)
        
        # Gestione memoria PDF per evitare errori di download
        if 'pdf_piano' not in st.session_state:
            st.session_state.pdf_piano = None

        with st.form("form_piano_cura"):
            st.subheader("Dettaglio Cure Proposte")
            
            # Creiamo una tabella inseribile per il preventivo
            c1, c2 = st.columns([3, 1])
            lavoro_1 = c1.text_input("Descrizione Lavoro 1", "Igiene orale e controllo")
            prezzo_1 = c2.number_input("Prezzo 1 (€)", min_value=0.0, step=50.0)
            
            lavoro_2 = c1.text_input("Descrizione Lavoro 2", "")
            prezzo_2 = c2.number_input("Prezzo 2 (€)", min_value=0.0, step=50.0)
            
            lavoro_3 = c1.text_input("Descrizione Lavoro 3", "")
            prezzo_3 = c2.number_input("Prezzo 3 (€)", min_value=0.0, step=50.0)
            
            lavoro_4 = c1.text_input("Descrizione Lavoro 4", "")
            prezzo_4 = c2.number_input("Prezzo 4 (€)", min_value=0.0, step=50.0)

            note_piano = st.text_area("Note aggiuntive o modalità di pagamento (es. Dilazione in 12 mesi)")
            
            genera_piano = st.form_submit_button("1. GENERA PIANO DI CURA")
            
            if genera_piano:
                # Calcolo totale
                totale_piano = prezzo_1 + prezzo_2 + prezzo_3 + prezzo_4
                
                pdf = FPDF()
                pdf.add_page()
                
                # INTESTAZIONE CENTRALE (Dati richiesti da te)
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, "STUDIO ODONTOIATRICO GA.MA. SRL", 0, 1, 'C')
                pdf.set_font("Arial", '', 10)
                pdf.cell(190, 5, "Via XX Settembre, 7 - 84091 Battipaglia (SA)", 0, 1, 'C')
                pdf.cell(190, 5, "Tel. 0828345054 - P.IVA 03036130650", 0, 1, 'C')
                pdf.ln(10)
                
                # TITOLO DOCUMENTO
                pdf.set_font("Arial", 'B', 14)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(190, 12, "PIANO DI CURA E PREVENTIVO SPESA", 1, 1, 'C', True)
                pdf.ln(5)
                
                # DATI PAZIENTE (CF, Via, Città)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(190, 7, f"Paziente: {p_dati['Nome']}", 0, 1)
                pdf.set_font("Arial", '', 10)
                indirizzo_p = f"{p_dati.get('Via', '')} - {p_dati.get('Citta', '')} ({p_dati.get('Provincia', '')})"
                pdf.cell(190, 7, f"Indirizzo: {indirizzo_p.upper()}", 0, 1)
                pdf.cell(190, 7, f"Codice Fiscale: {p_dati.get('CF', 'N.D.').upper()}", 0, 1)
                pdf.cell(190, 7, f"Data emissione: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
                pdf.ln(10)
                
                # TABELLA PRESTAZIONI
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(140, 10, "PRESTAZIONE ODONTOIATRICA PROPOSTA", 1, 0, 'C')
                pdf.cell(50, 10, "IMPORTO", 1, 1, 'C')
                
                pdf.set_font("Arial", '', 10)
                lavori = [(lavoro_1, prezzo_1), (lavoro_2, prezzo_2), (lavoro_3, prezzo_3), (lavoro_4, prezzo_4)]
                
                for lav, prezzo in lavori:
                    if lav: # Stampa solo se la riga non è vuota
                        pdf.cell(140, 10, lav, 1)
                        pdf.cell(50, 10, format_it(prezzo).replace("€", "Euro"), 1, 1, 'R')
                
                # TOTALE PIANO
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(140, 10, "TOTALE COMPLESSIVO DEL PIANO DI CURA", 1, 0, 'R')
                pdf.cell(50, 10, format_it(totale_piano).replace("€", "Euro"), 1, 1, 'R')
                
                # NOTE
                if note_piano:
                    pdf.ln(5)
                    pdf.set_font("Arial", 'I', 9)
                    pdf.multi_cell(190, 5, f"Note: {note_piano}")
                
                # TERMINI E VALIDITÀ
                pdf.ln(10)
                pdf.set_font("Arial", '', 8)
                pdf.multi_cell(190, 4, "Il presente preventivo ha validità di 30 giorni. Le prestazioni indicate potrebbero subire variazioni in base all'evoluzione clinica del caso durante l'esecuzione delle cure.")
                
                # DIRETTORE SANITARIO A PIÈ DI PAGINA
                pdf.set_y(-40)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(190, 5, "Direttore Sanitario", 0, 1, 'R')
                pdf.cell(190, 5, '"Dott. Stefano Pio Gammella(iscrizione albo Odontoiatri Salerno n. 1487)"', 0, 1, 'R')
                
                # Salvataggio
                st.session_state.pdf_piano = pdf.output(dest='S').encode('latin-1', errors='ignore')
                st.success("Piano di cura generato! Scarica il documento qui sotto.")

        # Tasto download fuori dal form
        if st.session_state.pdf_piano:
            st.download_button(
                label="📥 SCARICA PDF PIANO DI CURA",
                data=st.session_state.pdf_piano,
                file_name=f"Piano_Cura_{p_scelto.replace(' ','_')}.pdf",
                mime="application/pdf",
                width="stretch"
            )
            # =========================================================
# VISUALIZZAZIONE ARCHIVIO STORICO (IN FONDO ALLA PAGINA)
# =========================================================
if menu == "📄 Fattura Sanitaria":
    st.write("---")
    with st.expander("📊 Visualizza e Ristampa Fatture dall'Archivio"):
        if "fatture" in st.session_state.db and len(st.session_state.db["fatture"]) > 0:
            # Mostra la tabella con i dati salvati
            # Come deve diventare:
            st.dataframe(st.session_state.db["fatture"], width="stretch")
            
            st.write("### 🖨️ Ristampa una Fattura")
            lista_numeri_fatture = [f["numero"] for f in st.session_state.db["fatture"]]
            fattura_da_recuperare = st.selectbox("Seleziona il numero di fattura da ristampare", lista_numeri_fatture)
            
            clicca_recupera = st.button("🔄 RIGENERA PDF SELEZIONATO")
            
            if clicca_recupera:
                f_dati = next(f for f in st.session_state.db["fatture"] if f["numero"] == fattura_da_recuperare)
                
                # 1. Recupera il profilo del paziente dall'anagrafica usando la chiave corretta "Nome"
                paz_info = next((p for p in st.session_state.db["pazienti"] if p["Nome"] == f_dati["paziente"]), {})
                
                # 2. Forza il recupero del Codice Fiscale dall'anagrafica se nella vecchia fattura manca o è generico
                paz_cf = f_dati.get("codice_fiscale", "")
                if not paz_cf or paz_cf == "NON SPECIFICATO" or paz_cf.strip() == "":
                    paz_cf = paz_info.get("CF", "")
                
                # 3. Forza la ricostruzione dell'Indirizzo aggiornato dall'anagrafica
                if paz_info.get("Via") or paz_info.get("Citta"):
                    indirizzo_completo = f"{paz_info.get('Via', '')} - {paz_info.get('Citta', '')} ({paz_info.get('Provincia', '')})"
                else:
                    indirizzo_completo = f_dati.get("indirizzo", "")

                valore_importo = float(f_dati["importo"])
                descrizione_cura = f_dati.get("descrizione", "Cure Odontoiatriche Specialistiche")
                
                f_pdf = FPDF()
                f_pdf.add_page()
                
                f_pdf.set_font("Arial", 'B', 14)
                f_pdf.cell(190, 6, "STUDIO ODONTOIATRICO GA.MA. SRL", 0, 1, 'C')
                
                f_pdf.set_font("Arial", '', 10)
                f_pdf.cell(190, 5, "Via XX Settembre, 7 - 84091 Battipaglia (SA)", 0, 1, 'C')
                f_pdf.cell(190, 5, "Tel. 0828345054 - C.F. - P.IVA 03036130650", 0, 1, 'C')
                f_pdf.cell(190, 5, "Email centromedicogamasrl@gmail.com - Pec studiogamasrl@pec.it", 0, 1, 'C')
                f_pdf.cell(190, 5, "CCIAA E NUMERO REA SA02566010 - Capitale Sociale Euro 10.400", 0, 1, 'C')
                f_pdf.ln(10)
                
                f_pdf.set_font("Arial", 'B', 11)
                f_pdf.cell(190, 6, f"FATTURA N. {f_dati['numero']}", 0, 1, 'L')
                
                f_pdf.set_font("Arial", '', 11)
                f_pdf.cell(190, 6, f"Spett.le: {f_dati['paziente'].upper()}", 0, 1, 'L')
                
                testo_indirizzo = str(indirizzo_completo).upper() if str(indirizzo_completo).strip() and str(indirizzo_completo).strip() != "- ()" else "NON SPECIFICATO"
                f_pdf.cell(190, 6, f"Indirizzo: {testo_indirizzo}", 0, 1, 'L')
                
                testo_cf = str(paz_cf).upper() if paz_cf else "NON SPECIFICATO"
                f_pdf.cell(190, 6, f"Codice Fiscale: {testo_cf}", 0, 1, 'L')
                
                data_emissione = f_dati['data']
                if "-" in data_emissione:
                    try:
                        parti = data_emissione.split("-")
                        data_emissione = f"{parti[2]}/{parti[1]}/{parti[0]}"
                    except:
                        pass
                f_pdf.cell(190, 6, f"Data Emissione: {data_emissione}", 0, 1, 'L')
                f_pdf.ln(10)
                
                f_pdf.set_font("Arial", 'B', 10)
                f_pdf.cell(140, 7, "DESCRIZIONE", 1, 0, 'L')
                f_pdf.cell(50, 7, "IMPORTO", 1, 1, 'R')
                
                f_pdf.set_font("Arial", '', 10)
                f_pdf.cell(140, 7, f" {descrizione_cura}", 1, 0, 'L')
                f_pdf.cell(50, 7, f"{valore_importo:,.2f} Euro ", 1, 1, 'R')
                
                f_pdf.cell(140, 7, " IVA Esente ai sensi dell'art. 10, comma 1, n. 18 del D.P.R. 633/72", 1, 0, 'L')
                f_pdf.cell(50, 7, "0,00 Euro ", 1, 1, 'R')
                
                ha_bollo = valore_importo > 77.47
                valore_totale = valore_importo + 2.00 if ha_bollo else valore_importo
                if ha_bollo:
                    f_pdf.cell(140, 7, " Imposta di bollo", 1, 0, 'L')
                    f_pdf.cell(50, 7, "2,00 Euro ", 1, 1, 'R')
                
                f_pdf.set_font("Arial", 'B', 10)
                f_pdf.cell(140, 7, " TOTALE FATTURA", 1, 0, 'L')
                f_pdf.cell(50, 7, f"{valore_totale:,.2f} Euro ", 1, 1, 'R')
                f_pdf.ln(10)
                
                f_pdf.set_font("Arial", 'I', 9)
                if ha_bollo:
                    nota_completa = "Imposta di bollo da 2,00 Euro assolta sull'originale per importi superiori a 77,47 Euro ed e' a carico del paziente."
                    f_pdf.multi_cell(190, 5, nota_completa, 0, 'L')
                    f_pdf.ln(4)
                
                f_pdf.set_font("Arial", '', 10)
                f_pdf.cell(190, 6, f"Metodo di Pagamento: {f_dati['metodo_pagamento']}", 0, 1, 'L')
                
                f_pdf.set_y(260)
                f_pdf.set_font("Arial", '', 10)
                f_pdf.cell(190, 5, "Direttore Sanitario - Dott. Stefano Pio Gammella (iscrizione albo Odontoiatri Salerno n. 1487)", 0, 1, 'R')
                
                if hasattr(f_pdf, 'pages'):
                    for i in range(1, len(f_pdf.pages) + 1):
                        if i in f_pdf.pages:
                            f_pdf.pages[i] = f_pdf.pages[i].replace("€", "Euro")
                
                st.session_state.pdf_sanitario = f_pdf.output(dest='S').encode('latin-1', errors='ignore')
                st.session_state.nome_file_sanitario = f"Fattura_{f_dati['numero'].replace('/', '_')}.pdf"
                st.success(f"Fattura {f_dati['numero']} rigenerata nel visualizzatore!")
                
                st.write("---")
                st.download_button(
                    label="📥 SCARICA / STAMPA PDF FATTURA",
                    data=st.session_state.pdf_sanitario,
                    file_name=st.session_state.nome_file_sanitario,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                    key="download_recupero_stampa"
                )
        # Questo else è quello originale del codice (lasciare intatto così com'è)
        else:
            st.info("Non ci sono ancora fatture salvate nell'archivio.")

# =========================================================================
# 📦 NUOVA SEZIONE: GESTIONE MAGAZZINO, LOTTI E SCADENZE
# =========================================================================
elif menu == "📦 Magazzino":
    st.title("📦 Gestione Magazzino, Lotti e Scadenze")
    
    # Inizializzazione controllata delle sotto-chiavi se assenti
    if "magazzino" not in st.session_state.db:
        st.session_state.db["magazzino"] = {}
    if "storico_magazzino" not in st.session_state.db:
        st.session_state.db["storico_magazzino"] = []

    # --- 1. EXPANDER PER INSERIRE O AGGIORNARE PRODOTTI ---
    with st.expander("➕ Aggiungi o Aggiorna Voce in Magazzino", expanded=False):
        with st.form("form_magazzino", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                nome_prodotto = st.text_input("Nome Prodotto (es. Monouso, Composito):").strip().upper()
                lotto_prodotto = st.text_input("Numero Lotto:").strip().upper()
                quantita_prodotto = st.number_input("Quantità Iniziale:", min_value=0, step=1, value=1)
            with col_f2:
                soglia_prodotto = st.number_input("Soglia Minima Sottoscorta:", min_value=1, step=1, value=2)
                data_scadenza_prod = st.date_input("Data di Scadenza:", value=datetime.today())
            
            submit_mag = st.form_submit_button("Registra in Magazzino")
            
            if submit_mag:
                if nome_prodotto and lotto_prodotto:
                    chiave_univoca = f"{nome_prodotto} (Lotto: {lotto_prodotto})"
                    data_scad_str = data_scadenza_prod.strftime("%d/%m/%Y")
                    
                    st.session_state.db["magazzino"][chiave_univoca] = {
                        "Quantità": quantita_prodotto,
                        "Scadenza": data_scad_str,
                        "Soglia": soglia_prodotto if soglia_prodotto else 2
                    }
                    
                    st.session_state.db["storico_magazzino"].append({
                        "Data/Ora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Operazione": "Carico Iniziale/Aggiornamento",
                        "Articolo": chiave_univoca,
                        "Quantità": f"+{quantita_prodotto}"
                    })
                    
                    salva_dati(st.session_state.db)
                    st.success(f"Articolo '{chiave_univoca}' registrato con successo!")
                    st.rerun()
                else:
                    st.error("Per favore, compila sia il Nome Prodotto che il Numero Lotto.")

    st.divider()

    # --- 2. BARRA DI RICERCA E FILTRI AVANZATI ---
    st.subheader("🔍 Filtra e Cerca nel Magazzino")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        ricerca_testo = st.text_input("Cerca per nome o lotto:", "").strip().upper()
    with col_c2:
        filtro_stato = st.selectbox("Filtra per stato scorte:", ["Tutti", "In Sottoscorta", "Scaduti", "Disponibili"])

    # --- 3. TABELLA OPERATIVA DELLE SCORTE ---
    oggi_dt = datetime.now()
    articoli_filtrati = {}

    for k, v in st.session_state.db["magazzino"].items():
        if ricerca_testo and ricerca_testo not in k.upper():
            continue
        
        try:
            data_scad_dt = datetime.strptime(v["Scadenza"], "%d/%m/%Y")
            is_scaduto = (data_scad_dt - oggi_dt).days < 0
        except:
            is_scaduto = False
            
        is_sottoscorta = v["Quantità"] <= v.get("Soglia", 2)

        if filtro_stato == "In Sottoscorta" and not is_sottoscorta:
            continue
        elif filtro_stato == "Scaduti" and not is_scaduto:
            continue
        elif filtro_stato == "Disponibili" and (is_sottoscorta or is_scaduto):
            continue
            
        articoli_filtrati[k] = v

    if articoli_filtrati:
        st.write(f"Trovati {len(articoli_filtrati)} articoli corrispondenti:")
        
        header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([3, 1, 1, 1.5, 1.5])
        header_col1.markdown("**Articolo (Lotto)**")
        header_col2.markdown("**Quantità**")
        header_col3.markdown("**Soglia**")
        header_col4.markdown("**Scadenza**")
        header_col5.markdown("**Azioni Rapide**")
        st.markdown("---")

        for item_key, item_info in list(articoli_filtrati.items()):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1.5, 1.5])
            
            try:
                dt_scad = datetime.strptime(item_info["Scadenza"], "%d/%m/%Y")
                scaduto = (dt_scad - oggi_dt).days < 0
            except:
                scaduto = False
            sottoscorta = item_info["Quantità"] <= item_info.get("Soglia", 2)

            if scaduto:
                col1.write(f"🔴 {item_key} (SCADUTO)")
            elif sottoscorta:
                col1.write(f"⚠️ {item_key} (Sotto-soglia)")
            else:
                col1.write(f"📦 {item_key}")

            col2.write(f"**{item_info['Quantità']}**")
            col3.write(f"{item_info.get('Soglia', 2)}")
            col4.write(f"{item_info['Scadenza']}")
            
            btn_sub_col1, btn_sub_col2 = col5.columns(2)
            safe_key = item_key.replace(" ", "_").replace("(", "").replace(")", "").replace(":", "")
            
            if btn_sub_col1.button("➕", key=f"piu_{safe_key}"):
                st.session_state.db["magazzino"][item_key]["Quantità"] += 1
                st.session_state.db["storico_magazzino"].append({
                    "Data/Ora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Operazione": "Carico Rapido",
                    "Articolo": item_key,
                    "Quantità": "+1"
                })
                salva_dati(st.session_state.db)
                st.rerun()
                
            if btn_sub_col2.button("➖", key=f"meno_{safe_key}"):
                if st.session_state.db["magazzino"][item_key]["Quantità"] > 0:
                    st.session_state.db["magazzino"][item_key]["Quantità"] -= 1
                    st.session_state.db["storico_magazzino"].append({
                        "Data/Ora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Operazione": "Scarico Rapido",
                        "Articolo": item_key,
                        "Quantità": "-1"
                    })
                    salva_dati(st.session_state.db)
                    st.rerun()
                else:
                    st.error("Impossibile scendere sotto lo zero!")
            st.markdown("<hr style='margin:0.2rem 0;' />", unsafe_allow_html=True)
    else:
        st.info("Nessun articolo trovato in magazzino con i filtri selezionati.")

    st.divider()

    # --- 4. CRONOLOGIA RECENTE E RIMOZIONE MANUALE ---
    col_down1, col_down2 = st.columns(2)
    
    with col_down1:
        with st.expander("⏳ Cronologia Registro Movimenti (Ultime 30 operazioni)"):
            if not st.session_state.db["storico_magazzino"]:
                st.info("Nessun movimento registrato finora.")
            else:
                cronologia_ordinata = st.session_state.db["storico_magazzino"][::-1][:30]
                st.dataframe(cronologia_ordinata, use_container_width=True, hide_index=True)

    with col_down2:
        with st.expander("🗑️ RIMUOVI VOCE MANUALE"):
            if st.session_state.db["magazzino"]:
                scelta_elimina_1 = st.selectbox(
                    "Seleziona voce da cancellare definitivamente:", 
                    list(st.session_state.db["magazzino"].keys()), 
                    key="elimina_box_magazzino_univoco"
                )
                
                if st.button("Elimina Definitivamente", type="secondary", key="btn_elimina_magazzino_principale"):
                    del st.session_state.db["magazzino"][scelta_elimina_1]
                    st.session_state.db["storico_magazzino"].append({
                        "Data/Ora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Operazione": "Eliminazione Totale Voce",
                        "Articolo": scelta_elimina_1,
                        "Quantità": "Reset"
                    })
                    salva_dati(st.session_state.db)
                    st.success("Voce rimossa completamente dal database.")
                    st.rerun()
            else:
                st.info("Magazzino vuoto.")
    
        