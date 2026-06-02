import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide")
st.title("🌐 Live Workflow Tool (Full Headers)")

# ✅ DB
conn = sqlite3.connect("workflow.db", check_same_thread=False)

# ✅ LOGIN
users = {
    "coder": {"password": "123", "role": "CODER"},
    "auditor": {"password": "123", "role": "AUDITOR"},
    "sme": {"password": "123", "role": "SME"},
    "pdoa": {"password": "123", "role": "PDOA"},
}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u]["password"] == p:
            st.session_state.login = True
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

if st.button("Logout"):
    st.session_state.login = False
    st.rerun()

role = st.session_state.role
st.subheader("Logged in as: " + role)

# ✅ DB FUNCTIONS
def load_data():
    try:
        return pd.read_sql("SELECT * FROM workflow", conn)
    except:
        return pd.DataFrame()

def save_data(df):
    df.to_sql("workflow", conn, if_exists="replace", index=False)

df = load_data()

# ✅ FIRST UPLOAD
if df.empty:
    file = st.file_uploader("Upload Excel", type=["xlsx"])
    if file:
        df = pd.read_excel(file, engine="openpyxl")
        df.columns = df.columns.str.strip()

        # Ensure workflow columns
        for col in ["Agree/Disagree", "Auditor's Review Status", "SME Status", "Final Status"]:
            if col not in df.columns:
                df[col] = ""

        save_data(df)
        st.success("✅ Data loaded")
        st.rerun()

    st.stop()

# ✅ CLEAN
df["Agree/Disagree"] = df["Agree/Disagree"].fillna("").str.upper()
df["Auditor's Review Status"] = df["Auditor's Review Status"].fillna("")
df["SME Status"] = df["SME Status"].fillna("")

# ✅ WORKFLOW
coder_df = df[(df["Agree/Disagree"] != "DISAGREE") & (df["Auditor's Review Status"] == "")]
auditor_df = df[df["Agree/Disagree"] == "DISAGREE"]
sme_df = df[(df["Agree/Disagree"] == "DISAGREE") & (df["Auditor's Review Status"] != "")]
pdoa_df = df[df["SME Status"] != ""]

edited = None

if role == "CODER":
    edited = st.data_editor(coder_df, use_container_width=True)

elif role == "AUDITOR":
    edited = st.data_editor(auditor_df, use_container_width=True)

elif role == "SME":
    edited = st.data_editor(sme_df, use_container_width=True)

elif role == "PDOA":
    st.dataframe(pdoa_df)

# ✅ SAVE
if edited is not None:
    if st.button("Save Changes"):
        for i in edited.index:
            df.loc[i, edited.columns] = edited.loc[i]

        df.loc[df["SME Status"] != "", "Final Status"] = "COMPLETED"

        save_data(df)
        st.success("✅ Saved")
        st.rerun()
