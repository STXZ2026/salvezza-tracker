
import streamlit as st
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE ---
API_KEY = "c8cac2cec6e64345868d516c077c1685" 
ID_SERIE_A = "SA"

st.set_page_config(page_title="Survival Tracker Pro", layout="wide")

def carica_dati():
    headers = {'X-Auth-Token': API_KEY}
    url_s = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/standings"
    url_m = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/matches"
    try:
        res_s = requests.get(url_s, headers=headers, timeout=5)
        res_m = requests.get(url_m, headers=headers, timeout=5)
        if res_s.status_code != 200: return None, 0, [], 38, []
        
        data_s = res_s.json()
        standings = data_s['standings'][0]['table']
        # La classifica dell'API segue già i criteri ufficiali (punti, scontri diretti, diff. reti)
        
        # Identifichiamo le ultime 8 squadre per il monitoraggio dinamico
        ultime_8_standings = standings[-8:]
        
        # Calcolo quota dinamica sulla 18esima (terzultima)
        terzultima = standings[17]
        quota_f = max(34, min(int((terzultima['points'] / max(1, terzultima['playedGames'])) * 38) + 1, 40))
        
        return ultime_8_standings, standings[0]['playedGames'], res_m.json().get('matches', []), quota_f, standings
    except: return None, 0, [], 38, []

ultime_8, giocata, tutti_match, soglia_salvezza, classifica_completa = carica_dati()

# --- 2. COLORI DINAMICI (Dal Verde al Rosso Scuro) ---
colori_scala = [
    "#8B0000", # 20° - Rosso Scuro
    "#FF0000", # 19° - Rosso
    "#FF4500", # 18° - Rosso/Arancio
    "#FF8C00", # 17° - Arancio/Giallo
    "#FFD700", # 16° - Giallo
    "#ADFF2F", # 15° - Giallo/Verde
    "#32CD32", # 14° - Verde Chiaro
    "#008000"  # 13° - Verde Brillante
]

# --- 3. LOGICA NOTIFICHE "VOLANTI" (Live Score) ---
match_live = [m for m in tutti_match if m['status'] == 'IN_PLAY']
if match_live:
    for m in match_live:
        st.toast(f"⚽ LIVE: {m['homeTeam']['shortName']} {m['score']['fullTime']['home']} - {m['score']['fullTime']['away']} {m['awayTeam']['shortName']}", icon="📢")

# --- 4. INTERFACCIA ---
st.title("🏆 SURVIVAL TRACKER LIVE")
st.markdown(f"**Target Salvezza: {soglia_salvezza}pt** | Monitoraggio dinamico ultime 8")

# Layout per smartphone: mostriamo le squadre in ordine di classifica (dalla 13° alla 20°)
# Invertiamo l'ordine per avere la migliore (13°) in alto e la peggiore (20°) in fondo
per_display = list(reversed(ultime_8))

for idx, team in enumerate(per_display):
    nome_sq = team['team']['shortName']
    punti = team['points']
    posizione = team['position']
    perc_salvezza = min(int((punti / soglia_salvezza) * 100), 100)
    p_mancanti = max(0, soglia_salvezza - punti)
    
    # Colore in base alla posizione (0 è la 13°, 7 è la 20°)
    bg_color = "#000000" if posizione > 17 and giocata > 35 and (soglia_salvezza - punti) > ((38-giocata)*3) else colori_scala[7-idx]
    
    # CSS per ridurre altezza box
    st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 5px 15px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; color: white;">
            <span style="font-weight: bold; font-size: 1.2em;">{posizione}° {nome_sq}</span>
            <span style="font-size: 1.8em; font-weight: 900;">{punti} <small style="font-size: 0.4em;">PT</small></span>
        </div>
        <div style="background-color: #f8f9fa; padding: 10px; border: 1px solid #ddd; border-top:none; display: flex; align-items: center; justify-content: space-around; margin-bottom: 5px;">
            <div style="text-align: center;">
                <p style="font-size: 0.6em; margin:0; color: #666; font-weight: bold;">POSSIBILITÀ SALVEZZA</p>
                <div style="position: relative; width: 50px; height: 50px; border-radius: 50%; background: conic-gradient({bg_color} {perc_salvezza * 3.6}deg, #e0e0e0 0deg); margin: 0 auto;">
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 38px; height: 38px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 0.8em; font-weight: bold; color: #222;">{perc_salvezza}%</span>
                    </div>
                </div>
            </div>
            <div style="text-align: center;">
                <p style="font-size: 0.9em; color: #d63384; font-weight: bold; margin:0;">MANCANO: {p_mancanti}pt</p>
                <p style="font-size: 0.6em; color: #888; margin:0;">V: {team['won']} | N: {team['draw']} | P: {team['lost']} (DR: {team['goalDifference']})</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Expander compatti per mobile
    with st.expander(f"Dettagli {nome_sq}"):
        tab1, tab2 = st.tabs(["📅 Calendario", "🎯 Piano"])
        with tab1:
            prossimi = [m for m in tutti_match if (m['homeTeam']['id'] == team['team']['id'] or m['awayTeam']['id'] == team['team']['id']) and m['status'] == 'TIMED'][:5]
            for m in prossimi:
                st.write(f"Match: {m['homeTeam']['shortName']} vs {m['awayTeam']['shortName']}")
        with tab2:
            st.write(f"Analisi per raggiungere quota {soglia_salvezza}...")

st.sidebar.button("🔄 AGGIORNA LIVE")
