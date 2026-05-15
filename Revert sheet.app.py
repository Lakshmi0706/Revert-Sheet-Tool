import streamlit as st
import pandas as pd
import io
from datetime import datetime

# ── PAGE CONFIG ─────────────────────────────
st.set_page_config(
    page_title="Revert Sheet Review Tool",
    page_icon="📋",
    layout="wide"
)

# ── INIT SESSION ───────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "role" not in st.session_state:
    st.session_state.role = "Coder"
if "name" not in st.session_state:
    st.session_state.name = ""

# ── FUNCTIONS ──────────────────────────────
def normalize_df(raw):
    df = pd.DataFrame()

    def get_col(keys):
        for c in raw.columns:
            if any(k in c.lower() for k in keys):
                return c
        return None

    id_col = get_col(["id","ticket","case"])
    coder_col = get_col(["coder","agent"])
    auditor_col = get_col(["auditor","reviewer"])
    status_col = get_col(["status","result"])
    desc_col = get_col(["description","case","query"])
    comment_col = get_col(["comment","remark","feedback"])

    df["ID"] = raw[id_col] if id_col else range(len(raw))
    df["Coder Name"] = raw[coder_col] if coder_col else "Unknown"
    df["Auditor Name"] = raw[auditor_col] if auditor_col else "Unknown"
    df["Final Status"] = raw[status_col].astype(str).str.lower() if status_col else "fail"
    df["Description"] = raw[desc_col] if desc_col else ""
    df["Auditor Comment"] = raw[comment_col] if comment_col else ""

    df["Coder Response"] = ""
    df["Coder Note"] = ""
    df["SME Comment"] = ""
    df["SME Closed"] = ""

    return df

def export_excel(df):
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()

# ── SIDEBAR ────────────────────────────────
with st.sidebar:

    st.title("📋 RSR Tool")

    file = st.file_uploader("Upload Excel / CSV", type=["xlsx","csv"])

    if file:
        if file.name.endswith(".csv"):
            raw = pd.read_csv(file)
        else:
            raw = pd.read_excel(file)

        st.session_state.df = normalize_df(raw)
        st.success("✅ File Loaded")

    st.radio("Select Role", ["Coder","Auditor","SME"], key="role")

    if st.session_state.df is not None:
        df = st.session_state.df

        if st.session_state.role == "Coder":
            names = df["Coder Name"].astype(str).unique()
        elif st.session_state.role == "Auditor":
            names = df["Auditor Name"].astype(str).unique()
        else:
            names = ["SME Panel"]

        st.selectbox("Select Name", names, key="name")

        st.download_button(
            "⬇ Download Excel",
            export_excel(df),
            file_name="updated_revert_sheet.xlsx"
        )

# ── MAIN ───────────────────────────────────
df = st.session_state.df

if df is None:
    st.info("👈 Upload file from sidebar to start")
    st.stop()

role = st.session_state.role
name = st.session_state.name

st.title(f"{role} Dashboard")

# ── FILTER LOGIC ───────────────────────────
if role == "Coder":
    queue = df[
        (df["Final Status"] == "fail") &
        (df["Coder Name"].astype(str) == str(name)) &
        (df["Coder Response"] == "")
    ]

elif role == "Auditor":
    queue = df[
        (df["Final Status"] == "fail") &
        (df["Auditor Name"].astype(str) == str(name)) &
        (df["Coder Response"] == "disagree") &
        (df["SME Closed"] != "Yes")
    ]

else:  # SME
    queue = df[
        (df["Coder Response"] == "disagree") &
        (df["SME Closed"] != "Yes")
    ]

# ── DISPLAY ───────────────────────────────
if queue.empty:
    st.success("✅ No items in queue")
else:
    for i, row in queue.iterrows():

        st.markdown("---")
        st.subheader(f"ID: {row['ID']}")
        st.write("📌 Description:", row["Description"])
        st.write("📝 Auditor Comment:", row["Auditor Comment"])

        # CODER
        if role == "Coder":

            resp = st.radio(
                f"Response {i}",
                ["agree", "disagree"],
                key=f"resp_{i}"
            )

            note = st.text_area("Note", key=f"note_{i}")

            if st.button("Submit", key=f"btn_{i}"):
                df.at[i, "Coder Response"] = resp
                df.at[i, "Coder Note"] = note
                st.success("✅ Saved")
                st.rerun()

        # AUDITOR
        elif role == "Auditor":
            st.info("⏳ Waiting for SME decision")

        # SME
        else:
            st.write("Coder Response:", row["Coder Response"])
            st.write("Coder Note:", row["Coder Note"])

            comment = st.text_area("SME Comment", key=f"sme_{i}")

            if st.button("Close Case", key=f"close_{i}"):
                df.at[i, "SME Comment"] = comment
                df.at[i, "SME Closed"] = "Yes"
                st.success("✅ Closed")
                st.rerun()

# ── STATS ─────────────────────────────────
st.divider()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total", len(df))
c2.metric("Fails", (df["Final Status"] == "fail").sum())
c3.metric("Disagreed", (df["Coder Response"] == "disagree").sum())
c4.metric("Closed", (df["SME Closed"] == "Yes").sum())
