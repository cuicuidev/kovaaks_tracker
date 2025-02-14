import streamlit as st
import requests

API_URL = "https://burning-selena-cuicuidev-ea43dc33.koyeb.app"

def main():
    with requests.get(f"{API_URL}/download/setup.exe", stream=True) as response:
        response.raise_for_status()
        file = response.content
    st.download_button("Download setup", data=file, file_name="kovaaks_tracker_tool_setup.exe", mime="application/octet-stream")

if __name__ == "__main__":
    main()