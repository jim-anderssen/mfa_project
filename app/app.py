"""
NUTS2 Waste Hotspot Visualizer
Interactive map showing geographical waste clusters across European regions.
"""
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pathlib import Path

# Page config
st.set_page_config(
    page_title="NUTS2 Waste Hotspots",
    page_icon="🗺️",
    layout="wide"
)

# Color palette for clusters
CLUSTER_COLORS = [
    "#e41a1c",  # red
    "#377eb8",  # blue
    "#4daf4a",  # green
    "#984ea3",  # purple
    "#ff7f00",  # orange
    "#ffff33",  # yellow
    "#a65628",  # brown
    "#f781bf",  # pink
]

@st.cache_data
def load_data():
    """Load the NUTS2 hotspot data."""
    data_path = Path(__file__).parent.parent / "data" / "processed" / "nuts2_geographical_hotspots.csv"
    return pd.read_csv(data_path)

@st.cache_data
def load_high_value_data():
    """Load the detailed high-value waste data (recyclables only)."""
    data_path = Path(__file__).parent.parent / "data" / "processed" / "nuts2_high_value_with_geo.csv"
    return pd.read_csv(data_path)

@st.cache_data
def load_full_detail_data():
    """Load complete waste data with all waste types, joined with geo_cluster."""
    data_path = Path(__file__).parent.parent / "data" / "processed"
    detail = pd.read_csv(data_path / "nuts2_waste_allocated_detail.csv")
    geo = pd.read_csv(data_path / "nuts2_geographical_hotspots.csv")[["nuts2_region", "geo_cluster"]]
    return detail.merge(geo, on="nuts2_region", how="left")

def format_number(n, prefix="", suffix=""):
    """Format large numbers with K/M suffixes."""
    if n >= 1e9:
        return f"{prefix}{n/1e9:.1f}B{suffix}"
    elif n >= 1e6:
        return f"{prefix}{n/1e6:.1f}M{suffix}"
    elif n >= 1e3:
        return f"{prefix}{n/1e3:.1f}K{suffix}"
    return f"{prefix}{n:.0f}{suffix}"

def get_top_items(df_detail, region_code, group_col, value_col, n=5):
    """Get top N items by value for a region."""
    region_data = df_detail[df_detail["nuts2_region"] == region_code]
    if region_data.empty:
        return []
    grouped = region_data.groupby(group_col)[value_col].sum().nlargest(n)
    return [(name, val) for name, val in grouped.items()]

def create_map(df, df_detail, selected_clusters):
    """Create Folium map with NUTS2 region markers. Shows all regions but grays out non-selected clusters."""
    # Create map centered on Europe
    m = folium.Map(
        location=[50, 10],
        zoom_start=4,
        tiles="CartoDB positron"
    )

    # Calculate radius scaling across ALL data
    max_waste = df["total_waste_tonnes"].max()
    min_waste = df["total_waste_tonnes"].min()

    # Determine if we're filtering (not all clusters selected)
    all_clusters = set(df["geo_cluster"].unique())
    is_filtering = selected_clusters and set(selected_clusters) != all_clusters

    for _, row in df.iterrows():
        cluster = int(row["geo_cluster"])
        is_selected = not selected_clusters or cluster in selected_clusters

        # Scale radius between 5 and 20
        if max_waste > min_waste:
            scaled_radius = 5 + 15 * (row["total_waste_tonnes"] - min_waste) / (max_waste - min_waste)
        else:
            scaled_radius = 10

        # Get cluster color - gray out if not selected
        if is_selected:
            color = CLUSTER_COLORS[cluster % len(CLUSTER_COLORS)]
            fill_opacity = 0.6
        else:
            color = "#cccccc"
            fill_opacity = 0.3
            scaled_radius = scaled_radius * 0.7  # Make grayed out markers smaller

        # Get top 5 NACE activities and waste types for this region
        top_nace = get_top_items(df_detail, row["nuts2_region"], "nace_activity", "allocated_waste_tonnes", 5)
        top_waste = get_top_items(df_detail, row["nuts2_region"], "waste_description", "allocated_waste_tonnes", 5)

        # Build NACE list HTML
        nace_html = ""
        if top_nace:
            nace_html = "<b>Top NACE activities:</b><br>"
            for name, val in top_nace:
                short_name = name[:25] + "..." if len(name) > 25 else name
                nace_html += f"• {short_name}: {format_number(val, suffix=' t')}<br>"

        # Build waste list HTML
        waste_html = ""
        if top_waste:
            waste_html = "<b>Top waste types:</b><br>"
            for name, val in top_waste:
                short_name = name[:25] + "..." if len(name) > 25 else name
                waste_html += f"• {short_name}: {format_number(val, suffix=' t')}<br>"

        # Create popup content
        popup_html = f"""
        <div style="font-family: sans-serif; width: 280px; font-size: 12px;">
            <b style="font-size: 14px;">{row['nuts2_name']}</b> ({row['nuts2_region']})<br>
            <hr style="margin: 5px 0;">
            <b>Cluster:</b> {cluster} &nbsp;|&nbsp;
            <b>Waste:</b> {format_number(row['total_waste_tonnes'], suffix=' t')} &nbsp;|&nbsp;
            <b>Economic:</b> {format_number(row['total_economic_eur'], prefix='€')}<br>
            <hr style="margin: 5px 0;">
            {nace_html}
            <hr style="margin: 5px 0;">
            {waste_html}
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=scaled_radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=fill_opacity,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['nuts2_name']} (Cluster {cluster}) - Click to select"
        ).add_to(m)

    # Return filtered df for stats (only selected clusters)
    if selected_clusters:
        df_filtered = df[df["geo_cluster"].isin(selected_clusters)]
    else:
        df_filtered = df

    return m, df_filtered

def find_cluster_by_location(df, lat, lon, tolerance=0.5):
    """Find the cluster of a region by its approximate lat/lon."""
    for _, row in df.iterrows():
        if abs(row["lat"] - lat) < tolerance and abs(row["lon"] - lon) < tolerance:
            return int(row["geo_cluster"])
    return None

# Main app
st.title("🗺️ NUTS2 Geographical Waste Hotspots")
st.markdown("Interactive visualization of waste generation clusters across European NUTS2 regions.")

# Load base data
df = load_data()

# Sidebar
st.sidebar.header("Data & Filters")

# Dataset toggle
data_source = st.sidebar.radio(
    "Dataset",
    ["High-value recyclables", "All waste types"],
    help="High-value: metals, paper, glass (37K rows, faster)\nAll: includes combustion, sludges, minerals (192K rows)"
)

# Load detail data based on selection
if data_source == "All waste types":
    df_detail = load_full_detail_data()
    st.sidebar.caption("Loading all 192K records...")
else:
    df_detail = load_high_value_data()

# Initialize session state for selected clusters
all_clusters = sorted(df["geo_cluster"].unique())
if "selected_clusters" not in st.session_state:
    st.session_state.selected_clusters = list(all_clusters)
if "last_processed_click" not in st.session_state:
    st.session_state.last_processed_click = None

st.sidebar.markdown("---")

# Cluster selection with session state sync
def on_cluster_change():
    """Callback when multiselect changes."""
    st.session_state.selected_clusters = st.session_state.cluster_multiselect

selected_clusters = st.sidebar.multiselect(
    "Select Geo Clusters",
    options=all_clusters,
    default=st.session_state.selected_clusters,
    format_func=lambda x: f"Cluster {x}",
    key="cluster_multiselect",
    on_change=on_cluster_change
)

# Buttons for quick selection
col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("Select All", use_container_width=True):
        st.session_state.selected_clusters = list(all_clusters)
        st.rerun()
with col_btn2:
    if st.button("Clear All", use_container_width=True):
        st.session_state.selected_clusters = []
        st.rerun()

# Country filter
all_countries = sorted(df["country_code"].unique())
selected_countries = st.sidebar.multiselect(
    "Filter by Country",
    options=all_countries,
    default=[]
)

# Apply country filter
if selected_countries:
    df = df[df["country_code"].isin(selected_countries)]

# Sidebar stats
st.sidebar.markdown("---")
st.sidebar.subheader("Summary Statistics")

# Create map
m, df_filtered = create_map(df, df_detail, selected_clusters)

# Show stats
st.sidebar.metric("Regions shown", len(df_filtered))
st.sidebar.metric("Total waste", format_number(df_filtered["total_waste_tonnes"].sum(), suffix=" t"))
st.sidebar.metric("Economic value", format_number(df_filtered["total_economic_eur"].sum(), prefix="€"))

# Legend in sidebar - show all clusters with selection state
st.sidebar.markdown("---")
st.sidebar.subheader("Cluster Legend")
for cluster in sorted(df["geo_cluster"].unique()):
    is_selected = cluster in st.session_state.selected_clusters
    color = CLUSTER_COLORS[int(cluster) % len(CLUSTER_COLORS)] if is_selected else "#cccccc"
    count = len(df[df["geo_cluster"] == cluster])
    selected_marker = "●" if is_selected else "○"
    st.sidebar.markdown(
        f'<span style="color:{color}; font-size:20px;">{selected_marker}</span> Cluster {cluster} ({count} regions)',
        unsafe_allow_html=True
    )

# Display map
col1, col2 = st.columns([3, 1])

with col1:
    st.caption("Click on a region to toggle its cluster selection")
    map_data = st_folium(m, width=800, height=600, returned_objects=["last_object_clicked"])

    # Handle map clicks - toggle cluster selection
    if map_data and map_data.get("last_object_clicked"):
        clicked = map_data["last_object_clicked"]
        if clicked and "lat" in clicked and "lng" in clicked:
            click_key = (round(clicked["lat"], 4), round(clicked["lng"], 4))
            # Only process if this is a new click
            if click_key != st.session_state.last_processed_click:
                clicked_cluster = find_cluster_by_location(df, clicked["lat"], clicked["lng"])
                if clicked_cluster is not None:
                    st.session_state.last_processed_click = click_key
                    current_selection = list(st.session_state.selected_clusters)
                    if clicked_cluster in current_selection:
                        # If already selected and there are other selections, remove it
                        if len(current_selection) > 1:
                            current_selection.remove(clicked_cluster)
                    else:
                        # Add to selection
                        current_selection.append(clicked_cluster)
                    st.session_state.selected_clusters = current_selection
                    st.rerun()

with col2:
    with st.expander("Top Regions by Waste", expanded=True):
        top_regions = df_filtered.nlargest(10, "total_waste_tonnes")[
            ["nuts2_name", "country_code", "total_waste_tonnes", "geo_cluster"]
        ].copy()
        top_regions["total_waste_tonnes"] = top_regions["total_waste_tonnes"].apply(
            lambda x: format_number(x, suffix=" t")
        )
        top_regions.columns = ["Region", "Country", "Waste", "Cluster"]
        st.dataframe(top_regions, hide_index=True, use_container_width=True)

# Detailed cluster data section
st.markdown("---")
st.subheader("Detailed Waste Data by Cluster")

# Filter detail data by selected clusters and countries
df_detail_filtered = df_detail.copy()
if selected_clusters:
    df_detail_filtered = df_detail_filtered[df_detail_filtered["geo_cluster"].isin(selected_clusters)]
if selected_countries:
    df_detail_filtered = df_detail_filtered[df_detail_filtered["country_code"].isin(selected_countries)]

# Region selector for drilling down
available_regions = sorted(df_detail_filtered["nuts2_name"].unique())
selected_regions = st.multiselect(
    "Filter by specific regions (leave empty for all)",
    options=available_regions,
    default=[]
)

if selected_regions:
    df_detail_filtered = df_detail_filtered[df_detail_filtered["nuts2_name"].isin(selected_regions)]

# Waste type exclusion filter
with st.expander("Exclude Waste Types", expanded=False):
    # Identify aggregated waste codes (subtotals)
    AGGREGATE_CODES = ["W01-05", "W06", "W06_07A", "W077_08", "W09", "W091_092",
                       "W10", "W126_127", "W128_13", "W12A", "W12B"]

    # Get all unique waste codes
    all_waste_codes = sorted(df_detail_filtered["waste"].unique()) if "waste" in df_detail_filtered.columns else []

    # Quick toggle for aggregates
    exclude_aggregates = st.checkbox(
        "Exclude aggregated/subtotal waste types",
        value=False,
        help="Removes subtotals like 'Chemical wastes (subtotal)', 'Recyclable wastes (subtotal)', etc."
    )

    # Manual exclusion
    excluded_wastes = st.multiselect(
        "Manually exclude specific waste codes",
        options=all_waste_codes,
        default=[],
        help="Select waste codes to exclude from all calculations"
    )

    # Apply exclusions
    if exclude_aggregates:
        excluded_wastes = list(set(excluded_wastes + [c for c in AGGREGATE_CODES if c in all_waste_codes]))

    if excluded_wastes:
        df_detail_filtered = df_detail_filtered[~df_detail_filtered["waste"].isin(excluded_wastes)]
        st.caption(f"Excluding {len(excluded_wastes)} waste types: {', '.join(excluded_wastes[:5])}{'...' if len(excluded_wastes) > 5 else ''}")

# Sort by economic potential and display
df_detail_display = df_detail_filtered.sort_values("economic_potential_eur", ascending=False)

# Summary metrics for selected data
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Records", f"{len(df_detail_display):,}")
with col_m2:
    st.metric("Total Waste", format_number(df_detail_display["allocated_waste_tonnes"].sum(), suffix=" t"))
with col_m3:
    st.metric("Economic Potential", format_number(df_detail_display["economic_potential_eur"].sum(), prefix="€"))
with col_m4:
    st.metric("Unique Regions", df_detail_display["nuts2_region"].nunique())

# Top NACE and Waste Type summaries side by side
with st.expander("NACE Activities & Waste Types", expanded=True):
    # Controls row: toggles and sort option
    col_toggle1, col_toggle2, col_sort = st.columns(3)
    with col_toggle1:
        show_nace_table = st.checkbox("Show NACE table", value=True, key="show_nace")
    with col_toggle2:
        show_waste_table = st.checkbox("Show Waste table", value=True, key="show_waste")
    with col_sort:
        sort_by = st.radio("Sort by", ["Waste (tonnes)", "Economic potential"], horizontal=True, key="sort_tables")

    sort_col = "allocated_waste_tonnes" if sort_by == "Waste (tonnes)" else "economic_potential_eur"

    col_nace, col_waste = st.columns(2)

    # Get top 20 NACE activities for display and selection (needed for NACE selector even if table hidden)
    top_nace_data = df_detail_filtered.groupby("nace_activity").agg({
        "allocated_waste_tonnes": "sum",
        "economic_potential_eur": "sum"
    }).nlargest(20, sort_col).reset_index()

    # NACE activity selector (always visible)
    nace_options = ["All NACE activities"] + top_nace_data["nace_activity"].tolist()
    selected_nace = st.selectbox(
        "Select NACE to see waste breakdown",
        options=nace_options,
        key="nace_selector"
    )

    with col_nace:
        if show_nace_table:
            sort_label = "waste" if sort_by == "Waste (tonnes)" else "economic potential"
            st.markdown(f"**Top 20 NACE Activities (by {sort_label})**")
            # Display top 20 NACE summary
            top_nace_summary = top_nace_data.copy()
            top_nace_summary["allocated_waste_tonnes"] = top_nace_summary["allocated_waste_tonnes"].apply(
                lambda x: format_number(x, suffix=" t")
            )
            top_nace_summary["economic_potential_eur"] = top_nace_summary["economic_potential_eur"].apply(
                lambda x: format_number(x, prefix="€")
            )
            top_nace_summary.columns = ["NACE Activity", "Waste", "Economic Potential"]
            st.dataframe(top_nace_summary, hide_index=True, use_container_width=True, height=400)

    with col_waste:
        if show_waste_table:
            sort_label = "volume" if sort_by == "Waste (tonnes)" else "economic potential"
            # Show waste breakdown based on NACE selection
            if selected_nace and selected_nace != "All NACE activities":
                st.markdown(f"**Top 10 Waste Types for: {selected_nace[:30]}{'...' if len(selected_nace) > 30 else ''} (by {sort_label})**")
                nace_waste_data = df_detail_filtered[df_detail_filtered["nace_activity"] == selected_nace]
                top_waste_summary = nace_waste_data.groupby("waste_description").agg({
                    "allocated_waste_tonnes": "sum",
                    "economic_potential_eur": "sum"
                }).nlargest(10, sort_col).reset_index()
            else:
                st.markdown(f"**Top 10 Waste Types (by {sort_label})**")
                top_waste_summary = df_detail_filtered.groupby("waste_description").agg({
                    "allocated_waste_tonnes": "sum",
                    "economic_potential_eur": "sum"
                }).nlargest(10, sort_col).reset_index()
            top_waste_summary["allocated_waste_tonnes"] = top_waste_summary["allocated_waste_tonnes"].apply(
                lambda x: format_number(x, suffix=" t")
            )
            top_waste_summary["economic_potential_eur"] = top_waste_summary["economic_potential_eur"].apply(
                lambda x: format_number(x, prefix="€")
            )
            top_waste_summary.columns = ["Waste Type", "Waste", "Economic Potential"]
            st.dataframe(top_waste_summary, hide_index=True, use_container_width=True, height=400)

with st.expander("All Records", expanded=False):
    records_sort = st.radio(
        "Sort records by",
        ["Economic potential", "Waste (tonnes)"],
        horizontal=True,
        key="records_sort"
    )
    records_sort_col = "economic_potential_eur" if records_sort == "Economic potential" else "allocated_waste_tonnes"
    df_detail_sorted = df_detail_filtered.sort_values(records_sort_col, ascending=False)

    # Display detailed table with formatted numbers
    df_detail_table = df_detail_sorted[[
        "nuts2_name", "country_code", "nace_activity", "waste_description",
        "allocated_waste_tonnes", "economic_potential_eur", "geo_cluster"
    ]].copy()
    df_detail_table["allocated_waste_tonnes"] = df_detail_table["allocated_waste_tonnes"].apply(
        lambda x: format_number(x, suffix=" t")
    )
    df_detail_table["economic_potential_eur"] = df_detail_table["economic_potential_eur"].apply(
        lambda x: format_number(x, prefix="€")
    )
    df_detail_table.columns = ["Region", "Country", "NACE Activity", "Waste Type",
                               "Waste", "Economic Potential", "Cluster"]
    st.dataframe(df_detail_table, hide_index=True, use_container_width=True, height=400)

# Aggregated view by region
with st.expander("View Aggregated by Region"):
    agg_sort = st.radio(
        "Sort by",
        ["Economic potential", "Waste (tonnes)"],
        horizontal=True,
        key="agg_sort"
    )
    agg_sort_col = "economic_potential_eur" if agg_sort == "Economic potential" else "allocated_waste_tonnes"

    agg_by_region = df_detail_filtered.groupby(["nuts2_name", "country_code", "geo_cluster"]).agg({
        "allocated_waste_tonnes": "sum",
        "economic_potential_eur": "sum",
        "nace_activity": "nunique",
        "waste_description": "nunique"
    }).reset_index().sort_values(agg_sort_col, ascending=False)

    agg_by_region["allocated_waste_tonnes"] = agg_by_region["allocated_waste_tonnes"].apply(
        lambda x: format_number(x, suffix=" t")
    )
    agg_by_region["economic_potential_eur"] = agg_by_region["economic_potential_eur"].apply(
        lambda x: format_number(x, prefix="€")
    )
    agg_by_region.columns = ["Region", "Country", "Cluster", "Total Waste",
                             "Economic Potential", "NACE Activities", "Waste Types"]
    st.dataframe(agg_by_region, hide_index=True, use_container_width=True)
