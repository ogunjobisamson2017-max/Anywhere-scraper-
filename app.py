import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Anywhere Scraper Fixed", page_icon="🌍")
st.title("🌍 Anywhere Business Scraper")

business = st.text_input("What business?", "pharmacy")
location = st.text_input("Where? Example: Ikeja, Lagos or Houston, Texas, USA", "Ikeja, Lagos, Nigeria")
radius = st.slider("Radius km", 2, 30, 10)

if st.button("🔍 Scrape Now"):
    try:
        with st.spinner(f"Finding {location}..."):
            # Step 1: Geocode
            geo_url = "https://nominatim.openstreetmap.org/search"
            r = requests.get(geo_url, params={"q": location, "format": "json", "limit": 1}, headers={"User-Agent": "ScraperFix/1.0"}, timeout=20)
            j = r.json()
            if not j:
                st.error("Location not found. Use format: 'City, State, Country' e.g. Houston, Texas, USA")
                st.stop()
            lat, lon = j[0]['lat'], j[0]['lon']
            st.info(f"Found: {j[0]['display_name']}")

        with st.spinner(f"Scraping {business} near {location}..."):
            query = f'[out:json][timeout:25];(nwr["name"~"{business}",i](around:{radius*1000},{lat},{lon});nwr["shop"~"{business}",i](around:{radius*1000},{lat},{lon});nwr["amenity"~"{business}",i](around:{radius*1000},{lat},{lon}););out center 50;'

            # Retry 3 times
            data_json = None
            for i in range(3):
                resp = requests.get("https://overpass-api.de/api/interpreter", params={"data": query}, timeout=30)
                if resp.status_code == 200 and resp.text:
                    try:
                        data_json = resp.json()
                        break
                    except:
                        time.sleep(2)
                time.sleep(3)

            if not data_json or not data_json.get('elements'):
                st.warning("No results or server busy. Try: 1) Increase radius 2) Try 'restaurant' 3) Wait 10 sec and try again")
                st.stop()

            rows = []
            for el in data_json['elements']:
                tags = el.get('tags', {})
                rows.append({"Name": tags.get('name','N/A'), "Phone": tags.get('phone', tags.get('contact:phone','')), "Type": tags.get('shop', tags.get('amenity',''))})

            df = pd.DataFrame(rows)
            st.success(f"Found {len(df)} businesses!")
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False), "results.csv", "text/csv")
    except Exception as e:
        st.error(f"Error: {e}")
        st.write("Tip: Type full location like 'Lagos, Nigeria' or 'Texas, USA'")

st.caption("No API key needed!")
