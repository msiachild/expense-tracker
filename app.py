import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope,
)

client = gspread.authorize(creds)

sheet = client.open_by_key("1rCd-REYtsmtQ48mLDYFcp-o_a5WVr8Ihqx9rWS3GDRE").sheet1
