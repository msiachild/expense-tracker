import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS expenses(
date TEXT,
category TEXT,
item TEXT,
amount REAL
)
""")

st.title("📒 每月开销记录")

# 输入记录
d = st.date_input("日期", date.today())

category = st.selectbox(
"类别",
["餐饮","油费","购物","家庭","医疗","固定开销","其他"]
)

item = st.text_input("项目")

amount = st.number_input("金额", min_value=0.0)

if st.button("保存"):
    c.execute(
        "INSERT INTO expenses VALUES (?,?,?,?)",
        (str(d), category, item, amount)
    )
    conn.commit()
    st.success("记录成功")


# 导入CSV
st.subheader("导入CSV数据")

uploaded_file = st.file_uploader("选择CSV文件", type="csv")

if uploaded_file is not None:
    df_import = pd.read_csv(uploaded_file)
    df_import.to_sql("expenses", conn, if_exists="append", index=False)
    st.success("数据导入成功")


# 重新读取数据库（重要）
df = pd.read_sql("SELECT * FROM expenses", conn)

# 显示记录
st.subheader("记录")
st.dataframe(df)

# 总开销
st.subheader("总开销")
st.write(df["amount"].sum())

# 类别汇总
st.subheader("类别开销汇总")

category_summary = df.groupby("category")["amount"].sum().reset_index()

st.dataframe(category_summary)