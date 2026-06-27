import streamlit as st
import sqlite3
import json
import time
import os
import pandas as pd

st.set_page_config(page_title="Inbox Pilot Dashboard", layout="wide")

DB_PATH = os.environ.get("DB_PATH", os.path.join("workflows", "workflow.db"))
METRICS_DIR = os.environ.get("METRICS_DIR", "metrics")


@st.cache_resource
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def load_tasks():
    db = get_db()
    try:
        df = pd.read_sql_query(
            "SELECT ticket_id, email_text, classification, reply, status FROM tasks ORDER BY rowid DESC",
            db
        )
        return df
    except Exception:
        return pd.DataFrame(columns=["ticket_id", "email_text", "classification", "reply", "status"])


def load_metrics():
    metrics_file = os.path.join(METRICS_DIR, "metrics.jsonl")
    if not os.path.exists(metrics_file):
        return []
    entries = []
    with open(metrics_file, "r") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def load_audit(ticket_id):
    db = get_db()
    try:
        cursor = db.execute(
            "SELECT action, details, timestamp, hash FROM audit_log WHERE ticket_id = ? ORDER BY timestamp",
            (ticket_id,)
        )
        return cursor.fetchall()
    except Exception:
        return []


st.title("Inbox Pilot Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["Tasks", "Stats", "Audit", "Metrics"])

with tab1:
    st.subheader("All Tasks")
    df = load_tasks()
    if df.empty:
        st.info("No tasks yet.")
    else:
        status_filter = st.selectbox("Filter by status", ["All"] + list(df["status"].unique()))
        if status_filter != "All":
            df = df[df["status"] == status_filter]
        st.dataframe(
            df[["ticket_id", "email_text", "classification", "status"]].rename(columns={
                "ticket_id": "Ticket",
                "email_text": "Email",
                "classification": "Class",
                "status": "Status"
            }),
            use_container_width=True
        )

with tab2:
    st.subheader("Workflow Statistics")
    df = load_tasks()
    if df.empty:
        st.info("No data yet.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tasks", len(df))
        col2.metric("Completed", len(df[df["status"] == "logged & completed"]))
        col3.metric("Awaiting Human", len(df[df["status"] == "awaiting_human_response"]))

        st.subheader("By Classification")
        class_counts = df["classification"].value_counts()
        st.bar_chart(class_counts)

        st.subheader("By Status")
        status_counts = df["status"].value_counts()
        st.bar_chart(status_counts)

with tab3:
    st.subheader("Audit Trail")
    ticket_input = st.text_input("Enter Ticket ID")
    if ticket_input:
        history = load_audit(ticket_input)
        if not history:
            st.info(f"No audit entries for {ticket_input}")
        else:
            audit_df = pd.DataFrame(history, columns=["Action", "Details", "Timestamp", "Hash"])
            audit_df["Time"] = pd.to_datetime(audit_df["Timestamp"], unit="s").dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(audit_df[["Action", "Details", "Time", "Hash"]], use_container_width=True)

with tab4:
    st.subheader("Performance Metrics")
    metrics = load_metrics()
    if not metrics:
        st.info("No metrics yet. Process some emails first.")
    else:
        df = pd.DataFrame(metrics)
        st.subheader("By Operation")
        summary = df.groupby("name").agg(
            count=("name", "count"),
            avg_ms=("duration_ms", "mean"),
            max_ms=("duration_ms", "max"),
            errors=("error", lambda x: x.notna().sum())
        ).round(2)
        st.dataframe(summary, use_container_width=True)

        st.subheader("Recent Calls")
        recent = df.tail(20).copy()
        recent["time"] = pd.to_datetime(recent["timestamp"], unit="s").dt.strftime("%H:%M:%S")
        st.dataframe(recent[["name", "duration_ms", "time", "error"]], use_container_width=True)
