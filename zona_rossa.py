# --- CHIAVE DA COPIARE c8cac2cec6e64345868d516c077c1685

import streamlit as st
import requests
from datetime import datetime, timedelta
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# --- 1. CONFIGURAZIONE ---
API_KEY = "8cac2cec6e64345868d516c077c1685" 
ID_SERIE_A = "SA"

st.set_page_config(page_title="Survival Tracker Pro", layout="wide")

# AGGIORNAMENTO AUTOMATICO OGNI 60 SECONDI
if st_autorefresh:
    st_autorefresh(interval=60 * 1000, key="datarefresh")

def carica_dati():
    headers = {'X-Auth-Token': API_KEY}
    url_s = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/standings"
    url_m = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/matches"
    
    try:
        res_s = requests.get(url_s, headers=headers, timeout=5)
        res_m = requests.get(url_m, headers=headers, timeout=5)
        
        if res_s.status_code != 200: return None, 0, [], 38, {}, []
        
        data_s = res_s.json()
        standings = data_s['standings'][0]['table']
        
        # Monitoraggio dinamico: ultime 8 squadre (posizioni 13-20)
        ultime_8 = standings[12:20]
        
        # Quota dinamica sulla 18esima
        terzultima = standings[17]
        giocate_t = max(1, terzultima['playedGames'])
        quota_f = max(34, min(int((terzultima['points'] / giocate_t) * 38) + 1, 40))
        
        posizioni = {item['team']['name']: item['position'] for item in standings}
        
        tutti_match = res_m.json().get('matches', [])
        match_live = [m for m in tutti_match if m['status'] in ['IN_PLAY', 'PAUSED']]
        match_futuri = [m for m in tutti_match if m['status'] == 'TIMED']
        
        return ultime_8, standings[0]['playedGames'], match_futuri, quota_f, posizioni, match_live
    except:
        return None, 0, [], 38, {}, []

# Caricamento dati
ultime_8, giocata, calendario, soglia_salvezza, pos_classifica, live_matches = carica_dati()

# --- 2. SCALA CROMATICA DECISA (13° -> 20°) ---
# Invertita: Verde (13°) -> Rosso/Nero (20°)
colori_scala = [
    "#2E7D32", # 13° - Verde Bosco
    "#689F38", # 14° - Verde Erba
    "#AFB42B", # 15° - Giallo Limone
    "#FBC02D", # 16° - Giallo Sole
    "#FFA000", # 17° - Arancio Ambra
    "#F57C00", # 18° - Arancio Acceso
    "#D32F2F", # 19° - Rosso Fuoco
    "#3E0000"  # 20° - Rosso Scuro/Nero (Hellas Verona/Ultima)
]

# --- 3. NOTIFICHE LIVE ---
if live_matches:
    for m in live_matches:
        fase = "LIVE" if m['status'] == 'IN_PLAY' else "INTERVALLO"
        st.toast(f"⚽ {fase}: {m['homeTeam']['shortName']} {m['score']['fullTime']['home']} - {m['score']['fullTime']['away']} {m['awayTeam']['shortName']}", icon="📢")

# --- 4. INTERFACCIA PRINCIPALE ---
st.title("🏆 RANKING SALVEZZA LIVE")
st.markdown(f"**Target Salvezza: {soglia_salvezza}pt** | Aggiornato: {datetime.now().strftime('%H:%M:%S')}")



if ultime_8:
    for idx, team in enumerate(ultime_8):
        nome_full = team['team']['name']
        nome_display = nome_full.replace("FC", "").replace("CFC", "").replace("US", "").replace("Hellas", "").strip().upper()
        punti = team['points']
        pos = team['position']
        p_mancanti = max(0, soglia_salvezza - punti)
        
        # Algoritmo Percentuale Gerarchica con bonus posizione
        base_perc = (punti / soglia_salvezza) * 100
        bonus_pos = (20 - pos)
        perc_salv = min(int(base_perc + bonus_pos), 99)
        
        bg_color = colori_scala[idx]
        if (38 - giocata) * 3 < p_mancanti:
            bg_color, perc_salv = "#000000", 0

        # Rendering Box Squadra (Ottimizzato iPhone)
        st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 8px 15px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; color: white; margin-top: 10px;">
                <div style="display: flex; flex-direction: column;">
                    <span style="font-size: 0.61em; font-weight: bold; opacity: 0.85;">{pos}° POSTO</span>
                    <span style="font-weight: bold; font-size: 1.15em; letter-spacing: -0.5px;">{nome_display}</span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 2.2em; font-weight: 900; line-height: 1;">{punti}</span>
                    <span style="font-size: 0.6em; font-weight: bold; display: block;">PUNTI</span>
                </div>
            </div>
            <div style="background-color: #f8f9fa; padding: 6px 10px; border: 1px solid #ddd; border-top:none; display: flex; align-items: center; justify-content: space-between; border-radius: 0 0 10px 10px; margin-bottom: 2px;">
                <div style="text-align: center; flex: 1; border-right: 1px solid #eee;">
                    <p style="font-size: 0.55em; margin:0; color: #666; font-weight: bold;">POSSIBILITÀ SALVEZZA</p>
                    <div style="position: relative; width: 42px; height: 42px; border-radius: 50%; background: conic-gradient({bg_color} {perc_salv * 3.6}deg, #e0e0e0 0deg); margin: 2px auto;">
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 32px; height: 32px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 0.75em; font-weight: bold; color: #222;">{perc_salv}%</span>
                        </div>
                    </div>
                </div>
                <div style="text-align: center; flex: 1.5;">
                    <p style="font-size: 0.9em; color: #d63384; font-weight: bold; margin:0;">MANCANO: {p_mancanti}pt</p>
                    <p style="font-size: 0.5em; color: #888; margin:0;">V:{team['won']} N:{team['draw']} P:{team['lost']} | DR:{team['goalDifference']}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander(f"📊 ANALISI E CALENDARIO"):
            tab_p, tab_c = st.tabs(["🎯 Piano Salvezza", "📅 Date"])
            with tab_p:
                partite_sq = [m for m in calendario if nome_full in m['homeTeam']['name'] or nome_full in m['awayTeam']['name']]
                acc_p, target_p = 0, soglia_salvezza - punti
                for m in partite_sq:
                    h, a = m['homeTeam']['name'], m['awayTeam']['name']
                    is_h = nome_full in h
                    avv = a if is_h else h
                    p_avv = pos_classifica.get(avv, 10)
                    if acc_p >= target_p: res, icon, bg = "SALVEZZA RAGGIUNTA", "🥳", "#1a1c23"
                    elif p_avv <= 6: res, icon, bg = "SCONFITTA PREVISTA", "💀", "#212529"
                    elif p_avv >= 14 or is_h: res, icon, bg = "VITTORIA OBBLIGATORIA", "🔥", "#212529"; acc_p += 3
                    else: res, icon, bg = "PAREGGIO UTILE", "🤝", "#212529"; acc_p += 1
                    st.markdown(f"<div style='background-color:{bg}; padding:8px; border-radius:5px; color:white; margin-bottom:5px; font-size:0.8em;'>{icon} <b>{res}</b> vs {avv}</div>", unsafe_allow_html=True)
            with tab_c:
                for m in [m for m in calendario if nome_full in m['homeTeam']['name'] or nome_full in m['awayTeam']['name']][:5]:
                    dt = datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
                    st.markdown(f"<div style='font-size:0.85em; border-bottom:1px solid #eee; padding:3px;'><b>{dt.strftime('%d/%m')}</b>: {m['homeTeam']['shortName']} vs {m['awayTeam']['shortName']}</div>", unsafe_allow_html=True)

st.sidebar.button("🔄 AGGIORNA LIVE")

      
