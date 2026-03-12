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
def get_data(csv_url):
    try:
        # 【关键】在链接后加一个时间戳，防止浏览器缓存旧数据
        # 这样每次刷新或保存，App 都会强制去 Google 拿最干净的数据
        sep = "&" if "?" in csv_url else "?"
        url_with_cache_buster = f"{csv_url}{sep}t={int(time.time())}"
        
        # 读取数据，强制指定列名
        df_raw = pd.read_csv(url_with_cache_buster, thousands=",", skiprows=1, names=["date", "category", "item", "amount"])
        
        # 清洗：去掉全是空的行，并将金额转为数字
        df_raw = df_raw.dropna(how='all')
        df_raw["amount"] = pd.to_numeric(df_raw["amount"], errors='coerce').fillna(0)
        
        return df_raw
    except Exception as e:
        # 如果报错，返回一个带标题的空表，保证后续绘图不崩溃
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


