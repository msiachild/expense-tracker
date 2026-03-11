import streamlit as st
import pandas as pd
from datetime import date
import os

st.title("📒 每月开销记录")

file = "expenses.csv"

# 如果文件不存在就创建
if not os.path.exists(file):
    df = pd.DataFrame(columns=["date","category","item","amount"])
    df.to_csv(file, index=False)

# 读取数据
df = pd.read_csv(file)

d = st.date_input("日期", date.today())

category = st.selectbox(
    "类别",
    ["餐饮","油费","购物","家庭","医疗","固定开销","其他"]
)

item = st.text_input("项目")

amount = st.number_input("金额", min_value=0.0)

if st.button("保存"):
    new = pd.DataFrame([[d, category, item, amount]],
                       columns=["date","category","item","amount"])

    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(file, index=False)

    st.success("记录成功")

st.subheader("记录")
st.dataframe(df)

st.subheader("总开销")

if not df.empty:
    st.write(df["amount"].sum())

st.subheader("类别开销汇总")

if not df.empty:
    summary = df.groupby("category")["amount"].sum()
    st.dataframe(summary)
