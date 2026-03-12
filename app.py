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

    # ========================
    # 旧分类 Mapping
    # ========================

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

    # ========================
    # Income / Expense
    # ========================

    income = df[df["category"] == "收入"]["amount"].sum()

    expense = df[df["category"] != "收入"]["amount"].sum()

    balance = income - expense

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Income", round(income, 2))
    col2.metric("Total Expense", round(expense, 2))
    col3.metric("Balance", round(balance, 2))

    # ========================
    # Recent Records
    # ========================

    st.subheader("Recent Records")

    st.dataframe(df.tail(3))

    # ========================
    # Expense by Category
    # ========================

    st.subheader("Expense by Category")

    expense_df = df[df["category"] != "收入"]

    category_summary = expense_df.groupby("category")["amount"].sum()

    # 固定排序
    order = [
        "固定开销",
        "信用卡",
        "日常与餐饮",
        "育儿与家庭",
        "其他支出"
    ]

    category_summary = category_summary.reindex(order).fillna(0)

    st.dataframe(category_summary)

    # ========================
    # Pie Chart
    # ========================

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

    # ========================
    # Daily Trend
    # ========================

    st.subheader("Daily Expense Trend")

    daily = expense_df.groupby("date")["amount"].sum()

    st.line_chart(daily)

except Exception as e:

    st.error("Failed to load data")
    st.write(e)
