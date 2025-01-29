import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime

# Configuration
DB_PATH = "data.db"
DATA_COLUMNS = ['Date', 'NAV', 'Vni', 'NAV_index', 'Vni_index']

def init_database():
    Path(DB_PATH).touch()

def execute_query(query, params=None):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql(query, conn, params=params)
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None

def save_to_sqlite(df, table_name):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        return True
    except sqlite3.Error as e:
        st.error(f"Error saving to database: {e}")
        return False

def delete_entry(date, table_name):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM "{table_name}" WHERE Date = ?', (date,))
            conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error deleting entry: {e}")
        return False

def fetch_from_sqlite(table_name):
    return execute_query(f'SELECT * FROM "{table_name}"')

def display_amount_editor(df):
    """Create a simplified editor for Amount table with date picker and auto-calculated total"""
    st.subheader("Amount Editor")
    
    # Initialize session state for resetting
    if 'reset_amount' not in st.session_state:
        st.session_state.reset_amount = False
    
    # Initialize DataFrame if None
    if df is None:
        df = pd.DataFrame(columns=['Date', 'MH', 'TA', 'AT', 'Total'])
    else:
        # Create a copy of the DataFrame to avoid warnings
        df = df.copy()
    
    # Convert Date to datetime if it's not already
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Date picker for search/entry
    if st.session_state.reset_amount:
        selected_date = st.date_input("Select Date", datetime.now().date(), key='reset_date_amount')
        st.session_state.reset_amount = False
    else:
        selected_date = st.date_input("Select Date", datetime.now().date())
    
    # Check if data exists for selected date
    selected_date = pd.to_datetime(selected_date)
    mask = df['Date'].dt.date == selected_date.date()
    existing_data = df.loc[mask].iloc[0] if len(df[mask]) > 0 else None
    
    # Input fields
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        mh_value = st.number_input(
            "MH",
            value=float(existing_data['MH']) if existing_data is not None and not st.session_state.reset_amount else 0.0,
            format="%.2f",
            key=f"mh_{st.session_state.reset_amount}"
        )
    
    with col2:
        ta_value = st.number_input(
            "TA",
            value=float(existing_data['TA']) if existing_data is not None and not st.session_state.reset_amount else 0.0,
            format="%.2f",
            key=f"ta_{st.session_state.reset_amount}"
        )
    
    with col3:
        at_value = st.number_input(
            "AT",
            value=float(existing_data['AT']) if existing_data is not None and not st.session_state.reset_amount else 0.0,
            format="%.2f",
            key=f"at_{st.session_state.reset_amount}"
        )
    
    with col4:
        total = mh_value + ta_value + at_value
        st.text_input("Total", value=f"{total:.2f}", disabled=True)
    
    # Save and Delete buttons in the same row
    col1, col2 = st.columns(2)
    with col1:
        save_clicked = st.button("Save Amount Data", type="primary")
    with col2:
        delete_clicked = st.button("Delete Entry", type="secondary")
    
    if save_clicked:
        new_data = {
            'Date': selected_date,
            'MH': mh_value,
            'TA': ta_value,
            'AT': at_value,
            'Total': total
        }
        
        if existing_data is not None:
            df.loc[mask] = new_data
        else:
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        
        if save_to_sqlite(df, "Amount"):
            st.success("Data saved successfully!")
            st.session_state.reset_amount = True
            st.experimental_rerun()
    
    if delete_clicked and existing_data is not None:
        if delete_entry(selected_date, "Amount"):
            st.success("Entry deleted successfully!")
            df = df[~mask]  # Using boolean indexing instead of equality
            save_to_sqlite(df, "Amount")
            st.session_state.reset_amount = True
            st.experimental_rerun()
    
    # Display full table
    if not df.empty:
        st.subheader("Amount Table")
        display_df = df.copy()
        display_df['Date'] = display_df['Date'].dt.date
        st.dataframe(display_df.sort_values('Date', ascending=False))
    
    return df

def display_data_editor(df):
    """Create a simplified editor for Data table with date picker and auto-calculated indices"""
    st.subheader("Data Editor")
    
    # Initialize session state for resetting
    if 'reset_data' not in st.session_state:
        st.session_state.reset_data = False
    
    # Initialize DataFrame if None
    if df is None:
        df = pd.DataFrame(columns=['Date', 'NAV', 'Vni', 'NAV_index', 'Vni_index'])
    else:
        # Create a copy of the DataFrame to avoid warnings
        df = df.copy()
    
    # Convert Date to datetime if it's not already
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Date picker for search/entry
    if st.session_state.reset_data:
        selected_date = st.date_input("Select Date", datetime.now().date(), key='reset_date_data')
        st.session_state.reset_data = False
    else:
        selected_date = st.date_input("Select Date", datetime.now().date())
    
    # Check if data exists for selected date
    selected_date = pd.to_datetime(selected_date)
    mask = df['Date'].dt.date == selected_date.date()
    existing_data = df.loc[mask].iloc[0] if len(df[mask]) > 0 else None
    
    # Input fields
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        nav_value = st.number_input(
            "NAV",
            value=float(existing_data['NAV']) if existing_data is not None and not st.session_state.reset_data else 0.0,
            format="%.2f",
            key=f"nav_{st.session_state.reset_data}"
        )
    
    with col2:
        vni_value = st.number_input(
            "VNI",
            value=float(existing_data['Vni']) if existing_data is not None and not st.session_state.reset_data else 0.0,
            format="%.2f",
            key=f"vni_{st.session_state.reset_data}"
        )
    
    # Calculate indices
    if not df.empty and len(df) > 0:
        first_nav = df.iloc[0]['NAV']
        first_vni = df.iloc[0]['Vni']
        nav_index = (nav_value / first_nav * 100) if first_nav != 0 else 0
        vni_index = (vni_value / first_vni * 100) if first_vni != 0 else 0
    else:
        nav_index = 100
        vni_index = 100
    
    with col3:
        st.text_input("NAV Index", value=f"{nav_index:.2f}", disabled=True)
    
    with col4:
        st.text_input("VNI Index", value=f"{vni_index:.2f}", disabled=True)
    
    # Save and Delete buttons in the same row
    col1, col2 = st.columns(2)
    with col1:
        save_clicked = st.button("Save Data", type="primary")
    with col2:
        delete_clicked = st.button("Delete Entry", type="secondary")
    
    if save_clicked:
        new_data = {
            'Date': selected_date,
            'NAV': nav_value,
            'Vni': vni_value,
            'NAV_index': nav_index,
            'Vni_index': vni_index
        }
        
        if existing_data is not None:
            df.loc[mask] = new_data
        else:
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        
        # Recalculate all indices based on the first entry
        if len(df) > 0:
            first_nav = df.iloc[0]['NAV']
            first_vni = df.iloc[0]['Vni']
            df['NAV_index'] = (df['NAV'] / first_nav * 100)
            df['Vni_index'] = (df['Vni'] / first_vni * 100)
        
        if save_to_sqlite(df, "Data"):
            st.success("Data saved successfully!")
            st.session_state.reset_data = True
            st.experimental_rerun()
    
    if delete_clicked and existing_data is not None:
        if delete_entry(selected_date, "Data"):
            st.success("Entry deleted successfully!")
            df = df[~mask]  # Using boolean indexing instead of equality
            
            # Recalculate indices after deletion
            if not df.empty:
                first_nav = df.iloc[0]['NAV']
                first_vni = df.iloc[0]['Vni']
                df['NAV_index'] = (df['NAV'] / first_nav * 100)
                df['Vni_index'] = (df['Vni'] / first_vni * 100)
            
            save_to_sqlite(df, "Data")
            st.session_state.reset_data = True
            st.experimental_rerun()
    
    # Display full table
    if not df.empty:
        st.subheader("Data Table")
        display_df = df.copy()
        display_df['Date'] = display_df['Date'].dt.date
        st.dataframe(display_df.sort_values('Date', ascending=False))
    
    return df

def create_visualization(df, selected_table):
    try:
        if df is None or df.empty:
            return None
            
        if selected_table == "Amount":
            # Convert Date to datetime if it's not already
            df['Date'] = pd.to_datetime(df['Date'])
            # Sort by date
            df = df.sort_values('Date')
            
            # Create bar chart for Amount
            fig = go.Figure()
            
            # Get list of unique dates and create numeric x-axis
            x_numeric = list(range(len(df['Date'])))
            
            # Add bars for each column except Date and Total
            for i, col in enumerate(['MH', 'TA', 'AT']):
                fig.add_trace(
                    go.Bar(
                        name=col,
                        x=x_numeric,
                        y=df[col],
                        text=[f'{x/1000000:.1f}M' for x in df[col]],
                        textposition='auto',
                        width=0.3,  # Increased overall width for the group
                        offset=(-0.15 + (0.15* i)),  # Position bars side by side within the group
                    )
                )
            
            # Add line for Total
            fig.add_trace(
                go.Scatter(
                    name='Total',
                    x=x_numeric,
                    y=df['Total'],
                    mode='lines+markers+text',
                    text=[f'{x/1000000000:.1f}B' for x in df['Total']],
                    textposition='top center',
                    line=dict(color='red', width=2),
                    marker=dict(size=8),
                )
            )
            
            fig.update_layout(
                title="Amount Distribution Over Time",
                xaxis_title="Date",
                yaxis_title="Amount (Billions)",
                barmode='overlay',  # Changed to overlay for manual positioning
                height=600,
                showlegend=True,
                hovermode='x unified',
                xaxis=dict(
                    tickmode='array',
                    ticktext=df['Date'].dt.strftime('%d-%m-%Y'),
                    tickvals=x_numeric,
                    tickangle=0,
                ),
                bargap=0.4,  # Gap between date groups
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2, # Move legend below the chart
                    xanchor="center",
                    x=0.5 # Center the legend horizontally
                )
            )
            return fig
            
        else:  # Data table
            # Convert Date to datetime if it's not already
            df['Date'] = pd.to_datetime(df['Date'])
            # Sort by date
            df = df.sort_values('Date')
            
            # Create two subplots
            fig = make_subplots(
                rows=2, 
                cols=1, 
                subplot_titles=("Relative NAV and VNI Over Time", "NAV Over Time"),
                vertical_spacing=0.2
            )
            
            # Add index comparison lines
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['NAV_index'],
                    name="NAV Index",
                    mode='lines',
                    text=[f'{x:.1f}%' for x in df['NAV_index']],
                    textposition='top center'
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Vni_index'],
                    name="VNI Index",
                    mode='lines',
                    text=[f'{x:.1f}%' for x in df['Vni_index']],
                    textposition='bottom center'
                ),
                row=1, col=1
            )
            
            # Add NAV and VNI lines
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['NAV'],
                    name="NAV",
                    mode='lines',
                    text=[f'{x:.1f}' for x in df['NAV']],
                    textposition='top center'
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                height=800,
                showlegend=True,
                hovermode='x unified',
                xaxis=dict(
                    tickangle=45,
                    tickformat='%d-%m-%Y'
                ),
                xaxis2=dict(
                    tickangle=45,
                    tickformat='%d-%m-%Y'
                )
            )
            
            # Update y-axis labels
            fig.update_yaxes(title_text="Relative Value", row=1, col=1)
            fig.update_yaxes(title_text="Value", row=2, col=1)
            
            return fig
            
    except Exception as e:
        st.error(f"Error creating visualization: {e}")
        return None
    
def main():
    """Main application logic"""
    st.set_page_config(page_title="VN Account Tracker", layout="wide")
    
    init_database()
    
    with st.sidebar:
        st.title("Dashboard Controls")
        selected_table = st.selectbox(
            "Select Dataset",
            ["Amount", "Data"],
            help="Choose which dataset to view and edit"
        )
    
    st.title("Data Visualization Dashboard")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if os.path.exists(DB_PATH):
            df = fetch_from_sqlite(selected_table)
            if selected_table == "Amount":
                df = display_amount_editor(df)
            else:
                df = display_data_editor(df)
        else:
            st.warning("Database not found. Please create a new entry to initialize the database.")
    
    with col2:
        if df is not None and not df.empty:
            st.subheader(f"{selected_table} Visualization")
            fig = create_visualization(df, selected_table)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()