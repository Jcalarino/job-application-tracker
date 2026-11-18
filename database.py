"""Database helpers for the Job Application Tracker.

Connection settings come from config.py (kept out of GitHub).
Every query uses %s placeholders, never string concatenation,
which protects against SQL injection.
"""
import mysql.connector
from config import config


def get_connection():
    return mysql.connector.connect(**config)


def fetch_all(sql, params=None):
    """Run a SELECT and return a list of dictionaries."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


def fetch_one(sql, params=None):
    """Run a SELECT and return one dictionary (or None)."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        conn.close()


def execute(sql, params=None):
    """Run an INSERT, UPDATE or DELETE. Returns the new row id (for inserts)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return new_id
    except mysql.connector.Error:
        conn.rollback()
        raise
    finally:
        conn.close()
