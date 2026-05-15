import streamlit as stimport streamlit as pandas as pd
import io
from datetime import datetime

# ── PAGE CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="Revert Sheet Review Tool",
    page_icon="📋",
    layout="wide"
)

# ── CLEAN CSS ──────────────────────────────────────────
st.markdown("""
<style>
.main { background: #0f1117; }
.rsr-card {
    background:#22263a;
    border:1px solid #2e3350;
    border-radius:12px;
    padding:15px;
    margin-bottom:10px;
}
.badge {
    padding:4px 10px;
    border-radius:15px;
    font-size:11px;
    margin-right:5px;
}
.pass { background:#0f2d1e; color:#22c55e; }
.fail { background:#2d0f18; color:#f43f5e; }
.agree { background:#0f2d1e; color:#22c55e; }
.disagree { background:#2d0f18; color:#f43f5e; }
.closed { background:#444; color:#ddd; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────
for k, v in {
    "df": None,
    "role": "Coder",
    "name": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── HELPERS ────────────────────────────────────────────
def normalize_df(raw):
    df = pd.DataFrame()
    cols = [c.lower() for c in raw.columns]

    def get_col(keyword_list):
        for c in raw.columns:
            for k in keyword_list:
                if k in c.lower():
                    return c
        return None

    df["ID"] = raw[get_col(["id","ticket","case"])].astype(str) if get_col(["id"]) else range(len(raw))
    df["Coder Name"] = raw[get_col(["coder","agent"])] if get_col(["coder"]) else "Unknown"
    df["Auditor Name"] = raw[get_col(["auditor","reviewer"])] if get_col(["auditor"]) else "Unknown"
    df["Final Status"] = raw[get_col(["status","result"])].str.lower()
    df["Description"] = raw[get_col(["description","case","query"])] if get_col(["description"]) else ""
    df["Auditor Comment"] = raw[get_col(["comment","remark"])] if get_col(["comment"]) else ""

    df["Coder Response"] = ""
    df["Coder Note"] = ""
    df["SME Comment"] = ""
    df["SME Closed"] = ""

    return df

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ── SIDEBAR ────────────────────────────────────────────
with st.sidebar:

    st.title("📋 RSR Tool")

    file = st.file_uploader("Upload Excel/CSV", type=["xlsx","csv"])

    if file:
        if file.name.endswith(".csv"):
            raw = pd.read_csv(file)
        else:
            raw = pd.read_excel(file)

        st.session_state.df = normalize_df(raw)
        st.success("File loaded ✅")

    st.radio("Role", ["Coder","Auditor","SME"], key="role")

    if st.session_state.df is not None:

        df = st.session_state.df

        if st.session_state.role == "Coder":
            names = df["Coder Name"].unique()
        elif st.session_state.role == "Auditor":
            names = df["Auditor Name"].unique()
        else:
            names = ["SME Panel"]

        st.selectbox("Select Name", names, key="name")

        st.download_button(
            "⬇ Download Excel",
            to_excel(df),
            file_name="updated_revert.xlsx"
        )

# ── MAIN ───────────────────────────────────────────────
df = st.session_state.df

if df is None:
    st.info("Upload a file to begin.")
    st.stop()

role = st.session_state.role
name = st.session_state.name

# ── FILTER LOGIC ───────────────────────────────────────
if role == "Coder":
    queue = df[(df["Final Status"]=="fail") & (df["Coder Name"]==name) & (df["Coder Response"]=="")]

elif role == "Auditor":
    queue = df[(df["Final Status"]=="fail") &
               (df["Auditor Name"]==name) &
               (df["Coder Response"]=="disagree") &
               (df["SME Closed"]!="Yes")]

else:  # SME
    queue = df[(df["Coder Response"]=="disagree") & (df["SME Closed"]!="Yes")]

# ── DISPLAY ───────────────────────────────────────────
st.header(f"{role} Queue")

if queue.empty:
    st.success("No items ✅")
else:

    for i, row in queue.iterrows():

        with st.container():
            st.markdown(f"### {row['ID']}")
            st.write(row["Description"])

            st.write("**Auditor Comment:**", row["Auditor Comment"])

            # CODER VIEW
            if role == "Coder":

                resp = st.radio(
                    f"Response {i}",
                    ["agree","disagree"],
                    key=f"resp_{i}"
                )

                note = st.text_area("Note", key=f"note_{i}")

                if st.button("Submit", key=f"btn_{i}"):

                    df.at[i, "Coder Response"] = resp
                    df.at[i, "Coder Note"] = note
                    st.success("Saved ✅")
                    st.rerun()

            # SME VIEW
            elif role == "SME":

                st.write("Coder said:", row["Coder Response"])
                st.write("Coder Note:", row["Coder Note"])

                comment = st.text_area("SME Comment", key=f"sme_{i}")

                if st.button("Close", key=f"close_{i}"):

                    df.at[i, "SME Comment"] = comment
                    df.at[i, "SME Closed"] = "Yes"
                    st.success("Closed ✅")
                    st.rerun()

            # AUDITOR VIEW
            else:
                st.info("Waiting for SME resolution")

# ── STATS ──────────────────────────────────────────────
st.divider()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", len(df))
c2.metric("Fail", (df["Final Status"]=="fail").sum())
c3.metric("Disagree", (df["Coder Response"]=="disagree").sum())
c4.metric("Closed", (df["SME Closed"]=="Yes").sum())
