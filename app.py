import streamlit as st
from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt

# ========================
# 1. 填入你的和太太的最新链接
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
# 2. 侧边栏：用户切换
# ========================
st.sidebar.title("👥 账户切换")
view_mode = st.sidebar.radio("当前使用者：", ["本人", "太太", "家庭汇总"])

# 统一的数据加载函数
import time

def get_data(csv_url):
    try:
        # 判断链接类型
        if "export?format=csv" in csv_url:
            # 你原本的链接，不需要加时间戳
            final_url = csv_url
        else:
            # 太太的发布链接，需要加时间戳防缓存
            sep = "&" if "?" in csv_url else "?"
            final_url = f"{csv_url}{sep}t={int(time.time())}"
        
        # 读取数据
        # 注意：如果你原本的表第一行就是数据（没有标题），请把 skiprows=1 删掉
        df_raw = pd.read_csv(final_url, thousands=",", skiprows=1, names=["date", "category", "item", "amount"])
        
        # 彻底清洗：去掉空行
        df_raw = df_raw.dropna(subset=["amount"]) 
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
# 4. 新增记录
# ========================
if current_script:
    with st.expander("➕ 记一笔"):
        d = st.date_input("日期", date.today())
        cat = st.selectbox("分类", ["收入", "固定开销", "信用卡", "日常与餐饮", "育儿与家庭", "其他支出"])
        it = st.text_input("项目")
        amt = st.number_input("金额", min_value=0.0)
        
if st.button("点此保存"):
            payload = {"date": str(d), "category": cat, "item": it, "amount": amt}
            try:
                res = requests.post(current_script, json=payload, timeout=10)
                # 打印详细的状态码和返回内容
                if res.status_code == 200:
                    st.success("保存成功！")
                    st.rerun()
                else:
                    st.error(f"保存失败。状态码: {res.status_code}")
                    st.write("错误反馈:", res.text) # 这里会显示 Google 返回的具体报错
            except Exception as e:
                st.error(f"请求发送出错: {e}")

# ========================
# 5. 图表展示
# ========================
st.divider()
if not df.empty:
    # 基础清洗
    df["amount"] = pd.to_numeric(df["amount"], errors='coerce').fillna(0)
    
    # 指标
    inc = df[df["category"] == "收入"]["amount"].sum()
    exp = df[df["category"] != "收入"]["amount"].sum()
    st.columns(3)[0].metric("总收入", f"{inc:,.2f}")
    st.columns(3)[1].metric("总支出", f"{exp:,.2f}")
    st.columns(3)[2].metric("结余", f"{inc-exp:,.2f}")
    
    # 饼图
    exp_df = df[df["category"] != "收入"]
    if not exp_df.empty:
        summary = exp_df.groupby("category")["amount"].sum()
        fig, ax = plt.subplots()
        ax.pie(summary, labels=summary.index, autopct='%1.1f%%')
        st.pyplot(fig)
    
    st.write("**最近记录**")
    st.dataframe(df.tail(5), use_container_width=True)
else:
    st.info("当前账本还没有数据。")


