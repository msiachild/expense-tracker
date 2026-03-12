import streamlit as st
from datetime import date
import requests
import pandas as pd

# Google Apps Script API
SHEET_URL = "https://script.google.com/macros/s/AKfycbzxJnB82RKPi-SNVatTZLHtJRBRjdF3vVjHU5SomeFlaozdR-48u3H4diflI9h2WWFjtQ/exec"

# Google Sheet CSV
DATA_URL = "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/export?format=csv"

st.title("📒 每月收支记录")

# ========= 新增记录 =========
st.subheader("新增记录")

d = st.date_input("日期", date.today())

category = st.selectbox(
    "类别",
    [
        "收入",
        "住房与贷款",
        "通讯与网络",
        "保险与健康",
        "育儿与家庭",
        "日常与餐饮",
        "其他支出",
        "信用卡"
    ]
)

item = st.text_input("项目")
amount = st.number_input("金额", min_value=0.0)

if st.button("保存记录"):

    data = {
        "date": str(d),
        "category": category,
        "item": item,
        "amount": amount
    }

    try:
        requests.post(SHEET_URL, json=data)
        st.success("记录成功")
    except:
        st.error("写入失败，请检查 Google Script")

# ========= 读取数据 =========
st.subheader("📊 最新记录")

try:

    df = pd.read_csv(DATA_URL, thousands=",")

    # 确保列名正确
    df.columns = ["date", "category", "item", "amount"]

    # 清理 category
    df["category"] = df["category"].astype(str).str.strip()

    # 金额转数字
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    st.dataframe(df.tail(10))

    # ===== 收入 =====
    income = df[df["category"] == "收入"]["amount"].sum()

    # ===== 支出 =====
    expense = df[df["category"] != "收入"]["amount"].sum()

    # ===== 余额 =====
    balance = income - expense

    st.subheader("💰 当前余额")
    st.write(round(balance, 2))

    st.subheader("💸 总支出")
    st.write(round(expense, 2))

    st.subheader("💵 总收入")
    st.write(round(income, 2))

    # ===== 分类统计 =====
    st.subheader("📊 支出分类统计")

    expense_df = df[df["category"] != "收入"]
    category_summary = expense_df.groupby("category")["amount"].sum().reset_index()

    st.dataframe(category_summary)

except Exception as e:
    st.error("读取数据失败")
    st.write(e)
