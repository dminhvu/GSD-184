import io
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="GSD-184: Tynic")
st.title("GSD-184: Tynic")


def process_file(file):
    # 1. Read incoming file (no header)
    if file.name.lower().endswith(".csv"):
        df = pd.read_csv(file, header=None)
    elif file.name.lower().endswith((".xls", ".xlsx")):
        df = pd.read_excel(file, header=None)
    else:
        st.error("Unsupported file format. Please upload a CSV or Excel file.")
        return None
    if df.empty:
        st.error("The uploaded file is empty.")
        return None
    if df.shape[1] < 5:
        st.error("Input file must have at least 5 columns (A-E).")
        return None

    # 2. Prepare output DataFrame with headings
    output = pd.DataFrame()
    output["Debtor Reference"] = ""  # Col A
    output["Transaction Type"] = ""  # Col B
    output["Document Number"] = ""  # Col C
    output["Document Date"] = ""  # Col D
    output["Document Balance"] = ""  # Col E

    # 3. Data transformations according to requirements

    # A. Column A stays in Column A ("Debtor Reference")
    output["Debtor Reference"] = df.iloc[:, 0]

    # B. Column B moves to Column C ("Document Number")
    output["Document Number"] = df.iloc[:, 1]

    # C. Column C moves to Column D, reformatted as date DD/MM/YYYY ("Document Date")
    def parse_date(val):
        # Try common date formats
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(str(val), fmt).strftime("%d/%m/%Y")
            except Exception:
                continue
        try:
            # Fallback to pandas
            return pd.to_datetime(val, dayfirst=True, errors="coerce").strftime(
                "%d/%m/%Y"
            )
        except Exception:
            return ""

    output["Document Date"] = df.iloc[:, 2].apply(parse_date)

    # D. Column D moves to Column E, as float with 2 decimals ("Document Balance")
    def to_float_str(x):
        try:
            return f"{float(str(x).replace(',', '')):.2f}"
        except Exception:
            return ""

    output["Document Balance"] = df.iloc[:, 3].apply(to_float_str)

    # E. Column E moves to Column B, transformed to ALL CAPS, CRN->CRD ("Transaction Type")
    def transform_transaction_type(x):
        x = str(x).upper().replace("CRN", "CRD")
        return x

    output["Transaction Type"] = df.iloc[:, 4].apply(transform_transaction_type)

    # F. Final order: Debtor Reference, Transaction Type, Document Number, Document Date, Document Balance
    output = output[
        [
            "Debtor Reference",
            "Transaction Type",
            "Document Number",
            "Document Date",
            "Document Balance",
        ]
    ]

    return output


def get_csv_download_link(df):
    csv = df.to_csv(index=False)
    return io.BytesIO(csv.encode())


st.write("Upload your Excel or CSV file:")
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    processed_df = process_file(uploaded_file)
    if processed_df is not None:
        st.write("Processed Data:")
        st.dataframe(processed_df)
        csv_buffer = get_csv_download_link(processed_df)
        st.download_button(
            label="Download Processed File",
            data=csv_buffer,
            file_name="tynic_upload.csv",
            mime="text/csv",
        )
