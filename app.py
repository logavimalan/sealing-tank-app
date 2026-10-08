import sqlite3
from datetime import date, datetime
import pandas as pd
import streamlit as st

DB_NAME = "ANO2 SEALING TANK RECORD.db"


def get_db_connection():
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  return conn


st.set_page_config(
    page_title="Hot DI Water Sealing Record", page_icon="🧪", layout="wide"
)

# Top Navigation Tabs
tab_entry, tab_view = st.tabs(
    ["📝 New Record Entry", "📊 Check & Search Records"]
)

# ---------------------------------------------------------
# TAB 1: RECORD ENTRY FORM
# ---------------------------------------------------------
with tab_entry:
  st.title("🧪 Hot DI Water Sealing Record Entry (RPFRM-56)")
  st.caption("Richport Technology Production Form")

  conn = get_db_connection()
  tanks_query = conn.execute(
      "SELECT tank_id, line_name, di_water_vol_l, chem_vol_l FROM tanks"
  ).fetchall()
  conn.close()

  tank_dict = {row["tank_id"]: dict(row) for row in tanks_query}
  tank_options = list(tank_dict.keys())

  st.subheader("1. Batch / Job Details")
  with st.form("sealing_header_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
      part_name = st.text_input("Part Name *")
      tir_number = st.text_input("TIR Number *")
    with col2:
      record_date = st.date_input("Date", value=date.today())
      sealing_hr = st.selectbox(
          "Sealing Duration", ["20hr", "8hr", "6hr", "3hr"]
      )
    with col3:
      quantity = st.number_input("Quantity (Qty) *", min_value=1, step=1)
      selected_tank = st.selectbox("Tank No *", options=tank_options)

    if selected_tank:
      spec = tank_dict[selected_tank]
      st.info(
          f"**Selected Line:** {spec['line_name']} | **DI Water Vol:**"
          f" {spec['di_water_vol_l']} L | **Target Chem Vol:**"
          f" {spec['chem_vol_l']} L"
      )

    st.markdown("---")
    st.subheader("2. Hourly Readings (Log Table)")

    entries = []
    current_time_str = datetime.now().strftime("%H:%M")

    header_cols = st.columns([1, 2, 2, 2, 3, 2])
    header_cols[0].write("**No**")
    header_cols[1].write("**Time**")
    header_cols[2].write("**pH**")
    header_cols[3].write("**Temp (°C)**")
    header_cols[4].write("**Bath Makeup**")
    header_cols[5].write("**Resistivity**")

    for idx in range(1, 11):
      c0, c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 2, 3, 2])
      c0.write(f"**{idx}**")
      t_val = c1.text_input(
          f"Time {idx}",
          value=current_time_str if idx == 1 else "",
          label_visibility="collapsed",
      )
      ph_val = c2.number_input(
          f"pH {idx}",
          min_value=0.0,
          max_value=14.0,
          step=0.1,
          format="%.2f",
          key=f"ph_{idx}",
          label_visibility="collapsed",
      )
      temp_val = c3.number_input(
          f"Temp {idx}",
          min_value=0.0,
          max_value=100.0,
          step=0.5,
          format="%.1f",
          key=f"temp_{idx}",
          label_visibility="collapsed",
      )
      makeup_val = c4.text_input(
          f"Makeup {idx}", key=f"mk_{idx}", label_visibility="collapsed"
      )
      res_val = c5.number_input(
          f"Resistivity {idx}",
          min_value=0.0,
          step=0.1,
          format="%.2f",
          key=f"res_{idx}",
          label_visibility="collapsed",
      )

      if t_val.strip() != "":
        entries.append({
            "entry_no": idx,
            "check_time": t_val,
            "ph_level": ph_val if ph_val > 0 else None,
            "temperature_c": temp_val if temp_val > 0 else None,
            "bath_makeup": makeup_val,
            "resistivity": res_val if res_val > 0 else None,
        })

    st.markdown("---")
    st.subheader("3. Verification & Submit")
    operator_sig = st.text_input("Operator Name / Badge ID *")
    submit_button = st.form_submit_button("Submit Sealing Record")

  if submit_button:
    if not part_name or not tir_number or not operator_sig:
      st.error(
          "Please fill in all required fields (Part Name, TIR, Operator Name)."
      )
    else:
      try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
                INSERT INTO sealing_records 
                (part_name, record_date, tir_number, sealing_hr, quantity, tank_id, operator_signature)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                part_name,
                str(record_date),
                tir_number,
                sealing_hr,
                quantity,
                selected_tank,
                operator_sig,
            ),
        )
        record_id = cursor.lastrowid

        for entry in entries:
          cursor.execute(
              """
                    INSERT INTO sealing_log_entries 
                    (record_id, entry_no, check_time, ph_level, temperature_c, bath_makeup, resistivity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
              (
                  record_id,
                  entry["entry_no"],
                  entry["check_time"],
                  entry["ph_level"],
                  entry["temperature_c"],
                  entry["bath_makeup"],
                  entry["resistivity"],
              ),
          )

        conn.commit()
        conn.close()
        st.success(f"Record #{record_id} saved successfully!")
      except Exception as e:
        st.error(f"Error saving record: {e}")

# ---------------------------------------------------------
# TAB 2: VIEW & SEARCH HISTORICAL RECORDS
# ---------------------------------------------------------
with tab_view:
  st.title("📊 Sealing Records Database")

  conn = get_db_connection()

  search_tir = st.text_input("🔍 Filter by TIR Number or Part Name")

  query = """
        SELECT 
            r.record_id AS 'Record ID',
            r.record_date AS 'Date',
            r.tir_number AS 'TIR No',
            r.part_name AS 'Part Name',
            r.quantity AS 'Qty',
            r.tank_id AS 'Tank',
            r.sealing_hr AS 'Duration',
            r.operator_signature AS 'Operator',
            e.entry_no AS 'Check #',
            e.check_time AS 'Time',
            e.ph_level AS 'pH',
            e.temperature_c AS 'Temp (°C)',
            e.bath_makeup AS 'Bath Makeup',
            e.resistivity AS 'Resistivity'
        FROM sealing_records r
        LEFT JOIN sealing_log_entries e ON r.record_id = e.record_id
    """

  if search_tir:
    query += f" WHERE r.tir_number LIKE '%{search_tir}%' OR r.part_name LIKE '%{search_tir}%'"

  query += " ORDER BY r.record_id DESC, e.entry_no ASC"

  df = pd.read_sql_query(query, conn)
  conn.close()

  if not df.empty:
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Records as CSV",
        data=csv,
        file_name="sealing_tank_records.csv",
        mime="text/csv",
    )
  else:
    st.info("No sealing records found matching your query.")