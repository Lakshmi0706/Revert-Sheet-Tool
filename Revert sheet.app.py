import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide")
st.title("🌐 Live Workflow Tool (Multi User)")

# ✅ DATABASE CONNECTION
conn = sqlite3.connect("workflow.db", check_same_thread=False)
cursor = conn.cursor()

# ✅ CREATE TABLE
cursor.execute("""
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

# ✅ LOGIN STATE
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ✅ LOGIN PAGE
if not st.session_state.logged_in:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u]["password"] == p:
            st.session_state.logged_in = True
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ✅ LOGOUT
if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

role = st.session_state.role
st.subheader(f"Logged in as: {role}")

# ✅ LOAD DATA FROM DB
def load_data():
    return pd.read_sql("SELECT * FROM workflow", conn)

# ✅ SAVE DATA TO DB
def save_data(df):
    df.to_sql("workflow", conn, if_exists="replace", index=False)

df = load_data()

# ✅ FIRST TIME DATA LOAD
if df.empty:
    st.info("Upload Excel file (only first time)")
    file = st.file_uploader("Upload", type=["xlsx"])

    if file is not None:
        new_df = pd.read_excel(file, engine="openpyxl")
        new_df.columns = new_df.columns.str.strip()

        # ✅ Map your columns
        new_df = new_df.rename(columns={
            "SAP ID": "sap_id",
            "Name": "name",
            "Agree/Disagree": "agree_disagree",
            "Auditor's Review Status": "auditor_status",
            "SME Status": "sme_status",
            "Final Status": "final_status"
        })

        new_df = new_df[["sap_id", "name", "agree_disagree",
                         "auditor_status", "sme_status", "final_status"]]

        save_data(new_df)
        st.success("Data loaded ✅")
        st.rerun()

    st.stop()

# ✅ PROCESS WORKFLOW
df["agree_disagree"] = df["agree_disagree"].fillna("")
df["auditor_status"] = df["auditor_status"].fillna("")
df["sme_status"] = df["sme_status"].fillna("")

coder_df = df[(df["agree_disagree"] != "DISAGREE") & (df["auditor_status"] == "")]
auditor_df = df[df["agree_disagree"].str.upper() == "DISAGREE"]
sme_df = df[(df["agree_disagree"].str.upper() == "DISAGREE") & (df["auditor_status"] != "")]
pdoa_df = df[df["sme_status"] != ""]

# ✅ ROLE VIEWS

# 👤 CODER
if role == "CODER":
    st.subheader("CODER - Update Agree/Disagree")
    edited = st.data_editor(coder_df, num_rows="dynamic")

# 👤 AUDITOR
elif role == "AUDITOR":
    st.subheader("AUDITOR - Only DISAGREE items")
    edited = st.data_editor(auditor_df, num_rows="dynamic")

# 👤 SME
elif role == "SME":
    st.subheader("SME - Review")
    edited = st.data_editor(sme_df, num_rows="dynamic")

# 👤 PDOA
elif role == "PDOA":
    st.subheader("PDOA - Completed")
    st.dataframe(pdoa_df)
    edited = None

# ✅ SAVE CHANGES (LIVE UPDATE)
if edited is not None:
    if st.button("✅ Save Changes"):
        for i in edited.index:
            df.loc[i, edited.columns] = edited.loc[i]

        # ✅ Final Status update
        df.loc[df["sme_status"] != "", "final_status"] = "COMPLETED"

        save_data(df)
        st.success("✅ Saved & Moved to Next Stage")
        st.rerun()
``
