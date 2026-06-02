import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide")
st.title("🌐 Live Workflow Tool")

# ✅ DATABASE
conn = sqlite3.connect("workflow.db", check_same_thread=False)

# ✅ USERS
users = {
    "admin": {"password": "123", "role": "ADMIN"},
    "coder": {"password": "123", "role": "CODER"},
    "auditor": {"password": "123", "role": "AUDITOR"},
    "sme": {"password": "123", "role": "SME"},
    "pdoa": {"password": "123", "role": "PDOA"},
}

# ✅ SESSION
if "login" not in st.session_state:
    st.session_state.login = False

# ✅ LOGIN
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

# ✅ ✅ ADMIN UPLOAD (ALWAYS AVAILABLE ✅)
if role == "ADMIN":
    st.subheader("📤 Upload / Replace File")

    file = st.file_uploader("Upload Excel File", type=["xlsx"])

    if file is not None:
        new_df = pd.read_excel(file, engine="openpyxl")
        new_df.columns = new_df.columns.str.strip()

        # ✅ Ensure workflow columns exist
        workflow_cols = [
            "Agree/Disagree",
            "Auditor's Review Status",
            "SME Status",
            "Final Status"
        ]

        for col in workflow_cols:
            if col not in new_df.columns:
                new_df[col] = ""

        # ✅ Replace old data
        save_data(new_df)

        st.success("✅ File uploaded successfully (visible to all users)")
        st.rerun()

# ✅ STOP IF NO DATA
if df.empty:
    st.warning("⚠️ No data available. Admin must upload file.")
    st.stop()

# ✅ CLEAN DATA
df["Agree/Disagree"] = df["Agree/Disagree"].fillna("").str.upper()
df["Auditor's Review Status"] = df["Auditor's Review Status"].fillna("")
df["SME Status"] = df["SME Status"].fillna("")

# ✅ WORKFLOW FILTERS
coder_df = df[(df["Agree/Disagree"] != "DISAGREE") & (df["Auditor's Review Status"] == "")]
auditor_df = df[df["Agree/Disagree"] == "DISAGREE"]
sme_df = df[(df["Agree/Disagree"] == "DISAGREE") & (df["Auditor's Review Status"] != "")]
pdoa_df = df[df["SME Status"] != ""]

edited = None

# ✅ ✅ ROLE VIEWS

if role == "CODER":
    st.subheader("CODER VIEW")
    edited = st.data_editor(coder_df, use_container_width=True)

elif role == "AUDITOR":
    st.subheader("AUDITOR VIEW (DISAGREE ONLY)")
    edited = st.data_editor(auditor_df, use_container_width=True)

elif role == "SME":
    st.subheader("SME VIEW")
    edited = st.data_editor(sme_df, use_container_width=True)

elif role == "PDOA":
    st.subheader("PDOA VIEW (COMPLETED)")
    st.dataframe(pdoa_df)

# ✅ SAVE CHANGES
if edited is not None:
    if st.button("✅ Save Changes"):

        for i in edited.index:
            df.loc[i, edited.columns] = edited.loc[i]

        # ✅ Final Status update
        df.loc[df["SME Status"] != "", "Final Status"] = "COMPLETED"

        save_data(df)

        st.success("✅ Changes saved successfully")
        st.rerun()
