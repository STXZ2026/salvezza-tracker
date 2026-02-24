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
    url_m = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/matches?status=SCHEDULED"
    url_live = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/matches"
    
    try:
        res_s = requests.get(url_s, headers=headers, timeout=5)
        res_m = requests.get(url_m, headers=headers, timeout=5)
        res_l = requests.get(url_live, headers=headers, timeout=5)
        
        if res_s.status_code != 200: return None, 0, [], 38, {}, []
        
        data_s = res_s.json()
        standings = data_s['standings'][0]['table']
        
        # Monitoraggio dinamico: prendiamo le ultime 8 squadre (posizioni 13-20)
        ultime_8 = standings[12:20]
        
        # Calcolo quota dinamica sulla 18esima (terzultima)
        terzultima = standings[17]
        giocate_t = max(1, terzultima['playedGames'])
        quota_f = max(34, min(int((terzultima['points'] / giocate_t) * 38) + 1, 40))
        
        posizioni = {item['team']['name']: item['position'] for item in standings}
        match_live = [m for m in res_l.json().get('matches', []) if m['status'] == 'IN_PLAY']
        
        return ultime_8, standings[0]['playedGames'], res_m.json().get('matches', []), quota_f, posizioni, match_live
    except:
        return None, 0, [], 38, {}, []

# Caricamento dati
ultime_8, giocata, calendario, soglia_salvezza, pos_classifica, live_matches = carica_dati()

# --- 2. SCALA CROMATICA PERSONALIZZATA (13° -> 20°) ---
colori_scala = [
    "#708238", # 13° - Verde Salvia (Spento, per il Torino/capolista del gruppo)
    "#8DB600", # 14° - Verde Mela scuro
    "#ADFF2F", # 15° - Giallo/Verde
    "#FFD700", # 16° - Giallo
    "#FFA500", # 17° - Giallo/Arancio
    "#FF4500", # 18° - Rosso/Arancio (Terzultima)
    "#D2042D", # 19° - Rosso
    "#800020"  # 20° - Rosso Scuro (Ultima)
]

# --- 3. NOTIFICHE LIVE (TOAST) ---
if live_matches:
    for m in live_matches:
        st.toast(f"⚽ {m['homeTeam']['shortName']} {m['score']['fullTime']['home']} - {m['score']['fullTime']['away']} {m['awayTeam']['shortName']}", icon="📢")

# --- 4. INTERFACCIA PRINCIPALE ---
st.title("🏆 RANKING SALVEZZA LIVE")
st.markdown(f"**Target Salvezza: {soglia_salvezza}pt** | Proiezione Giornata {giocata}")

if ultime_8:
    for idx, team in enumerate(ultime_8):
        nome_full = team['team']['name']
        nome_display = nome_full.replace("FC", "").replace("CFC", "").replace("US", "").strip().upper()
        punti = team['points']
        pos = team['position']
        p_mancanti = max(0, soglia_salvezza - punti)
        
        # Algoritmo Percentuale Gerarchica (Bonus posizione per evitare duplicati)
        base_perc = (punti / soglia_salvezza) * 100
        bonus_pos = (20 - pos) # La 13° ha +7%, la 20° ha +0%
        perc_salv = min(int(base_perc + bonus_pos), 99)
        
        # Colore di sfondo
        bg_color = colori_scala[idx]
        # Controllo retrocessione matematica
        if (38 - giocata) * 3 < p_mancanti:
            bg_color, perc_salv = "#000000", 0

        # Rendering Box Squadra (Ottimizzato per Smartphone)
        st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 8px 15px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; color: white; margin-top: 10px;">
                <div style="display: flex; flex-direction: column;">
                    <span style="font-size: 0.6em; font-weight: bold; opacity: 0.8;">{pos}° POSTO</span>
                    <span style="font-weight: bold; font-size: 1.1em; letter-spacing: -0.5px;">{nome_display}</span>
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

        # --- DETTAGLI SOTTO-VOCE (PIANO E CALENDARIO) ---
        with st.expander(f"📊 PIANO SALVEZZA E CALENDARIO {nome_display}"):
            tab_p, tab_c = st.tabs(["🎯 Piano Salvezza", "📅 Calendario"])
            
            with tab_p:
                partite_sq = [m for m in calendario if nome_full in m['homeTeam']['name'] or nome_full in m['awayTeam']['name']]
                acc_p = 0
                target_p = soglia_salvezza - punti
                
                for m in partite_sq:
                    h, a = m['homeTeam']['name'], m['awayTeam']['name']
                    is_h = nome_full in h
                    avv = a if is_h else h
                    p_avv = pos_classifica.get(avv, 10)
                    
                    if acc_p >= target_p: res, icon, bg = "SALVEZZA RAGGIUNTA", "🥳", "#1a1c23"
                    elif p_avv <= 6: res, icon, bg = "SCONFITTA PREVISTA", "💀", "#212529"
                    elif p_avv >= 14 or is_h: res, icon, bg = "VITTORIA OBBLIGATORIA", "🔥", "#212529"; acc_p += 3
                    else: res, icon, bg = "PAREGGIO UTILE", "🤝", "#212529"; acc_p += 1
                    
                    st.markdown(f"""
                        <div style="background-color: {bg}; padding: 8px; border-radius: 5px; color: white; margin-bottom: 5px; border: 1px solid #444; display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 1.2em;">{icon}</span>
                            <div style="display: flex; flex-direction: column;">
                                <b style="font-size: 0.75em;">{res}</b>
                                <span style="font-size: 0.85em;">vs {avv}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            with tab_c:
                for m in [m for m in calendario if nome_full in m['homeTeam']['name'] or nome_full in m['awayTeam']['name']]:
                    dt = datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
                    st.markdown(f"""
                        <div style="padding: 5px; border-bottom: 1px solid #eee; font-size: 0.85em;">
                            <b>{dt.strftime('%d/%m - %H:%M')}</b>: {m['homeTeam']['shortName']} vs {m['awayTeam']['shortName']}
                        </div>
                    """, unsafe_allow_html=True)

else:
    st.error("Dati non disponibili. Controlla l'API Key.")

st.sidebar.button("🔄 AGGIORNA LIVE")

