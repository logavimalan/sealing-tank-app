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
    
    # 12-hour format for the preset values
    current_time_12 = datetime.now().strftime("%I:%M")
    current_ampm = datetime.now().strftime("%p")
    ampm_index = 0 if current_ampm == "AM" else 1

    tc1, tc2, tc3, tc4 = st.columns([2, 1, 2, 1])
    with tc1:
        time_in_val = st.text_input("PART IN *", value=current_time_12)
    with tc2:
        in_ampm = st.selectbox("AM/PM", ["AM", "PM"], index=ampm_index, key="in_ampm")
    with tc3:
        time_out_val = st.text_input("PART OUT *")
    with tc4:
        out_ampm = st.selectbox("AM/PM", ["AM", "PM"], index=ampm_index, key="out_ampm")

    # Combine values for database 
    time_in = f"{time_in_val} {in_ampm}" if time_in_val.strip() else ""
    time_out = f"{time_out_val} {out_ampm}" if time_out_val.strip() else ""

    st.markdown("---")
    st.subheader("4. Process Reading Log")

    r_col1, r_col_ap, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns([1.2, 1, 1.2, 1.2, 1.2, 1.2, 1.2])
    with r_col1:
        check_time_val = st.text_input("Time *", value=current_time_12)
    with r_col_ap:
        chk_ampm = st.selectbox("AM/PM", ["AM", "PM"], index=ampm_index, key="chk_ampm")
    with r_col2:
        temp_val = st.number_input("Temp (°C)", min_value=0.0, max_value=120.0, step=0.1, format="%.1f")
    with r_col3:
        ph_before = st.number_input("pH Before Adj", min_value=0.0, max_value=14.0, step=0.01, format="%.2f")
    with r_col4:
        buffer_added = st.text_input("Buffer Added (ml)")
    with r_col5:
        ph_after = st.number_input("pH After Adj", min_value=0.0, max_value=14.0, step=0.01, format="%.2f")
    with r_col6:
        resistivity = st.number_input("Resistivity", min_value=0.0, step=0.1, format="%.2f")
    
    # Combine values for database
    check_time = f"{check_time_val} {chk_ampm}" if check_time_val.strip() else ""

    st.markdown("---")
    st.subheader("5. Operator Verification")
    operator_sig = st.text_input("Operator Name / Badge ID *")

    if st.button("Submit Sealing Record", type="primary"):
        if not tir_inputs:
            st.error("Please fill in at least one Part Number, TIR NO and Quantity.")
        elif not operator_sig or not time_in_val or not time_out_val or not check_time_val:
            st.error("Please complete all required fields (Operator Name, PART IN, PART OUT, Reading Time).")
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO sealing_records_v6
                    (record_date, shift, tank_id, time_in, time_out, sealing_hr, operator_signature,
                     check_time, temperature_c, ph_before, buffer_added, ph_after, resistivity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(record_date), shift, selected_tank, time_in, time_out, sealing_hr, operator_sig,
                    check_time, temp_val if temp_val > 0 else None, ph_before if ph_before > 0 else None,
                    buffer_added, ph_after if ph_after > 0 else None, resistivity if resistivity > 0 else None
                ))
                rec_id = cursor.lastrowid

                for item in tir_inputs:
                    cursor.execute("""
                        INSERT INTO sealing_tir_entries_v6 (record_id, part_number, tir_number, quantity)
                        VALUES (?, ?, ?, ?)
                    """, (rec_id, item["part"], item["tir"], item["qty"]))

                conn.commit()
                conn.close()
                st.success(f"Sealing Record #{rec_id} successfully saved!")
            except Exception as e:
                st.error(f"Error saving record: {e}")

with tab_view:
    st.title("📊 Sealing Records Database")

    conn = get_db_connection()
    search_q = st.text_input("🔍 Filter by TIR Number or Part Number")

    query = """
        SELECT 
            r.record_id AS 'Record ID',
            r.record_date AS 'Date',
            r.shift AS 'Shift',
            r.tank_id AS 'Tank',
            t.part_number AS 'Part Number',
            t.tir_number AS 'TIR No',
            t.quantity AS 'Qty',
            r.time_in AS 'PART IN',
            r.time_out AS 'PART OUT',
            r.sealing_hr AS 'Duration',
            r.check_time AS 'Log Time',
            r.temperature_c AS 'Temp (°C)',
            r.ph_before AS 'pH Before',
            r.buffer_added AS 'Buffer (ml)',
            r.ph_after AS 'pH After',
            r.resistivity AS 'Resistivity',
            r.operator_signature AS 'Operator'
        FROM sealing_records_v6 r
        JOIN sealing_tir_entries_v6 t ON r.record_id = t.record_id
    """

    if search_q:
        query += f" WHERE t.tir_number LIKE '%{search_q}%' OR t.part_number LIKE '%{search_q}%'"

    query += " ORDER BY r.record_id DESC"

    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, width="stretch")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Records as CSV",
            data=csv,
            file_name="hard_anodize_sealing_records.csv",
            mime="text/csv",
        )
    else:
        st.info("No sealing records found.")
