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
# 2. 侧边栏
# ========================
st.sidebar.title("👥 账户切换")
view_mode = st.sidebar.radio("当前使用者：", ["本人", "太太", "家庭汇总"])

# 统一的数据加载函数
def get_data(csv_url):
    try:
        if "export?format=csv" in csv_url:
            final_url = csv_url
        else:
            sep = "&" if "?" in csv_url else "?"
            final_url = f"{csv_url}{sep}t={int(time.time())}"
        
        # 读取数据
        df_raw = pd.read_csv(final_url, thousands=",", header=None)
        
        if df_raw.empty:
            return pd.DataFrame(columns=["date", "category", "item", "amount"])

        # 智能判定标题行
        first_cell = str(df_raw.iloc[0, 0]).lower()
        if "date" in first_cell or "日期" in first_cell:
            df_raw = df_raw.drop(index=0)

        df_raw.columns = ["date", "category", "item", "amount"]
        
        # --- 重点修复开始 ---
        # 1. 强制清理分类列：转字符串、去前后空格、处理英文变中文
        df_raw["category"] = df_raw["category"].astype(str).str.strip()
        mapping = {"Income": "收入", "INCOME": "收入"}
        df_raw["category"] = df_raw["category"].replace(mapping)
        
        # 2. 强制转换金额：确保是数字
        df_raw["amount"] = pd.to_numeric(df_raw["amount"], errors='coerce').fillna(0)
        # --- 重点修复结束 ---
        
        df_raw = df_raw.dropna(subset=["date"])
        return df_raw
    except Exception as e:
        return pd.DataFrame(columns=["date", "category", "item", "amount"])

# ========================
# 3. 页面逻辑
# ========================
if view_mode == "家庭汇总":
    st.title("🏠 家庭财务总览")
    df1 = get_data(USER_CONFIG["本人"]["csv"])
    df2 = get_data(USER_CONFIG["太太"]["csv"])
    df = pd.concat([df1, df2], ignore_index=True)
    current_script = None
else:
    st.title(f"💰 {view_mode} 的账本")
    current_script = USER_CONFIG[view_mode]["script"]
    df = get_data(USER_CONFIG[view_mode]["csv"])

# ========================
# 4. 新增记录 (注意缩进修正)
# ========================
if current_script:
    with st.expander("➕ 记一笔", expanded=True):
        d = st.date_input("日期", date.today())
        cat = st.selectbox("分类", ["日常与餐饮", "固定开销", "信用卡", "育儿与家庭", "其他支出", "收入"])
        it = st.text_input("项目")
        amt = st.number_input("金额", min_value=0.0, step=0.1)
        
        # 修正：保存按钮必须在 if current_script 的缩进内
        if st.button("点此保存"):
            payload = {"date": str(d), "category": cat, "item": it, "amount": amt}
            try:
                res = requests.post(current_script, json=payload, timeout=10)
                if res.status_code == 200:
                    st.success("✅ 保存成功！正在刷新...")
                    time.sleep(1) # 给 Google Sheet 一点反应时间
                    st.rerun()
                else:
                    st.error(f"❌ 保存失败 (Code: {res.status_code})")
            except Exception as e:
                st.error(f"请求出错: {e}")

# ========================
# 5. 图表展示
# ========================
st.divider()
if not df.empty:
    # 基础清洗确保类型正确
    df["amount"] = pd.to_numeric(df["amount"], errors='coerce').fillna(0)
    
    # 概览指标
    inc = df[df["category"] == "收入"]["amount"].sum()
    exp = df[df["category"] != "收入"]["amount"].sum()
    bal = inc - exp

    c1, c2, c3 = st.columns(3)
    c1.metric("总收入", f"RM {inc:,.2f}")
    c2.metric("总支出", f"RM {exp:,.2f}")
    c3.metric("结余", f"RM {bal:,.2f}", delta_color="normal")
    
    # 支出图表
    st.write("---")
    exp_df = df[df["category"] != "收入"]
    if not exp_df.empty:
        col_left, col_right = st.columns(2)
        with col_left:
            summary = exp_df.groupby("category")["amount"].sum()
            fig, ax = plt.subplots(figsize=(5,5))
            ax.pie(summary, labels=summary.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)
        with col_right:
            # 每日趋势
            daily = exp_df.groupby("date")["amount"].sum()
            st.line_chart(daily)
    
    st.write("**最近 5 条记录**")
    st.dataframe(df.tail(5), use_container_width=True)
else:
    st.info("💡 当前账本还没有数据，请尝试添加第一笔账单。")


