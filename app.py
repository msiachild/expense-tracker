import streamlit as st
from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.title("💰 Personal Finance Dashboard")

# ========================
# User Select
# ========================

user = st.selectbox("User", ["TTC", "Wife"])

URLS = {
    "TTC": {
        "script": "https://script.google.com/macros/s/AKfycbzxJnB82RKPi-SNVatTZLHtJRBRjdF3vVjHU5SomeFlaozdR-48u3H4diflI9h2WWFjtQ/exec",
        "data": "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/export?format=csv"
    },
    "Wife": {
        "script": "https://script.google.com/macros/s/AKfycbwvRKC_cw0MqLUnsezPZdzigk4Z_3rAzp2fvNzMsJnEQW1nCVT2ps70TM9ObmnJwRau/exec",
        "data": "https://docs.google.com/spreadsheets/d/1YIZt7mcYS7llnJa1JANB5rz-o2EE_AqOi1j2h8M97Vg/export?format=csv"
    }
}

SHEET_URL = URLS[user]["script"]
DATA_URL = URLS[user]["data"]

# ========================
# Add Record
# ========================

st.subheader("Add Record")

d = st.date_input("Date", date.today())

category = st.selectbox(
    "Category",
    [
        "收入",
        "固定开销",
        "信用卡",
        "日常与餐饮",
        "育儿与家庭",
        "其他支出"
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

    df.columns = ["date", "category", "item", "amount"]

    df["category"] = df["category"].astype(str).str.strip()

    mapping = {
        "Housing": "固定开销",
        "Insurance": "固定开销",
        "Communication": "其他支出",
        "Childcare": "育儿与家庭",
        "Food": "日常与餐饮",
        "Other": "其他支出",
        "Credit Card": "信用卡",
        "Income": "收入"
    }

    df["category"] = df["category"].replace(mapping)

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    df["date"] = pd.to_datetime(df["date"])

    income = df[df["category"] == "收入"]["amount"].sum()
    expense = df[df["category"] != "收入"]["amount"].sum()

    balance = income - expense

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Income", round(income, 2))
    col2.metric("Total Expense", round(expense, 2))
    col3.metric("Balance", round(balance, 2))

    st.subheader("Recent Records")

    st.dataframe(df.tail(3))

    st.subheader("Expense by Category")

    expense_df = df[df["category"] != "收入"]

    category_summary = expense_df.groupby("category")["amount"].sum()

    order = [
        "固定开销",
        "信用卡",
        "日常与餐饮",
        "育儿与家庭",
        "其他支出"
    ]

    category_summary = category_summary.reindex(order).fillna(0)

    st.dataframe(category_summary)

    st.subheader("Expense Distribution")

    label_map = {
        "固定开销": "Fixed",
        "信用卡": "Credit Card",
        "日常与餐饮": "Food",
        "育儿与家庭": "Childcare",
        "其他支出": "Other"
    }

    labels = [label_map.get(i, i) for i in category_summary.index]

    fig, ax = plt.subplots()

    ax.pie(
        category_summary,
        labels=labels,
        autopct='%1.1f%%'
    )

    ax.axis('equal')

    st.pyplot(fig)

    st.subheader("Daily Expense Trend")

    daily = expense_df.groupby("date")["amount"].sum()

    st.line_chart(daily)

except Exception as e:

    st.error("Failed to load data")
    st.write(e)
