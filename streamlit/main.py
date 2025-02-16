import os
import streamlit as st
import requests
import datetime

import pandas as pd
import plotly.express as px

API_URL = "https://chubby-krystyna-cuicuidev-da9ab1a9.koyeb.app"

def main():

    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None

    st.title("KovaaK's Tracking Tool")
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
        s4, s5 =  st.tabs(["Season 4", "Season 5"])
        show_season(s4, 4, "intermediate")
        show_season(s5, 5, "intermediate")


def show_season(anchor, season, difficulty):
    response = requests.get(f"{API_URL}/entries/voltaic-s{season}-{difficulty}", headers={"Authorization" : f"Bearer {st.session_state['access_token']}"})
    data = response.json()
    if data:
        df = pd.DataFrame(data).sort_values("ctime")
        df.loc[:,"ctime"] = df["ctime"].apply(lambda x: datetime.datetime.fromtimestamp(float(x)/1_000_000_000))

        fig = px.line(data_frame=df, x="ctime", y="score", color="scenario")
        anchor.plotly_chart(fig)

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

if __name__ == "__main__":
    main()