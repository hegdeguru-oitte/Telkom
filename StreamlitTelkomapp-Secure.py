import streamlit as st
import cx_Oracle
import pandas as pd
import io
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()

# Set page configuration
st.set_page_config(page_title="Database Query App", page_icon="🔍", layout="wide")

# Custom CSS to improve the look and feel and add the logo
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6
    }
    .main {
        background: #ffffff;
        padding: 3rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stSelectbox {
        background-color: #f1f3f6;
    }
    .logo-text {
        position: sticky;
        left: 40px;
        top: 10px;
        z-index: 0;
        background-color: #2596be;
        color: white;
        padding: 10px 10px;
        margin-bottom: 25px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 20px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
<div class="logo-text">Telkom</div>
""", unsafe_allow_html=True)

# Initialize Oracle client only if it hasn't been initialized yet
try:
    cx_Oracle.init_oracle_client(lib_dir=r"C:\Users\gurhegde\Downloads\instantclient_21_13")
except cx_Oracle.ProgrammingError:
    pass

# Initialize session state for database configurations
if 'databases' not in st.session_state:
    st.session_state.databases = {
        "GRA_Database": {
            "user": os.getenv("GRA_DB_USER"),
            "pwd": os.getenv("GRA_DB_PASSWORD"),
            "host": os.getenv("GRA_DB_HOST"),
            "service_name": os.getenv("GRA_DB_SERVICE"),
            "portno": int(os.getenv("GRA_DB_PORT", 1525))
        },
        "Singleview_Database": {
            "user": os.getenv("SV_DB_USER"),
            "pwd": os.getenv("SV_DB_PASSWORD"),
            "host": os.getenv("SV_DB_HOST"),
            "service_name": os.getenv("SV_DB_SERVICE"),
            "portno": int(os.getenv("SV_DB_PORT", 1527))
        }
    }


def execute_query(db_config, sql_query, service_names):
    connection = cx_Oracle.connect(
        db_config["user"],
        db_config["pwd"],
        f"{db_config['host']}:{db_config['portno']}/{db_config['service_name']}"
    )
    cursor = connection.cursor()
    
    quoted_service_names = ["'{}'".format(name) for name in service_names]
    chunk_size = 999
    chunks = [quoted_service_names[i:i + chunk_size] for i in range(0, len(quoted_service_names), chunk_size)]
    
    result = pd.DataFrame()
    
    for chunk in chunks:
        placeholders = ','.join(chunk)
        query = sql_query.format(placeholders)
        cursor.execute(query)
        chunk_result = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        result = pd.concat([result, chunk_result], ignore_index=True)
    
    cursor.close()
    connection.close()
    
    return result

# App title and description
st.title("📊 Advanced Database Query App")


# Sidebar for database selection, configuration, and file upload
with st.sidebar:
    st.header("Configuration")
    
    # Database selection
    selected_db = st.selectbox("Select Database", list(st.session_state.databases.keys()), key="db_select")
    
    # New database configuration (collapsible)
    with st.expander("Add New Database"):
        new_db_name = st.text_input("Database Name")
        new_db_user = st.text_input("User")
        new_db_pwd = st.text_input("Password", type="password")
        new_db_host = st.text_input("Host")
        new_db_service = st.text_input("Service Name")
        new_db_port = st.number_input("Port", min_value=1, max_value=65535, value=1521)
        
        if st.button("Add Database"):
            if new_db_name and new_db_user and new_db_pwd and new_db_host and new_db_service:
                st.session_state.databases[new_db_name] = {
                    "user": new_db_user,
                    "pwd": new_db_pwd,
                    "host": new_db_host,
                    "service_name": new_db_service,
                    "portno": new_db_port
                }
                st.success(f"Database '{new_db_name}' added successfully!")
            else:
                st.error("Please fill in all fields to add a new database.")
    
    # File upload
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="file_upload")
    st.markdown("Note: \n Make sure the column header of the uploaded file is SERVICENAME")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("SQL Query Input")
    sql_query = st.text_area("Enter your SQL query", height=500, key="sql_input")

with col2:
    st.subheader("Query Execution")
    execute_button = st.button("Execute Query", key="execute_btn")
    if uploaded_file is not None:
        st.success("File uploaded successfully!")

# Results area
if uploaded_file is not None and execute_button:
    data = pd.read_excel(uploaded_file, dtype={'SERVICENAME': str})
    service_names = data['SERVICENAME'].tolist()

    with st.spinner("Executing query..."):
        result = execute_query(st.session_state.databases[selected_db], sql_query, service_names)
        st.success("Query executed successfully!")
    

    
   
    
    # Create a download button for the results
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        result.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    
    st.download_button(
        label="Download Result",
        data=output,
        file_name="query_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# Footer
st.markdown("---")
