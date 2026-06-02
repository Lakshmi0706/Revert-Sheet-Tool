import streamlit as st
import pandas as pd

st.set_page_config(page_title="Revert Sheet Tool", layout="wide")

st.title("Revert Sheet Tool")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # ✅ FIX: Explicitly specify openpyxl engine
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        st.success("File uploaded successfully!")

        st.subheader("Preview Data")
        st.dataframe(df)

        # Example transformation (modify if needed)
        st.subheader("Processed Output")
        
        # Example logic: reverse rows
        processed_df = df.iloc[::-1]

        st.dataframe(processed_df)

        # Download button
        output_file = "processed_output.xlsx"
        processed_df.to_excel(output_file, index=False, engine="openpyxl")

        with open(output_file, "rb") as f:
            st.download_button(
                label="Download Processed File",
                data=f,
                file_name="processed_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except ImportError:
        st.error("❌ Missing dependency: openpyxl. Please install it.")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
