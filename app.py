import sqlite3
from datetime import date, datetime
import pandas as pd
import streamlit as st

DB_NAME = "ANO2 SEALING TANK RECORD.db"


def init_db():
  """Creates updated tables to support Part Number entries."""
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

  # Master Sealing Header (Updated to v5 to prevent column errors)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sealing_records_v5 (
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
            ph_level REAL,
            bath_makeup TEXT,
            resistivity REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

  # Dedicated entries table updated with part_number column
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sealing_tir_entries_v5 (
            tir_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER REFERENCES sealing_records_v5(record_id) ON DELETE CASCADE,
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
    page_icon
