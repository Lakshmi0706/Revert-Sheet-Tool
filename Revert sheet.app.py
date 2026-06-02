import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide")
st.title("🌐 Live Workflow Tool (Full Headers)")

# ✅ DATABASE
conn = sqlite3.connect("workflow.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS workflow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT
)
""")
conn.commit()

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

# ✅ LOAD DB
def load_data():
    try:
        df = pd.read_sql("SELECT * FROM workflow", conn)
        if df.empty:
            return pd.DataFrame()
        return pd.read_json(df["data"][0])
    except:
        return pd.DataFrame()

# ✅ SAVE DB
def save_data(df):
    conn.execute("DELETE FROM workflow")
    conn.commit()
    df_json = df.to_json()
    conn.execute("INSERT INTO workflow (data) VALUES (?)", (df_json,))
    conn.commit()

df = load_data()

# ✅ FIRST TIME UPLOAD
if df.empty:
    file = st.file_uploader("Upload Excel file", type=["xlsx"])
    if file is not None:
        df = pd.read_excel(file, engine="openpyxl")
        df.columns = df.columns.str.strip()

        # ✅ DO NOT REMOVE ANY COLUMNS ✅

        # Ensure workflow columns exist
        if "Agree/Disagree" not in df.columns:
            df["Agree/Disagree"] = ""
        if "Auditor's Review Status" not in df.columns:
            df["Auditor's Review Status"] = ""
        if "SME Status" not in df.columns:
            df["SME Status"] = ""
        if "Final Status" not in df.columns:
            df["Final Status"] = ""

        save_data(df)
        st.success("✅ Full data loaded")
        st.rerun()

    st.stop()

# ✅ CLEAN VALUES
df["Agree/Disagree"] = df["Agree/Disagree"].fillna("").str.upper()
df["Auditor's Review Status"] = df["Auditor's Review Status"].fillna("")
df["SME Status"] = df["SME Status"].fillna("")

# ✅ WORKFLOW FILTERS
coder_df = df[(df["Agree/Disagree"] != "DISAGREE") & (df["Auditor's Review Status"] == "")]
auditor_df = df[df["Agree/Disagree"] == "DISAGREE"]
sme_df = df[(df["Agree/Disagree"] == "DISAGREE") & (df["Auditor's Review Status"] != "")]
pdoa_df = df[df["SME Status"] != ""]

edited = None

# ✅ ROLE VIEWS (FULL DATA SHOWN ✅)

if role == "CODER":
    st.subheader("CODER VIEW")
    edited = st.data_editor(coder_df, use_container_width=True)

elif role == "AUDITOR":
    st.subheader("AUDITOR VIEW")
    edited = st.data_editor(auditor_df, use_container_width=True)

elif role == "SME":
    st.subheader("SME VIEW")
    edited = st.data_editor(sme_df, use_container_width=True)

elif role == "PDOA":
    st.subheader("PDOA VIEW")
    st.dataframe(pdoa_df)

# ✅ SAVE
if edited is not None:
    if st.button("Save Changes"):

        for idx in edited.index:
            df.loc[idx, edited.columns] = edited.loc[idx]

        # ✅ FINAL STATUS UPDATE
        df.loc[df["SME Status"] != "", "Final Status"] = "COMPLETED"

        save_data(df)
        st.success("✅ Updated successfully")
        st.rerun()
