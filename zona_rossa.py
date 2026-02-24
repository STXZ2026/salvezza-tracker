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
        
        # Monitoraggio dinamico dalla 13° alla 20°
        ultime_8_dinamiche = standings[12:20]
        
        # Quota dinamica sulla 18°
        terzultima = standings[17]
        quota_f = max(34, min(int((terzultima['points'] / max(1, terzultima['playedGames'])) * 38) + 1, 40))
        
        return ultime_8_dinamiche, standings[0]['playedGames'], res_m.json().get('matches', []), quota_f
    except: return None, 0, [], 38

ultime_8, giocata, tutti_match, soglia_salvezza = carica_dati()

# --- 2. SCALA CROMATICA (13° -> 20°) ---
colori_scala = [
    "#00A36C", "#76BA1B", "#ADFF2F", "#FFD700", 
    "#FFA500", "#FF4500", "#D2042D", "#800020"
]

# --- 3. NOTIFICHE LIVE ---
match_live = [m for m in tutti_match if m['status'] == 'IN_PLAY']
for m in match_live:
    st.toast(f"⚽ LIVE: {m['homeTeam']['shortName']} {m['score']['fullTime']['home']}-{m['score']['fullTime']['away']} {m['awayTeam']['shortName']}", icon="📢")

# --- 4. INTERFACCIA ---
st.title("🏆 RANKING SALVEZZA LIVE")
st.markdown(f"**Target Salvezza: {soglia_salvezza}pt**")

for idx, team in enumerate(ultime_8):
    nome_sq = team['team']['name'].replace("FC", "").replace("CFC", "").strip()
    punti = team['points']
    pos = team['position']
    p_mancanti = max(0, soglia_salvezza - punti)
    
    # --- NUOVO ALGORITMO PERCENTUALE GRADUALE ---
    # Calcolo base sulla quota
    base_perc = (punti / soglia_salvezza) * 100
    # Bonus posizione: la 13° prende +7%, la 14° +6% ... la 20° +0%
    bonus_pos = (20 - pos) 
    perc_salv = min(int(base_perc + bonus_pos), 99) 
    
    # Se i punti sono zero o molto bassi, evitiamo percentuali troppo alte dal solo bonus
    if punti < 5: perc_salv = max(perc_salv - 10, 1)

    bg_color = colori_scala[idx]
    # Se matematicamente retrocessa
    if (38 - giocata) * 3 < p_mancanti:
        bg_color = "#000000"
        perc_salv = 0

    # Layout compatto per iPhone
    st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 8px 15px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; color: white; margin-top: 8px;">
            <div style="display: flex; flex-direction: column;">
                <span style="font-size: 0.7em; font-weight: bold; opacity: 0.8;">{pos}° POSTO</span>
                <span style="font-weight: bold; font-size: 1.1em; letter-spacing: -0.5px;">{nome_sq.upper()}</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 2em; font-weight: 900; line-height: 1;">{punti}</span>
                <span style="font-size: 0.7em; font-weight: bold; display: block;">PUNTI</span>
            </div>
        </div>
        <div style="background-color: #f8f9fa; padding: 6px 10px; border: 1px solid #ddd; border-top:none; display: flex; align-items: center; justify-content: space-between; border-radius: 0 0 10px 10px; margin-bottom: 4px;">
            <div style="text-align: center; flex: 1; border-right: 1px solid #eee;">
                <p style="font-size: 0.55em; margin:0; color: #666; font-weight: bold;">POSSIBILITÀ SALVEZZA</p>
                <div style="position: relative; width: 42px; height: 42px; border-radius: 50%; background: conic-gradient({bg_color} {perc_salv * 3.6}deg, #e0e0e0 0deg); margin: 2px auto;">
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 32px; height: 32px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 0.75em; font-weight: bold; color: #222;">{perc_salv}%</span>
                    </div>
                </div>
            </div>
            <div style="text-align: center; flex: 1.5;">
                <p style="font-size: 0.85em; color: #d63384; font-weight: bold; margin:0;">MANCANO: {p_mancanti}pt</p>
                <p style="font-size: 0.55em; color: #888; margin:0;">V:{team['won']} N:{team['draw']} P:{team['lost']} | DR:{team['goalDifference']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander(f"Dettagli {nome_sq}"):
        st.write(f"Vittorie: {team['won']}, Pareggi: {team['draw']}, Sconfitte: {team['lost']}")
        st.write(f"Differenza Reti: {team['goalDifference']}")

st.sidebar.button("🔄 AGGIORNA LIVE")

