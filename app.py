import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Anywhere Business Scraper", page_icon="🌍")
st.title("🌍 Anywhere Business Scraper")
st.write("Works ANYWHERE in the world - Lagos, London, Dubai, USA!")

business_type = st.text_input("What business?", "pharmacy")
location = st.text_input("Which city / location?", "Lagos, Nigeria")
radius = st.slider("Search radius (km)", 2, 30, 10)

if st.button("🔍 Scrape Anywhere"):
    with st.spinner(f"Searching {business_type} in {location}..."):
        try:
            # Step 1: Find location coordinates
            geo_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
            geo_res = requests.get(geo_url, headers={"User-Agent":"AnywhereScraper/1.0"}).json()

            if not geo_res:
                st.error("Location not found. Try 'Ikeja, Lagos' or 'London, UK'")
            else:
                lat = geo_res[0]['lat']
                lon = geo_res[0]['lon']
                st.success(f"Found: {geo_res[0]['display_name']}")

                # Step 2: Search businesses using OpenStreetMap (FREE, works ANYWHERE)
                overpass_url = "https://overpass-api.de/api/interpreter"
                query = f"""
                [out:json][timeout:25];
                (
                  nwr["name"]["amenity"~"{business_type}",i](around:{radius*1000},{lat},{lon});
                  nwr["name"]["shop"~"{business_type}",i](around:{radius*1000},{lat},{lon});
                  nwr["name"~"{business_type}",i](around:{radius*1000},{lat},{lon});
                );
                out center 100;
                """
                res = requests.get(overpass_url, params={'data': query}).json()

                data = []
                for el in res.get('elements', []):
                    tags = el.get('tags', {})
                    data.append({
                        'Name': tags.get('name','Unknown'),
                        'Type': tags.get('amenity', tags.get('shop','Business')),
                        'Street': tags.get('addr:street',''),
                        'Phone': tags.get('phone', tags.get('contact:phone','')),
                        'Latitude': el.get('lat', el.get('center',{}).get('lat')),
                        'Longitude': el.get('lon', el.get('center',{}).get('lon')),
                    })

                if data:
                    df = pd.DataFrame(data)
                    st.balloons()
                    st.write(f"Found {len(df)} businesses in {location}!")
                    st.dataframe(df)

                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download CSV", csv, f"{business_type}_{location}.csv", "text/csv")
                else:
                    st.warning(f"No '{business_type}' found in {location}. Try different spelling like 'restaurant' or 'supermarket'")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.caption("No API key needed. Works in ANY city worldwide!")
