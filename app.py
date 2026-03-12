import streamlit as st
from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt

# ========================
# 1. 用户配置中心
# ========================
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
# 2. 侧边栏：切换模式
# ========================
st.sidebar.title("👥 账户切换")
view_mode = st.sidebar.radio("选择查看模式：", ["本人", "太太", "家庭汇总"])

# 辅助函数：安全加载 CSV
def load_data(url):
    try:
        temp_df = pd.read_csv(url, thousands=",")
        if temp_df.empty:
            return pd.DataFrame(columns=["date", "category", "item", "amount"])
        # 强制格式化列名，防止因 Google Sheet 第一行不同而报错
        temp_df.columns = ["date", "category", "item", "amount"][:len(temp_df.columns)]
        return temp_df
    except:
        return pd.DataFrame(columns=["date", "category", "item", "amount"])

# ========================
# 3. 核心逻辑处理
# ========================
if view_mode == "家庭汇总":
    st.title("🏠 家庭财务总览")
    df_me = load_data(USER_CONFIG["本人"]["csv"])
    df_wife = load_data(USER_CONFIG["太太"]["csv"])
    df = pd.concat([df_me, df_wife], ignore_index=True)
    show_add_record = False
else:
    st.title(f"💰 {view_mode} 的财务看板")
    DATA_URL = USER_CONFIG[view_mode]["csv"]
    SHEET_URL = USER_CONFIG[view_mode]["script"]
    df = load_data(DATA_URL)
    show_add_record = True

# ========================
# 4. 添加记录 (仅在单人模式显示)
# ========================
if show_add_record:
    with st.expander(f"➕ 为 【{view_mode}】 新增记录", expanded=False):
        d = st.date_input("日期", date.today())
        category = st.selectbox("分类", ["收入", "固定开销", "信用卡", "日常与餐饮", "育儿与家庭", "其他支出"])
        item = st.text_input("项目内容")
        amount = st.number_input("金额", min_value=0.0)

        if st.button("保存记录"):
            post_data = {"date": str(d), "category": category, "item": item, "amount": amount}
            try:
                requests.post(SHEET_URL, json=post_data)
                st.success(f"✅ 已保存到 {view_mode} 的账本")
                st.rerun() # 刷新以显示新数据
            except:
                st.error("保存失败，请检查网络")

# ========================
# 5. 数据处理与可视化
# ========================
st.divider()

if df.empty or len(df) < 1:
    st.warning("⚠️ 当前选择的账本中没有数据，请先添加记录或检查 CSV 链接。")
else:
    try:
        # 数据清洗
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["category"] = df["category"].astype(str).str.strip()
        
        # 兼容旧分类 Mapping
        mapping = {
            "Housing": "固定开销", "Insurance": "固定开销", 
            "Communication": "其他支出", "Childcare": "育儿与家庭",
            "Food": "日常与餐饮", "Other": "其他支出",
            "Credit Card": "信用卡", "Income": "收入"
        }
        df["category"] = df["category"].replace(mapping)
        df["date"] = pd.to_datetime(df["date"])

        # 指标计算
        income = df[df["category"] == "收入"]["amount"].sum()
        expense = df[df["category"] != "收入"]["amount"].sum()
        balance = income - expense

        col1, col2, col3 = st.columns(3)
        col1.metric("总收入", f"RM {income:,.2f}")
        col2.metric("总支出", f"RM {expense:,.2f}")
        col3.metric("结余", f"RM {balance:,.2f}")

        # 最近记录
        st.subheader("📑 最近记录")
        st.dataframe(df.tail(5), use_container_width=True)

        # 支出分布
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("🍕 支出占比")
            expense_df = df[df["category"] != "收入"]
            if not expense_df.empty:
                category_summary = expense_df.groupby("category")["amount"].sum()
                fig, ax = plt.subplots()
                ax.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                st.pyplot(fig)
            else:
                st.write("暂无支出数据")

        with col_right:
            st.subheader("📈 每日趋势")
            if not expense_df.empty:
                daily = expense_df.groupby("date")["amount"].sum()
                st.line_chart(daily)
            else:
                st.write("暂无支出趋势")

    except Exception as e:
        st.error(f"数据处理出错: {e}")
