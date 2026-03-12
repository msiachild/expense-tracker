import streamlit as st
from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt

SHEET_URL = "你的script url"

DATA_URL = "你的sheet csv url"

st.title("💰 Personal Finance Dashboard")

# =========================
# Add Record
# =========================

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

    requests.post(SHEET_URL, json=data)

    st.success("Saved")

# =========================
# Load Data
# =========================

df = pd.read_csv(DATA_URL, thousands=",")

df.columns = ["date","category","item","amount"]

df["date"] = pd.to_datetime(df["date"])

df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

# =========================
# Current Month Data
# =========================

current_month = pd.Timestamp.today().month

current_year = pd.Timestamp.today().year

month_df = df[
    (df["date"].dt.month == current_month) &
    (df["date"].dt.year == current_year)
]

# =========================
# Income / Expense
# =========================

income = month_df[month_df["category"] == "Income"]["amount"].sum()

expense = month_df[month_df["category"] != "Income"]["amount"].sum()

balance = income - expense

col1,col2,col3 = st.columns(3)

col1.metric("Income", round(income,2))
col2.metric("Expense", round(expense,2))
col3.metric("Balance", round(balance,2))

# =========================
# Recent Records (3 only)
# =========================

st.subheader("Recent Records")

st.dataframe(df.sort_values("date",ascending=False).head(3))

# =========================
# Monthly Fixed Expenses
# =========================

st.subheader("Monthly Fixed Expenses")

fixed_categories = [
    "Housing",
    "Communication",
    "Insurance",
    "Childcare"
]

fixed_df = month_df[month_df["category"].isin(fixed_categories)]

st.dataframe(fixed_df)

fixed_total = fixed_df["amount"].sum()

st.write("Total Fixed Expense:", round(fixed_total,2))

# =========================
# Monthly Expense Summary
# =========================

st.subheader("This Month Expense Summary")

expense_df = month_df[month_df["category"] != "Income"]

category_summary = expense_df.groupby("category")["amount"].sum()

st.dataframe(category_summary)

# =========================
# Pie Chart
# =========================

fig, ax = plt.subplots()

ax.pie(
    category_summary,
    labels=category_summary.index,
    autopct='%1.1f%%'
)

ax.axis('equal')

st.pyplot(fig)

# =========================
# Daily Trend
# =========================

st.subheader("Daily Expense Trend")

daily = expense_df.groupby("date")["amount"].sum()

st.line_chart(daily)
