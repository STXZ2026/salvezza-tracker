import streamlit as st
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE ---
API_KEY = "c8cac2cec6e64345868d516c077c1685" 
ID_SERIE_A = "SA"

st.set_page_config(page_title="Survival Tracker Pro", layout="wide")

# Funzione recupero dati
def carica_dati():
    headers = {'X-Auth-Token': API_KEY}
    url_s = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/standings"
    url_m = f"https://api.football-data.org/v4/competitions/{ID_SERIE_A}/matches?status=SCHEDULED"
    try:
        res_s = requests.get(url_s, headers=headers, timeout=5)
        res_m = requests.get(url_m, headers=headers, timeout=5)
        if res_s.status_code != 200: return None, 25, [], 38, {}
        data_s = res_s.json()
        standings = data_s['standings'][0]['table']
        terzultima = standings[17]
        p_terz, g_terz = terzultima['points'], terzultima['playedGames']
        quota_f = max(34, min(int((p_terz / g_terz) * 38) + 1, 40)) if g_terz > 0 else 38
        classifica = {item['team']['name']: item['points'] for item in standings}
        posizioni = {item['team']['name']: item['position'] for item in standings}
        return classifica, standings[0]['playedGames'], res_m.json().get('matches', []), quota_f, posizioni
    except: return None, 25, [], 38, {}

classifica_vera, giocata, calendario, soglia_salvezza, posizioni_classifica = carica_dati()

if classifica_vera is None:
    st.error("Errore di connessione. Ricarica la pagina.")
    st.stop()

squadre_target = ["Torino", "Genoa", "Cremonese", "Lecce", "Fiorentina", "Pisa", "Verona"]

# --- 2. ELABORAZIONE ---
analisi_gruppo = []
for sq in squadre_target:
    p = next((v for k, v in classifica_vera.items() if sq in k), 0)
    nome_full = next((k for k in classifica_vera.keys() if sq in k), sq)
    perc = min(int((p / soglia_salvezza) * 100), 100)
    analisi_gruppo.append({"nome": sq, "nome_full": nome_full, "punti": p, "perc": perc})

# --- 3. INTERFACCIA ---
st.title("🏆 SURVIVAL TRACKER LIVE")
st.markdown(f"**Giornata {giocata}** | Obiettivo Salvezza: **{soglia_salvezza}pt**")

# Creiamo le colonne
cols = st.columns(len(squadre_target))

for i, dati in enumerate(analisi_gruppo):
    if dati['nome'] in ["Torino", "Genoa"]: color, lbl, txt = "#28A745", "✅ ZONA SICURA", "white"
    elif dati['nome'] in ["Cremonese", "Lecce", "Fiorentina"]: color, lbl, txt = "#FFA500", "⚖️ IN BILICO", "black"
    else: color, lbl, txt = "#FF4B4B", "⚠️ CRITICO", "white"

    p_mancanti = max(0, soglia_salvezza - dati['punti'])

    with cols[i]:
        # Box Squadra Principale
        st.markdown(f"""
            <div style="background-color: {color}; padding: 10px; border-radius: 10px 10px 0 0; text-align: center;">
                <p style="font-size: 0.7em; font-weight: bold; color: {txt}; margin:0;">{lbl}</p>
                <h3 style="color: {txt}; margin: 5px 0; font-size: 1.1em;">{dati['nome']}</h3>
            </div>
        """, unsafe_allow_html=True)

        # Tachimetro
        st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 15px 0; text-align: center; border: 1px solid #ddd; border-top:none; border-bottom:none;">
                <div style="position: relative; width: 70px; height: 70px; border-radius: 50%; background: conic-gradient({color} {dati['perc'] * 3.6}deg, #e0e0e0 0deg); margin: 0 auto;">
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 52px; height: 52px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 1.4em; font-weight: bold; color: #222;">{dati['punti']}</span>
                    </div>
                </div>
                <p style="font-size: 0.85em; color: #d63384; margin-top: 10px; font-weight: bold;">MANCANO: {p_mancanti}pt</p>
            </div>
        """, unsafe_allow_html=True)

        # --- SEZIONE DETTAGLIO INTEGRATA (PER IPHONE) ---
        # Usiamo gli expander per tenere tutto ordinato e sotto la squadra
        with st.expander("📅 Calendario"):
            partite = [m for m in calendario if dati['nome_full'] in m['homeTeam']['name'] or dati['nome_full'] in m['awayTeam']['name']]
            for m in partite:
                d_obj = datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
                st.markdown(f"""
                    <div style="background-color: #f1f3f5; padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #333; font-size: 0.8em; color: black;">
                        <b>{d_obj.strftime('%d/%m')}</b> - {m['homeTeam']['name']} vs {m['awayTeam']['name']}
                    </div>
                """, unsafe_allow_html=True)

        with st.expander("🎯 Piano Salvezza"):
            partite_p = [m for m in calendario if dati['nome_full'] in m['homeTeam']['name'] or dati['nome_full'] in m['awayTeam']['name']]
            accumulo = 0
            p_target = soglia_salvezza - dati['punti']
            
            for m in partite_p:
                home, away = m['homeTeam']['name'], m['awayTeam']['name']
                is_home = dati['nome_full'] in home
                avv = away if is_home else home
                pos_avv = posizioni_classifica.get(avv, 10)
                
                if accumulo >= p_target: res, icon, bg = "SALVEZZA RAGGIUNTA", "🥳", "#1a1c23"
                elif pos_avv <= 6: res, icon, bg = "SCONFITTA PREVISTA", "💀", "#212529"
                elif pos_avv >= 14 or is_home: res, icon, bg = "VITTORIA OBBLIGATORIA", "🔥", "#212529"
                else: res, icon, bg = "PAREGGIO UTILE", "🤝", "#212529"
                
                if res == "VITTORIA OBBLIGATORIA": accumulo += 3
                elif res == "PAREGGIO UTILE": accumulo += 1
                
                st.markdown(f"""
                    <div style="background-color: {bg}; padding: 10px; border-radius: 8px; text-align: center; color: white; border: 1px solid #444; margin-bottom: 8px;">
                        <span style="font-size: 1.1em;">{icon}</span><br>
                        <span style="font-size: 0.65em; font-weight: bold;">{res}</span><br>
                        <span style="font-size: 0.9em; font-weight: bold;">vs {avv}</span>
                    </div>
                """, unsafe_allow_html=True)

st.sidebar.button("🔄 AGGIORNA DATI LIVE")
