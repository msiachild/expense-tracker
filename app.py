import streamlit as st
from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# Google Apps Script API
# =========================
SHEET_URL = "https://script.google.com/macros/s/AKfycbzxJnB82RKPi-SNVatTZLHtJRBRjdF3vVjHU5SomeFlaozdR-48u3H4diflI9h2WWFjtQ/exec"

# =========================
# Google Sheet CSV
# =========================
DATA_URL = "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/export?format=csv"

st.title("📊 个人财务 Dashboard")

# =========================
# 新增记录
# =========================
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
        st.error("写入失败")

# =========================
# 读取数据
# =========================
st.subheader("财务统计")

try:

    df = pd.read_csv(DATA_URL, thousands=",")

    df.columns = ["date","category","item","amount"]

    df["category"] = df["category"].astype(str).str.strip()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    df["date"] = pd.to_datetime(df["date"])

    # =========================
    # 收入 / 支出
    # =========================

    income = df[df["category"] == "收入"]["amount"].sum()
    expense = df[df["category"] != "收入"]["amount"].sum()
    balance = income - expense

    col1,col2,col3 = st.columns(3)

    col1.metric("💵 总收入", round(income,2))
    col2.metric("💸 总支出", round(expense,2))
    col3.metric("💰 当前余额", round(balance,2))

    # =========================
    # 最近记录
    # =========================

    st.subheader("最近记录")

    st.dataframe(df.tail(10))

    # =========================
    # 分类统计
    # =========================

    st.subheader("支出分类统计")

    expense_df = df[df["category"] != "收入"]

    category_summary = expense_df.groupby("category")["amount"].sum()

    st.dataframe(category_summary)

    # =========================
    # 饼图
    # =========================

    st.subheader("支出结构")

    fig1, ax1 = plt.subplots()
    ax1.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%')
    ax1.axis('equal')

    st.pyplot(fig1)

    # =========================
    # 每日支出趋势
    # =========================

    st.subheader("每日支出趋势")

    daily = expense_df.groupby("date")["amount"].sum()

    st.line_chart(daily)

except Exception as e:
    st.error("读取数据失败")
    st.write(e)
