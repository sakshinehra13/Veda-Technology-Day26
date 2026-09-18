import streamlit as st
import pandas as pd
import json
import io
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Configuration-Driven ETL Pipeline",
    page_icon="⚡",
    layout="wide"
)

# --- CUSTOM CSS (Properly wrapped in strings to fix SyntaxError) ---
st.markdown("""
<style>
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; }
    ::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #555; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Configuration-Driven ETL Pipeline Dashboard")
st.markdown("Task 26: Build an ETL pipeline whose input source, transformations, output location, and validation rules are controlled through configuration[cite: 1].")

# --- INITIALIZE SESSION STATE FOR LOGS & DATA ---
if "logs" not in st.session_state:
    st.session_state.logs = []
if "raw_df" not in st.session_state:
    # Default sample data
    st.session_state.raw_df = pd.DataFrame({
        "emp_id": [101, 102, 103, 104, 105, None],
        "emp_name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
        "emp_sal": [45000, 62000, 75000, 48000, 90000, 55000]
    })
if "final_df" not in st.session_state:
    st.session_state.final_df = None

def log_message(stage, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] [{stage.upper()}] {message}")

# --- SIDEBAR: CONFIGURATION EDITOR ---
st.sidebar.header("⚙️ Pipeline Configuration")
st.sidebar.markdown("Modify JSON configuration below to control the pipeline behavior in real-time[cite: 1].")

default_config = {
  "source": {
    "format": "csv"
  },
  "transformations": {
    "drop_nulls": True,
    "rename_columns": {
      "emp_id": "ID",
      "emp_name": "Name",
      "emp_sal": "Salary"
    },
    "filter_condition": "Salary > 50000"
  },
  "validation": {
    "not_null_columns": ["ID", "Name", "Salary"],
    "min_salary": 0
  },
  "output": {
    "format": "csv"
  }
}

config_text = st.sidebar.text_area("config.json", value=json.dumps(default_config, indent=2), height=320)

try:
    config = json.loads(config_text)
except Exception as e:
    st.sidebar.error(f"Invalid JSON Configuration: {e}")
    config = default_config

# --- TABS FOR APP NAVIGATION ---
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Pipeline Runner", "📊 Data Inspector", "📜 Pipeline Logs", "💡 Interview Guide"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Input Data Source")
        uploaded_file = st.file_uploader("Upload custom CSV file (Optional)", type=["csv"])
        if uploaded_file is not None:
            st.session_state.raw_df = pd.read_csv(uploaded_file)
            st.success("Uploaded file loaded successfully!")
        
        st.dataframe(st.session_state.raw_df, use_container_width=True)
        st.info(f"Raw Records Count: **{len(st.session_state.raw_df)}**")

    with col2:
        st.subheader("2. Execute ETL Pipeline")
        st.markdown("Click below to run extraction, configuration-based transformation, validation, and loading[cite: 1].")
        
        if st.button("▶ Run Pipeline", type="primary"):
            st.session_state.logs = [] # Reset logs
            try:
                # EXTRACT
                df = st.session_state.raw_df.copy()
                log_message("EXTRACT", f"Loaded {len(df)} records from data source.")
                
                # TRANSFORM
                t_config = config.get("transformations", {})
                if t_config.get("drop_nulls"):
                    df = df.dropna()
                    log_message("TRANSFORM", "Dropped rows with null values.")
                
                rename_map = t_config.get("rename_columns", {})
                df = df.rename(columns=rename_map)
                log_message("TRANSFORM", f"Renamed columns using mapping: {rename_map}")
                
                condition = t_config.get("filter_condition")
                if condition:
                    df = df.query(condition)
                    log_message("TRANSFORM", f"Applied filter query: '{condition}'. Remaining records: {len(df)}")
                
                # VALIDATE
                v_config = config.get("validation", {})
                for col in v_config.get("not_null_columns", []):
                    if col in df.columns and df[col].isnull().any():
                        raise ValueError(f"Validation failed: Column '{col}' contains null values.")
                
                min_sal = v_config.get("min_salary")
                if min_sal is not None and 'Salary' in df.columns:
                    if (df['Salary'] < min_sal).any():
                        raise ValueError("Validation failed: Salary below minimum threshold.")
                log_message("VALIDATE", "All validation rules passed successfully.")
                
                # LOAD
                st.session_state.final_df = df
                log_message("LOAD", f"Successfully loaded {len(df)} records to final destination.")
                
                st.success("Pipeline executed successfully!")
            except Exception as e:
                log_message("ERROR", str(e))
                st.error(f"Pipeline Failed: {e}")

    if st.session_state.final_df is not None:
        st.divider()
        st.subheader("3. Final Transformed Dataset")
        st.dataframe(st.session_state.final_df, use_container_width=True)
        
        csv_data = st.session_state.final_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Final Dataset (CSV)",
            data=csv_data,
            file_name="final_data.csv",
            mime="text/csv"
        )

with tab2:
    st.subheader("📊 Data Inspection Stage-by-Stage")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Raw Data Schema & Stats**")
        st.write(st.session_state.raw_df.dtypes)
    with colB:
        st.markdown("**Final Data Schema & Stats**")
        if st.session_state.final_df is not None:
            st.write(st.session_state.final_df.dtypes)
        else:
            st.caption("Run the pipeline in Tab 1 to generate final data.")

with tab3:
    st.subheader("📜 Live Pipeline Logs")
    if st.session_state.logs:
        for log in st.session_state.logs:
            if "ERROR" in log:
                st.error(log)
            elif "SUCCESS" in log or "VALIDATE" in log:
                st.success(log)
            else:
                st.info(log)
    else:
        st.caption("No logs yet. Run the pipeline to view activity metrics.")

with tab4:
    st.subheader("💡 Interview Guide & Concepts")
    st.markdown("""
    * **What is ETL?** Extract, Transform, Load — the standard process of moving and cleansing data from sources to target warehouses[cite: 1].
    * **What is the difference between ETL and ELT?** ETL transforms data before loading onto a target server, whereas ELT loads raw data first and transforms it inside scalable cloud warehouses[cite: 1].
    * **Why should pipelines be configurable?** It separates hardcoded logic from parameters, allowing non-developers to adjust rules, file paths, and thresholds safely[cite: 1].
    * **What metrics should be logged?** Record counts at each stage, timestamps, error exceptions, success status flags, and data quality check results[cite: 1].
    """)