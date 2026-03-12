if st.button("Save Record"):

    payload = {
        "date": str(d),
        "category": category,
        "item": item,
        "amount": amount
    }

    try:
        requests.post(SCRIPT_URL, data=payload)
        st.success("Record Saved")
    except:
        st.error("Save failed")
