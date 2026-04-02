import streamlit as st
from datetime import date
import requests
import pandas as pd
import altair as alt
import time

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
# 2. 核心数据处理
# ========================
def get_data(csv_url):
    try:
        sep = "&" if "?" in csv_url else "?"
        final_url = f"{csv_url}{sep}t={int(time.time())}"
        df_raw = pd.read_csv(final_url, header=None)
        if df_raw.empty:
            return pd.DataFrame(columns=["date", "category", "item", "amount"])

        # 处理标题行
        first_row_str = str(df_raw.iloc[0, 0]).lower()
        if "date" in first_row_str or "日期" in first_row_str:
            df_raw = df_raw.drop(index=0)

        df_raw.columns = ["date", "category", "item", "amount"]
        # 金额清洗
        df_raw["amount"] = pd.to_numeric(df_raw["amount"].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        # 日期转换（关键：用于月份筛选）
        df_raw["date"] = pd.to_datetime(df_raw["date"], errors='coerce')
        df_raw["category"] = df_raw["category"].astype(str).str.strip()
        df_raw["category"] = df_raw["category"].replace(["Income", "income", "INCOME"], "收入")
        return df_raw.dropna(subset=["date"])
    except:
        return pd.DataFrame(columns=["date", "category", "item", "amount"])

# ========================
# 3. 界面逻辑与月份筛选
# ========================
st.sidebar.title("👥 账户切换")
view_mode = st.sidebar.radio("当前使用者：", ["老公", "太太", "家庭汇总"])

# 自动获取当前日期
today = date.today()
current_month = today.month

# 月份选择器：默认选中当前月份
selected_month = st.sidebar.selectbox(
    "查看月份：", 
    options=[4, 3, 2, 1], 
    index=0 if current_month == 4 else 1,
    format_func=lambda x: f"2026年 {x}月"
)

# 加载数据
if view_mode == "家庭汇总":
    st.title(f"🏠 家庭汇总 ({selected_month}月)")
    df_me = get_data(USER_CONFIG["老公"]["csv"])
    df_wife = get_data(USER_CONFIG["太太"]["csv"])
    df_all = pd.concat([df_me, df_wife], ignore_index=True)
    current_script = None
else:
    st.title(f"💰 {view_mode} 的账本 ({selected_month}月)")
    df_all = get_data(USER_CONFIG[view_mode]["csv"])
    current_script = USER_CONFIG[view_mode]["script"]

# 核心过滤：只保留选中月份的数据
df = df_all[df_all['date'].dt.month == selected_month].copy()

# ========================
# 4. 记账功能 (个人页显示)
# ========================
if current_script:
    with st.expander("➕ 快速记账", expanded=True):
        d = st.date_input("日期", date.today())
        cat = st.selectbox("分类", ["日常与餐饮", "固定开销", "信用卡", "育儿与家庭", "其他支出", "收入"])
        item = st.text_input("项目内容")
        amt = st.number_input("金额", min_value=0.0, step=10.0)
        if st.button("确认保存"):
            payload = {"date": str(d), "category": cat, "item": item, "amount": amt}
            try:
                res = requests.post(current_script, json=payload, timeout=10)
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
    income_mask = df["category"].str.contains("收入", na=False)
    inc = df[income_mask]["amount"].sum()
    exp = df[~income_mask]["amount"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("总收入", f"RM {inc:,.2f}")
    m2.metric("总支出", f"RM {exp:,.2f}")
    m3.metric("本月结余", f"RM {inc-exp:,.2f}")

    exp_df = df[~income_mask]
    if not exp_df.empty:
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**支出分类占比**")
            summary = exp_df.groupby("category")["amount"].sum().reset_index()
            # 使用 Altair 解决中文乱码
            pie = alt.Chart(summary).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("amount:Q"),
                color=alt.Color("category:N", legend=alt.Legend(title="分类")),
                tooltip=["category", "amount"]
            ).properties(height=250)
            st.altair_chart(pie, use_container_width=True)
            
        with c2:
            st.write("**每日趋势**")
            trend = exp_df.copy()
            st.line_chart(trend.groupby('date')['amount'].sum())

    # --- 差异化清单展示 ---
    if view_mode == "家庭汇总":
        st.subheader("📁 各类别支出统计")
        if not exp_df.empty:
            cat_summary = exp_df.groupby("category")["amount"].agg(['sum', 'count']).reset_index()
            cat_summary.columns = ["分类名称", "总支出", "交易笔数"]
            cat_summary["占比"] = (cat_summary["总支出"] / exp * 100).map("{:.1f}%".format)
            cat_summary["总支出"] = cat_summary["总支出"].map("RM {:,.2f}".format)
            
            # 以表格形式展示汇总，不显示流水
            st.table(cat_summary.sort_values("交易笔数", ascending=False))
        else:
            st.info("本月暂无支出记录")
    else:
        st.subheader("📑 本月流水明细")
        display_df = df.copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_df.sort_index(ascending=False), use_container_width=True)
else:
    st.info(f"💡 {selected_month}月 暂无数据。")
