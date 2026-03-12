import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

st.title("💰 Personal Finance Dashboard")

# =========================

# User Selection

# =========================

user = st.selectbox("User", ["TTC", "Wife"])

TTC_SCRIPT = "https://script.google.com/macros/s/AKfycbzxJnB82RKPi-SNVatTZLHtJRBRjdF3vVjHU5SomeFlaozdR-48u3H4diflI9h2WWFjtQ/exec"
TTC_DATA = "https://docs.google.com/spreadsheets/d/1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE/export?format=csv"

WIFE_SCRIPT = "https://script.google.com/macros/s/AKfycbxLT5KM3_t5wowIA7crfAeaOtyA4X0vexRbyiU9Oj9Sp1szDcYF7CLnA-qCZCy7bjsi/exec"
WIFE_DATA = "https://docs.google.com/spreadsheets/d/1YIZt7mcYS7llnJa1JANB5rz-o2EE_AqOi1j2h8M97Vg/export?format=csv"

if user == "TTC":
SCRIPT_URL = TTC_SCRIPT
DATA_URL = TTC_DATA
else:
SCRIPT_URL = WIFE_SCRIPT
DATA_URL = WIFE_DATA

# =========================

# Add Record

# =========================

st.subheader("Add Record")

d = st.date_input("Date", date.today())

category = st.selectbox(
"Category",
["收入","固定开销","信用卡","日常与餐饮","育儿与家庭","其他支出"]
)

item = st.text_input("Item")

amount = st.number_input("Amount", min_value=0.0)

if st.button("Save Record"):

```
payload = {
    "date": str(d),
    "category": category,
    "item": item,
    "amount": amount
}

try:
    requests.post(SCRIPT_URL, json=payload)
    st.success("Record Saved")
except:
    st.error("Save failed")
```

# =========================

# Load Data

# =========================

st.subheader("Financial Overview")

try:

```
df = pd.read_csv(DATA_URL)

if df.empty:
    st.info("No data yet")
    st.stop()

df.columns = ["date","category","item","amount"]

df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

df["date"] = pd.to_datetime(df["date"], errors="coerce")

df = df.dropna(subset=["date"])

# Income / Expense

income = df[df["category"]=="收入"]["amount"].sum()
expense = df[df["category"]!="收入"]["amount"].sum()

col1,col2,col3 = st.columns(3)

col1.metric("Income",round(income,2))
col2.metric("Expense",round(expense,2))
col3.metric("Balance",round(income-expense,2))

# Recent

st.subheader("Recent Records")
st.dataframe(df.tail(3))

# Expense by Category

st.subheader("Expense by Category")

exp = df[df["category"]!="收入"]

summary = exp.groupby("category")["amount"].sum()

order = ["固定开销","信用卡","日常与餐饮","育儿与家庭","其他支出"]

summary = summary.reindex(order).fillna(0)

st.dataframe(summary)

# Pie Chart

st.subheader("Expense Distribution")

if summary.sum() > 0:

    fig,ax = plt.subplots()

    labels = ["Fixed","Credit Card","Food","Childcare","Other"]

    ax.pie(summary,labels=labels,autopct='%1.1f%%')

    ax.axis("equal")

    st.pyplot(fig)

else:
    st.info("No expense data yet")

# Daily Trend

st.subheader("Daily Expense Trend")

daily = exp.groupby("date")["amount"].sum()

st.line_chart(daily)
```

except Exception as e:

```
st.error("Failed to load data")
st.write(e)
```
