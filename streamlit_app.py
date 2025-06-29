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
</style>
""", unsafe_allow_html=True)

# Function to save maps as PNG and return BytesIO object
def save_map_as_png(fig, filename_prefix):
    """Save matplotlib figure as PNG and return BytesIO object"""
    try:
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        buffer.seek(0)
        
        # Also save to disk for reference
        fig.savefig(f"{filename_prefix}.png", format='png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        
        return buffer
    except Exception as e:
        st.warning(f"Could not save map {filename_prefix}: {e}")
        return BytesIO()

# Function to safely get numeric value
def safe_numeric(value, default=0):
    """Safely convert value to numeric, return default if conversion fails"""
    try:
        if pd.isna(value):
            return default
        return float(value) if value != '' else default
    except (ValueError, TypeError):
        return default

# Function to generate comprehensive summaries with error handling
def generate_summaries(df):
    """Generate District, Chiefdom, and Gender summaries with error handling"""
    summaries = {}
    
    # Check if dataframe is empty
    if df.empty:
        st.warning("No data available for summary generation.")
        return {
            'overall': {
                'total_schools': 0,
                'total_districts': 0,
                'total_chiefdoms': 0,
                'total_boys': 0,
                'total_girls': 0,
                'total_enrollment': 0,
                'total_itn': 0,
                'coverage': 0,
                'itn_remaining': 0,
                'gender_ratio': 0
            },
            'district': [],
            'chiefdom': []
        }
    
    # Overall Summary
    overall_summary = {
        'total_schools': len(df),
        'total_districts': len(df['District'].dropna().unique()) if 'District' in df.columns else 0,
        'total_chiefdoms': len(df['Chiefdom'].dropna().unique()) if 'Chiefdom' in df.columns else 0,
        'total_boys': 0,
        'total_girls': 0,
        'total_enrollment': 0,
        'total_itn': 0
    }
    
    try:
        # Calculate totals using the correct columns
        for class_num in range(1, 6):
            # Total enrollment from "Number of enrollments in class X"
            enrollment_col = f"Number of enrollments in class {class_num}"
            if enrollment_col in df.columns:
                overall_summary['total_enrollment'] += int(df[enrollment_col].apply(safe_numeric).sum())
            
            # Boys and girls for gender analysis AND ITN calculation
            boys_col = f"Number of boys in class {class_num}"
            girls_col = f"Number of girls in class {class_num}"
            if boys_col in df.columns:
                overall_summary['total_boys'] += int(df[boys_col].apply(safe_numeric).sum())
            if girls_col in df.columns:
                overall_summary['total_girls'] += int(df[girls_col].apply(safe_numeric).sum())
        
        # Total ITNs = boys + girls (actual beneficiaries)
        overall_summary['total_itn'] = overall_summary['total_boys'] + overall_summary['total_girls']
        
        # Calculate coverage and gender ratio
        overall_summary['coverage'] = (overall_summary['total_itn'] / overall_summary['total_enrollment'] * 100) if overall_summary['total_enrollment'] > 0 else 0
        overall_summary['itn_remaining'] = overall_summary['total_enrollment'] - overall_summary['total_itn']
        overall_summary['gender_ratio'] = (overall_summary['total_girls'] / overall_summary['total_boys'] * 100) if overall_summary['total_boys'] > 0 else 0
        
    except Exception as e:
        st.warning(f"Error calculating overall summary: {e}")
    
    summaries['overall'] = overall_summary
    
    # District Summary
    district_summary = []
    try:
        if 'District' in df.columns:
            unique_districts = df['District'].dropna().unique()
            for district in unique_districts:
                district_data = df[df['District'] == district]
                district_stats = {
                    'district': district,
                    'schools': len(district_data),
                    'chiefdoms': len(district_data['Chiefdom'].dropna().unique()) if 'Chiefdom' in district_data.columns else 0,
                    'boys': 0,
                    'girls': 0,
                    'enrollment': 0,
                    'itn': 0
                }
                
                try:
                    for class_num in range(1, 6):
                        # Total enrollment from "Number of enrollments in class X"
                        enrollment_col = f"Number of enrollments in class {class_num}"
                        if enrollment_col in district_data.columns:
                            district_stats['enrollment'] += int(district_data[enrollment_col].apply(safe_numeric).sum())
                        
                        # Boys and girls for gender analysis AND ITN calculation
                        boys_col = f"Number of boys in class {class_num}"
                        girls_col = f"Number of girls in class {class_num}"
                        if boys_col in district_data.columns:
                            district_stats['boys'] += int(district_data[boys_col].apply(safe_numeric).sum())
                        if girls_col in district_data.columns:
                            district_stats['girls'] += int(district_data[girls_col].apply(safe_numeric).sum())
                    
                    # Total ITNs = boys + girls (actual beneficiaries)
                    district_stats['itn'] = district_stats['boys'] + district_stats['girls']
                    
                    # Calculate coverage
                    district_stats['coverage'] = (district_stats['itn'] / district_stats['enrollment'] * 100) if district_stats['enrollment'] > 0 else 0
                    district_stats['itn_remaining'] = district_stats['enrollment'] - district_stats['itn']
                    
                except Exception as e:
                    st.warning(f"Error processing district {district}: {e}")
                
                district_summary.append(district_stats)
    except Exception as e:
        st.warning(f"Error generating district summary: {e}")
    
    summaries['district'] = district_summary
    
    # Chiefdom Summary
    chiefdom_summary = []
    try:
        if 'District' in df.columns and 'Chiefdom' in df.columns:
            unique_districts = df['District'].dropna().unique()
            for district in unique_districts:
                district_data = df[df['District'] == district]
                unique_chiefdoms = district_data['Chiefdom'].dropna().unique()
                for chiefdom in unique_chiefdoms:
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
                    
                    try:
                        for class_num in range(1, 6):
                            # Total enrollment from "Number of enrollments in class X"
                            enrollment_col = f"Number of enrollments in class {class_num}"
                            if enrollment_col in chiefdom_data.columns:
                                chiefdom_stats['enrollment'] += int(chiefdom_data[enrollment_col].apply(safe_numeric).sum())
                            
                            # Boys and girls for gender analysis AND ITN calculation
                            boys_col = f"Number of boys in class {class_num}"
                            girls_col = f"Number of girls in class {class_num}"
                            if boys_col in chiefdom_data.columns:
                                chiefdom_stats['boys'] += int(chiefdom_data[boys_col].apply(safe_numeric).sum())
                            if girls_col in chiefdom_data.columns:
                                chiefdom_stats['girls'] += int(chiefdom_data[girls_col].apply(safe_numeric).sum())
                        
                        # Total ITNs = boys + girls (actual beneficiaries)
                        chiefdom_stats['itn'] = chiefdom_stats['boys'] + chiefdom_stats['girls']
                        
                        # Calculate coverage
                        chiefdom_stats['coverage'] = (chiefdom_stats['itn'] / chiefdom_stats['enrollment'] * 100) if chiefdom_stats['enrollment'] > 0 else 0
                        chiefdom_stats['itn_remaining'] = chiefdom_stats['enrollment'] - chiefdom_stats['itn']
                        
                    except Exception as e:
                        st.warning(f"Error processing chiefdom {chiefdom} in {district}: {e}")
                    
                    chiefdom_summary.append(chiefdom_stats)
    except Exception as e:
        st.warning(f"Error generating chiefdom summary: {e}")
    
    summaries['chiefdom'] = chiefdom_summary
    
    return summaries

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

# Initialize variables
df_original = pd.DataFrame()
extracted_df = pd.DataFrame()
gdf = None
map_images = {}

try:
    if uploaded_file:
        # Read the uploaded Excel file with error handling
        try:
            df_original = pd.read_excel(uploaded_file)
            
            # Check if dataframe is empty
            if df_original.empty:
                st.warning("⚠️ The Excel file is empty. Please upload a file with data.")
                st.stop()
                
            # Check if required column exists
            if "Scan QR code" not in df_original.columns:
                st.error("❌ Required column 'Scan QR code' not found in the Excel file.")
                st.info("Available columns: " + ", ".join(df_original.columns.tolist()))
                st.stop()
                
        except FileNotFoundError:
            st.error("❌ Excel file not found. Please ensure the file exists in the correct location.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error reading Excel file: {e}")
            st.stop()
        
        # Load shapefile with error handling
        try:
            gdf = gpd.read_file("Chiefdom2021.shp")
            st.success("✅ Shapefile loaded successfully!")
        except Exception as e:
            st.warning(f"⚠️ Could not load shapefile: {e}")
            gdf = None
        
        # Create empty lists to store extracted data
        districts, chiefdoms, phu_names, community_names, school_names = [], [], [], [], []
        
        # Process each row in the "Scan QR code" column with error handling
        try:
            for qr_text in df_original["Scan QR code"]:
                if pd.isna(qr_text):
                    districts.append(None)
                    chiefdoms.append(None)
                    phu_names.append(None)
                    community_names.append(None)
                    school_names.append(None)
                    continue
                    
                try:
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
                    
                except Exception as e:
                    # If processing a single row fails, add None values
                    districts.append(None)
                    chiefdoms.append(None)
                    phu_names.append(None)
                    community_names.append(None)
                    school_names.append(None)
                    
        except Exception as e:
            st.error(f"❌ Error processing QR code data: {e}")
            st.stop()
        
        # Create a new DataFrame with extracted values
        try:
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
                    
        except Exception as e:
            st.error(f"❌ Error creating extracted DataFrame: {e}")
            st.stop()

        # Only proceed with sidebar and analysis if we have valid data
        if not extracted_df.empty:
            # Create sidebar filters
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
            try:
                for level in hierarchy[grouping_selection]:
                    # Filter out None/NaN values and get sorted unique values
                    if level in filtered_df.columns:
                        level_values = sorted(filtered_df[level].dropna().unique())
                        
                        if level_values:
                            # Create selectbox for this level
                            selected_value = st.sidebar.selectbox(f"Select {level}", level_values)
                            selected_values[level] = selected_value
                            
                            # Apply filter to the dataframe
                            filtered_df = filtered_df[filtered_df[level] == selected_value]
                        else:
                            st.sidebar.warning(f"No data available for {level}")
                    else:
                        st.sidebar.warning(f"Column {level} not found in data")
            except Exception as e:
                st.sidebar.error(f"Error applying filters: {e}")
                filtered_df = extracted_df.copy()

            # Display maps section with error handling
            try:
                st.subheader("🗺️ Geographic Distribution Maps")
                
                if gdf is not None and not extracted_df.empty:
                    # OVERALL SIERRA LEONE MAP FIRST
                    st.write("**Sierra Leone - All Districts Overview**")
                    
                    try:
                        # Create overall Sierra Leone map
                        fig_overall, ax_overall = plt.subplots(figsize=(16, 10))
                        
                        # Plot all chiefdoms with gray edges (base layer)
                        gdf.plot(ax=ax_overall, color='white', edgecolor='gray', alpha=0.8, linewidth=0.5)
                        
                        # Plot district boundaries with thick black lines
                        if 'FIRST_DNAM' in gdf.columns:
                            district_boundaries = gdf.dissolve(by='FIRST_DNAM')
                            district_boundaries.plot(ax=ax_overall, facecolor='none', edgecolor='black', linewidth=3, alpha=1.0)
                            
                            # Add district labels at centroids
                            for idx, row in district_boundaries.iterrows():
                                try:
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
                                except Exception as e:
                                    continue  # Skip if centroid calculation fails
                        
                        # Extract and plot GPS coordinates with error handling
                        all_coords_extracted = []
                        if "GPS Location" in extracted_df.columns:
                            all_gps_data = extracted_df["GPS Location"].dropna()
                            
                            for idx, gps_val in enumerate(all_gps_data):
                                try:
                                    if pd.notna(gps_val):
                                        gps_str = str(gps_val).strip()
                                        
                                        if ',' in gps_str:
                                            parts = gps_str.split(',')
                                            if len(parts) == 2:
                                                lat = float(parts[0].strip())
                                                lon = float(parts[1].strip())
                                                
                                                # Check if coordinates are in valid range for Sierra Leone
                                                if 6.0 <= lat <= 11.0 and -14.0 <= lon <= -10.0:
                                                    all_coords_extracted.append([lat, lon])
                                except (ValueError, TypeError):
                                    continue  # Skip invalid coordinates
                        
                        # Plot GPS points on the overall map
                        if all_coords_extracted:
                            try:
                                lats, lons = zip(*all_coords_extracted)
                                
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
                                
                                ax_overall.legend(fontsize=14, loc='best')
                            except Exception as e:
                                st.warning(f"Could not plot GPS points: {e}")
                        
                        # Customize overall map
                        ax_overall.set_title('Sierra Leone - School Distribution by District', fontsize=18, fontweight='bold', pad=20)
                        ax_overall.set_xlabel('Longitude', fontsize=14)
                        ax_overall.set_ylabel('Latitude', fontsize=14)
                        ax_overall.grid(True, alpha=0.3, linestyle='--')
                        
                        # Set axis limits to show full country
                        ax_overall.set_xlim(gdf.total_bounds[0] - 0.1, gdf.total_bounds[2] + 0.1)
                        ax_overall.set_ylim(gdf.total_bounds[1] - 0.1, gdf.total_bounds[3] + 0.1)
                        
                        plt.tight_layout()
                        st.pyplot(fig_overall)
                        
                        # Save overall map
                        map_images['sierra_leone_overall'] = save_map_as_png(fig_overall, "Sierra_Leone_Overall_Map")
                        
                    except Exception as e:
                        st.warning(f"Could not create overall Sierra Leone map: {e}")
                    
                    st.divider()
                    
                    # Individual district maps with error handling
                    districts_to_map = ["BO", "BOMBALI"]
                    
                    for district_name in districts_to_map:
                        try:
                            st.write(f"**{district_name} District - All Chiefdoms**")
                            
                            # Filter shapefile for district
                            district_gdf = gdf[gdf['FIRST_DNAM'] == district_name].copy()
                            
                            if len(district_gdf) > 0:
                                # Filter data for district to get GPS coordinates
                                district_data = extracted_df[extracted_df["District"] == district_name].copy()
                                
                                # Create the district plot
                                fig_district, ax_district = plt.subplots(figsize=(14, 8))
                                
                                # Plot chiefdom boundaries
                                district_gdf.plot(ax=ax_district, color='white', edgecolor='black', alpha=0.8, linewidth=2)
                                
                                # Extract GPS coordinates for this district
                                coords_extracted = []
                                if len(district_data) > 0 and "GPS Location" in district_data.columns:
                                    gps_data = district_data["GPS Location"].dropna()
                                    
                                    for idx, gps_val in enumerate(gps_data):
                                        try:
                                            if pd.notna(gps_val):
                                                gps_str = str(gps_val).strip()
                                                
                                                if ',' in gps_str:
                                                    parts = gps_str.split(',')
                                                    if len(parts) == 2:
                                                        lat = float(parts[0].strip())
                                                        lon = float(parts[1].strip())
                                                        
                                                        # Check if coordinates are valid
                                                        if 6.0 <= lat <= 11.0 and -14.0 <= lon <= -10.0:
                                                            coords_extracted.append([lat, lon])
                                        except (ValueError, TypeError):
                                            continue
                                
                                # Plot GPS points
                                if coords_extracted:
                                    try:
                                        lats, lons = zip(*coords_extracted)
                                        
                                        scatter = ax_district.scatter(
                                            lons, lats,
                                            c='red',
                                            s=150,
                                            alpha=1.0,
                                            edgecolors='white',
                                            linewidth=3,
                                            zorder=100,
                                            label=f'Schools ({len(coords_extracted)})',
                                            marker='o'
                                        )
                                        
                                        # Set map extent with padding
                                        margin = 0.05
                                        ax_district.set_xlim(min(lons) - margin, max(lons) + margin)
                                        ax_district.set_ylim(min(lats) - margin, max(lats) + margin)
                                        
                                        ax_district.legend(fontsize=12, loc='best')
                                    except Exception as e:
                                        st.warning(f"Could not plot GPS points for {district_name}: {e}")
                                
                                # Add chiefdom labels
                                try:
                                    for idx, row in district_gdf.iterrows():
                                        if 'FIRST_CHIE' in row and pd.notna(row['FIRST_CHIE']):
                                            centroid = row.geometry.centroid
                                            ax_district.annotate(
                                                row['FIRST_CHIE'], 
                                                (centroid.x, centroid.y),
                                                xytext=(5, 5), 
                                                textcoords='offset points',
                                                fontsize=9,
                                                ha='left',
                                                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7)
                                            )
                                except Exception as e:
                                    st.warning(f"Could not add chiefdom labels for {district_name}: {e}")
                                
                                # Customize plot
                                title_text = f'{district_name} District - Chiefdoms: {len(district_gdf)}'
                                if coords_extracted:
                                    title_text += f' | GPS Points: {len(coords_extracted)}'
                                ax_district.set_title(title_text, fontsize=16, fontweight='bold')
                                ax_district.set_xlabel('Longitude', fontsize=12)
                                ax_district.set_ylabel('Latitude', fontsize=12)
                                ax_district.grid(True, alpha=0.3, linestyle='--')
                                
                                plt.tight_layout()
                                st.pyplot(fig_district)
                                
                                # Save district map
                                map_images[f'{district_name.lower()}_district'] = save_map_as_png(fig_district, f"{district_name}_District_Map")
                                
                                # Display chiefdoms list
                                try:
                                    if 'FIRST_CHIE' in district_gdf.columns:
                                        chiefdoms = district_gdf['FIRST_CHIE'].dropna().tolist()
                                        if chiefdoms:
                                            st.write(f"**Chiefdoms in {district_name} District ({len(chiefdoms)}):**")
                                            chiefdom_cols = st.columns(3)
                                            for i, chiefdom in enumerate(chiefdoms):
                                                with chiefdom_cols[i % 3]:
                                                    st.write(f"• {chiefdom}")
                                except Exception as e:
                                    st.warning(f"Could not display chiefdoms list for {district_name}: {e}")
                            else:
                                st.warning(f"No chiefdoms found for {district_name} district in shapefile")
                            
                            st.divider()
                            
                        except Exception as e:
                            st.warning(f"Could not create map for {district_name} district: {e}")
                            continue
                
                else:
                    if gdf is None:
                        st.warning("⚠️ Shapefile not loaded. Cannot display maps.")
                    if extracted_df.empty:
                        st.warning("⚠️ No data available for mapping.")
                        
            except Exception as e:
                st.error(f"❌ Error in maps section: {e}")

            # Display data sections with error handling
            try:
                # Display Original Data Sample
                st.subheader("📄 Original Data Sample")
                if not df_original.empty:
                    st.dataframe(df_original.head())
                else:
                    st.warning("No original data to display")
                
                # Display Extracted Data
                st.subheader("📋 Extracted Data")
                if not extracted_df.empty:
                    st.dataframe(extracted_df)
                    
                    # Add download button for CSV
                    try:
                        csv = extracted_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Extracted Data as CSV",
                            data=csv,
                            file_name="extracted_school_data.csv",
                            mime="text/csv"
                        )
                    except Exception as e:
                        st.warning(f"Could not create CSV download: {e}")
                else:
                    st.warning("No extracted data to display")
                    
            except Exception as e:
                st.error(f"❌ Error displaying data sections: {e}")

            # Generate summaries with error handling
            try:
                summaries = generate_summaries(extracted_df)
                
                # Display Overall Summary
                st.subheader("📊 Overall Summary")
                
                if summaries and 'overall' in summaries:
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
                else:
                    st.warning("Could not generate overall summary")
                    
            except Exception as e:
                st.error(f"❌ Error generating summaries: {e}")
                summaries = {
                    'overall': {
                        'total_schools': 0, 'total_districts': 0, 'total_chiefdoms': 0,
                        'total_boys': 0, 'total_girls': 0, 'total_enrollment': 0,
                        'total_itn': 0, 'coverage': 0, 'gender_ratio': 0
                    },
                    'district': [], 'chiefdom': []
                }

            # Gender Analysis with error handling
            try:
                st.subheader("👫 Gender Analysis")
                
                if (summaries['overall']['total_boys'] > 0 or summaries['overall']['total_girls'] > 0):
                    # Overall gender distribution pie chart
                    fig_gender, ax_gender = plt.subplots(figsize=(10, 8))
                    labels = ['Boys', 'Girls']
                    sizes = [summaries['overall']['total_boys'], summaries['overall']['total_girls']]
                    colors = ['#4A90E2', '#F39C12']
                    
                    # Only create pie chart if we have data
                    if sum(sizes) > 0:
                        wedges, texts, autotexts = ax_gender.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                                                colors=colors, startangle=90)
                        ax_gender.set_title('Overall Gender Distribution', fontsize=16, fontweight='bold', pad=20)
                        plt.setp(autotexts, size=14, weight="bold")
                        plt.setp(texts, size=12, weight="bold")
                        plt.tight_layout()
                        st.pyplot(fig_gender)
                        
                        # Save gender chart
                        map_images['gender_overall'] = save_map_as_png(fig_gender, "Overall_Gender_Distribution")
                    else:
                        st.warning("No gender data available for pie chart")
                        
                    # Gender ratio by district chart
                    if summaries['district']:
                        try:
                            districts = [d['district'] for d in summaries['district']]
                            boys_counts = [d['boys'] for d in summaries['district']]
                            girls_counts = [d['girls'] for d in summaries['district']]
                            
                            if sum(boys_counts) > 0 or sum(girls_counts) > 0:
                                fig_gender_district, ax_gender_district = plt.subplots(figsize=(14, 8))
                                x = np.arange(len(districts))
                                width = 0.35
                                
                                bars1 = ax_gender_district.bar(x - width/2, boys_counts, width, label='Boys', 
                                                             color='#4A90E2', edgecolor='navy', linewidth=1)
                                bars2 = ax_gender_district.bar(x + width/2, girls_counts, width, label='Girls', 
                                                             color='#F39C12', edgecolor='darkorange', linewidth=1)
                                
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
                                    if height > 0:
                                        ax_gender_district.annotate(f'{int(height):,}',
                                                                  xy=(bar.get_x() + bar.get_width() / 2, height),
                                                                  xytext=(0, 3), textcoords="offset points",
                                                                  ha='center', va='bottom', fontsize=10, fontweight='bold')
                                
                                for bar in bars2:
                                    height = bar.get_height()
                                    if height > 0:
                                        ax_gender_district.annotate(f'{int(height):,}',
                                                                  xy=(bar.get_x() + bar.get_width() / 2, height),
                                                                  xytext=(0, 3), textcoords="offset points",
                                                                  ha='center', va='bottom', fontsize=10, fontweight='bold')
                                
                                plt.tight_layout()
                                st.pyplot(fig_gender_district)
                                
                                # Save gender district chart
                                map_images['gender_district'] = save_map_as_png(fig_gender_district, "Gender_Distribution_by_District")
                        except Exception as e:
                            st.warning(f"Could not create gender district chart: {e}")
                else:
                    st.warning("No gender data available for analysis")
                    
            except Exception as e:
                st.warning(f"Could not create gender analysis: {e}")

            # Enrollment and ITN Distribution Analysis with error handling
            try:
                st.subheader("📊 Enrollment and ITN Distribution Analysis")
                
                # Calculate district analysis with error handling
                district_analysis = []
                
                if summaries['district']:
                    for district_info in summaries['district']:
                        try:
                            district_analysis.append({
                                'District': district_info['district'],
                                'Total_Enrollment': district_info['enrollment'],
                                'Total_ITN': district_info['itn'],
                                'ITN_Remaining': district_info.get('itn_remaining', 0),
                                'Coverage': district_info['coverage']
                            })
                        except Exception as e:
                            st.warning(f"Error processing district {district_info.get('district', 'Unknown')}: {e}")
                            continue
                
                if district_analysis:
                    district_df = pd.DataFrame(district_analysis)
                    
                    # Create enhanced bar chart
                    try:
                        fig_enhanced, ax_enhanced = plt.subplots(figsize=(16, 8))
                        
                        x = np.arange(len(district_df['District']))
                        width = 0.25
                        
                        bars1 = ax_enhanced.bar(x - width, district_df['Total_Enrollment'], width, 
                                               label='Total Enrollment', color='#47B5FF', edgecolor='navy', linewidth=1)
                        bars2 = ax_enhanced.bar(x, district_df['Total_ITN'], width, 
                                               label='ITNs Distributed', color='lightcoral', edgecolor='darkred', linewidth=1)
                        bars3 = ax_enhanced.bar(x + width, district_df['ITN_Remaining'], width, 
                                               label='ITNs Remaining', color='hotpink', edgecolor='darkmagenta', linewidth=1)
                        
                        ax_enhanced.set_title('District Analysis: Enrollment vs ITN Distribution', fontsize=16, fontweight='bold', pad=20)
                        ax_enhanced.set_xlabel('Districts', fontsize=12, fontweight='bold')
                        ax_enhanced.set_ylabel('Number of Students/ITNs', fontsize=12, fontweight='bold')
                        ax_enhanced.set_xticks(x)
                        ax_enhanced.set_xticklabels(district_df['District'], rotation=45, ha='right')
                        ax_enhanced.legend(fontsize=12)
                        ax_enhanced.grid(axis='y', alpha=0.3, linestyle='--')
                        
                        # Add value labels
                        for bars in [bars1, bars2, bars3]:
                            for bar in bars:
                                height = bar.get_height()
                                if height > 0:
                                    ax_enhanced.annotate(f'{int(height):,}',
                                                        xy=(bar.get_x() + bar.get_width() / 2, height),
                                                        xytext=(0, 3), textcoords="offset points",
                                                        ha='center', va='bottom', fontsize=9, fontweight='bold')
                        
                        plt.tight_layout()
                        st.pyplot(fig_enhanced)
                        
                        # Save enhanced chart
                        map_images['enhanced_enrollment_analysis'] = save_map_as_png(fig_enhanced, "Enhanced_Enrollment_Analysis")
                        
                    except Exception as e:
                        st.warning(f"Could not create enrollment analysis chart: {e}")
                        
                    # Create overall pie chart
                    try:
                        st.subheader("📊 Overall Distribution Overview (Pie Chart)")
                        
                        overall_enrollment = district_df['Total_Enrollment'].sum()
                        overall_distributed = district_df['Total_ITN'].sum()
                        overall_remaining = district_df['ITN_Remaining'].sum()
                        
                        if overall_enrollment > 0:
                            fig_overall_pie, ax_overall_pie = plt.subplots(figsize=(10, 8))
                            
                            sizes = [overall_distributed, overall_remaining]
                            labels = [f'ITNs Distributed\n({overall_distributed:,})', f'ITNs Remaining\n({overall_remaining:,})']
                            colors = ['lightcoral', 'hotpink']
                            explode = (0.05, 0)
                            
                            if sum(sizes) > 0:
                                wedges, texts, autotexts = ax_overall_pie.pie(sizes, labels=labels, autopct='%1.1f%%',
                                                                             colors=colors, startangle=90, explode=explode)
                                ax_overall_pie.set_title(f'Overall ITN Distribution Status\nTotal Enrollment: {overall_enrollment:,}', 
                                                        fontsize=16, fontweight='bold', pad=20)
                                
                                plt.setp(autotexts, size=12, weight="bold", color='white')
                                plt.setp(texts, size=11, weight="bold")
                                
                                plt.tight_layout()
                                st.pyplot(fig_overall_pie)
                                
                                # Save overall pie chart
                                map_images['overall_distribution_pie'] = save_map_as_png(fig_overall_pie, "Overall_Distribution_Pie")
                        else:
                            st.warning("No enrollment data available for overall pie chart")
                            
                    except Exception as e:
                        st.warning(f"Could not create overall pie chart: {e}")
                else:
                    st.warning("No district analysis data available")
                    
            except Exception as e:
                st.warning(f"Could not create enrollment and ITN analysis: {e}")

            # Summary Tables with error handling
            try:
                if summaries['district']:
                    st.subheader("📈 District Summary Table")
                    district_summary_df = pd.DataFrame(summaries['district'])
                    st.dataframe(district_summary_df)
                
                if summaries['chiefdom']:
                    st.subheader("📈 Chiefdom Summary Table")
                    chiefdom_summary_df = pd.DataFrame(summaries['chiefdom'])
                    st.dataframe(chiefdom_summary_df)
                    
            except Exception as e:
                st.warning(f"Could not display summary tables: {e}")

            # Data export section with error handling
            try:
                st.subheader("📥 Export Complete Dataset")
                st.write("Download the complete extracted dataset in your preferred format:")

                download_col1, download_col2, download_col3 = st.columns(3)

                with download_col1:
                    try:
                        csv_data = extracted_df.to_csv(index=False)
                        st.download_button(
                            label="📄 Download Complete Data as CSV",
                            data=csv_data,
                            file_name="complete_extracted_data.csv",
                            mime="text/csv",
                            help="Download all extracted data in CSV format"
                        )
                    except Exception as e:
                        st.warning(f"Could not create CSV download: {e}")

                with download_col2:
                    try:
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
                    except Exception as e:
                        st.warning(f"Could not create Excel download: {e}")

                with download_col3:
                    if st.button("📋 Generate Comprehensive Word Report", help="Generate and download comprehensive report"):
                        try:
                            st.info("Word report generation would go here - requires python-docx library")
                        except Exception as e:
                            st.error(f"Could not generate Word report: {e}")
                            
            except Exception as e:
                st.warning(f"Could not create export section: {e}")

            # Final summary
            try:
                st.info(f"📋 **Dataset Summary**: {len(extracted_df)} total records processed")
                
                if map_images:
                    st.success(f"✅ **Maps Saved**: {len(map_images)} visualization maps have been saved")
                    
                    with st.expander("📁 View Saved Map Files"):
                        for map_name in map_images.keys():
                            st.write(f"• {map_name}.png")
            except Exception as e:
                st.warning(f"Could not display final summary: {e}")
        
        else:
            st.error("❌ No valid data found after processing. Please check your Excel file.")

except Exception as e:
    st.error(f"❌ Critical error in application: {e}")
    st.info("Please check your data files and try again.")
