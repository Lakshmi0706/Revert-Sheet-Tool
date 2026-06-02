import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide")
st.title("🌐 Live Workflow Tool (Multi User)")

# ✅ DATABASE CONNECTION
conn = sqlite3.connect("workflow.db", check_same_thread=False)

# ✅ CREATE TABLE
conn.execute("""
CREATE TABLE IF NOT EXISTS workflow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sap_id TEXT,
    name TEXT,
    agree_disagree TEXT,
    auditor_status TEXT,
    sme_status TEXT,
    final_status TEXT
)
""")
conn.commit()

# ✅ LOGIN USERS
users = {
    "coder": {"password": "123", "role": "CODER"},
    "auditor": {"password": "123", "role": "AUDITOR"},
    "sme": {"password": "123", "role": "SME"},
    "pdoa": {"password": "123", "role": "PDOA"},
}

# ✅ SESSION
if "login" not in st.session_state:
    st.session_state.login = False

# ✅ LOGIN PAGE
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

# ✅ LOGOUT
if st.button("Logout"):
    st.session_state.login = False
    st.rerun()

role = st.session_state.role
st.subheader(f"Logged in as: {role}")

# ✅ LOAD DATA
def load_data():
    try:
        return pd.read_sql("SELECT * FROM workflow", conn)
    except:
        return pd.DataFrame()

# ✅ SAVE DATA
def save_data(df):
    df.to_sql("workflow", conn, if_exists="replace", index=False)

df = load_data()

# ✅ FIRST TIME UPLOAD
if df.empty:
    st.warning("Upload Excel file (first time only)")
    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file is not None:
        new_df = pd.read_excel(file, engine="openpyxl")
        new_df.columns = new_df.columns.str.strip()

        # ✅ MAP COLUMNS
        new_df = new_df.rename(columns={
            "SAP ID": "sap_id",
            "Name": "name",
            "Agree/Disagree": "agree_disagree",
            "Auditor's Review Status": "auditor_status",
            "SME Status": "sme_status",
            "Final Status": "final_status"
        })

        new_df = new_df[
            [
                "sap_id",
                "name",
                "agree_disagree",
                "auditor_status",
                "sme_status",
                "final_status",
            ]
        ]

        save_data(new_df)
        st.success("✅ Data loaded")
        st.rerun()

    st.stop()

# ✅ CLEAN VALUES
df["agree_disagree"] = df["agree_disagree"].fillna("").str.upper()
df["auditor_status"] = df["auditor_status"].fillna("")
df["sme_status"] = df["sme_status"].fillna("")

# ✅ WORKFLOW FILTERS (FIXED ✅)

coder_df = df[(df["agree_disagree"] != "DISAGREE") & (df["auditor_status"] == "")]
auditor_df = df[df["agree_disagree"] == "DISAGREE"]
sme_df = df[(df["agree_disagree"] == "DISAGREE") & (df["auditor_status"] != "")]
pdoa_df = df[df["sme_status"] != ""]

# ✅ ROLE VIEWS

edited = None

if role == "CODER":
    st.subheader("CODER - Update Agree/Disagree")
    edited = st.data_editor(coder_df, use_container_width=True)

elif role == "AUDITOR":
    st.subheader("AUDITOR - DISAGREE Items")
    edited = st.data_editor(auditor_df, use_container_width=True)

elif role == "SME":
    st.subheader("SME - Review")
    edited = st.data_editor(sme_df, use_container_width=True)

elif role == "PDOA":
    st.subheader("PDOA - Completed")
    st.dataframe(pdoa_df)

# ✅ SAVE LOGIC
if edited is not None:
    if st.button("✅ Save Changes"):

        for idx in edited.index:
            df.loc[idx, edited.columns] = edited.loc[idx]

        # ✅ Final Status update
        df.loc[df["sme_status"] != "", "final_status"] = "COMPLETED"

        save_data(df)
        st.success("✅ Saved successfully")
        st.rerun()
``
