import streamlit as st
from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Google Script API
SHEET_URL = "https://script.google.com/macros/s/AKfycbzxJnB82RKPi-SNVatTZLHtJRBRjdF3vVjHU5SomeFlaozdR-48u3H4diflI9h2WWFjtQ/exec"

# Google Sheet CSV
DATA_URL = "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/export?format=csv"

st.title("💰 Personal Finance Dashboard")

# ========================
# Add Record
# ========================

st.subheader("Add Record")

d = st.date_input("Date", date.today())

category = st.selectbox(
    "Category",
    [
        "Income",
        "Housing",
        "Communication",
        "Insurance",
        "Childcare",
        "Food",
        "Other",
        "Credit Card"
    ]
)

item = st.text_input("Item")
amount = st.number_input("Amount", min_value=0.0)

if st.button("Save Record"):

    data = {
        "date": str(d),
        "category": category,
        "item": item,
        "amount": amount
    }

    try:
        requests.post(SHEET_URL, json=data)
        st.success("Record Saved")
    except:
        st.error("Failed to save record")

# ========================
# Load Data
# ========================

st.subheader("Financial Overview")

try:

    df = pd.read_csv(DATA_URL, thousands=",")

    df.columns = ["date","category","item","amount"]

    df["category"] = df["category"].astype(str).str.strip()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    df["date"] = pd.to_datetime(df["date"])

    # ========================
    # Income / Expense
    # ========================

    income = df[df["category"] == "Income"]["amount"].sum()
    expense = df[df["category"] != "Income"]["amount"].sum()
    balance = income - expense

    col1,col2,col3 = st.columns(3)

    col1.metric("Total Income", round(income,2))
    col2.metric("Total Expense", round(expense,2))
    col3.metric("Balance", round(balance,2))

    # ========================
    # Recent Records (3 only)
    # ========================

    st.subheader("Recent Records")

    st.dataframe(df.sort_values("date",ascending=False).head(3))

    # ========================
    # Monthly Fixed Expenses
    # ========================

    st.subheader("Monthly Fixed Expenses")

    fixed_categories = [
        "Housing",
        "Communication",
        "Insurance",
        "Childcare"
    ]

    fixed_df = df[df["category"].isin(fixed_categories)]

    st.dataframe(fixed_df)

    st.write("Total Fixed Expense:", round(fixed_df["amount"].sum(),2))

    # ========================
    # Category Summary
    # ========================

    st.subheader("Expense by Category")

    expense_df = df[df["category"] != "Income"]

    category_summary = expense_df.groupby("category")["amount"].sum()

    st.dataframe(category_summary)

    # ========================
    # Pie Chart
    # ========================

    st.subheader("Expense Distribution")

    fig, ax = plt.subplots()

    ax.pie(
        category_summary,
        labels=category_summary.index,
        autopct='%1.1f%%'
    )

    ax.axis('equal')

    st.pyplot(fig)

    # ========================
    # Daily Trend
    # ========================

    st.subheader("Daily Expense Trend")

    daily = expense_df.groupby("date")["amount"].sum()

    st.line_chart(daily)

except Exception as e:

    st.error("Failed to load data")
    st.write(e)
