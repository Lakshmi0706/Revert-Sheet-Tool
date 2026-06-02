import streamlit as st
import pandas as pd

st.set_page_config(page_title="Workflow Tool", layout="wide")
st.title("🔐 Role-Based Workflow Tool")

# ✅ USERS (LOGIN)
users = {
    "coder": {"password": "123", "role": "CODER"},
    "auditor": {"password": "123", "role": "AUDITOR"},
    "sme": {"password": "123", "role": "SME"},
    "pdoa": {"password": "123", "role": "PDOA"},
}

# ✅ SESSION
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ✅ LOGIN SCREEN
if not st.session_state.logged_in:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = users[username]["role"]
            st.success(f"Logged in as {st.session_state.role}")
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

# ✅ FILE UPLOAD
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file, engine="openpyxl")
    df.columns = df.columns.str.strip()

    # ✅ BUCKETS
    coder_rows = []
    auditor_rows = []
    sme_rows = []
    pdoa_rows = []

    # ✅ MAIN WORKFLOW LOGIC
    for _, row in df.iterrows():

        coder = str(row.get("Agree/Disagree", "")).strip().upper()
        auditor = str(row.get("Auditor's Review Status", "")).strip().upper()
        sme = str(row.get("SME Status", "")).strip().upper()

        # ✅ SME → PDOA
        if sme not in ["", "NAN"]:
            row["Final Status"] = "COMPLETED"
            pdoa_rows.append(row)

        # ✅ AUDITOR → SME
        elif auditor not in ["", "NAN"]:
            sme_rows.append(row)

        # ✅ CODER → AUDITOR (ONLY DISAGREE)
        elif coder == "DISAGREE":
            auditor_rows.append(row)

        # ✅ CODER (AGREE stays here ✅)
        else:
            coder_rows.append(row)

    # ✅ CONVERT
    coder_df = pd.DataFrame(coder_rows)
    auditor_df = pd.DataFrame(auditor_rows)
    sme_df = pd.DataFrame(sme_rows)
    pdoa_df = pd.DataFrame(pdoa_rows)

    st.success("✅ Workflow processed successfully!")

    # ✅ ROLE-BASED DISPLAY
    if role == "CODER":
        st.subheader("📌 CODER VIEW")
        st.dataframe(coder_df)

    elif role == "AUDITOR":
        st.subheader("📌 AUDITOR VIEW (Only DISAGREE items)")
        st.dataframe(auditor_df)

    elif role == "SME":
        st.subheader("📌 SME VIEW")
        st.dataframe(sme_df)

    elif role == "PDOA":
        st.subheader("📌 PDOA VIEW (Completed)")
        st.dataframe(pdoa_df)

    # ✅ SAVE OUTPUT FILE
    output_file = "workflow_output.xlsx"

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        coder_df.to_excel(writer, sheet_name="CODER", index=False)
        auditor_df.to_excel(writer, sheet_name="AUDITOR", index=False)
        sme_df.to_excel(writer, sheet_name="SME", index=False)
        pdoa_df.to_excel(writer, sheet_name="PDOA", index=False)

    # ✅ DOWNLOAD
    with open(output_file, "rb") as f:
        st.download_button(
            "⬇️ Download Workflow File",
            data=f,
            file_name=output_file
        )
