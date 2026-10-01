import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Business Scraper - USA & Nigeria")

st.title("Business Scraper - Anywhere")

business = st.text_input("What business?", "restaurant").strip().lower()
location = st.text_input("Where? Example: Ikeja, Lagos or Houston, Texas, USA", "Ikeja, Lagos, Nigeria")
radius_km = st.slider("Radius km", 1, 50, 10)

if st.button("🔍 Scrape Now"):
    if not business or not location:
        st.error("Enter business and location")
        st.stop()

    with st.spinner(f"Finding {location}..."):
        # Geocode with timeout
        try:
            geo = requests.get(
                f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1",
                headers={"User-Agent": "business-scraper/1.0"},
                timeout=15
            ).json()
            if not geo:
                st.error("Location not found. Try 'Ikeja, Lagos, Nigeria'")
                st.stop()
            lat, lon = float(geo[0]['lat']), float(geo[0]['lon'])
            display_name = geo[0]['display_name']
            st.success(f"Found: {display_name}")
        except Exception as e:
            st.error(f"Map server busy, wait 10s and try again. Error: {e}")
            st.stop()

    with st.spinner(f"Scraping {business} near {location}..."):
        radius_m = radius_km * 1000
        # Simple, fast query - works for Nigeria
        query = f"""
        [out:json][timeout:30];
        (
          node["amenity"~"{business}",i](around:{radius_m},{lat},{lon});
          way["amenity"~"{business}",i](around:{radius_m},{lat},{lon});
          node["shop"~"{business}",i](around:{radius_m},{lat},{lon});
          way["shop"~"{business}",i](around:{radius_m},{lat},{lon});
          node["name"~"{business}",i](around:{radius_m},{lat},{lon});
        );
        out center 20;
        """

        servers = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.openstreetmap.ru/api/interpreter"
        ]

        results = []
        for server in servers:
            try:
                r = requests.post(server, data={"data": query}, timeout=35)
                if r.status_code == 200:
                    data = r.json()
                    results = data.get("elements", [])
                    break
            except:
                continue

        if not results:
            st.warning(f"No '{business}' found in {radius_km}km. Try: 1) Bigger radius 30km 2) Try 'pharmacy' or 'supermarket' in Lagos 3) Try location 'Lagos, Nigeria'")
        else:
            rows = []
            for el in results:
                tags = el.get("tags", {})
                rows.append({
                    "Name": tags.get("name", "Unnamed"),
                    "Type": tags.get("amenity") or tags.get("shop") or business,
                    "Phone": tags.get("phone") or tags.get("contact:phone") or "",
                    "Lat": el.get("lat") or el.get("center", {}).get("lat"),
                    "Lon": el.get("lon") or el.get("center", {}).get("lon"),
                })
            df = pd.DataFrame(rows)
            st.success(f"Found {len(df)} businesses!")
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False), "businesses.csv", "text/csv")
