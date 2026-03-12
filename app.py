import streamlit as st
from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt

# ========================
# 1. 用户配置中心
# ========================
# 请在这里填入太太的 CSV 链接
USER_CONFIG = {
    "本人": {
        "script": "https://script.google.com/macros/s/AKfycbzxJnB82RKPi-SNVatTZLHtJRBRjdF3vVjHU5SomeFlaozdR-48u3H4diflI9h2WWFjtQ/exec",
        "csv": "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/export?format=csv"
    },
    "太太": {
        "script": "https://script.google.com/macros/s/AKfycbyFb9k-EcAI-wcJuwxppFtgibwriOOu4FXwW5Cd6_M6ZGy-V8WLjbuJvADbNtwDfP3t/exec",
        "csv": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQPjrycXVQ1CZvdX-fKvaC_XGOLkpzjET146x5s7a58R7eigrOF1n0H56TCvF17uXODkJnQlhiQNypP/pub?output=csv" 
    }
}

# ========================
# 2. 侧边栏：切换用户
# ========================
st.sidebar.title("👥 账户切换")
current_user = st.sidebar.radio("当前记录人：", list(USER_CONFIG.keys()))

# 动态获取当前选中的 URL
SHEET_URL = USER_CONFIG[current_user]["script"]
DATA_URL = USER_CONFIG[current_user]["csv"]

st.title(f"💰 {current_user} 的财务看板")

# ========================
# 3. 添加记录 (Add Record)
# ========================
st.subheader(f"新增记录 ({current_user})")

d = st.date_input("日期", date.today())
category = st.selectbox(
    "分类",
    ["收入", "固定开销", "信用卡", "日常与餐饮", "育儿与家庭", "其他支出"]
)
item = st.text_input("项目内容")
amount = st.number_input("金额", min_value=0.0)

if st.button("保存记录"):
    data = {
        "date": str(d),
        "category": category,
        "item": item,
        "amount": amount
    }
    try:
        # 发送到当前选中的 SHEET_URL
        requests.post(SHEET_URL, json=data)
        st.success(f"✅ 已保存到 {current_user} 的账本")
    except:
        st.error("保存失败，请检查网络或 Script URL")

# ========================
# 4. 加载与展示数据 (Load Data)
# ========================
st.divider() # 画一条分割线
st.subheader(f"📊 {current_user} 的财务概览")

try:
    # 加载当前用户的 CSV
    df = pd.read_csv(DATA_URL, thousands=",")
    df.columns = ["date", "category", "item", "amount"]
    df["category"] = df["category"].astype(str).str.strip()

    # 兼容旧分类 Mapping
    mapping = {
        "Housing": "固定开销", "Insurance": "固定开销", 
        "Communication": "其他支出", "Childcare": "育儿与家庭",
        "Food": "日常与餐饮", "Other": "其他支出",
        "Credit Card": "信用卡", "Income": "收入"
    }
    df["category"] = df["category"].replace(mapping)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"])

    # 计算指标
    income = df[df["category"] == "收入"]["amount"].sum()
    expense = df[df["category"] != "收入"]["amount"].sum()
    balance = income - expense

    col1, col2, col3 = st.columns(3)
    col1.metric("总收入", f"RM {income:,.2f}")
    col2.metric("总支出", f"RM {expense:,.2f}")
    col3.metric("结余", f"RM {balance:,.2f}")

    # 最近记录
    st.write("---")
    st.write("**最近 3 条记录**")
    st.dataframe(df.tail(3), use_container_width=True)

    # 支出分布饼图
    st.write("---")
    st.write("**支出分布**")
    expense_df = df[df["category"] != "收入"]
    category_summary = expense_df.groupby("category")["amount"].sum()
    
    # 绘图逻辑保持不变...
    label_map = {"固定开销": "Fixed", "信用卡": "Credit", "日常与餐饮": "Food", "育儿与家庭": "Childcare", "其他支出": "Other"}
    labels = [label_map.get(i, i) for i in category_summary.index]
    
    fig, ax = plt.subplots()
    ax.pie(category_summary, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

    # 趋势图
    st.write("---")
    st.write("**每日支出趋势**")
    daily = expense_df.groupby("date")["amount"].sum()
    st.line_chart(daily)

except Exception as e:
    st.warning("暂无数据或加载失败。请确保 Google Sheet 已发布为 CSV 且有数据。")
