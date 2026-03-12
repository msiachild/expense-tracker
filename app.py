import streamlit as st
from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time

# ========================
# 1. 链接配置
# ========================
USER_CONFIG = {
    "本人": {
        "script": "https://script.google.com/macros/s/AKfycbzxJnB82RKPi-SNVatTZLHtJRBRjdF3vVjHU5SomeFlaozdR-48u3H4diflI9h2WWFjtQ/exec",
        "csv": "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/export?format=csv"
    },
    "太太": {
        "script": "https://script.google.com/macros/s/AKfycbzr7Fg9p9oQj2J7sGbBEejAGM6eWp_0qsJY31aoK6FFqzMzbGqQgloaBz1APD7TaQeS/exec", 
        "csv": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTxVWMdIqN7E-2Kz1fLBzwItX7yjK_EILOCbek3ynR5OhkhXh2lcP8Q6ljwq3q8yehmGrz0njcF7ilR/pub?output=csv"
    }
}

# ========================
# 2. 核心数据加载 (解决 0 数据问题)
# ========================
def get_data(csv_url):
    try:
        # 为所有链接添加时间戳，强制刷新，解决“删了数据还显示”或“有数据不显示”的问题
        sep = "&" if "?" in csv_url else "?"
        final_url = f"{csv_url}{sep}t={int(time.time())}"
        
        # 读取原始数据
        df_raw = pd.read_csv(final_url, thousands=",", header=None)
        
        if df_raw.empty:
            return pd.DataFrame(columns=["date", "category", "item", "amount"])

        # 智能判定：如果第一行包含字母标题，则剔除
        first_row_str = str(df_raw.iloc[0].values).lower()
        if "date" in first_row_str or "日期" in first_row_str or "category" in first_row_str:
            df_raw = df_raw.drop(index=0)

        # 强制设置列名
        df_raw.columns = ["date", "category", "item", "amount"]
        
        # 数据大扫除：去掉所有空格，统一分类名称
        df_raw["category"] = df_raw["category"].astype(str).str.strip()
        # 兼容英文分类
        mapping = {"Income": "收入", "Food": "日常与餐饮", "Fixed": "固定开销", "Credit": "信用卡"}
        df_raw["category"] = df_raw["category"].replace(mapping)
        
        # 强制转换金额
        df_raw["amount"] = pd.to_numeric(df_raw["amount"], errors='coerce').fillna(0)
        
        # 去掉无效行
        df_raw = df_raw.dropna(subset=["date"])
        
        return df_raw
    except Exception as e:
        return pd.DataFrame(columns=["date", "category", "item", "amount"])

# ========================
# 3. 界面逻辑
# ========================
st.sidebar.title("👥 账户切换")
view_mode = st.sidebar.radio("当前使用者：", ["本人", "太太", "家庭汇总"])

if view_mode == "家庭汇总":
    st.title("🏠 家庭财务总览")
    df_me = get_data(USER_CONFIG["本人"]["csv"])
    df_wife = get_data(USER_CONFIG["太太"]["csv"])
    df = pd.concat([df_me, df_wife], ignore_index=True)
    current_script = None
else:
    st.title(f"💰 {view_mode} 的账本")
    df = get_data(USER_CONFIG[view_mode]["csv"])
    current_script = USER_CONFIG[view_mode]["script"]

# ========================
# 4. 记账功能 (修复缩进)
# ========================
if current_script:
    with st.expander("➕ 记一笔", expanded=True):
        col_d, col_c = st.columns(2)
        with col_d:
            d = st.date_input("日期", date.today())
        with col_c:
            cat = st.selectbox("分类", ["日常与餐饮", "固定开销", "信用卡", "育儿与家庭", "其他支出", "收入"])
        
        item = st.text_input("项目内容")
        amt = st.number_input("金额", min_value=0.0, step=10.0)
        
        if st.button("确认保存"):
            payload = {"date": str(d), "category": cat, "item": item, "amount": amt}
            try:
                res = requests.post(current_script, json=payload, timeout=10)
                if res.status_code == 200:
                    st.success("✅ 已存入 Google Sheet！正在更新图表...")
                    time.sleep(1.5) # 给 Google 数据库同步留一点时间
                    st.rerun()
                else:
                    st.error("保存失败，请检查 Script 权限")
            except:
                st.error("网络连接超时")

# ========================
# 5. 图表与统计
# ========================
st.divider()

if not df.empty:
    # 统计核心指标
    # 再次确保统计时分类名没有多余空格
    df["category"] = df["category"].str.strip()
    
    total_income = df[df["category"] == "收入"]["amount"].sum()
    total_expense = df[df["category"] != "收入"]["amount"].sum()
    net_balance = total_income - total_expense

    m1, m2, m3 = st.columns(3)
    m1.metric("总收入", f"RM {total_income:,.2f}")
    m2.metric("总支出", f"RM {total_expense:,.2f}")
    m3.metric("结余", f"RM {net_balance:,.2f}")

    # 可视化
    st.write("---")
    exp_df = df[df["category"] != "收入"]
    
    if not exp_df.empty:
        c_left, c_right = st.columns(2)
        with c_left:
            st.write("**支出构成**")
            pie_data = exp_df.groupby("category")["amount"].sum()
            fig, ax = plt.subplots()
            ax.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)
        with c_right:
            st.write("**支出趋势**")
            # 简单处理日期排序
            trend_data = exp_df.copy()
            trend_data['date'] = pd.to_datetime(trend_data['date'])
            daily_trend = trend_data.groupby('date')['amount'].sum()
            st.line_chart(daily_trend)

    st.write("**账目明细**")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
else:
    st.info("💡 暂无数据。如果你刚删除了表格内容，请记一笔新账开始。")
