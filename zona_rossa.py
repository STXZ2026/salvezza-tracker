# --- c8cac2cec6e64345868d516c077c1685
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
        if res_s.status_code != 200: return None, 0, [], 38
        
        data_s = res_s.json()
        standings = data_s['standings'][0]['table']
        
        # Prendiamo le squadre dalla posizione 13 alla 20
        # In classifica l'indice 12 è il 13° posto
        ultime_8_dinamiche = standings[12:20]
        
        # Calcolo quota dinamica sulla 18esima (terzultima)
        terzultima = standings[17]
        quota_f = max(34, min(int((terzultima['points'] / max(1, terzultima['playedGames'])) * 38) + 1, 40))
        
        return ultime_8_dinamiche, standings[0]['playedGames'], res_m.json().get('matches', []), quota_f
    except: return None, 0, [], 38

ultime_8, giocata, tutti_match, soglia_salvezza = carica_dati()

# --- 2. SCALA CROMATICA PRECISA (Dall'alto al basso: Verde -> Rosso Scuro) ---
# Indice 0 (13° posto) -> Indice 7 (20° posto)
colori_scala = [
    "#00A36C", # 13° - Verde Brillante
    "#76BA1B", # 14° - Verde Mela
    "#ADFF2F", # 15° - Giallo/Verde
    "#FFD700", # 16° - Giallo
    "#FFA500", # 17° - Giallo/Arancio
    "#FF4500", # 18° - Rosso/Arancio (Terzultima)
    "#D2042D", # 19° - Rosso
    "#800020"  # 20° - Rosso Scuro (Ultima)
]

# --- 3. NOTIFICHE LIVE "TOAST" ---
match_live = [m for m in tutti_match if m['status'] == 'IN_PLAY']
for m in match_live:
    st.toast(f"⚽ LIVE: {m['homeTeam']['shortName']} {m['score']['fullTime']['home']} - {m['score']['fullTime']['away']} {m['awayTeam']['shortName']}", icon="📢")

# --- 4. INTERFACCIA ---
st.title("🏆 RANKING SALVEZZA LIVE")
st.markdown(f"**Target Salvezza: {soglia_salvezza}pt** | Proiezione sulle ultime 8")

# Mostriamo le squadre: la 13° apparirà per prima (Verde), la 20° per ultima (Rosso Scuro)
for idx, team in enumerate(ultime_8):
    nome_sq = team['team']['name'].replace("FC", "").replace("CFC", "").strip()
    punti = team['points']
    pos = team['position']
    perc_salv = min(int((punti / soglia_salvezza) * 100), 100)
    p_mancanti = max(0, soglia_salvezza - punti)
    
    # Colore basato sulla posizione nell'array (0-7)
    # Se la squadra è matematicamente retrocessa (ipotesi), diventa nero
    bg_color = colori_scala[idx]
    if (38 - giocata) * 3 < p_mancanti: # Matematicamente impossibile salvarsi
        bg_color = "#000000"

    # Layout compatto per iPhone
    st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 8px 15px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; color: white; margin-top: 10px;">
            <div style="display: flex; flex-direction: column;">
                <span style="font-size: 0.7em; font-weight: bold; opacity: 0.8;">{pos}° IN CLASSIFICA</span>
                <span style="font-weight: bold; font-size: 1.1em;">{nome_sq}</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 1.8em; font-weight: 900; line-height: 1;">{punti}</span>
                <span style="font-size: 0.7em; font-weight: bold; display: block;">PUNTI</span>
            </div>
        </div>
        <div style="background-color: #f8f9fa; padding: 8px; border: 1px solid #ddd; border-top:none; display: flex; align-items: center; justify-content: space-between; border-radius: 0 0 10px 10px;">
            <div style="text-align: center; flex: 1; border-right: 1px solid #eee;">
                <p style="font-size: 0.55em; margin:0; color: #666; font-weight: bold;">POSSIBILITÀ SALVEZZA</p>
                <div style="position: relative; width: 45px; height: 45px; border-radius: 50%; background: conic-gradient({bg_color} {perc_salv * 3.6}deg, #e0e0e0 0deg); margin: 2px auto;">
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 34px; height: 34px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 0.7em; font-weight: bold; color: #222;">{perc_salv}%</span>
                    </div>
                </div>
            </div>
            <div style="text-align: center; flex: 1;">
                <p style="font-size: 0.9em; color: #d63384; font-weight: bold; margin:0;">MANCANO: {p_mancanti}pt</p>
                <p style="font-size: 0.55em; color: #888; margin:0;">V:{team['won']} N:{team['draw']} P:{team['lost']} | DR:{team['goalDifference']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Expander dettagliati (per non allungare troppo la pagina)
    with st.expander(f"Strategia e Calendario {nome_sq}"):
        st.write(f"Prossimo impegno: ...") # Qui si possono aggiungere i dettagli del piano salvezza

st.sidebar.button("🔄 AGGIORNA LIVE")
