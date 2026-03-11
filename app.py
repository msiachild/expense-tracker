import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

# Google API scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 读取 Streamlit Secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

# 打开 Google Sheet
sheet = client.open_by_key(
    "1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE"
).sheet1


st.title("📒 每月开销记录")

d = st.date_input("日期", date.today())

category = st.selectbox(
    "类别",
    ["餐饮","油费","购物","家庭","医疗","固定开销","其他"]
)

item = st.text_input("项目")

amount = st.number_input("金额", min_value=0.0)

if st.button("保存"):
    sheet.append_row([str(d), category, item, amount])
    st.success("记录成功")


# 读取数据
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.subheader("记录")

if not df.empty:
    st.dataframe(df)
else:
    st.write("暂无记录")

st.subheader("总开销")

if not df.empty:
    st.write(df["amount"].sum())

st.subheader("类别开销汇总")

if not df.empty:
    category_summary = df.groupby("category")["amount"].sum()
    st.dataframe(category_summary)
