### Part 1

import streamlit as st
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from io import BytesIO
import base64

# Custom CSS with blue and white theme and zoom functionality
st.markdown("""
<style>
    /* Allow zoom functionality */
    .stApp {
        zoom: 1 !important;
        transform: scale(1) !important;
        transform-origin: 0 0 !important;
    }
    
    /* Increase sidebar width */
    section[data-testid="stSidebar"] {
        width: 320px !important;
        background-color: #f8f9fd !important;
    }
    
    /* Main app styling with blue theme */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin-left: 0 !important;
        max-width: none !important;
        background-color: white !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Title styling */
    h1 {
        color: #2c3e50 !important;
        text-align: center !important;
        font-weight: 700 !important;
        margin-bottom: 2rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Subheader styling */
    h2, h3 {
        color: #34495e !important;
        border-bottom: 2px solid #3498db !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-left: 1rem !important;
        margin-left: 0 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #3498db, #2980b9) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 0.5rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #2980b9, #1f5f8b) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4) !important;
    }
    
    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(45deg, #27ae60, #229954) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 0.5rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(45deg, #229954, #1e7e34) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(39, 174, 96, 0.4) !important;
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #74b9ff, #0984e3) !important;
        border: 1px solid #ddd !important;
        padding: 1rem !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    [data-testid="metric-container"] > div {
        color: white !important;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Info box styling */
    .stInfo {
        background: linear-gradient(135deg, #74b9ff, #0984e3) !important;
        color: white !important;
        border-radius: 10px !important;
    }
    
    /* Warning box styling */
    .stWarning {
        background: linear-gradient(135deg, #fdcb6e, #e17055) !important;
        color: white !important;
        border-radius: 10px !important;
    }
    
    /* Success box styling */
    .stSuccess {
        background: linear-gradient(135deg, #00b894, #00a085) !important;
        color: white !important;
        border-radius: 10px !important;
    }
    
    /* Report export button styling */
    .report-button {
        background: linear-gradient(45deg, #e74c3c, #c0392b) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3) !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        width: 100% !important;
        margin: 1rem 0 !important;
    }
    
    .report-button:hover {
        background: linear-gradient(45deg, #c0392b, #a93226) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# Function to save maps as PNG and return BytesIO object
def save_map_as_png(fig, filename_prefix):
    """Save matplotlib figure as PNG and return BytesIO object"""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    buffer.seek(0)
    
    # Also save to disk for reference
    fig.savefig(f"{filename_prefix}.png", format='png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    
    return buffer

# Function to generate comprehensive summaries
def generate_summaries(df):
    """Generate District, Chiefdom, and Gender summaries"""
    summaries = {}
    
    # Overall Summary
    overall_summary = {
        'total_schools': len(df),
        'total_districts': len(df['District'].dropna().unique()),
        'total_chiefdoms': len(df['Chiefdom'].dropna().unique()),
        'total_boys': 0,
        'total_girls': 0,
        'total_enrollment': 0,
        'total_itn': 0
    }
    
    # Calculate totals using the correct columns
    for class_num in range(1, 6):
        # Total enrollment from "Number of enrollments in class X"
        enrollment_col = f"How many pupils are enrolled in Class {class_num}?"
        if enrollment_col in df.columns:
            overall_summary['total_enrollment'] += int(df[enrollment_col].fillna(0).sum())
        
        # Boys and girls for gender analysis AND ITN calculation
        boys_col = f"How many boys in Class {class_num} received ITNs?"
        girls_col = f"How many girls in Class {class_num} received ITNs?"
        if boys_col in df.columns:
            overall_summary['total_boys'] += int(df[boys_col].fillna(0).sum())
        if girls_col in df.columns:
            overall_summary['total_girls'] += int(df[girls_col].fillna(0).sum())
    
    # Total ITNs = boys + girls (actual beneficiaries)
    overall_summary['total_itn'] = overall_summary['total_boys'] + overall_summary['total_girls']
    
    # Calculate coverage
    overall_summary['coverage'] = (overall_summary['total_itn'] / overall_summary['total_enrollment'] * 100) if overall_summary['total_enrollment'] > 0 else 0
    overall_summary['itn_remaining'] = overall_summary['total_enrollment'] - overall_summary['total_itn']
    
    summaries['overall'] = overall_summary
    
    # District Summary
    district_summary = []
    for district in df['District'].dropna().unique():
        district_data = df[df['District'] == district]
        district_stats = {
            'district': district,
            'schools': len(district_data),
            'chiefdoms': len(district_data['Chiefdom'].dropna().unique()),
            'boys': 0,
            'girls': 0,
            'enrollment': 0,
            'itn': 0
        }
        
        for class_num in range(1, 6):
            # Total enrollment from "Number of enrollments in class X"
            enrollment_col = f"How many pupils are enrolled in Class {class_num}?"
            if enrollment_col in district_data.columns:
                district_stats['enrollment'] += int(district_data[enrollment_col].fillna(0).sum())
            
            # Boys and girls for gender analysis AND ITN calculation
            boys_col = f"How many boys in Class {class_num} received ITNs?"
            girls_col = f"How many girls in Class {class_num} received ITNs?"
            if boys_col in district_data.columns:
                district_stats['boys'] += int(district_data[boys_col].fillna(0).sum())
            if girls_col in district_data.columns:
                district_stats['girls'] += int(district_data[girls_col].fillna(0).sum())
        
        # Total ITNs = boys + girls (actual beneficiaries)
        district_stats['itn'] = district_stats['boys'] + district_stats['girls']
        
        # Calculate coverage
        district_stats['coverage'] = (district_stats['itn'] / district_stats['enrollment'] * 100) if district_stats['enrollment'] > 0 else 0
        district_stats['itn_remaining'] = district_stats['enrollment'] - district_stats['itn']
        
        district_summary.append(district_stats)
    
    summaries['district'] = district_summary
    
    # Chiefdom Summary
    chiefdom_summary = []
    for district in df['District'].dropna().unique():
        district_data = df[df['District'] == district]
        for chiefdom in district_data['Chiefdom'].dropna().unique():
            chiefdom_data = district_data[district_data['Chiefdom'] == chiefdom]
            chiefdom_stats = {
                'district': district,
                'chiefdom': chiefdom,
                'schools': len(chiefdom_data),
                'boys': 0,
                'girls': 0,
                'enrollment': 0,
                'itn': 0
            }
            
            for class_num in range(1, 6):
                # Total enrollment from "Number of enrollments in class X"
                enrollment_col = f"How many pupils are enrolled in Class {class_num}?"
                if enrollment_col in chiefdom_data.columns:
                    chiefdom_stats['enrollment'] += int(chiefdom_data[enrollment_col].fillna(0).sum())
                
                # Boys and girls for gender analysis AND ITN calculation
                boys_col = f"How many boys in Class {class_num} received ITNs?"
                girls_col = f"How many girls in Class {class_num} received ITNs?"
                if boys_col in chiefdom_data.columns:
                    chiefdom_stats['boys'] += int(chiefdom_data[boys_col].fillna(0).sum())
                if girls_col in chiefdom_data.columns:
                    chiefdom_stats['girls'] += int(chiefdom_data[girls_col].fillna(0).sum())
            
            # Total ITNs = boys + girls (actual beneficiaries)
            chiefdom_stats['itn'] = chiefdom_stats['boys'] + chiefdom_stats['girls']
            
            # Calculate coverage
            chiefdom_stats['coverage'] = (chiefdom_stats['itn'] / chiefdom_stats['enrollment'] * 100) if chiefdom_stats['enrollment'] > 0 else 0
            chiefdom_stats['itn_remaining'] = chiefdom_stats['enrollment'] - chiefdom_stats['itn']
            
            chiefdom_summary.append(chiefdom_stats)
    
    summaries['chiefdom'] = chiefdom_summary
    
    return summaries
    
### Part 2-----------------------------------------------------------------------------------------------------------------

# Logo Section - Clean 4 Logo Layout
col1, col2, col3, col4 = st.columns(4)

with col1:
    try:
        st.image("NMCP.png", width=230)
        st.markdown('<p style="text-align: center; font-size: 12px; font-weight: 600; color: #2c3e50; margin-top: 5px;">National Malaria Control Program</p>', unsafe_allow_html=True)
    except:
        st.markdown("""
        <div style="width: 230px; height: 160px; border: 2px dashed #3498db; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f8f9fd, #e3f2fd); border-radius: 10px; margin: 0 auto;">
            <div style="text-align: center; color: #666; font-size: 11px;">
                NMCP.png<br>Not Found
            </div>
        </div>
        <p style="text-align: center; font-size: 12px; font-weight: 600; color: #2c3e50; margin-top: 5px;">National Malaria Control Program</p>
        """, unsafe_allow_html=True)

with col2:
    try:
        st.image("icf_sl.png", width=230)
        st.markdown('<p style="text-align: center; font-size: 12px; font-weight: 600; color: #2c3e50; margin-top: 5px;">ICF Sierra Leone</p>', unsafe_allow_html=True)
    except:
        st.markdown("""
        <div style="width: 230px; height: 160px; border: 2px dashed #3498db; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f8f9fd, #e3f2fd); border-radius: 10px; margin: 0 auto;">
            <div style="text-align: center; color: #666; font-size: 11px;">
                icf_sl.png<br>Not Found
            </div>
        </div>
        <p style="text-align: center; font-size: 12px; font-weight: 600; color: #2c3e50; margin-top: 5px;">ICF Sierra Leone</p>
        """, unsafe_allow_html=True)

with col3:
    try:
        st.image("pmi.png", width=230)
        st.markdown('<p style="text-align: center; font-size: 12px; font-weight: 600; color: #2c3e50; margin-top: 5px;">PMI Evolve</p>', unsafe_allow_html=True)
    except:
        st.markdown("""
        <div style="width: 230px; height: 160px; border: 2px dashed #3498db; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f8f9fd, #e3f2fd); border-radius: 10px; margin: 0 auto;">
            <div style="text-align: center; color: #666; font-size: 11px;">
                pmi.png<br>Not Found
            </div>
        </div>
        <p style="text-align: center; font-size: 12px; font-weight: 600; color: #2c3e50; margin-top: 5px;">PMI Evolve</p>
        """, unsafe_allow_html=True)

with col4:
    try:
        st.image("abt.png", width=230)
        st.markdown('<p style="text-align: center; font-size: 12px; font-weight: 600; color: #2c3e50; margin-top: 5px;">Abt Associates</p>', unsafe_allow_html=True)
    except:
        st.markdown("""
        <div style="width: 230px; height: 160px; border: 2px dashed #3498db; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f8f9fd, #e3f2fd); border-radius: 10px; margin: 0 auto;">
            <div style="text-align: center; color: #666; font-size: 11px;">
                abt.png<br>Not Found
            </div>
        </div>
        <p style="text-align: center; font-size: 12px; font-weight: 600; color: #2c3e50; margin-top: 5px;">Abt Associates</p>
        """, unsafe_allow_html=True)

st.markdown("---")  # Add a horizontal line separator

# Streamlit App
st.title("📊 School Based Distribution of ITNs in SL")

# Upload file
uploaded_file = "latest_sbd1_06_10_2025 (1).xlsx"
if uploaded_file:
    # Read the uploaded Excel file
    df_original = pd.read_excel(uploaded_file)
    
    # Load shapefile
    try:
        gdf = gpd.read_file("Chiefdom2021.shp")
        st.success("✅ Shapefile loaded successfully!")
    except Exception as e:
        st.error(f"❌ Could not load shapefile: {e}")
        gdf = None
    
    # Create empty lists to store extracted data
    districts, chiefdoms, phu_names, community_names, school_names = [], [], [], [], []
    
    # Process each row in the "Scan QR code" column
    for qr_text in df_original["Scan QR code"]:
        if pd.isna(qr_text):
            districts.append(None)
            chiefdoms.append(None)
            phu_names.append(None)
            community_names.append(None)
            school_names.append(None)
            continue
            
        # Extract values using regex patterns
        district_match = re.search(r"District:\s*([^\n]+)", str(qr_text))
        districts.append(district_match.group(1).strip() if district_match else None)
        
        chiefdom_match = re.search(r"Chiefdom:\s*([^\n]+)", str(qr_text))
        chiefdoms.append(chiefdom_match.group(1).strip() if chiefdom_match else None)
        
        phu_match = re.search(r"PHU name:\s*([^\n]+)", str(qr_text))
        phu_names.append(phu_match.group(1).strip() if phu_match else None)
        
        community_match = re.search(r"Community name:\s*([^\n]+)", str(qr_text))
        community_names.append(community_match.group(1).strip() if community_match else None)
        
        school_match = re.search(r"Name of school:\s*([^\n]+)", str(qr_text))
        school_names.append(school_match.group(1).strip() if school_match else None)
    
    # Create a new DataFrame with extracted values
    extracted_df = pd.DataFrame({
        "District": districts,
        "Chiefdom": chiefdoms,
        "PHU Name": phu_names,
        "Community Name": community_names,
        "School Name": school_names
    })
    
    # Add all other columns from the original DataFrame
    for column in df_original.columns:
        if column != "Scan QR code":  # Skip the QR code column since we've already processed it
            extracted_df[column] = df_original[column]
    
    # Create sidebar filters early so they're available for all sections
    st.sidebar.header("Filter Options")
    
    # Create radio buttons to select which level to group by
    grouping_selection = st.sidebar.radio(
        "Select the level for grouping:",
        ["District", "Chiefdom", "PHU Name", "Community Name", "School Name"],
        index=0  # Default to 'District'
    )
    
    # Dictionary to define the hierarchy for each grouping level
    hierarchy = {
        "District": ["District"],
        "Chiefdom": ["District", "Chiefdom"],
        "PHU Name": ["District", "Chiefdom", "PHU Name"],
        "Community Name": ["District", "Chiefdom", "PHU Name", "Community Name"],
        "School Name": ["District", "Chiefdom", "PHU Name", "Community Name", "School Name"]
    }
    
    # Initialize filtered dataframe with the full dataset
    filtered_df = extracted_df.copy()
    
    # Dictionary to store selected values for each level
    selected_values = {}
    
    # Apply filters based on the hierarchy for the selected grouping level
    for level in hierarchy[grouping_selection]:
        # Filter out None/NaN values and get sorted unique values
        level_values = sorted(filtered_df[level].dropna().unique())
        
        if level_values:
            # Create selectbox for this level
            selected_value = st.sidebar.selectbox(f"Select {level}", level_values)
            selected_values[level] = selected_value
            
            # Apply filter to the dataframe
            filtered_df = filtered_df[filtered_df[level] == selected_value]
    
    # Store map images for report
    map_images = {}
    
    # Display Dual Maps at the top
    st.subheader("🗺️ Geographic Distribution Maps")
    
    if gdf is not None:
        # OVERALL SIERRA LEONE MAP FIRST
        st.write("**Sierra Leone - All Districts Overview**")
        
        # Create overall Sierra Leone map
        fig_overall, ax_overall = plt.subplots(figsize=(16, 10))
        
        # Plot all chiefdoms with gray edges (base layer)
        gdf.plot(ax=ax_overall, color='white', edgecolor='gray', alpha=0.8, linewidth=0.5)
        
        # Plot district boundaries with thick black lines
        # Get district boundaries by dissolving chiefdoms by FIRST_DNAM
        if 'FIRST_DNAM' in gdf.columns:
            district_boundaries = gdf.dissolve(by='FIRST_DNAM')
            district_boundaries.plot(ax=ax_overall, facecolor='none', edgecolor='black', linewidth=3, alpha=1.0)
            
            # Add district labels at centroids
            for idx, row in district_boundaries.iterrows():
                centroid = row.geometry.centroid
                ax_overall.annotate(
                    idx,  # District name
                    (centroid.x, centroid.y),
                    fontsize=12,
                    fontweight='bold',
                    ha='center',
                    va='center',
                    color='black',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='black')
                )
        
        # Extract and plot ALL GPS coordinates from entire dataset
        all_coords_extracted = []
        if "GPS Location" in extracted_df.columns:
            all_gps_data = extracted_df["GPS Location"].dropna()
            
            st.write(f"**Debug: Processing {len(all_gps_data)} GPS entries for overall map**")
            
            for idx, gps_val in enumerate(all_gps_data):
                if pd.notna(gps_val):
                    gps_str = str(gps_val).strip()
                    
                    # Handle the specific format: 8.6103181,-12.2029534
                    if ',' in gps_str:
                        try:
                            parts = gps_str.split(',')
                            if len(parts) == 2:
                                lat = float(parts[0].strip())
                                lon = float(parts[1].strip())
                                
                                # Check if coordinates are in valid range for Sierra Leone
                                if 6.0 <= lat <= 11.0 and -14.0 <= lon <= -10.0:
                                    all_coords_extracted.append([lat, lon])
                        except ValueError:
                            continue
            
            st.write(f"**Total valid coordinates for overall map: {len(all_coords_extracted)}**")
        
        # Plot GPS points on the overall map
        if all_coords_extracted:
            lats, lons = zip(*all_coords_extracted)
            
            # Plot GPS points with #47B5FF color
            scatter = ax_overall.scatter(
                lons, lats,
                c='#47B5FF',
                s=100,
                alpha=0.9,
                edgecolors='white',
                linewidth=2,
                zorder=100,
                label=f'Schools ({len(all_coords_extracted)})',
                marker='o'
            )
            
            # Add legend
            ax_overall.legend(fontsize=14, loc='best')
            
            # Show coordinate range for verification
            st.write(f"**Overall coordinate range:** Lat: {min(lats):.4f} to {max(lats):.4f}, Lon: {min(lons):.4f} to {max(lons):.4f}")
        
        # Customize overall map
        ax_overall.set_title('Sierra Leone - School Distribution by District', fontsize=18, fontweight='bold', pad=20)
        ax_overall.set_xlabel('Longitude', fontsize=14)
        ax_overall.set_ylabel('Latitude', fontsize=14)
        
        # Add grid for reference
        ax_overall.grid(True, alpha=0.3, linestyle='--')
        
        # Set axis limits to show full country
        ax_overall.set_xlim(gdf.total_bounds[0] - 0.1, gdf.total_bounds[2] + 0.1)
        ax_overall.set_ylim(gdf.total_bounds[1] - 0.1, gdf.total_bounds[3] + 0.1)
        
        plt.tight_layout()
        st.pyplot(fig_overall)
        
        # Save overall map
        map_images['sierra_leone_overall'] = save_map_as_png(fig_overall, "Sierra_Leone_Overall_Map")
        
        st.divider()
        
        # NOW THE INDIVIDUAL DISTRICT MAPS
        # Define specific districts for left and right maps
        left_district = "BO"
        right_district = "BOMBALI"
        
        # BO DISTRICT MAP - Full width
        st.write(f"**{left_district} District - All Chiefdoms**")
        
        # Filter shapefile for BO district
        bo_gdf = gdf[gdf['FIRST_DNAM'] == left_district].copy()
        
        if len(bo_gdf) > 0:
            # Filter data for BO district to get GPS coordinates
            bo_data = extracted_df[extracted_df["District"] == left_district].copy()
            
            # Create the BO district plot
            fig_bo, ax_bo = plt.subplots(figsize=(14, 8))
            
            # Plot chiefdom boundaries in white with black edges
            bo_gdf.plot(ax=ax_bo, color='white', edgecolor='black', alpha=0.8, linewidth=2)
            
            # Extract and plot GPS coordinates FIRST
            coords_extracted = []
            if len(bo_data) > 0 and "GPS Location" in bo_data.columns:
                gps_data = bo_data["GPS Location"].dropna()
                
                st.write(f"**Debug: Found {len(gps_data)} GPS entries for BO District**")
                
                for idx, gps_val in enumerate(gps_data):
                    if pd.notna(gps_val):
                        gps_str = str(gps_val).strip()
                        st.write(f"GPS {idx+1}: {gps_str}")
                        
                        # Handle the specific format: 8.6103181,-12.2029534
                        if ',' in gps_str:
                            try:
                                parts = gps_str.split(',')
                                if len(parts) == 2:
                                    lat = float(parts[0].strip())
                                    lon = float(parts[1].strip())
                                    
                                    # Check if coordinates are in valid range for Sierra Leone
                                    if 6.0 <= lat <= 11.0 and -14.0 <= lon <= -10.0:
                                        coords_extracted.append([lat, lon])
                                        st.write(f"✅ Valid coordinates: {lat}, {lon}")
                                    else:
                                        st.write(f"❌ Invalid coordinates (outside Sierra Leone): {lat}, {lon}")
                            except ValueError as e:
                                st.write(f"❌ Could not parse coordinates: {gps_str} - Error: {e}")
                
                st.write(f"**Total valid coordinates extracted: {len(coords_extracted)}**")
            
            # Plot GPS points on the shapefile
            if coords_extracted:
                lats, lons = zip(*coords_extracted)
                
                # Plot GPS points with high visibility
                scatter = ax_bo.scatter(
                    lons, lats,
                    c='red',
                    s=150,
                    alpha=1.0,
                    edgecolors='white',
                    linewidth=3,
                    zorder=100,  # Very high z-order to ensure visibility
                    label=f'Schools ({len(coords_extracted)})',
                    marker='o'
                )
                
                # Add text labels for each point
                for i, (lat, lon) in enumerate(coords_extracted):
                    ax_bo.annotate(f'S{i+1}', 
                                  (lon, lat),
                                  xytext=(5, 5), 
                                  textcoords='offset points',
                                  fontsize=10,
                                  fontweight='bold',
                                  color='red',
                                  bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
                
                # Show coordinate range for verification
                st.write(f"**Coordinate range:** Lat: {min(lats):.4f} to {max(lats):.4f}, Lon: {min(lons):.4f} to {max(lons):.4f}")
                
                # Set map extent to include all points with padding
                margin = 0.05
                ax_bo.set_xlim(min(lons) - margin, max(lons) + margin)
                ax_bo.set_ylim(min(lats) - margin, max(lats) + margin)
                
            # Add chiefdom labels
            for idx, row in bo_gdf.iterrows():
                if 'FIRST_CHIE' in row and pd.notna(row['FIRST_CHIE']):
                    centroid = row.geometry.centroid
                    ax_bo.annotate(
                        row['FIRST_CHIE'], 
                        (centroid.x, centroid.y),
                        xytext=(5, 5), 
                        textcoords='offset points',
                        fontsize=9,
                        ha='left',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7)
                    )
            
            # Customize plot
            title_text = f'{left_district} District - Chiefdoms: {len(bo_gdf)}'
            if coords_extracted:
                title_text += f' | GPS Points: {len(coords_extracted)}'
            ax_bo.set_title(title_text, fontsize=16, fontweight='bold')
            ax_bo.set_xlabel('Longitude', fontsize=12)
            ax_bo.set_ylabel('Latitude', fontsize=12)
            
            # Add legend if GPS points exist
            if coords_extracted:
                ax_bo.legend(fontsize=12, loc='best')
            
            # Add grid for reference
            ax_bo.grid(True, alpha=0.3, linestyle='--')
            
            plt.tight_layout()
            st.pyplot(fig_bo)
            
            # Save BO district map
            map_images['bo_district'] = save_map_as_png(fig_bo, f"{left_district}_District_Map")
            
            # Display chiefdoms list
            if 'FIRST_CHIE' in bo_gdf.columns:
                chiefdoms = bo_gdf['FIRST_CHIE'].dropna().tolist()
                st.write(f"**Chiefdoms in {left_district} District ({len(chiefdoms)}):**")
                chiefdom_cols = st.columns(3)
                for i, chiefdom in enumerate(chiefdoms):
                    with chiefdom_cols[i % 3]:
                        st.write(f"• {chiefdom}")
        else:
            st.warning(f"No chiefdoms found for {left_district} district in shapefile")
        
        st.divider()
        
        # BOMBALI DISTRICT MAP - Full width
        st.write(f"**{right_district} District - All Chiefdoms**")
        
        # Filter shapefile for BOMBALI district
        bombali_gdf = gdf[gdf['FIRST_DNAM'] == right_district].copy()
        
        if len(bombali_gdf) > 0:
            # Filter data for BOMBALI district to get GPS coordinates
            bombali_data = extracted_df[extracted_df["District"] == right_district].copy()
            
            # Create the BOMBALI district plot
            fig_bombali, ax_bombali = plt.subplots(figsize=(14, 8))
            
            # Plot chiefdom boundaries in white with black edges
            bombali_gdf.plot(ax=ax_bombali, color='white', edgecolor='black', alpha=0.8, linewidth=2)
            
            # Extract and plot GPS coordinates FIRST
            coords_extracted = []
            if len(bombali_data) > 0 and "GPS Location" in bombali_data.columns:
                gps_data = bombali_data["GPS Location"].dropna()
                
                st.write(f"**Debug: Found {len(gps_data)} GPS entries for BOMBALI District**")
                
                for idx, gps_val in enumerate(gps_data):
                    if pd.notna(gps_val):
                        gps_str = str(gps_val).strip()
                        st.write(f"GPS {idx+1}: {gps_str}")
                        
                        # Handle the specific format: 8.6103181,-12.2029534
                        if ',' in gps_str:
                            try:
                                parts = gps_str.split(',')
                                if len(parts) == 2:
                                    lat = float(parts[0].strip())
                                    lon = float(parts[1].strip())
                                    
                                    # Check if coordinates are in valid range for Sierra Leone
                                    if 6.0 <= lat <= 11.0 and -14.0 <= lon <= -10.0:
                                        coords_extracted.append([lat, lon])
                                        st.write(f"✅ Valid coordinates: {lat}, {lon}")
                                    else:
                                        st.write(f"❌ Invalid coordinates (outside Sierra Leone): {lat}, {lon}")
                            except ValueError as e:
                                st.write(f"❌ Could not parse coordinates: {gps_str} - Error: {e}")
                
                st.write(f"**Total valid coordinates extracted: {len(coords_extracted)}**")
            
            # Plot GPS points on the shapefile
            if coords_extracted:
                lats, lons = zip(*coords_extracted)
                
                # Plot GPS points with high visibility
                scatter = ax_bombali.scatter(
                    lons, lats,
                    c='red',
                    s=150,
                    alpha=1.0,
                    edgecolors='white',
                    linewidth=3,
                    zorder=100,  # Very high z-order to ensure visibility
                    label=f'Schools ({len(coords_extracted)})',
                    marker='o'
                )
                
                # Add text labels for each point
                for i, (lat, lon) in enumerate(coords_extracted):
                    ax_bombali.annotate(f'S{i+1}', 
                                       (lon, lat),
                                       xytext=(5, 5), 
                                       textcoords='offset points',
                                       fontsize=10,
                                       fontweight='bold',
                                       color='red',
                                       bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
                
                # Show coordinate range for verification
                st.write(f"**Coordinate range:** Lat: {min(lats):.4f} to {max(lats):.4f}, Lon: {min(lons):.4f} to {max(lons):.4f}")
                
                # Set map extent to include all points with padding
                margin = 0.05
                ax_bombali.set_xlim(min(lons) - margin, max(lons) + margin)
                ax_bombali.set_ylim(min(lats) - margin, max(lats) + margin)
                
            # Add chiefdom labels
            for idx, row in bombali_gdf.iterrows():
                if 'FIRST_CHIE' in row and pd.notna(row['FIRST_CHIE']):
                    centroid = row.geometry.centroid
                    ax_bombali.annotate(
                        row['FIRST_CHIE'], 
                        (centroid.x, centroid.y),
                        xytext=(5, 5), 
                        textcoords='offset points',
                        fontsize=9,
                        ha='left',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7)
                    )
            
            # Customize plot
            title_text = f'{right_district} District - Chiefdoms: {len(bombali_gdf)}'
            if coords_extracted:
                title_text += f' | GPS Points: {len(coords_extracted)}'
            ax_bombali.set_title(title_text, fontsize=16, fontweight='bold')
            ax_bombali.set_xlabel('Longitude', fontsize=12)
            ax_bombali.set_ylabel('Latitude', fontsize=12)
            
            # Add legend if GPS points exist
            if coords_extracted:
                ax_bombali.legend(fontsize=12, loc='best')
            
            # Add grid for reference
            ax_bombali.grid(True, alpha=0.3, linestyle='--')
            
            plt.tight_layout()
            st.pyplot(fig_bombali)
            
            # Save BOMBALI district map
            map_images['bombali_district'] = save_map_as_png(fig_bombali, f"{right_district}_District_Map")
            
            # Display chiefdoms list
            if 'FIRST_CHIE' in bombali_gdf.columns:
                chiefdoms = bombali_gdf['FIRST_CHIE'].dropna().tolist()
                st.write(f"**Chiefdoms in {right_district} District ({len(chiefdoms)}):**")
                chiefdom_cols = st.columns(3)
                for i, chiefdom in enumerate(chiefdoms):
                    with chiefdom_cols[i % 3]:
                        st.write(f"• {chiefdom}")
        else:
            st.warning(f"No chiefdoms found for {right_district} district in shapefile")
    else:
        st.error("Shapefile not loaded. Cannot display map.")
    
    # Display Original Data Sample
    st.subheader("📄 Original Data Sample")
    st.dataframe(df_original.head())
    
    # Display Extracted Data
    st.subheader("📋 Extracted Data")
    st.dataframe(extracted_df)
    
    # Add download button for CSV
    csv = extracted_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Extracted Data as CSV",
        data=csv,
        file_name="extracted_school_data.csv",
        mime="text/csv"
    )
    
    # Generate comprehensive summaries
    summaries = generate_summaries(extracted_df)
    
    # Display Overall Summary
    st.subheader("📊 Overall Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Schools", f"{summaries['overall']['total_schools']:,}")
    with col2:
        st.metric("Total Students", f"{summaries['overall']['total_enrollment']:,}")
    with col3:
        st.metric("Total ITNs", f"{summaries['overall']['total_itn']:,}")
    with col4:
        st.metric("Coverage", f"{summaries['overall']['coverage']:.1f}%")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Districts", f"{summaries['overall']['total_districts']}")
    with col6:
        st.metric("Chiefdoms", f"{summaries['overall']['total_chiefdoms']}")
    with col7:
        st.metric("Boys", f"{summaries['overall']['total_boys']:,}")
    with col8:
        st.metric("Girls", f"{summaries['overall']['total_girls']:,}")
    
    # Gender Analysis
    st.subheader("👫 Gender Analysis")
    
    # Overall gender distribution pie chart
    fig_gender, ax_gender = plt.subplots(figsize=(10, 8))
    labels = ['Boys', 'Girls']
    sizes = [summaries['overall']['total_boys'], summaries['overall']['total_girls']]
    colors = ['#4A90E2', '#F39C12']
    
    wedges, texts, autotexts = ax_gender.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                            colors=colors, startangle=90)
    ax_gender.set_title('Overall Gender Distribution', fontsize=16, fontweight='bold', pad=20)
    plt.setp(autotexts, size=14, weight="bold")
    plt.setp(texts, size=12, weight="bold")
    plt.tight_layout()
    st.pyplot(fig_gender)
    
    # Save gender chart
    map_images['gender_overall'] = save_map_as_png(fig_gender, "Overall_Gender_Distribution")
    
    # Gender ratio by district chart
    districts = [d['district'] for d in summaries['district']]
    boys_counts = [d['boys'] for d in summaries['district']]
    girls_counts = [d['girls'] for d in summaries['district']]
    
    fig_gender_district, ax_gender_district = plt.subplots(figsize=(14, 8))
    x = np.arange(len(districts))
    width = 0.35
    
    bars1 = ax_gender_district.bar(x - width/2, boys_counts, width, label='Boys', color='#4A90E2', edgecolor='navy', linewidth=1)
    bars2 = ax_gender_district.bar(x + width/2, girls_counts, width, label='Girls', color='#F39C12', edgecolor='darkorange', linewidth=1)
    
    ax_gender_district.set_title('Gender Distribution by District', fontsize=16, fontweight='bold', pad=20)
    ax_gender_district.set_xlabel('Districts', fontsize=12, fontweight='bold')
    ax_gender_district.set_ylabel('Number of Students', fontsize=12, fontweight='bold')
    ax_gender_district.set_xticks(x)
    ax_gender_district.set_xticklabels(districts, rotation=45, ha='right')
    ax_gender_district.legend(fontsize=12)
    ax_gender_district.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax_gender_district.annotate(f'{int(height):,}',
                                  xy=(bar.get_x() + bar.get_width() / 2, height),
                                  xytext=(0, 3),
                                  textcoords="offset points",
                                  ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    for bar in bars2:
        height = bar.get_height()
        ax_gender_district.annotate(f'{int(height):,}',
                                  xy=(bar.get_x() + bar.get_width() / 2, height),
                                  xytext=(0, 3),
                                  textcoords="offset points",
                                  ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(fig_gender_district)
    
    # Save gender district chart
    map_images['gender_district'] = save_map_as_png(fig_gender_district, "Gender_Distribution_by_District")
    
    # Enrollment and ITN Distribution Analysis
    st.subheader("📊 Enrollment and ITN Distribution Analysis")
    
    # Calculate total enrollment and ITN distribution by district
    district_analysis = []
    
    for district in extracted_df['District'].dropna().unique():
        district_data = extracted_df[extracted_df['District'] == district]
        
        total_enrollment = 0
        total_boys = 0
        total_girls = 0
        
        # Sum enrollments and boys/girls by class using correct columns
        for class_num in range(1, 6):
            # Use "Number of enrollments in class X" for total students
            enrollment_col = f"Number of enrollments in class {class_num}"
            if enrollment_col in district_data.columns:
                total_enrollment += int(district_data[enrollment_col].fillna(0).sum())
            
            # Use boys + girls for total ITNs (actual beneficiaries)
            boys_col = f"Number of boys in class {class_num}"
            girls_col = f"Number of girls in class {class_num}"
            if boys_col in district_data.columns:
                total_boys += int(district_data[boys_col].fillna(0).sum())
            if girls_col in district_data.columns:
                total_girls += int(district_data[girls_col].fillna(0).sum())
        
        total_itn = total_boys + total_girls  # Total ITNs = boys + girls
        itn_remaining = total_enrollment - total_itn  # Remaining = enrollment - distributed
        coverage = (total_itn / total_enrollment * 100) if total_enrollment > 0 else 0
        
        district_analysis.append({
            'District': district,
            'Total_Enrollment': total_enrollment,
            'Total_ITN': total_itn,
            'ITN_Remaining': itn_remaining,
            'Coverage': coverage
        })
    
    district_df = pd.DataFrame(district_analysis)
    
    # Create enhanced bar chart with enrollment, distributed, and remaining
    fig_enhanced, ax_enhanced = plt.subplots(figsize=(16, 8))
    
    x = np.arange(len(district_df['District']))
    width = 0.25
    
    # Create bars for each category
    bars1 = ax_enhanced.bar(x - width, district_df['Total_Enrollment'], width, 
                           label='Total Enrollment', color='#47B5FF', edgecolor='navy', linewidth=1)
    bars2 = ax_enhanced.bar(x, district_df['Total_ITN'], width, 
                           label='ITNs Distributed (Boys + Girls)', color='lightcoral', edgecolor='darkred', linewidth=1)
    bars3 = ax_enhanced.bar(x + width, district_df['ITN_Remaining'], width, 
                           label='ITNs Remaining', color='hotpink', edgecolor='darkmagenta', linewidth=1)
    
    # Customize the chart
    ax_enhanced.set_title('District Analysis: Enrollment vs ITN Distribution', fontsize=16, fontweight='bold', pad=20)
    ax_enhanced.set_xlabel('Districts', fontsize=12, fontweight='bold')
    ax_enhanced.set_ylabel('Number of Students/ITNs', fontsize=12, fontweight='bold')
    ax_enhanced.set_xticks(x)
    ax_enhanced.set_xticklabels(district_df['District'], rotation=45, ha='right')
    ax_enhanced.legend(fontsize=12)
    ax_enhanced.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax_enhanced.annotate(f'{int(height):,}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    for bar in bars2:
        height = bar.get_height()
        ax_enhanced.annotate(f'{int(height):,}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    for bar in bars3:
        height = bar.get_height()
        if height > 0:  # Only show label for positive values
            ax_enhanced.annotate(f'{int(height):,}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(fig_enhanced)
    
    # Save enhanced chart
    map_images['enhanced_enrollment_analysis'] = save_map_as_png(fig_enhanced, "Enhanced_Enrollment_Analysis")
    
    # Create overall pie chart for enrollment vs distributed vs remaining
    st.subheader("📊 Overall Distribution Overview (Pie Chart)")
    
    # Calculate overall totals
    overall_enrollment = district_df['Total_Enrollment'].sum()
    overall_distributed = district_df['Total_ITN'].sum()
    overall_remaining = district_df['ITN_Remaining'].sum()
    
    if overall_enrollment > 0:
        fig_overall_pie, ax_overall_pie = plt.subplots(figsize=(10, 8))
        
        sizes = [overall_distributed, overall_remaining]
        labels = [f'ITNs Distributed\n({overall_distributed:,})', f'ITNs Remaining\n({overall_remaining:,})']
        colors = ['lightcoral', 'hotpink']
        explode = (0.05, 0)  # Slightly separate the distributed slice
        
        wedges, texts, autotexts = ax_overall_pie.pie(sizes, labels=labels, autopct='%1.1f%%',
                                                     colors=colors, startangle=90, explode=explode)
        ax_overall_pie.set_title(f'Overall ITN Distribution Status\nTotal Enrollment: {overall_enrollment:,}', 
                                fontsize=16, fontweight='bold', pad=20)
        
        # Enhance text styling
        plt.setp(autotexts, size=12, weight="bold", color='white')
        plt.setp(texts, size=11, weight="bold")
        
        plt.tight_layout()
        st.pyplot(fig_overall_pie)
        
        # Save overall pie chart
        map_images['overall_distribution_pie'] = save_map_as_png(fig_overall_pie, "Overall_Distribution_Pie")
    
    # District-level pie charts
    st.subheader("📊 District-Level Distribution (Pie Charts)")
    
    # Enrollment pie chart
    if district_df['Total_Enrollment'].sum() > 0:
        fig_pie1, ax_pie1 = plt.subplots(figsize=(10, 8))
        colors_enrollment = ['#87CEEB', '#4682B4', '#1E90FF', '#0000CD', '#000080']
        # Filter out zero values for pie chart
        enrollment_data = district_df[district_df['Total_Enrollment'] > 0]
        if len(enrollment_data) > 0:
            wedges, texts, autotexts = ax_pie1.pie(enrollment_data['Total_Enrollment'], 
                                                  labels=enrollment_data['District'],
                                                  autopct='%1.1f%%',
                                                  colors=colors_enrollment[:len(enrollment_data)],
                                                  startangle=90)
            ax_pie1.set_title('Total Enrollment Distribution by District', fontsize=16, fontweight='bold', pad=20)
            plt.setp(autotexts, size=12, weight="bold")
            plt.setp(texts, size=11, weight="bold")
            plt.tight_layout()
            st.pyplot(fig_pie1)
            
            # Save enrollment pie chart
            map_images['enrollment_pie'] = save_map_as_png(fig_pie1, "Enrollment_Distribution_Pie")
        else:
            st.warning("No enrollment data available for pie chart")
    else:
        st.warning("No enrollment data available for pie chart")
    
    # ITN distribution pie chart
    if district_df['Total_ITN'].sum() > 0:
        fig_pie2, ax_pie2 = plt.subplots(figsize=(10, 8))
        colors_itn = ['#90EE90', '#32CD32', '#228B22', '#006400', '#004000']
        # Filter out zero values for pie chart
        itn_data = district_df[district_df['Total_ITN'] > 0]
        if len(itn_data) > 0:
            wedges, texts, autotexts = ax_pie2.pie(itn_data['Total_ITN'], 
                                                  labels=itn_data['District'],
                                                  autopct='%1.1f%%',
                                                  colors=colors_itn[:len(itn_data)],
                                                  startangle=90)
            ax_pie2.set_title('Total ITN Distribution by District', fontsize=16, fontweight='bold', pad=20)
            plt.setp(autotexts, size=12, weight="bold")
            plt.setp(texts, size=11, weight="bold")
            plt.tight_layout()
            st.pyplot(fig_pie2)
            
            # Save ITN pie chart
            map_images['itn_pie'] = save_map_as_png(fig_pie2, "ITN_Distribution_Pie")
        else:
            st.warning("No ITN distribution data available for pie chart")
    else:
        st.warning("No ITN distribution data available for pie chart")
    
    # Display Summary Tables
    st.subheader("📈 District Summary Table")
    district_summary_df = pd.DataFrame(summaries['district'])
    st.dataframe(district_summary_df)
    
    st.subheader("📈 Chiefdom Summary Table")
    chiefdom_summary_df = pd.DataFrame(summaries['chiefdom'])
    st.dataframe(chiefdom_summary_df)

### part 3----------------------------------------------------------------------------------------------------------------

# Chiefdoms Analysis by District
    st.subheader("📊 Chiefdoms Analysis by District")
    
    # Get all unique districts that have chiefdom data
    districts_with_chiefdoms = extracted_df[extracted_df['Chiefdom'].notna()]['District'].unique()
    
    for district in districts_with_chiefdoms:
        st.write(f"### {district} District - Chiefdoms Analysis")
        
        # Filter data for this district
        district_data = extracted_df[extracted_df['District'] == district]
        district_chiefdoms = district_data['Chiefdom'].dropna().unique()
        
        if len(district_chiefdoms) > 0:
            # Calculate by chiefdom for this district
            district_chiefdom_analysis = []
            
            for chiefdom in district_chiefdoms:
                chiefdom_data = district_data[district_data['Chiefdom'] == chiefdom]
                
                total_enrollment = 0
                total_boys = 0
                total_girls = 0
                
                for class_num in range(1, 6):
                    # Use "Number of enrollments in class X" for total students
                    enrollment_col = f"Number of enrollments in class {class_num}"
                    if enrollment_col in chiefdom_data.columns:
                        total_enrollment += int(chiefdom_data[enrollment_col].fillna(0).sum())
                    
                    # Use boys + girls for total ITNs (actual beneficiaries)
                    boys_col = f"Number of boys in class {class_num}"
                    girls_col = f"Number of girls in class {class_num}"
                    if boys_col in chiefdom_data.columns:
                        total_boys += int(chiefdom_data[boys_col].fillna(0).sum())
                    if girls_col in chiefdom_data.columns:
                        total_girls += int(chiefdom_data[girls_col].fillna(0).sum())
                
                total_itn = total_boys + total_girls  # Total ITNs = boys + girls
                coverage = (total_itn / total_enrollment * 100) if total_enrollment > 0 else 0
                
                district_chiefdom_analysis.append({
                    'Chiefdom': chiefdom,
                    'Total_Enrollment': total_enrollment,
                    'Total_ITN': total_itn,
                    'Coverage': coverage
                })
            
            district_chiefdom_df = pd.DataFrame(district_chiefdom_analysis)
            district_chiefdom_df = district_chiefdom_df.sort_values('Total_Enrollment', ascending=False)
            
            if len(district_chiefdom_df) > 0:
                # Create individual large plots for this district's chiefdoms
                
                # Plot 1: Total Enrollment by Chiefdoms in this District (Blue)
                fig1, ax1 = plt.subplots(figsize=(16, 10))
                bars1 = ax1.barh(district_chiefdom_df['Chiefdom'], district_chiefdom_df['Total_Enrollment'], 
                                 color='#4682B4', edgecolor='navy', linewidth=1.5)
                ax1.set_title(f'{district} District - Total Enrollment by Chiefdom', fontsize=18, fontweight='bold', pad=20)
                ax1.set_xlabel('Number of Students', fontsize=14, fontweight='bold')
                ax1.set_ylabel('Chiefdoms', fontsize=14, fontweight='bold')
                
                # Add value labels
                for i, v in enumerate(district_chiefdom_df['Total_Enrollment']):
                    if v > 0:  # Only show label if value is greater than 0
                        ax1.text(v + max(district_chiefdom_df['Total_Enrollment']) * 0.02, i, 
                                 f'{int(v):,}', va='center', fontweight='bold', fontsize=12)
                
                # Customize appearance
                ax1.grid(axis='x', alpha=0.3, linestyle='--')
                ax1.tick_params(axis='both', which='major', labelsize=11)
                plt.tight_layout()
                st.pyplot(fig1)
                
                # Save enrollment chart
                map_images[f'{district}_enrollment'] = save_map_as_png(fig1, f"{district}_Enrollment_by_Chiefdom")
                
                # Plot 2: Total ITN Distributed by Chiefdoms in this District (Green)
                fig2, ax2 = plt.subplots(figsize=(16, 10))
                bars2 = ax2.barh(district_chiefdom_df['Chiefdom'], district_chiefdom_df['Total_ITN'], 
                                 color='#32CD32', edgecolor='darkgreen', linewidth=1.5)
                ax2.set_title(f'{district} District - Total ITN Distributed by Chiefdom', fontsize=18, fontweight='bold', pad=20)
                ax2.set_xlabel('Number of ITNs', fontsize=14, fontweight='bold')
                ax2.set_ylabel('Chiefdoms', fontsize=14, fontweight='bold')
                
                # Add value labels
                for i, v in enumerate(district_chiefdom_df['Total_ITN']):
                    if v > 0:  # Only show label if value is greater than 0
                        ax2.text(v + max(district_chiefdom_df['Total_ITN']) * 0.02, i, 
                                 f'{int(v):,}', va='center', fontweight='bold', fontsize=12)
                
                # Customize appearance
                ax2.grid(axis='x', alpha=0.3, linestyle='--')
                ax2.tick_params(axis='both', which='major', labelsize=11)
                plt.tight_layout()
                st.pyplot(fig2)
                
                # Save ITN chart
                map_images[f'{district}_itn'] = save_map_as_png(fig2, f"{district}_ITN_by_Chiefdom")
                
                # Plot 3: Coverage by Chiefdoms in this District (Orange)
                fig3, ax3 = plt.subplots(figsize=(16, 10))
                bars3 = ax3.barh(district_chiefdom_df['Chiefdom'], district_chiefdom_df['Coverage'], 
                                 color='#FF8C00', edgecolor='darkorange', linewidth=1.5)
                ax3.set_title(f'{district} District - ITN Coverage by Chiefdom (%)', fontsize=18, fontweight='bold', pad=20)
                ax3.set_xlabel('Coverage Percentage (%)', fontsize=14, fontweight='bold')
                ax3.set_ylabel('Chiefdoms', fontsize=14, fontweight='bold')
                
                # Add value labels
                for i, v in enumerate(district_chiefdom_df['Coverage']):
                    if v > 0:  # Only show label if value is greater than 0
                        ax3.text(v + max(district_chiefdom_df['Coverage']) * 0.02, i, 
                                 f'{v:.1f}%', va='center', fontweight='bold', fontsize=12)
                
                # Customize appearance
                ax3.grid(axis='x', alpha=0.3, linestyle='--')
                ax3.tick_params(axis='both', which='major', labelsize=11)
                ax3.set_xlim(0, max(district_chiefdom_df['Coverage']) * 1.15)  # Add some space for labels
                plt.tight_layout()
                st.pyplot(fig3)
                
                # Save coverage chart
                map_images[f'{district}_coverage'] = save_map_as_png(fig3, f"{district}_Coverage_by_Chiefdom")
                
                # Display summary table for this district
                st.write(f"**{district} District Summary:**")
                summary_cols = st.columns(3)
                with summary_cols[0]:
                    st.metric("Total Chiefdoms", len(district_chiefdom_df))
                with summary_cols[1]:
                    st.metric("Total Students", int(district_chiefdom_df['Total_Enrollment'].sum()))
                with summary_cols[2]:
                    st.metric("Total ITNs", int(district_chiefdom_df['Total_ITN'].sum()))
                
                st.divider()
            else:
                st.warning(f"No chiefdom data available for {district} district")
        else:
            st.warning(f"No chiefdoms found for {district} district")
    
    # Summary buttons section
    st.subheader("📊 Summary Reports")
    
    # Create two columns for the summary buttons
    col1, col2 = st.columns(2)
    
    # Button for District Summary
    with col1:
        district_summary_button = st.button("Show District Summary")
    
    # Button for Chiefdom Summary
    with col2:
        chiefdom_summary_button = st.button("Show Chiefdom Summary")
    
    # Display District Summary when button is clicked
    if district_summary_button:
        st.subheader("📈 Summary by District")
        
        # Create aggregation dictionary
        agg_dict = {}
        
        # Add enrollment columns to aggregation
        for class_num in range(1, 6):
            total_col = f"Number of enrollments in class {class_num}"
            boys_col = f"Number of boys in class {class_num}"
            girls_col = f"Number of girls in class {class_num}"
            
            if total_col in extracted_df.columns:
                agg_dict[total_col] = "sum"
            if boys_col in extracted_df.columns:
                agg_dict[boys_col] = "sum"
            if girls_col in extracted_df.columns:
                agg_dict[girls_col] = "sum"
        
        # Group by District and aggregate
        district_summary = extracted_df.groupby("District").agg(agg_dict).reset_index()
        
        # Calculate total enrollment
        district_summary["Total Enrollment"] = 0
        for class_num in range(1, 6):
            total_col = f"Number of enrollments in class {class_num}"
            if total_col in district_summary.columns:
                district_summary["Total Enrollment"] += district_summary[total_col]
        
        # Display summary table
        st.dataframe(district_summary)
        
        # Download button for district summary
        district_csv = district_summary.to_csv(index=False)
        st.download_button(
            label="📥 Download District Summary as CSV",
            data=district_csv,
            file_name="district_summary.csv",
            mime="text/csv"
        )
        
        # Create a bar chart for district summary
        fig, ax = plt.subplots(figsize=(12, 8))
        district_summary.plot(kind="bar", x="District", y="Total Enrollment", ax=ax, color="blue")
        ax.set_title("📊 Total Enrollment by District")
        ax.set_xlabel("")
        ax.set_ylabel("Number of Students")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)
    
    # Display Chiefdom Summary when button is clicked
    if chiefdom_summary_button:
        st.subheader("📈 Summary by Chiefdom")
        
        # Create aggregation dictionary
        agg_dict = {}
        
        # Add enrollment columns to aggregation
        for class_num in range(1, 6):
            total_col = f"Number of enrollments in class {class_num}"
            boys_col = f"Number of boys in class {class_num}"
            girls_col = f"Number of girls in class {class_num}"
            
            if total_col in extracted_df.columns:
                agg_dict[total_col] = "sum"
            if boys_col in extracted_df.columns:
                agg_dict[boys_col] = "sum"
            if girls_col in extracted_df.columns:
                agg_dict[girls_col] = "sum"
        
        # Group by District and Chiefdom and aggregate
        chiefdom_summary = extracted_df.groupby(["District", "Chiefdom"]).agg(agg_dict).reset_index()
        
        # Calculate total enrollment
        chiefdom_summary["Total Enrollment"] = 0
        for class_num in range(1, 6):
            total_col = f"Number of enrollments in class {class_num}"
            if total_col in chiefdom_summary.columns:
                chiefdom_summary["Total Enrollment"] += chiefdom_summary[total_col]
        
        # Display summary table
        st.dataframe(chiefdom_summary)
        
        # Download button for chiefdom summary
        chiefdom_csv = chiefdom_summary.to_csv(index=False)
        st.download_button(
            label="📥 Download Chiefdom Summary as CSV",
            data=chiefdom_csv,
            file_name="chiefdom_summary.csv",
            mime="text/csv"
        )
        
        # Create a temporary label for the chart
        chiefdom_summary['Label'] = chiefdom_summary['District'] + '\n' + chiefdom_summary['Chiefdom']
        
        # Create a bar chart for chiefdom summary
        fig, ax = plt.subplots(figsize=(14, 10))
        chiefdom_summary.plot(kind="barh", x="Label", y="Total Enrollment", ax=ax, color="blue")
        ax.set_title("📊 Total Enrollment by District and Chiefdom")
        ax.set_ylabel("")
        ax.set_xlabel("Number of Students")
        plt.tight_layout()
        st.pyplot(fig)
    
    # Visualization and filtering section
    st.subheader("🔍 Detailed Data Filtering and Visualization")
    
    # Check if data is available after filtering
    if not filtered_df.empty:
        st.write(f"### Filtered Data - {len(filtered_df)} records")
        st.dataframe(filtered_df)
        
        # Download button for filtered data
        filtered_csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=filtered_csv,
            file_name="filtered_data.csv",
            mime="text/csv"
        )
        
        # Define the hierarchy levels to include in the summary
        group_columns = hierarchy[grouping_selection]
        
        # Create aggregation dictionary for enrollment data
        agg_dict = {}
        for class_num in range(1, 6):
            total_col = f"Number of enrollments in class {class_num}"
            boys_col = f"Number of boys in class {class_num}"
            girls_col = f"Number of girls in class {class_num}"
            
            if total_col in filtered_df.columns:
                agg_dict[total_col] = "sum"
            if boys_col in filtered_df.columns:
                agg_dict[boys_col] = "sum"
            if girls_col in filtered_df.columns:
                agg_dict[girls_col] = "sum"
        
        # Group by the selected hierarchical columns
        grouped_data = filtered_df.groupby(group_columns).agg(agg_dict).reset_index()
        
        # Calculate total enrollment
        grouped_data["Total Enrollment"] = 0
        for class_num in range(1, 6):
            total_col = f"Number of enrollments in class {class_num}"
            if total_col in grouped_data.columns:
                grouped_data["Total Enrollment"] += grouped_data[total_col]
        
        # Summary Table with separate columns for each level
        st.subheader("📊 Detailed Summary Table")
        st.dataframe(grouped_data)
        
        # Create a temporary group column for the chart
        grouped_data['Group'] = grouped_data[group_columns].apply(lambda row: ','.join(row.astype(str)), axis=1)
        
        # Create a bar chart
        fig, ax = plt.subplots(figsize=(12, 8))
        grouped_data.plot(kind="bar", x="Group", y="Total Enrollment", ax=ax, color="blue")
        ax.set_title(f"Total Enrollment by {grouping_selection}")
        
        # Remove x-label as requested
        ax.set_xlabel("")
        
        ax.set_ylabel("Number of Students")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("No data available for the selected filters.")

    # Final Data Export Section
    st.subheader("📥 Export Complete Dataset")
    st.write("Download the complete extracted dataset in your preferred format:")

    # Create download buttons in columns
    download_col1, download_col2, download_col3 = st.columns(3)

    with download_col1:
        # CSV Download
        csv_data = extracted_df.to_csv(index=False)
        st.download_button(
            label="📄 Download Complete Data as CSV",
            data=csv_data,
            file_name="complete_extracted_data.csv",
            mime="text/csv",
            help="Download all extracted data in CSV format"
        )

    with download_col2:
        # Excel Download
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            extracted_df.to_excel(writer, sheet_name='Extracted Data', index=False)
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📊 Download Complete Data as Excel",
            data=excel_data,
            file_name="complete_extracted_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download all extracted data in Excel format"
        )

    with download_col3:
        # Word Report Download
        if st.button("📋 Generate Comprehensive Word Report", help="Generate and download comprehensive report with all maps and summaries in Word format"):
            # Generate Word report content
            from docx import Document
            from docx.shared import Inches, Pt
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.table import WD_TABLE_ALIGNMENT
            from datetime import datetime
            
            doc = Document()
            
            # Add logos to header (if available)
            try:
                # Create header section with logos
                header_para = doc.add_paragraph()
                header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # Try to add logos
                try:
                    logo_run1 = header_para.add_run()
                    logo_run1.add_picture("NMCP.png", width=Inches(1.5))
                    header_para.add_run("    ")  # Space between logos
                except:
                    header_para.add_run("NMCP    ")
                
                try:
                    logo_run2 = header_para.add_run()
                    logo_run2.add_picture("icf_sl (2).jpg", width=Inches(1.5))
                    header_para.add_run("    ")  # Space between logos
                except:
                    header_para.add_run("ICF Sierra Leone    ")
                
                header_para.add_run("Partner Logo")
                
                doc.add_paragraph()  # Add space after logos
            except:
                # If logos fail, add text headers
                header_para = doc.add_paragraph()
                header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                header_run = header_para.add_run("NMCP | ICF Sierra Leone | Partner Organization")
                header_run.font.size = Pt(12)
                header_run.bold = True
            
            # Add title page
            title = doc.add_heading('School-Based Distribution (SBD)', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            subtitle = doc.add_heading('Comprehensive Analysis Report with Maps and Summaries', level=1)
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add date and time
            current_datetime = datetime.now()
            date_para = doc.add_paragraph()
            date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            date_run = date_para.add_run(f"Generated on: {current_datetime.strftime('%B %d, %Y at %I:%M %p')}")
            date_run.font.size = Pt(12)
            date_run.bold = True
            
            # Add page break
            doc.add_page_break()
            
            # Add executive summary
            doc.add_heading('Executive Summary', level=1)
            
            summary_text = f"""
            This comprehensive report presents the analysis of School-Based Distribution (SBD) data collected across Sierra Leone, 
            covering {summaries['overall']['total_districts']} districts and {summaries['overall']['total_chiefdoms']} chiefdoms with a total of {summaries['overall']['total_schools']} school records.
            
            KEY FINDINGS:
            • Total Schools Surveyed: {summaries['overall']['total_schools']:,}
            • Districts Covered: {summaries['overall']['total_districts']}
            • Chiefdoms Covered: {summaries['overall']['total_chiefdoms']}
            • Total Student Enrollment: {summaries['overall']['total_enrollment']:,}
            • Total Boys: {summaries['overall']['total_boys']:,}
            • Total Girls: {summaries['overall']['total_girls']:,}
            • Gender Ratio (Girls:Boys): {summaries['overall']['gender_ratio']:.1f}%
            • Total ITNs Distributed: {summaries['overall']['total_itn']:,}
            • Overall Coverage Rate: {summaries['overall']['coverage']:.1f}%
            
            This report provides detailed analysis of enrollment patterns, gender distribution, ITN distribution effectiveness, 
            and geographic coverage across administrative boundaries with comprehensive maps and visualizations.
            """
            doc.add_paragraph(summary_text)
            
            # Add geographic maps section
            doc.add_heading('Geographic Distribution Maps', level=1)
            
            # Add Overall Sierra Leone map FIRST
            if 'sierra_leone_overall' in map_images:
                doc.add_heading('Sierra Leone - Overall Distribution', level=2)
                doc.add_paragraph("Overview of school distribution across all districts in Sierra Leone:")
                chart_para = doc.add_paragraph()
                chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                chart_run = chart_para.add_run()
                map_images['sierra_leone_overall'].seek(0)
                chart_run.add_picture(map_images['sierra_leone_overall'], width=Inches(6.5))
                doc.add_paragraph()  # Add spacing
            
            # Add BO District map
            if 'bo_district' in map_images:
                doc.add_heading('BO District Map', level=2)
                doc.add_paragraph("Geographic distribution of schools and chiefdoms in BO District:")
                chart_para = doc.add_paragraph()
                chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                chart_run = chart_para.add_run()
                map_images['bo_district'].seek(0)
                chart_run.add_picture(map_images['bo_district'], width=Inches(6))
                doc.add_paragraph()  # Add spacing after BO map
            
            # Add BOMBALI District map
            if 'bombali_district' in map_images:
                doc.add_heading('BOMBALI District Map', level=2)
                doc.add_paragraph("Geographic distribution of schools and chiefdoms in BOMBALI District:")
                chart_para = doc.add_paragraph()
                chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                chart_run = chart_para.add_run()
                map_images['bombali_district'].seek(0)
                chart_run.add_picture(map_images['bombali_district'], width=Inches(6))
                doc.add_paragraph()  # Add spacing after BOMBALI map
            
            # Add page break before charts
            doc.add_page_break()
            
            # Add overall summary charts
            doc.add_heading('Overall Analysis Charts', level=1)
            
            # Add enhanced enrollment analysis chart
            if 'enhanced_enrollment_analysis' in map_images:
                doc.add_heading('Enhanced Enrollment vs ITN Distribution Analysis', level=2)
                doc.add_paragraph("Comprehensive analysis showing total enrollment, ITNs distributed (boys + girls), and remaining ITNs needed across districts:")
                chart_para = doc.add_paragraph()
                chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                chart_run = chart_para.add_run()
                map_images['enhanced_enrollment_analysis'].seek(0)
                chart_run.add_picture(map_images['enhanced_enrollment_analysis'], width=Inches(6.5))
                doc.add_paragraph()  # Add spacing
            
            # Add overall distribution pie chart
            if 'overall_distribution_pie' in map_images:
                doc.add_heading('Overall ITN Distribution Status', level=2)
                doc.add_paragraph("Overall distribution status showing the proportion of students who have received ITNs versus those still waiting:")
                chart_para = doc.add_paragraph()
                chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                chart_run = chart_para.add_run()
                map_images['overall_distribution_pie'].seek(0)
                chart_run.add_picture(map_images['overall_distribution_pie'], width=Inches(5.5))
                doc.add_paragraph()  # Add spacing
            
            # Add gender analysis charts
            doc.add_heading('Gender Analysis', level=1)
            
            if 'gender_overall' in map_images:
                doc.add_heading('Overall Gender Distribution', level=2)
                doc.add_paragraph("Overall distribution of male and female students across all surveyed schools:")
                chart_para = doc.add_paragraph()
                chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                chart_run = chart_para.add_run()
                map_images['gender_overall'].seek(0)
                chart_run.add_picture(map_images['gender_overall'], width=Inches(5))
                doc.add_paragraph()  # Add spacing
            
            if 'gender_district' in map_images:
                doc.add_heading('Gender Distribution by District', level=2)
                doc.add_paragraph("Comparison of male and female student enrollment across districts:")
                chart_para = doc.add_paragraph()
                chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                chart_run = chart_para.add_run()
                map_images['gender_district'].seek(0)
                chart_run.add_picture(map_images['gender_district'], width=Inches(6.5))
                doc.add_paragraph()  # Add spacing
            
            # Add page break before pie charts
            doc.add_page_break()
            
            # Add pie charts
            doc.add_heading('Distribution Overview (Pie Charts)', level=1)
            
            if 'enrollment_pie' in map_images:
                doc.add_heading('Enrollment Distribution by District', level=2)
                doc.add_paragraph("Proportional distribution of student enrollment across districts:")
                chart_para = doc.add_paragraph()
                chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                chart_run = chart_para.add_run()
                map_images['enrollment_pie'].seek(0)
                chart_run.add_picture(map_images['enrollment_pie'], width=Inches(5))
                doc.add_paragraph()  # Add spacing
            
            if 'itn_pie' in map_images:
                doc.add_heading('ITN Distribution by District', level=2)
                doc.add_paragraph("Proportional distribution of ITNs distributed across districts:")
                chart_para = doc.add_paragraph()
                chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                chart_run = chart_para.add_run()
                map_images['itn_pie'].seek(0)
                chart_run.add_picture(map_images['itn_pie'], width=Inches(5))
                doc.add_paragraph()  # Add spacing
            
            # Add page break before chiefdom analysis
            doc.add_page_break()
            
            # Add chiefdom analysis charts
            doc.add_heading('Chiefdom Analysis by District', level=1)
            doc.add_paragraph("Detailed performance analysis at the chiefdom level within each district, showing enrollment, ITN distribution, and coverage rates.")
            
            for district in extracted_df['District'].dropna().unique():
                doc.add_heading(f'{district} District - Chiefdom Analysis', level=2)
                
                # Add enrollment chart
                enrollment_key = f'{district}_enrollment'
                if enrollment_key in map_images:
                    doc.add_heading(f'{district} District - Enrollment by Chiefdom', level=3)
                    doc.add_paragraph(f"Student enrollment across all chiefdoms in {district} District:")
                    chart_para = doc.add_paragraph()
                    chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    chart_run = chart_para.add_run()
                    map_images[enrollment_key].seek(0)
                    chart_run.add_picture(map_images[enrollment_key], width=Inches(6.5))
                    doc.add_paragraph()  # Add spacing
                
                # Add ITN distribution chart
                itn_key = f'{district}_itn'
                if itn_key in map_images:
                    doc.add_heading(f'{district} District - ITN Distribution by Chiefdom', level=3)
                    doc.add_paragraph(f"ITN distribution across all chiefdoms in {district} District:")
                    chart_para = doc.add_paragraph()
                    chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    chart_run = chart_para.add_run()
                    map_images[itn_key].seek(0)
                    chart_run.add_picture(map_images[itn_key], width=Inches(6.5))
                    doc.add_paragraph()  # Add spacing
                
                # Add coverage chart
                coverage_key = f'{district}_coverage'
                if coverage_key in map_images:
                    doc.add_heading(f'{district} District - Coverage by Chiefdom', level=3)
                    doc.add_paragraph(f"ITN coverage rates across all chiefdoms in {district} District:")
                    chart_para = doc.add_paragraph()
                    chart_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    chart_run = chart_para.add_run()
                    map_images[coverage_key].seek(0)
                    chart_run.add_picture(map_images[coverage_key], width=Inches(6.5))
                    doc.add_paragraph()  # Add spacing
                
                # Add page break between districts (except for the last one)
                districts_list = list(extracted_df['District'].dropna().unique())
                if district != districts_list[-1]:
                    doc.add_page_break()
            
            # Add District Summary Table
            doc.add_page_break()
            doc.add_heading('District Summary Table', level=1)
            
            # Create district summary table
            table = doc.add_table(rows=1, cols=8)
            table.style = 'Table Grid'
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # Add header row
            hdr_cells = table.rows[0].cells
            headers = ['District', 'Schools', 'Chiefdoms', 'Boys', 'Girls', 'Total Enrollment', 'ITNs', 'Coverage (%)']
            for i, header in enumerate(headers):
                hdr_cells[i].text = header
                for paragraph in hdr_cells[i].paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
            
            # Add district data
            for district_info in summaries['district']:
                row_cells = table.add_row().cells
                row_cells[0].text = district_info['district']
                row_cells[1].text = str(district_info['schools'])
                row_cells[2].text = str(district_info['chiefdoms'])
                row_cells[3].text = f"{int(district_info['boys']):,}"
                row_cells[4].text = f"{int(district_info['girls']):,}"
                row_cells[5].text = f"{int(district_info['enrollment']):,}"
                row_cells[6].text = f"{int(district_info['itn']):,}"
                row_cells[7].text = f"{district_info['coverage']:.1f}%"
            
            # Add Chiefdom Summary Table
            doc.add_page_break()
            doc.add_heading('Chiefdom Summary Table', level=1)
            
            # Create chiefdom summary table
            table2 = doc.add_table(rows=1, cols=8)
            table2.style = 'Table Grid'
            table2.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # Add header row
            hdr_cells2 = table2.rows[0].cells
            headers2 = ['District', 'Chiefdom', 'Schools', 'Boys', 'Girls', 'Total Enrollment', 'ITNs', 'Coverage (%)']
            for i, header in enumerate(headers2):
                hdr_cells2[i].text = header
                for paragraph in hdr_cells2[i].paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
            
            # Add chiefdom data
            for chiefdom_info in summaries['chiefdom']:
                row_cells2 = table2.add_row().cells
                row_cells2[0].text = chiefdom_info['district']
                row_cells2[1].text = chiefdom_info['chiefdom']
                row_cells2[2].text = str(chiefdom_info['schools'])
                row_cells2[3].text = f"{int(chiefdom_info['boys']):,}"
                row_cells2[4].text = f"{int(chiefdom_info['girls']):,}"
                row_cells2[5].text = f"{int(chiefdom_info['enrollment']):,}"
                row_cells2[6].text = f"{int(chiefdom_info['itn']):,}"
                row_cells2[7].text = f"{chiefdom_info['coverage']:.1f}%"
            
            # Add Gender Analysis Summary
            doc.add_page_break()
            doc.add_heading('Gender Analysis Summary', level=1)
            
            gender_analysis_text = f"""
            OVERALL GENDER DISTRIBUTION:
            
            • Total Boys: {summaries['overall']['total_boys']:,} ({summaries['overall']['total_boys']/summaries['overall']['total_enrollment']*100:.1f}%)
            • Total Girls: {summaries['overall']['total_girls']:,} ({summaries['overall']['total_girls']/summaries['overall']['total_enrollment']*100:.1f}%)
            
            GENDER DISTRIBUTION BY DISTRICT:
            """
            
            for district_info in summaries['district']:
                if district_info['enrollment'] > 0:
                    boys_pct = (district_info['boys'] / district_info['enrollment']) * 100
                    girls_pct = (district_info['girls'] / district_info['enrollment']) * 100
                    gender_analysis_text += f"""
            
            {district_info['district']} District:
            • Boys: {district_info['boys']:,} ({boys_pct:.1f}%)
            • Girls: {district_info['girls']:,} ({girls_pct:.1f}%)"""
            
            doc.add_paragraph(gender_analysis_text)
            
            # Add methodology section
            doc.add_page_break()
            doc.add_heading('Methodology & Data Sources', level=1)
            
            methodology_text = f"""
            DATA COLLECTION METHODOLOGY:
            
            • Data Source: School-Based Distribution (SBD) survey data
            • Collection Period: {current_datetime.strftime('%Y')}
            • Geographic Scope: {summaries['overall']['total_districts']} districts across Sierra Leone
            • Administrative Coverage: {summaries['overall']['total_chiefdoms']} chiefdoms
            • School Sample Size: {summaries['overall']['total_schools']:,} schools
            
            VISUAL ANALYTICS INCLUDED:
            
            • Geographic Maps: District and chiefdom boundary visualizations with GPS coordinates
            • Performance Charts: Bar charts showing enrollment and ITN distribution
            • Gender Analysis: Comprehensive gender distribution analysis by district and chiefdom
            • Coverage Analysis: Pie charts and performance comparisons
            • Comparative Analysis: District and chiefdom performance metrics
            
            DATA PROCESSING:
            
            • QR code extraction for geographic coordinates and administrative boundaries
            • Enrollment data aggregation across classes 1-5 with gender disaggregation
            • ITN distribution tracking by class level
            • Coverage calculation: (ITNs Distributed / Total Enrollment) × 100
            • Gender ratio calculation: (Girls / Boys) × 100
            • Geographic mapping using administrative boundaries (Chiefdom 2021.shp)
            
            ANALYSIS COMPONENTS:
            
            1. Overall Summary: Total schools, enrollment, ITN distribution, and coverage
            2. District Analysis: Performance metrics by district with gender breakdown
            3. Chiefdom Analysis: Detailed analysis by chiefdom within each district
            4. Gender Analysis: Comprehensive gender distribution and ratios
            5. Geographic Visualization: Maps showing school locations and administrative boundaries
            6. Performance Comparison: Visual comparisons across districts and chiefdoms
            """
            doc.add_paragraph(methodology_text)
            
            # Add recommendations section
            doc.add_heading('Key Recommendations', level=1)
            
            # Calculate top and bottom performing districts
            district_performance = [(d['district'], d['coverage']) for d in summaries['district']]
            district_performance.sort(key=lambda x: x[1], reverse=True)
            best_district = district_performance[0] if district_performance else ("N/A", 0)
            worst_district = district_performance[-1] if district_performance else ("N/A", 0)
            
            recommendations_text = f"""
            Based on the comprehensive analysis of SBD data with district and chiefdom analytics, the following recommendations are proposed:
            
            IMMEDIATE ACTIONS:
            
            1. PRIORITY INTERVENTION AREAS:
               • Focus additional resources on {worst_district[0]} District (Coverage: {worst_district[1]:.1f}%)
               • Investigate supply chain issues in underperforming areas
               • Strengthen coordination with district education offices
            
            2. BEST PRACTICE REPLICATION:
               • Study successful implementation in {best_district[0]} District (Coverage: {best_district[1]:.1f}%)
               • Document and replicate effective distribution strategies
               • Share lessons learned across all districts
            
            3. GENDER EQUITY FOCUS:
               • Ensure equal access to ITN distribution for boys and girls
               • Monitor gender-disaggregated data collection
            
            4. MONITORING & EVALUATION:
               • Establish real-time tracking systems for ITN distribution
               • Implement quarterly review meetings with district teams
               • Develop standardized reporting formats with visual dashboards
            
            STRATEGIC RECOMMENDATIONS:
            
            DISTRICT-LEVEL INTERVENTIONS:
            """
            
            for district_info in summaries['district']:
                recommendations_text += f"""
            
            {district_info['district']} District:
            • Coverage: {district_info['coverage']:.1f}% | Schools: {district_info['schools']} | Students: {district_info['enrollment']:,}
            • Boys: {district_info['boys']:,} | Girls: {district_info['girls']:,}
            • Recommended Actions: {'Maintain high performance and share best practices' if district_info['coverage'] > summaries['overall']['coverage'] else 'Require intensive support and resource allocation'}"""
            
            recommendations_text += f"""
            
            CHIEFDOM-LEVEL RECOMMENDATIONS:
            • Conduct chiefdom-specific assessments for targeted interventions
            • Establish chiefdom-level coordination committees
            • Develop micro-planning approaches for hard-to-reach communities
            • Implement peer-learning networks among chiefdoms
            
            GENDER-RESPONSIVE PROGRAMMING:
            • Ensure equal representation in school-based distribution teams
            • Address cultural barriers that may affect girls' school attendance
            • Monitor and report on gender-disaggregated coverage data
            • Implement targeted outreach for gender equity
            
            NEXT STEPS:
            
            • Conduct follow-up assessments in 6 months with gender-disaggregated analysis
            • Develop district and chiefdom-specific action plans based on visual analytics
            • Allocate additional resources based on performance gaps identified
            • Establish partnerships with local NGOs and community organizations
            • Create interactive dashboards for real-time monitoring with gender indicators
            • Implement chiefdom-level feedback mechanisms
            • Develop gender-sensitive training materials for distribution teams
            """
            doc.add_paragraph(recommendations_text)
            
            # Add footer with generation info
            doc.add_page_break()
            footer_para = doc.add_paragraph()
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_run = footer_para.add_run(f"\nComprehensive Report with Maps, District/Chiefdom/Gender Analysis\nGenerated by Enhanced SBD Analysis Dashboard\n{current_datetime.strftime('%B %d, %Y at %I:%M %p')}\n\nIncludes: Geographic Maps, District Summary, Chiefdom Summary, Gender Analysis, Visual Charts, and Performance Metrics")
            footer_run.font.size = Pt(10)
            footer_run.italic = True
            
            # Close matplotlib figures to free memory
            plt.close('all')
            
            # Save to BytesIO
            word_buffer = BytesIO()
            doc.save(word_buffer)
            word_data = word_buffer.getvalue()
            
            # Success message
            st.success("✅ Comprehensive Word report generated successfully with all maps and summaries!")
            
            st.download_button(
                label="💾 Download Complete Report with All Maps & Summaries",
                data=word_data,
                file_name=f"SBD_Complete_Report_Maps_Summaries_{current_datetime.strftime('%Y%m%d_%H%M')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                help="Download comprehensive report with maps, district/chiefdom/gender summaries, charts, and analysis in Word format"
            )

    # Display final summary
    st.info(f"📋 **Dataset Summary**: {len(extracted_df)} total records processed with comprehensive district, chiefdom, and gender analysis")
    
    # Display map files saved notification
    if map_images:
        st.success(f"✅ **Maps Saved**: {len(map_images)} visualization maps have been saved as PNG files")
        
        # Show list of saved maps
        with st.expander("📁 View Saved Map Files"):
            for map_name in map_images.keys():
                st.write(f"• {map_name}.png")
