import os
import streamlit as st
import requests
import datetime

import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go

from benchmarks import Benchmarks, Scenarios, Benchmark

API_URL = "https://chubby-krystyna-cuicuidev-da9ab1a9.koyeb.app"

def main():

    st.set_page_config(layout="wide", page_title="Aimalytics")

    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None

    if not st.session_state["access_token"]:
        st.title("Welcome to Aimalytics")
        st.header("The unofficial KovaaK's Tracking Tool.")
        st.write("Sign in to see your current progress!")
    else:
        st.title(f"Aimalytics: {st.session_state['username']}")
    st.sidebar.write("### Download")

    file_path = "streamlit/kovaaks_tracker_tool_setup.exe"

    try:
        with open(file_path, "br") as file:
            file_content = file.read()
            st.sidebar.download_button(
                label="Windows x64",
                data=file_content,
                file_name=os.path.basename(file_path),
                mime="application/octet-stream"
            )
    except FileNotFoundError:
        st.sidebar.error(f"Error: Setup file not found at path: {file_path}")
    except Exception as e:
        st.sidebar.error(f"An error occurred: {e}")

    authenticate()

    if st.session_state["access_token"]:
        nov, int_ =  st.tabs(["VT Season 5 Novice", "VT Season 5 Intermediate"])
        show_season(int_, 5, "intermediate")


def show_season(anchor, season, difficulty):
    c1, c2 = anchor.columns([3,1])
    response = requests.get(f"{API_URL}/entries/voltaic-s{season}-{difficulty}", headers={"Authorization" : f"Bearer {st.session_state['access_token']}"})
    data = response.json()
    if data:
        df = pd.DataFrame(data)
        df.loc[:,"ctime"] = df["ctime"].apply(lambda x: datetime.datetime.fromtimestamp(float(x)/1_000_000_000))

        dfs = []
        for hash_ in VOLTAIC_S5_INTERMEDIATE:
            df_ = df[df["hash"] == hash_]
            scores_series = df_.set_index(df_["ctime"]).resample("D").max()["score"]
            scores_series.name = df_["scenario"].dropna().unique()[0]
            dfs.append(scores_series)
            
        df__ = pd.concat(dfs, axis=1).interpolate("linear")

        series = []
        for col_pair, hash_pair, thresholds in zip(np.reshape(df__.columns, shape=(9,2)), np.reshape(VOLTAIC_S5_INTERMEDIATE, shape=(9,2)), np.reshape(VT_S5_INT_THRESHOLDS, shape=(9,2,4))):
            df_bench = df__[col_pair]
            df_bench.columns = hash_pair
            serie = parse_pair(df_bench, thresholds)
            series.append(serie)
            
        df_final = pd.concat(series, axis=1)
        fig = px.line(stats.hmean(df_final,axis=1), height=400)
        anchor.plotly_chart(fig)

        max_ = df_final.max(axis=0)
        THETA = [
            "Dynamic", "Static", "Linear",
            "Precise", "Reactive", "Control",
            "Speed", "Evasive", "Stability"
        ]
        fig = px.line_polar(theta=THETA, r=max_.values, line_close=True, range_r=[400,900])
        c2.plotly_chart(fig)

        random_data = np.expm1(np.random.normal(5.398594934535208, 1, 1000))
        random_data = random_data[np.where(random_data < 1250)]

        pdf = stats.gaussian_kde(random_data)

        fig = px.line(pdf.pdf(np.linspace(-100,1300,1000))*100)
        energy = stats.hmean(df_final.max(axis=0))
        trace = go.Scatter(
            x=[energy, energy],
            y=[0,.25],
            mode="lines"
        )
        fig.add_trace(trace)
        c1.plotly_chart(fig)

def authenticate():
    if not st.session_state["access_token"]:
        st.sidebar.write("### Sign in")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Sign in"):
            response = requests.post(f"{API_URL}/auth/token", data={"username" : username, "password" : password, "grant_type" : "password",})
            print(response.text)
            if response.status_code == 200:
                st.session_state["access_token"] = response.json()["access_token"]
                st.session_state["username"] = username
                st.rerun()
    else:
        st.sidebar.write(f"Signed in as **{st.session_state['username']}**")
        if st.sidebar.button("Sign out"):
            st.session_state["access_token"] = None
            st.rerun()

def match(score, array):
    closest_index = 0
    for idx, elem in enumerate(array):
        if elem <= score:
            closest_index = idx + 1
        else:
            break
    return closest_index

def choose(index, *args):
    return args[index - 1] if 0 < index <= len(args) else 0

def parse_pair(df, threshold_pair):
        
    def get_energy(score, thresholds):
        t1, t2, t3, t4 = thresholds
        e1, e2, e3, e4 = 500, 600, 700, 800

        match_array = [0, t1 - (t2 - t1), t1, t2, t3, t4]
        match_idx = match(score, match_array)
        if match_idx == 0:
            return 0

        base = choose(match_idx, 0, 400, e1, e2, e3, e4)
        adjustment = score - choose(match_idx, 0, t1 - (t2 - t1), t1, t2, t3, t4)
        denominator = choose(match_idx, t1 - (t2 - t1), t2 - t1, t2 - t1, t3 - t2, t4 - t3, t4 - t3)
        factor = choose(match_idx, 400, e1 - 400, e2 - e1, e3 - e2, e4 - e3, e4 - e3)

        if denominator == 0:
            return 0
        
        result = base + (adjustment / denominator) * factor
        return result
    
    df_ = df.copy()
    df_.iloc[:,0] = df_.iloc[:,0].apply(lambda x: get_energy(x, threshold_pair[0]))
    df_.iloc[:,1] = df_.iloc[:,1].apply(lambda x: get_energy(x, threshold_pair[1]))
    series = df_.max(axis=1)
    return series.cummax()

VOLTAIC_S5_INTERMEDIATE = [
    "830238e82c367ad2ba40df1da9968131", # PASU
    "86f9526f57828ad981f6c93b35811f94", # POPCORN
    "37975ba4bbbd5f9c593e7dbd72794baa", # 1W3TS
    "5c7668cf07b550bb2b7956f5709cf84e", # WW5T
    "ec8acdea37fa767767d705e389db1463", # FROGTAGON
    "47124ba125c1807fc7deb011c2f545a7", # FLOATING HEADS
    "b11e423dba738357ce774a01422e9d91", # PGT
    "ff38084d283c4e285150faee9c6b2832", # SNAKE TRACK
    "c4c11bf8a727b6e6c836138535bd0879", # AETHER
    "489b27e681807e0212eef50241bb0769", # GROUND
    "865d54422da5368dc290d1bbc2b9b566", # RAW CONTROL
    "a5fa9fbc3d55851b11534c60b85a9247", # CONTROLSPHERE
    "dfb397975f6fcec5bd2ebf3cd0b7a66a", # DOT TS
    "03d6156260b1b2b7893b746354b889c2", # EDDIE TS
    "ff777f42a21d6ddcf8791caf2821a2bd", # DRIFT TS
    "138c732d61151697949af4a3f51311fa", # FLY TS
    "e3b4fdab121562a8d4c8c2ac426c890c", # CONTROL TS
    "7cd5eee66632ebec0c33218d218ebf95", # PENTA BOUNCE
]

VT_S5_INT_THRESHOLDS = [
    (760, 840, 910, 970),
    (600, 690, 780, 860),
    (1120, 1220, 1310, 1390),
    (1310, 1400, 1490, 1570),
    (940, 1040, 1140, 1230),
    (610, 690, 770, 860),

    (2375, 2750, 3100, 3375),
    (2850, 3200, 3500, 3725),
    (2175, 2550, 2800, 3175),
    (2525, 2850, 3100, 3350),
    (2775, 3200, 3550, 3875),
    (2750, 3175, 3525, 3825),

    (1110, 1170, 1230, 1270),
    (900, 960, 1020, 1080),
    (390, 430, 460, 490),
    (470, 510, 540, 570),
    (430, 460, 490, 520),
    (450, 500, 540, 590),
]

if __name__ == "__main__":
    main()