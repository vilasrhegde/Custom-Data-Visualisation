import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import io
from streamlit_option_menu import option_menu
import plotly.graph_objects as go
from argon2 import PasswordHasher

ph = PasswordHasher()

# Database connection
conn = sqlite3.connect('data.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                data BLOB NOT NULL,
                uploaded_by TEXT NOT NULL
            )''')

conn.commit()

def hash_password(password):
    return ph.hash(password)

def check_password(hashed_password, password):
    try:
        ph.verify(hashed_password, password)
        return True
    except Exception as e:
        return False

def signup_user(username, password):
    hashed_password = hash_password(password)
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    stored_password = c.fetchone()
    if stored_password and check_password(password, stored_password[0]):
        return True
    return False

def save_dataset(name, description, df, uploaded_by):
    buffer = io.BytesIO()
    df.to_pickle(buffer)
    buffer.seek(0)
    df_bytes = buffer.read()
    c.execute("INSERT INTO datasets (name, description, data, uploaded_by) VALUES (?, ?, ?, ?)", (name, description, df_bytes, uploaded_by))
    conn.commit()

def load_datasets():
    c.execute("SELECT id, name, description, uploaded_by FROM datasets")
    return c.fetchall()

def load_dataset_by_id(dataset_id):
    c.execute("SELECT data FROM datasets WHERE id = ?", (dataset_id,))
    df_bytes = c.fetchone()[0]
    buffer = io.BytesIO(df_bytes)
    buffer.seek(0)
    return pd.read_pickle(buffer)

def show_data_info(df):
    st.write("Describe:")
    st.write(df.describe())
    st.write("Head:")
    st.write(df.head())
    st.write("Tail:")
    st.write(df.tail())
    st.write("Info:")
    buffer = io.StringIO()
    df.info(buf=buffer)
    # Filter only numeric columns for correlation
    numeric_df = df.select_dtypes(include=['number'])
    st.write("Correlation:")
    st.write(numeric_df.corr())

def show_data_graphs(df):
    #st.write("Correlation Matrix:")
    #numeric_df = df.select_dtypes(include=['number'])
    #fig = px.imshow(numeric_df.corr())
    #st.plotly_chart(fig)
    st.write("Null Values:")
    nulls = df.isnull().sum().reset_index()
    nulls.columns = ['Column', 'Null Values']
    fig = px.bar(nulls, x='Column', y='Null Values')
    st.plotly_chart(fig)

    st.write("Correlation Matrix:")
    df=df.select_dtypes(include=['number'])
    st.write(df.head())


def show_basic_visualizations(df):
    # Histogram
    st.subheader("Histogram")
    numeric_cols = df.select_dtypes(include=['number']).columns
    hist_col = st.selectbox("Select Column for Histogram", numeric_cols)
    fig_hist = px.histogram(df, x=hist_col)
    st.plotly_chart(fig_hist)

    # Bar Chart
    st.subheader("Bar Chart")
    categorical_cols = df.select_dtypes(include=['object']).columns
    bar_col = st.selectbox("Select Column for Bar Chart", categorical_cols)
    bar_count = df[bar_col].value_counts().reset_index()
    bar_count.columns = [bar_col, 'Count']
    fig_bar = px.bar(bar_count, x=bar_col, y='Count')
    st.plotly_chart(fig_bar)

    # Pie Chart
    st.subheader("Pie Chart")
    pie_col = st.selectbox("Select Column for Pie Chart", categorical_cols)
    pie_count = df[pie_col].value_counts().reset_index()
    pie_count.columns = [pie_col, 'Count']
    fig_pie = px.pie(pie_count, names=pie_col, values='Count')
    st.plotly_chart(fig_pie)

    # Line Chart
    st.subheader("Line Chart")
    line_col = st.selectbox("Select Column for Line Chart", numeric_cols)
    fig_line = px.line(df, y=line_col)
    st.plotly_chart(fig_line)

    # Scatter Plot
    st.subheader("Scatter Plot")
    x_col = st.selectbox("Select X Column for Scatter Plot", numeric_cols)
    y_col = st.selectbox("Select Y Column for Scatter Plot", numeric_cols, index=1)
    fig_scatter = px.scatter(df, x=x_col, y=y_col)
    st.plotly_chart(fig_scatter)

    # Box Plot
    st.subheader("Box Plot")
    box_col = st.selectbox("Select Column for Box Plot", numeric_cols)
    fig_box = px.box(df, y=box_col)
    st.plotly_chart(fig_box)

    # Heatmap
    st.subheader("Heatmap")
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='Viridis'
        ))
        fig_heatmap.update_layout(title='Correlation Matrix Heatmap')
        st.plotly_chart(fig_heatmap)
    else:
        st.write("Not enough numeric columns for a heatmap.")

    # Violin Plot
    st.subheader("Violin Plot")
    if len(numeric_cols) > 1 and len(categorical_cols) > 0:
        violin_y_col = st.selectbox("Select Numeric Column for Violin Plot", numeric_cols)
        violin_x_col = st.selectbox("Select Categorical Column for Violin Plot", categorical_cols)
        fig_violin = px.violin(df, y=violin_y_col, x=violin_x_col)
        st.plotly_chart(fig_violin)
    else:
        st.write("Not enough data for a violin plot.")



def custom_graph(df):
    st.write("Create Custom Graph")
    x_col = st.selectbox("Select X-axis Column", df.columns)
    y_col = st.selectbox("Select Y-axis Column", df.columns)
    graph_type = st.selectbox("Select Graph Type", ["Scatter", "Line", "Bar"])
    
    if graph_type == "Scatter":
        fig = px.scatter(df, x=x_col, y=y_col)
    elif graph_type == "Line":
        fig = px.line(df, x=x_col, y=y_col)
    elif graph_type == "Bar":
        fig = px.bar(df, x=x_col, y=y_col)
    
    st.plotly_chart(fig)

# Streamlit App
st.title("Data Exploration App")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Sign Up
def sign_up():
    st.subheader("Sign Up")
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")
    if st.button("Sign Up"):
        if signup_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("User signed up successfully!")
            st.experimental_rerun()
        else:
            st.error("Username already exists. Please choose a different username.")

# Log In
def log_in():
    st.subheader("Log In")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Log In"):
        if login_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

def upload_data():
    st.subheader("Upload Data")
    name = st.text_input("Dataset Name")
    description = st.text_area("Description")
    file = st.file_uploader("Upload Excel or CSV File", type=['xlsx', 'csv'])
    
    if file and st.button("Upload"):
        if file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file)
        
        save_dataset(name, description, df, st.session_state.username)
        st.success("File uploaded successfully!")

# Explore Data
def explore_data():
    st.subheader("Explore Data")
    datasets = load_datasets()
    dataset_id = st.selectbox("Select Dataset", [dataset[0] for dataset in datasets], format_func=lambda x: [dataset[1] for dataset in datasets if dataset[0] == x][0])
    if dataset_id:
        df = load_dataset_by_id(dataset_id)
        dataset_info = [dataset for dataset in datasets if dataset[0] == dataset_id][0]
        st.write(f"Uploaded by: {dataset_info[3]}")
        st.write(f"Description: {dataset_info[2]}")

        page = st.sidebar.selectbox("Explore Options", ["Data Info", "Basic Visualization", "Custom Graph", "Data Quality"])

        
        if page == "Data Info":
            show_data_info(df)
        elif page == "Basic Visualization":
            #show_data_graphs(df)
            show_basic_visualizations(df)
        elif page == "Custom Graph":
            custom_graph(df)
        elif page == "Data Quality":
            #st.write("Data Quality Information:")
            st.write(f"Number of Null Values:")
            st.table(df.isnull().sum())

# Main App
if st.session_state.logged_in:
    st.sidebar.title(f"Welcome {st.session_state.username}")
    page = option_menu(None, ["Upload Data", "Explore Data"], icons=["cloud-upload", "search"], menu_icon="cast", default_index=0, orientation="horizontal")
    if page == "Upload Data":
        upload_data()
    elif page == "Explore Data":
        explore_data()
else:
    page = option_menu(None, ["Sign Up", "Log In"], icons=["person-add", "log-in"], menu_icon="cast", default_index=0, orientation="horizontal")
    if page == "Sign Up":
        sign_up()
    elif page == "Log In":
        log_in()


conn.close()
