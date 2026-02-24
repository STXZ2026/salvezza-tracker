# --- CHIAVE DA COPIARE c8cac2cec6e64345868d516c077c1685

import streamlit as st
import requests
import re
from datetime import datetime, timedelta

# Gestione errore libreria autorefresh
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# --- 1. CONFIGURAZIONE ---
API_KEY = "c8cac2cec6e64345868d516c077c1685" 
ID_SERIE_A = "SA"

st.set_page_config(page_title="Survival Tracker Pro", layout="wide")

if st_autorefresh:
    st_autorefresh(interval=60 * 1000, key="datarefresh")

def pulisci_nome(nome):
    nome = re.sub(r'\d+', '', nome)
    sigle = ["FC", "CFC", "US", "ACF", "AC", "SC", "AS", "SS", "BC", "HELLAS", "H.", "BP", "1909"]
    for s in sigle:
        nome = re.sub(r'\b' + s + r'\b', '', nome, flags=re.IGNORECASE)
    nome = re.sub(r'\b[a-zA-Z]\b', '', nome)
    return nome.strip().upper()

def carica_dati():
    headers = {'X-Auth-Token': API_KEY}
    url_s = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/standings"
    # Carichiamo TUTTE le partite per avere il piano completo
    url_m = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/matches"
    
    try:
        res_s = requests.get(url_s, headers=headers, timeout=10)
        res_m = requests.get(url_m, headers=headers, timeout=10)
        
        if res_s.status_code != 200: return None, 0, [], 38, {}, []
        
        data_s = res_s.json()
        standings = data_s['standings'][0]['table']
        ultime_8 = standings[12:20]
        
        terzultima = standings[17]
        giocate_t = max(1, terzultima['playedGames'])
        quota_f = max(34, min(int((terzultima['points'] / giocate_t) * 38) + 1, 40))
        
        posizioni = {item['team']['name']: item['position'] for item in standings}
        tutti_match = res_m.json().get('matches', [])
        
        match_live = [m for m in tutti_match if m['status'] in ['IN_PLAY', 'PAUSED']]
        # Calendario futuro per il piano
        match_futuri = [m for m in tutti_match if m['status'] in ['TIMED', 'SCHEDULED']]
        
        return ultime_8, standings[0]['playedGames'], match_futuri, quota_f, posizioni, match_live
    except:
        return None, 0, [], 38, {}, []

ultime_8, giocata, calendario, soglia_salvezza, pos_classifica, live_matches = carica_dati()

# --- 2. SCALA CROMATICA ---
colori_scala = ["#2E7D32", "#689F38", "#AFB42B", "#FBC02D", "#FF8F00", "#D84315", "#B71C1C", "#8B0000"]

# --- 3. INTERFACCIA ---
st.title("🏆 RANKING SALVEZZA LIVE")
st.markdown(f"**Target Salvezza: {soglia_salvezza}pt** | {datetime.now().strftime('%H:%M:%S')}")

if ultime_8:
    for idx, team in enumerate(ultime_8):
        nome_full = team['team']['name']
        nome_clean = pulisci_nome(nome_full)
        punti = team['points']
        pos = team['position']
        p_mancanti = max(0, soglia_salvezza - punti)
        
        base_perc = (punti / soglia_salvezza) * 100
        bonus_pos = (20 - pos)
        perc_salv = min(int(base_perc + bonus_pos), 99)
        bg_color = colori_scala[idx]

        st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 8px 15px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; color: white; margin-top: 10px;">
                <div style="display: flex; flex-direction: column;">
                    <span style="font-size: 0.6em; font-weight: bold; opacity: 0.85;">{pos}° POSTO</span>
                    <span style="font-weight: bold; font-size: 1.3em;">{nome_clean}</span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 2.2em; font-weight: 900; line-height: 1;">{punti}</span>
                </div>
            </div>
            <div style="background-color: #f8f9fa; padding: 6px 10px; border: 1px solid #ddd; border-top:none; display: flex; align-items: center; justify-content: space-between; border-radius: 0 0 10px 10px;">
                <div style="text-align: center; flex: 1;">
                    <div style="position: relative; width: 42px; height: 42px; border-radius: 50%; background: conic-gradient({bg_color} {perc_salv * 3.6}deg, #e0e0e0 0deg); margin: 0 auto;">
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 32px; height: 32px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 0.7em; font-weight: bold; color: #222;">{perc_salv}%</span>
                        </div>
                    </div>
                </div>
                <div style="text-align: center; flex: 2;">
                    <p style="font-size: 0.9em; color: #d63384; font-weight: bold; margin:0;">MANCANO: {p_mancanti}pt</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander(f"📊 PIANO SALVEZZA E DATE"):
            tab_p, tab_c = st.tabs(["🎯 Strategia", "📅 Calendario"])
            
            # FILTRO PARTITE SQUADRA
            partite_sq = [m for m in calendario if nome_full in m['homeTeam']['name'] or nome_full in m['awayTeam']['name']]
            
            with tab_p:
                acc_p = 0
                target_p = soglia_salvezza - punti
                st.write(f"Cammino per i {soglia_salvezza} punti:")
                
                for m in partite_sq:
                    h, a = m['homeTeam']['name'], m['awayTeam']['name']
                    is_h = nome_full in h
                    avv = a if is_h else h
                    pos_avv = pos_classifica.get(avv, 10)
                    
                    # LOGICA PIANO COMPLETO
                    if acc_p >= target_p:
                        res, icon, bg = "SALVEZZA RAGGIUNTA", "🥳", "#1a1c23"
                    elif pos_avv <= 6:
                        res, icon, bg = "SCONFITTA PREVISTA", "💀", "#212529"
                    elif pos_avv >= 14 or is_h:
                        res, icon, bg = "VITTORIA OBBLIGATORIA", "🔥", "#212529"
                        acc_p += 3
                    else:
                        res, icon, bg = "PAREGGIO UTILE", "🤝", "#212529"
                        acc_p += 1
                    
                    st.markdown(f"""<div style='background-color:{bg}; padding:8px; border-radius:5px; color:white; margin-bottom:5px; font-size:0.8em; border-left: 4px solid {bg_color};'>
                        {icon} <b>{res}</b> vs {pulisci_nome(avv)} ({'Casa' if is_h else 'Fuori'})
                    </div>""", unsafe_allow_html=True)
            
            with tab_c:
                for m in partite_sq[:6]: # Mostra le prossime 6 date
                    dt = datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
                    st.markdown(f"<div style='font-size:0.8em; border-bottom:1px solid #eee; padding:5px;'><b>{dt.strftime('%d/%m')}</b>: {pulisci_nome(m['homeTeam']['name'])} vs {pulisci_nome(m['awayTeam']['name'])}</div>", unsafe_allow_html=True)

st.sidebar.button("🔄 AGGIORNA ORA")
