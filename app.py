import sqlite3
from datetime import date, datetime
import pandas as pd
import streamlit as st

DB_NAME = "ANO2 SEALING TANK RECORD.db"


def init_db():
  """Creates updated tables and pre-populates tank data."""
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # Tank Master Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS tanks (
            tank_id TEXT PRIMARY KEY,
            line_name TEXT NOT NULL,
            di_water_vol_l REAL,
            chem_vol_l REAL
        );
    """)

  cursor.execute("SELECT COUNT(*) FROM tanks")
  if cursor.fetchone()[0] == 0:
    tanks_data = [
        ("Tank 24", "Anodizing Line-1", 1400.0, 2.8),
        ("Tank 25", "Anodizing Line-1", 1400.0, 2.8),
        ("Tank 26", "Anodizing Line-1", 1400.0, 2.8),
        ("Tank 27", "Anodizing Line-1", 1400.0, 2.8),
        ("Tank 51", "Anodizing Line-2", 4330.0, 8.7),
        ("Tank 53/54", "Anodizing Line-2", 4330.0, 8.7),
        ("Tank 55", "Anodizing Line-2", 2850.0, 5.7),
        ("Tank 56", "Anodizing Line-2", 2850.0, 5.7),
        ("Tank 57", "Anodizing Line-2", 2850.0, 5.7),
        ("Tank 58", "Anodizing Line-2", 2850.0, 5.7),
    ]
    cursor.executemany(
        "INSERT INTO tanks VALUES (?, ?, ?, ?)", tanks_data
    )

  # Master Sealing Header
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sealing_records_v3 (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

  # Dedicated TIR & Quantity Table (One-to-Many)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sealing_tir_entries_v3 (
            tir_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER REFERENCES sealing_records_v3(record_id) ON DELETE CASCADE,
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
    layout="wide",
)

tab_entry, tab_view = st.tabs(
    ["📝 New Record Entry", "📊 Check & Search Records"]
)

# ---------------------------------------------------------
# TAB 1: RECORD ENTRY FORM
# ---------------------------------------------------------
with tab_entry:
  st.title("🧪 Hard Anodize - Hot DI Water Seal Record")
  st.caption("Richport Technology Production Form")

  conn = get_db_connection()
  tanks_query = conn.execute(
      "SELECT tank_id, line_name, di_water_vol_l, chem_vol_l FROM tanks"
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
        f"**Line:** {spec['line_name']} | **DI Water Vol:**"
        f" {spec['di_water_vol_l']} L | **Target Chem Vol:**"
        f" {spec['chem_vol_l']} L | **Specs:** pH 6.40–6.50 | Temp > 98.5°C"
    )

  st.markdown("---")
  st.subheader("2. TIR Numbers & Quantities")

  if "tir_count" not in st.session_state:
    st.session_state.tir_count = 1

  col_btn1, col_btn2 = st.columns([1, 5])
  with col_btn1:
    if st.button("➕ Add TIR Row"):
      st.session_state.tir_count += 1
  with col_btn2:
    if st.button("➖ Remove TIR Row") and st.session_state.tir_count > 1:
      st.session_state.tir_count -= 1

  tir_inputs = []
  for i in range(st.session_state.tir_count):
    t_col1, t_col2 = st.columns([3, 2])
    with t_col1:
      tir_num = st.text_input(f"TIR NO #{i+1} *", key=f"tir_no_{i}")
    with t_col2:
      qty = st.number_input(
          f"QTY #{i+1} *", min_value=1, step=1, key=f"qty_{i}"
      )
    if tir_num.strip():
      tir_inputs.append({"tir": tir_num.strip(), "qty": qty})

  st.markdown("---")
  st.subheader("3. Timing Details")
  time_col1, time_col2 = st.columns(2)
  with time_col1:
    time_in = st.text_input(
        "T.IN (Time In) *", value=datetime.now().strftime("%H:%M")
    )
  with time_col2:
    time_out = st.text_input("PART OUT (Time Out) *")

  st.markdown("---")
  st.subheader("4. Process Reading Log")

  r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns(5)
  with r_col1:
    check_time = st.text_input(
        "Time *", value=datetime.now().strftime("%H:%M")
    )
  with r_col2:
    temp_val = st.number_input(
        "Temp (°C)", min_value=0.0, max_value=120.0, step=0.1, format="%.1f"
    )
  with r_col3:
    ph_b_val = st.number_input(
        "pH Before Adj", min_value=0.0, max_value=14.0, step=0.01, format="%.2f"
    )
  with r_col4:
    buf_val = st.text_input("Buffer Added")
  with r_col5:
    ph_a_val = st.number_input(
        "pH After Adj", min_value=0.0, max_value=14.0, step=0.01, format="%.2f"
    )

  st.markdown("---")
  st.subheader("5. Operator Verification")
  operator_sig = st.text_input("Operator Name / Badge ID *")

  if st.button("Submit Sealing Record", type="primary"):
    if not tir_inputs:
      st.error("Please fill in at least one TIR NO and Quantity.")
    elif not operator_sig or not time_in or not time_out or not check_time:
      st.error(
          "Please complete all required fields (Operator Name, T.IN, PART OUT,"
          " Reading Time)."
      )
    else:
      try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
                INSERT INTO sealing_records_v3 
                (record_date, shift, tank_id, time_in, time_out, sealing_hr, operator_signature,
                 check_time, temperature_c, ph_before, buffer_added, ph_after)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(record_date),
                shift,
                selected_tank,
                time_in,
                time_out,
                sealing_hr,
                operator_sig,
                check_time,
                temp_val if temp_val > 0 else None,
                ph_b_val if ph_b_val > 0 else None,
                buf_val,
                ph_a_val if ph_a_val > 0 else None,
            ),
        )
        rec_id = cursor.lastrowid

        for item in tir_inputs:
          cursor.execute(
              """
                    INSERT INTO sealing_tir_entries_v3 (record_id, tir_number, quantity)
                    VALUES (?, ?, ?)
                """,
              (rec_id, item["tir"], item["qty"]),
          )

        conn.commit()
        conn.close()
        st.success(f"Sealing Record #{rec_id} successfully saved!")
      except Exception as e:
        st.error(f"Error saving record: {e}")

# ---------------------------------------------------------
# TAB 2: VIEW & SEARCH HISTORICAL RECORDS
# ---------------------------------------------------------
with tab_view:
  st.title("📊 Sealing Records Database")

  conn = get_db_connection()
  search_q = st.text_input("🔍 Filter by TIR Number")

  query = """
        SELECT 
            r.record_id AS 'Record ID',
            r.record_date AS 'Date',
            r.shift AS 'Shift',
            r.tank_id AS 'Tank',
            t.tir_number AS 'TIR No',
            t.quantity AS 'Qty',
            r.time_in AS 'Time IN',
            r.time_out AS 'Part OUT',
            r.sealing_hr AS 'Duration',
            r.check_time AS 'Log Time',
            r.temperature_c AS 'Temp (°C)',
            r.ph_before AS 'pH Before',
            r.buffer_added AS 'Buffer Added',
            r.ph_after AS 'pH After',
            r.operator_signature AS 'Operator'
        FROM sealing_records_v3 r
        JOIN sealing_tir_entries_v3 t ON r.record_id = t.record_id
    """

  if search_q:
    query += f" WHERE t.tir_number LIKE '%{search_q}%'"

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
