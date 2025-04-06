import os
import streamlit as st
import requests
import datetime

import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go

from benchmarks import Benchmark

API_URL = "http://127.0.0.1:8000"# "https://chubby-krystyna-cuicuidev-da9ab1a9.koyeb.app"

BENCHMARK_CATEGORIES = ["Dynamic", "Static", "Linear", "Precise", "Reactive", "Control", "Speed", "Evasive", "Stability"]

PLOTLY_COLOR_ACCENT=["rgb(1, 0, 1)", "rgb(1, 0.2, 1)", "rgb(1, 0.4, 1)"]

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
        st.title(f'Aimalytics for _**{st.session_state['username']}**_')
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
        nov, int_, adv =  st.tabs(["VT Season 5 Novice", "VT Season 5 Intermediate", "VT Season 5 Advanced"])
        show_season(nov, 5, "novice")
        show_season(int_, 5, "intermediate")
        show_season(adv, 5, "advanced")
        st.sidebar.write("---")        

def show_season(anchor, season, difficulty):
    response = requests.get(f"{API_URL}/entry/me/vt-s{season}-{difficulty}/all", headers={"Authorization" : f"Bearer {st.session_state['access_token']}"})
    
    if response.status_code != 200:
        anchor.warning("Unable to retrieve data.")
        return
    
    try:
        data = response.json()
        entries = data["entries"]
        thresholds = data["thresholds"]
        energy_thresholds = data["energy_thresholds"]
        del data
    except:
        anchor.warning("Unable to retrieve data.")
        return
    
    if not len(set([entry["hash"] for entry in entries if entry["hash"] in thresholds.keys()])) == len(thresholds.keys()):
        anchor.warning("Not enough data.")
        return
    
    # Processing
    benchmark = Benchmark(thresholds=thresholds, energy_thresholds=energy_thresholds)

    df = pd.DataFrame(entries)
    df.loc[:,"ctime"] = df["ctime"].apply(lambda x: datetime.datetime.fromtimestamp(float(x)/1_000_000_000))

    # Get the daily max score
    dfs = []
    for hash_ in benchmark.thresholds.keys():
        df_ = df[df["hash"] == hash_]
        scores_series = df_.set_index(df_["ctime"]).resample("D")["score"].max().apply(lambda x: benchmark.get_energy(x, hash_))
        scores_series.name = df_["scenario"].dropna().unique()[0]
        dfs.append(scores_series)
        
    df__ = pd.concat(dfs, axis=1).interpolate("linear")
    del dfs

    # Get the cumsum of the daily max score
    series = []
    for col_pair in np.reshape(df__.columns, shape=(9,2)):
        df_bench = df__[col_pair]
        serie = parse_pair(df_bench)
        series.append(serie)
    del df__
        
    df_energy_cummax = pd.concat(series, axis=1).dropna()
    fig_energy_progress = px.line(x=df_energy_cummax.index, y=stats.hmean(df_energy_cummax,axis=1), height=400, color_discrete_sequence=PLOTLY_COLOR_ACCENT)

    # All time max score for radar graph
    max_ = df_energy_cummax.max(axis=0)
    fig_radar = px.line_polar(theta=BENCHMARK_CATEGORIES, r=max_.values, line_close=True, range_r=[energy_thresholds[0] - 100, energy_thresholds[-1] + 100], color_discrete_sequence=PLOTLY_COLOR_ACCENT)
    fig_radar.update_layout(polar=dict(bgcolor = "rgba(0.0, 0.0, 0.0, 0.0)"))

    # Synthetic data as a placeholder
    percentile_data = requests.get(API_URL + f"/entry/percentiles/vt-s{season}-{difficulty}", headers={"Authorization" : f"Bearer {st.session_state['access_token']}"})
    percentiles_df = pd.DataFrame({k : [row["score"] for row in v] for k, v in percentile_data.json().items()}, index=range(1,101)).reset_index()
    percentiles_df = percentiles_df.drop(["index"], axis=1)

    percentiles = []

    for row in percentiles_df.iloc:
        energies = {hash_ : benchmark.get_energy(score, hash_) for hash_, score in row.to_dict().items()}
        pairs = [max(energy_a, energy_b) for energy_a, energy_b in zip(list(energies.values())[::2], list(energies.values())[1::2])]
        percentiles.append(stats.hmean(pairs))        

    # Histogram to compare with the population
    pdf = stats.gaussian_kde(percentiles)
    fig_histogram = px.line(pdf.pdf(np.linspace(-100,1300,1000))*100, color_discrete_sequence=PLOTLY_COLOR_ACCENT)
    energy = stats.hmean(df_energy_cummax.max(axis=0))
    trace = go.Scatter(
        x=[energy, energy],
        y=[0,.25],
        mode="lines"
    )
    fig_histogram.add_trace(trace)
    
    # Redering all charts
    c1, c2 = anchor.columns([3,1])
    c2.plotly_chart(fig_radar)
    c1.plotly_chart(fig_histogram)
    anchor.plotly_chart(fig_energy_progress)

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

def parse_pair(df):
    series = df.max(axis=1)
    return series.cummax()

if __name__ == "__main__":
    main()