import streamlit as st
from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time

# 基础设置：尝试解决中文字体问题，若环境不支持则备选英文
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ========================
# 1. 链接配置
# ========================
USER_CONFIG = {
    "老公": {
        "script": "https://script.google.com/macros/s/AKfycbzxJnB82RKPi-SNVatTZLHtJRBRjdF3vVjHU5SomeFlaozdR-48u3H4diflI9h2WWFjtQ/exec",
        "csv": "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/export?format=csv"
    },
    "太太": {
        "script": "https://script.google.com/macros/s/AKfycbzr7Fg9p9oQj2J7sGbBEejAGM6eWp_0qsJY31aoK6FFqzMzbGqQgloaBz1APD7TaQeS/exec", 
        "csv": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTxVWMdIqN7E-2Kz1fLBzwItX7yjK_EILOCbek3ynR5OhkhXh2lcP8Q6ljwq3q8yehmGrz0njcF7ilR/pub?output=csv"
    }
}

# ========================
# 2. 核心数据处理函数
# ========================
def get_data(csv_url):
    try:
        # 强制刷新缓存
        sep = "&" if "?" in csv_url else "?"
        final_url = f"{csv_url}{sep}t={int(time.time())}"
        
        # 读取数据 (不设标题，手动处理)
        df_raw = pd.read_csv(final_url, header=None)
        
        if df_raw.empty:
            return pd.DataFrame(columns=["date", "category", "item", "amount"])

        # 判定并移除标题行
        first_row_str = str(df_raw.iloc[0, 0]).lower()
        if "date" in first_row_str or "日期" in first_row_str:
            df_raw = df_raw.drop(index=0)

        df_raw.columns = ["date", "category", "item", "amount"]

        # --- 处理逗号和数字的关键步骤 ---
        # 1. 处理金额：先转字符串 -> 去掉逗号 -> 转浮点数
        df_raw["amount"] = df_raw["amount"].astype(str).str.replace(',', '', regex=False)
        df_raw["amount"] = pd.to_numeric(df_raw["amount"], errors='coerce').fillna(0)
        
        # 2. 处理分类：去空格 + 兼容变体
        df_raw["category"] = df_raw["category"].astype(str).str.strip()
        income_names = ["收入", "Income", "income", "INCOME"]
        df_raw["category"] = df_raw["category"].replace(income_names, "收入")
        
        return df_raw.dropna(subset=["date"])
    except Exception as e:
        return pd.DataFrame(columns=["date", "category", "item", "amount"])

# ========================
# 3. 界面逻辑
# ========================
st.sidebar.title("👥 账户切换")
view_mode = st.sidebar.radio("当前使用者：", ["老公", "太太", "家庭汇总"])

if view_mode == "家庭汇总":
    st.title("🏠 家庭财务总览")
    df_me = get_data(USER_CONFIG["老公"]["csv"])
    df_wife = get_data(USER_CONFIG["太太"]["csv"])
    df = pd.concat([df_me, df_wife], ignore_index=True)
    current_script = None
else:
    st.title(f"💰 {view_mode} 的账本")
    df = get_data(USER_CONFIG[view_mode]["csv"])
    current_script = USER_CONFIG[view_mode]["script"]

# ========================
# 4. 记账功能
# ========================
if current_script:
    with st.expander("➕ 快速记账", expanded=True):
        d = st.date_input("日期", date.today())
        cat = st.selectbox("分类", ["日常与餐饮", "固定开销", "信用卡", "育儿与家庭", "其他支出", "收入"])
        item = st.text_input("项目内容")
        amt = st.number_input("金额", min_value=0.0, step=100.0)
        
        if st.button("点此保存"):
            payload = {"date": str(d), "category": cat, "item": item, "amount": amt}
            try:
                res = requests.post(current_script, json=payload, timeout=10)
                if res.status_code == 200:
                    st.success("✅ 已同步到云端")
                    time.sleep(1)
                    st.rerun()
            except:
                st.error("网络请求失败")

# ========================
# 5. 指标与图表
# ========================
st.divider()

if not df.empty:
    # 基础数据准备
    income_mask = df["category"].str.contains("收入", na=False)
    df_income = df[income_mask]
    df_expense = df[~income_mask]
    
    inc_total = df_income["amount"].sum()
    exp_total = df_expense["amount"].sum()

    # 顶部三大指标
    m1, m2, m3 = st.columns(3)
    m1.metric("总收入", f"RM {inc_total:,.2f}")
    m2.metric("总支出", f"RM {exp_total:,.2f}")
    m3.metric("结余", f"RM {inc_total - exp_total:,.2f}")

    if view_mode == "家庭汇总":
        st.subheader("📊 家庭支出分类统计")
        
        if not df_expense.empty:
            # --- 核心修改：按分类汇总 ---
            category_summary = df_expense.groupby("category")["amount"].agg(['sum', 'count']).reset_index()
            category_summary.columns = ["消费类别", "支出金额 (RM)", "笔数"]
            
            # 计算占比
            category_summary["占比"] = (category_summary["支出金额 (RM)"] / exp_total * 100).map("{:.1f}%".format)
            # 格式化金额显示
            category_summary["支出金额 (RM)"] = category_summary["支出金额 (RM)"].map("¥{:,.2f}".format)
            
            # 展示分类清单（替代流水清单）
            st.dataframe(
                category_summary.sort_values("笔数", ascending=False), 
                use_container_width=True,
                hide_index=True
            )
            
            # 可选：展示具体的分类饼图
            fig, ax = plt.subplots(figsize=(6, 4))
            # 简单处理：如果分类是中文且环境不支持，饼图标签可能乱码，这里沿用您之前的翻译逻辑
            plot_data = df_expense.groupby("category")["amount"].sum()
            ax.pie(plot_data, labels=plot_data.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)
        else:
            st.info("本月暂无支出数据。")

    else:
        # --- 个人页面：保留流水清单便于核对 ---
        st.subheader(f"📑 {view_mode} 消费流水")
        st.dataframe(df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)

else:
    st.info("💡 暂无数据。")

