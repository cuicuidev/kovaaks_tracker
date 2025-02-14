import os
import streamlit as st

def main():
    file_path = "streamlit/kovaaks_tracker_tool_setup.exe"

    try:
        with open(file_path, "br") as file:
            file_content = file.read()
            st.download_button(
                label="Download setup",
                data=file_content,
                file_name=os.path.basename(file_path),
                mime="application/octet-stream"
            )
    except FileNotFoundError:
        st.error(f"Error: Setup file not found at path: {file_path}")
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()