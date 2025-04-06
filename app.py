import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import folium_static
import tempfile
import os

def upload_files():
    st.title("Upload Geospatial Data Files")
    
    uploaded_shapefile = st.file_uploader(
        "Upload Shapefile components (SHP, SHX, DBF, PRJ, optional CPG)", 
        type=["shp", "shx", "dbf", "prj", "cpg"], accept_multiple_files=True
    )
    uploaded_population = st.file_uploader("Upload Population CSV", type=["csv"])
    uploaded_land = st.file_uploader("Upload Land Data CSV", type=["csv"])
    
    return uploaded_shapefile, uploaded_population, uploaded_land

def save_uploaded_files(uploaded_files):
    temp_dir = tempfile.TemporaryDirectory()
    file_paths = {}

    for file in uploaded_files:
        file_path = os.path.join(temp_dir.name, file.name)
        file_paths[file.name.split('.')[-1]] = file_path
        with open(file_path, 'wb') as f:
            f.write(file.getvalue())

    return file_paths, temp_dir

def process_files(shapefile_paths, population_file, land_file):
    gdf = gpd.read_file(shapefile_paths['shp'])
    population_data = pd.read_csv(population_file, encoding='latin1')
    land_data = pd.read_csv(land_file)

    # Merge datasets
    gdf = gdf.merge(population_data, left_on='statename', right_on='State orÿUnion Territory', how='left')
    gdf = gdf.merge(land_data, left_on='statename', right_on='States/UTs', how='left')

    # Convert columns to numeric, handling potential string formatting issues
    gdf['Urban Planning'] = gdf['Urban pop. In %'].str.replace('%', '', regex=False).astype(float).fillna(0)
    gdf['Infrastructure Development'] = gdf['Net area sown'].astype(float).fillna(0)
    gdf['Environmental Conservation'] = gdf['Forests'].astype(float).fillna(0)
    
    # Fix: Remove commas before converting Density to float
    gdf['Socio-Economics Analysis'] = gdf['Density'].str.replace(',', '', regex=True).astype(float).fillna(0)

    # Assign recommendations based on data
    gdf['Urban Planning Recommendation'] = gdf['Urban Planning'].apply(
        lambda x: "Focus on sustainable urbanization in high urban density areas" if x > 60
        else "Enhance infrastructure resilience and promote mixed-use development" if x > 54.1
        else "Encourage eco-friendly transportation and smart city initiatives" if x > 48.2
        else "Strengthen public transport systems and pedestrian-friendly spaces" if x > 42.3
        else "Promote green building practices and energy-efficient policies" if x > 36.4
        else "Support community-driven urban projects and housing affordability" if x > 30.5
        else "Develop sustainable industrial zones and manage urban sprawl" if x > 24.6
        else "Improve basic infrastructure and access to essential services" if x > 18.7
        else "Encourage planned urban growth and reduce informal settlements" if x > 11
        else "Promote urban development in underdeveloped areas"
    )

    gdf['Infrastructure Development Recommendation'] = gdf['Infrastructure Development'].apply(
        lambda x: (
        "Expand infrastructure projects significantly in states with highly extensive agricultural land" if x > 10000
        else "Encourage large-scale infrastructure expansion to support agriculture and rural growth" if x > 8000
        else "Promote balanced infrastructure development to complement agricultural production" if x > 6000
        else "Focus on enhancing infrastructure to support medium-scale agricultural activities" if x > 4000
        else "Optimize infrastructure for better utilization in moderately agricultural areas" if x > 2000
        else "Prioritize infrastructure development in regions with limited agricultural land"
    ))
    gdf['Environmental Conservation Recommendation'] = gdf['Environmental Conservation'].apply(
        lambda x: (
        "Implement extensive reforestation and conservation programs to preserve ecosystems" if x > 5000
        else "Focus on large-scale afforestation and forest preservation projects" if x > 4500
        else "Strengthen community-driven conservation efforts and reforestation plans" if x > 4000
        else "Enhance forest management practices and sustainable land use strategies" if x > 3500
        else "Increase funding for conservation programs and biodiversity initiatives" if x > 3000
        else "Promote sustainable forestry and eco-friendly policies in high-impact areas" if x > 2500
        else "Support moderate-scale afforestation projects and community participation" if x > 2000
        else "Focus on targeted afforestation efforts in underutilized regions" if x > 1500
        else "Encourage community involvement and local conservation initiatives" if x > 1000
        else "Promote small-scale afforestation and awareness programs" if x > 500
        else "Initiate basic conservation and afforestation efforts in critical regions"
    )
    )
    gdf['Socio-Economics Analysis Recommendation'] = gdf['Socio-Economics Analysis'].apply(
        lambda x: (
        "Focus on rural development and connectivity in sparsely populated areas" if x <= 60
        else "Support sparsely populated regions with roadways and basic facilities" if x <= 120
        else "Enhance rural infrastructure and agricultural support" if x <= 180
        else "Improve access to education and healthcare in moderately populated areas" if x <= 240
        else "Invest in medium-density regions with industrial hubs" if x <= 300
        else "Promote urbanization in emerging towns and cities" if x <= 360
        else "Develop infrastructure and job opportunities in densely populated regions" if x <= 420
        else "Implement smart city projects for high-density urban areas" if x <= 480
        else "Enhance public transportation and housing in urban centers" if x <= 540
        else "Expand utilities and green spaces in highly urbanized areas" if x <= 600
        else "Focus on reducing congestion and pollution in urban hotspots" if x <= 660
        else "Prioritize high-density urban centers with smart city initiatives" if x <= 720
        else "Develop advanced infrastructure for mega-cities and metropolitan regions" if x <= 780
        else "Address overpopulation challenges with sustainable city planning"
    ))
    
    return gdf

def create_map(gdf, title, recommendation_column):
    m = folium.Map(location=[23.2599, 77.4126], zoom_start=5)
    
    folium.GeoJson(
        gdf,
        name=title,
        tooltip=GeoJsonTooltip(
            fields=['statename', recommendation_column], 
            aliases=['State:', 'Recommendation:'], 
            localize=True
        ),
        style_function=lambda x: {'fillColor': 'blue', 'fillOpacity': 0.6, 'weight': 0.5}
    ).add_to(m)
    
    file_path = f"{title.replace(' ', '_')}_Interactive_Map.html"
    m.save(file_path)
    return m, file_path

def main():
    st.title("Geospatial Analysis and Recommendations")
    
    shapefiles, population_file, land_file = upload_files()

    if shapefiles and population_file and land_file:
        st.success("Files uploaded successfully! Processing data...")
        
        shapefile_paths, temp_dir = save_uploaded_files(shapefiles)
        gdf = process_files(shapefile_paths, population_file, land_file)

        maps_info = {
            "Urban Planning": 'Urban Planning Recommendation',
            "Infrastructure Development": 'Infrastructure Development Recommendation',
            "Environmental Conservation": 'Environmental Conservation Recommendation',
            "Socio-Economics Analysis": 'Socio-Economics Analysis Recommendation'
        }

        for theme, column in maps_info.items():
            st.subheader(theme)
            m, file_path = create_map(gdf, theme, column)
            folium_static(m)

            with open(file_path, "rb") as file:
                st.download_button(
                    label=f"Download {theme} Map",
                    data=file,
                    file_name=file_path,
                    mime='text/html'
                )

if __name__ == "__main__":
    main()