if st.button("Save Record"):

    if user == "Wife":

        requests.post(
            SCRIPT_URL,
            data={
                "entry.815399500_year": d.year,
                "entry.815399500_month": d.month,
                "entry.815399500_day": d.day,
                "entry.211305940": category,
                "entry.1158868403": item,
                "entry.995005981": amount
            }
        )

    else:

        payload = {
            "date": str(d),
            "category": category,
            "item": item,
            "amount": amount
        }

        requests.post(SCRIPT_URL, data=payload)

    st.success("Record Saved")
