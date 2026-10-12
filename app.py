import sqlite3
from datetime import date, datetime
import pandas as pd
import streamlit as st

DB_NAME = "ANO2 SEALING TANK RECORD.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS tanks")
    cursor.execute("""
        CREATE TABLE tanks (
            tank_id TEXT PRIMARY KEY,
            line_name TEXT NOT NULL,
            di_water_vol_l REAL,
            chem_vol_l REAL
        );
    """)

    tanks_data = [
        ("Tank 51", "Anodizing Line-2", 4330.0, 8.7),
        ("Tank 52", "Anodizing Line-2", 4330.0, 8.7),
        ("Tank 53", "Anodizing Line-2", 4330.0, 8.7),
        ("Tank 54", "Anodizing Line-2", 4330.0, 8.7),
        ("Tank 55", "Anodizing Line-2", 2850.0, 5.7),
        ("Tank 56", "Anodizing Line-2", 2850.0, 5.7),
        ("Tank 57", "Anodizing Line-2", 2850.0, 5.7),
        ("Tank 58", "Anodizing Line-2", 2850.0, 5.7),
    ]
    cursor.executemany("INSERT INTO tanks VALUES (?, ?, ?, ?)", tanks_data)

    # Updated to v6 to include the new Process Reading Log columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sealing_records_v6 (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_date TEXT NOT NULL,
            shift TEXT NOT NULL,
            tank_id TEXT REFERENCES tanks(tank_id),
            time_in TEXT NOT NULL,
            time_out TEXT NOT NULL,
            sealing_hr TEXT NOT NULL,
            operator_signature TEXT NOT NULL,
            check_time TEXT NOT NULL,
            temperature_c REAL,
            ph_before REAL,
            buffer_added TEXT,
            ph_after REAL,
            resistivity REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sealing_tir_entries_v6 (
            tir_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER REFERENCES sealing_records_v6(record_id) ON DELETE CASCADE,
            part_number TEXT NOT NULL,
            tir_number TEXT NOT NULL,
            quantity INTEGER NOT NULL
        );
    """)

    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

st.set_page_config(
    page_title="Hard Anodize Hot DI Water Seal Record",
    page_icon="🧪",
    layout="wide"
)

tab_entry, tab_view = st.tabs(
    ["📝 New Record Entry", "📊 Check & Search Records"]
)

with tab_entry:
    st.title("🧪 Hard Anodize - Hot DI Water Seal Record")
    st.caption("Richport Technology Production Form")

    conn = get_db_connection()
    tanks_query = conn.execute(
        "SELECT tank_id, line_name, di_water_vol_l, chem_vol_l FROM tanks ORDER BY tank_id ASC"
    ).fetchall()
    conn.close()

    tank_dict = {row["tank_id"]: dict(row) for row in tanks_query}
    tank_options = list(tank_dict.keys())

    st.subheader("1. General & Tank Details")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        record_date = st.date_input("Date", value=date.today())
    with c2:
        shift = st.radio("Shift", ["Day", "Night"], horizontal=True)
    with c3:
        selected_tank = st.selectbox("Tank No *", options=tank_options)
    with c4:
        sealing_hr = st.selectbox(
            "Seal Duration",
            ["3 HR (180 MIN)", "20 HR", "8 HR", "6 HR"],
        )

    if selected_tank:
        spec = tank_dict[selected_tank]
        st.info(
            f"**Line:** {spec['line_name']} | "
            f"**Makeup Chemical:** 2 ml/L | "
            f"**DI Water Vol:** {spec['di_water_vol_l']} L | "
            f"**Target Chem Vol:** {spec['chem_vol_l']} L"
        )

    st.markdown("---")
    st.subheader("2. Part Numbers, TIR & Quantities")

    if "tir_count" not in st.session_state:
        st.session_state.tir_count = 1

    col_btn1, col_btn2 = st.columns([1, 5])
    with col_btn1:
        if st.button("➕ Add Item Row"):
            st.session_state.tir_count += 1
    with col_btn2:
        if st.button("➖ Remove Item Row") and st.session_state.tir_count > 1:
            st.session_state.tir_count -= 1

    tir_inputs = []
    for i in range(st.session_state.tir_count):
        t_col1, t_col2, t_col3 = st.columns([2, 2, 1])
        with t_col1:
            part_num = st.text_input(f"Part Number #{i+1} *", key=f"part_no_{i}")
        with t_col2:
            tir_num = st.text_input(f"TIR NO #{i+1} *", key=f"tir_no_{i}")
        with t_col3:
            qty = st.number_input(f"QTY #{i+1} *", min_value=1, step=1, key=f"qty_{i}")
        if part_num.strip() or tir_num.strip():
            tir_inputs.append({"part": part_num.strip(), "tir": tir_num.strip(), "qty": qty})

    st.markdown("---")
    st.subheader("3. Timing Details")
    time_col1, time_col2 = st.columns(2)
    with time_col1:
        time_in = st.text_input("T.IN (Time In) *", value=datetime.now().strftime("%H:%M"))
    with time_col2:
        time_out = st.text_input("PART OUT (Time Out) *")

    st.markdown("---")
    st.subheader("4. Process Reading Log")

    # Adjusted to 6 columns based on your request
    r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns(6)
    with r_col1:
        check_time = st.text_input("Time *", value=datetime.now().strftime("%H:%M"))
    with r_col2:
        temp_val = st.number_input("Temp (°C)", min_value=0.0, max_value=120.0, step=0.1, format="%.1f")
    with r_col3:
        ph_before = st.number_input("pH Before Adj", min_value=0.0, max_value=14.0, step=0.01, format="%.2f")
    with r_col4:
        buffer_added
