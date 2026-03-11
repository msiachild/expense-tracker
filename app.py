import streamlit as st
from datetime import date
import requests
import pandas as pd

# Google Script URL
SHEET_URL = "你的GoogleScriptURL"

# Google Sheet CSV读取
DATA_URL = "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/gviz/tq?tqx=out:csv"

st.title("📒 每月开销记录")

# ===== 输入薪金 =====
st.subheader("💰 本月薪金")

salary = st.number_input("输入本月薪金", min_value=0.0)

# ===== 输入开销 =====
st.subheader("新增记录")

d = st.date_input("日期", date.today())

category = st.selectbox(
    "类别",
    ["住房与贷款","通讯与网络","保险与健康","育儿与家庭","日常与餐饮","其他支出","信用卡"]
)

item = st.text_input("项目")

amount = st.number_input("金额", min_value=0.0)

if st.button("保存"):

    data = {
        "date": str(d),
        "category": category,
        "item": item,
        "amount": amount
    }

    requests.post(SHEET_URL, json=data)

    st.success("记录成功")

# ===== 读取数据 =====
st.subheader("📊 最新记录")

try:

    df = pd.read_csv(DATA_URL)

    if not df.empty:

        st.dataframe(df.tail(10))

        total_expense = df["amount"].sum()

        st.subheader("💸 总开销")
        st.write(total_expense)

        # ===== 余额计算 =====
        if salary > 0:

            balance = salary - total_expense

            st.subheader("💰 剩余金额")

            st.write(balance)

        # ===== 分类统计 =====
        st.subheader("📊 类别统计")

        st.dataframe(df.groupby("category")["amount"].sum())

except:
    st.write("暂无记录")
