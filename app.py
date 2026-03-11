import streamlit as st
from datetime import date
import requests
import pandas as pd

# Google Script URL
SHEET_URL = "你的GoogleScriptURL"

# Google Sheet CSV读取地址
DATA_URL = "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/gviz/tq?tqx=out:csv"

st.title("📒 每月开销记录")

# 输入区域
d = st.date_input("日期", date.today())

category = st.selectbox(
    "类别",
    ["餐饮","油费","购物","家庭","医疗","固定开销","其他"]
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

# 读取 Google Sheet
st.subheader("最新记录")

try:
    df = pd.read_csv(DATA_URL)

    if not df.empty:

        # 最新10条
        st.dataframe(df.tail(10))

        st.subheader("总开销")
        st.write(df["amount"].sum())

        st.subheader("类别统计")
        st.dataframe(df.groupby("category")["amount"].sum())

except:
    st.write("暂无记录")
