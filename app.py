import streamlit as st
from datetime import date
import requests

SHEET_URL = "https://script.google.com/macros/s/AKfycbxrHikteAjr0ZXtjX9zYX5nNFhSJ8_WKmwlPMMbXqw5nCjaugRd1MwtTq4tGBkg0yvG/exec"

st.title("📒 每月开销记录")

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

    r = requests.post(SHEET_URL, json=data)

    if r.status_code == 200:
        st.success("记录成功")
    else:
        st.error("写入失败")
