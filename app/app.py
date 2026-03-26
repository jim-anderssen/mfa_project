"""
Facility Waste Cluster Visualizer
Interactive map showing industrial facilities colored by waste profile clusters.
"""

import sys
import streamlit as st
import pandas as pd
import numpy as np
import re
import folium
from streamlit_folium import st_folium
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from mappings.ewc_stat import EWC_STAT_CODES, get_ewc_description
from mappings.ied_nace import get_ied_description as get_ied_detailed_description

# Page config
st.set_page_config(page_title="Facility Waste Clusters", page_icon="🏭", layout="wide")

# Color palette for clusters (12 colors for clusters 0-11)
CLUSTER_COLORS = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#ffff33",
    "#a65628",
    "#f781bf",
    "#17becf",
    "#66c2a5",
    "#fc8d62",
    "#8da0cb",
]


@st.cache_data
def load_facility_clusters():
    """Load facility cluster data."""
    data_path = (
        Path(__file__).parent.parent / "data" / "processed" / "facility_clusters.csv"
    )
    return pd.read_csv(data_path)


@st.cache_data
def load_facility_cluster_summary():
    """Load cluster summary data."""
    data_path = (
        Path(__file__).parent.parent
        / "data"
        / "processed"
        / "facility_cluster_summary.csv"
    )
    return pd.read_csv(data_path)


@st.cache_data
def load_facility_waste_allocated():
    """Load detailed waste allocation per facility."""
    data_path = (
        Path(__file__).parent.parent
        / "data"
        / "processed"
        / "facility_waste_allocated.csv"
    )
    return pd.read_csv(data_path)


@st.cache_data
def load_facility_waste_classified():
    """Load facility waste with technology classification."""
    data_path = (
        Path(__file__).parent.parent
        / "data"
        / "processed"
        / "facility_waste_classified_all_20260204.csv"
    )
    return pd.read_csv(data_path)


@st.cache_data
def load_nace_lookup():
    """Load NACE Rev2 descriptions including groups and classes."""
    path = (
        Path(__file__).parent.parent
        / "data/processed/lookuptables/nace_rev2_complete.csv"
    )
    df = pd.read_csv(path)
    # Build combined lookup: classes + groups + divisions
    lookup = {}
    # Add classes (most specific: 24.10)
    lookup.update(dict(zip(df["class"].astype(str), df["class_name"])))
    # Add groups (e.g., 17.1, 35.1)
    groups = df[["group", "group_name"]].drop_duplicates()
    lookup.update(dict(zip(groups["group"].astype(str), groups["group_name"])))
    # Add divisions (e.g., 17, 35)
    divisions = df[["division", "division_name"]].drop_duplicates()
    lookup.update(
        dict(zip(divisions["division"].astype(str), divisions["division_name"]))
    )
    return lookup


def get_nace_description(nace_code: str, nace_lookup: dict) -> str:
    """Get description for a NACE code, handling C prefix and format variations."""
    if pd.isna(nace_code):
        return "Unknown"
    # Strip C prefix (e.g., "C24.1" -> "24.1")
    code = str(nace_code).lstrip("C")
    # Try exact match
    if code in nace_lookup:
        return nace_lookup[code]
    # Try adding trailing zero (e.g., "24.1" -> "24.10")
    if "." in code:
        parts = code.split(".")
        if len(parts) == 2 and len(parts[1]) == 1:
            code_with_zero = parts[0] + "." + parts[1] + "0"
            if code_with_zero in nace_lookup:
                return nace_lookup[code_with_zero]
        # Try removing trailing zero (e.g., "24.10" -> "24.1")
        elif len(parts) == 2 and len(parts[1]) == 2 and parts[1].endswith("0"):
            code_short = parts[0] + "." + parts[1][0]
            if code_short in nace_lookup:
                return nace_lookup[code_short]
    return f"Unknown: {nace_code}"


def fix_nace_descriptions(df: pd.DataFrame, nace_lookup: dict) -> pd.DataFrame:
    """Fix nace_description column using lookup table."""
    df = df.copy()
    if "nace_description" in df.columns and "nace" in df.columns:
        df["nace_description"] = df["nace"].apply(
            lambda x: get_nace_description(x, nace_lookup)
        )
    return df


def compute_cluster_top_waste_types(
    df_classified: pd.DataFrame, df_clusters: pd.DataFrame
) -> dict:
    """Compute top waste types per cluster from facility allocation data, excluding aggregates."""
    exclude_codes = {"TOTAL", "TOT_X_MIN", "PRIM", "SEC"}

    # Get allocation columns
    alloc_cols = [
        col
        for col in df_classified.columns
        if col.startswith("alloc_") and col.endswith("_tonnes")
    ]

    # Merge cluster info
    df_merged = df_classified.merge(
        df_clusters[["facility_id", "cluster"]], on="facility_id", how="inner"
    )

    result = {}
    for cluster_id in df_merged["cluster"].unique():
        cluster_data = df_merged[df_merged["cluster"] == cluster_id]

        # Sum allocations by waste type
        waste_totals = {}
        for col in alloc_cols:
            waste_code = col.replace("alloc_", "").replace("_tonnes", "")
            if waste_code not in exclude_codes:
                total = cluster_data[col].sum()
                if total > 0:
                    waste_totals[waste_code] = total

        # Sort and get top 3
        sorted_wastes = sorted(waste_totals.items(), key=lambda x: x[1], reverse=True)[
            :3
        ]

        if sorted_wastes:
            grand_total = sum(v for v in waste_totals.values())
            formatted = ", ".join(
                f"{code}({amount / grand_total * 100:.1f}%)"
                for code, amount in sorted_wastes
            )
            result[cluster_id] = formatted
        else:
            result[cluster_id] = "N/A"

    return result


def get_waste_descriptions_from_top_types(top_waste_str: str) -> str:
    """Get descriptions for waste codes in top_waste_types string."""
    if pd.isna(top_waste_str) or top_waste_str == "N/A":
        return "N/A"

    # Parse codes like "W061(30%), W124(25%)"
    pattern = r"(\w+)\("
    codes = re.findall(pattern, top_waste_str)

    descriptions = []
    for code in codes[:3]:
        desc = EWC_STAT_CODES.get(code, f"Unknown code: {code}")
        descriptions.append(desc)

    return "; ".join(descriptions)


def format_number(n, prefix="", suffix=""):
    """Format large numbers with K/M suffixes."""
    if pd.isna(n):
        return "N/A"
    if n >= 1e9:
        return f"{prefix}{n / 1e9:.1f}B{suffix}"
    elif n >= 1e6:
        return f"{prefix}{n / 1e6:.1f}M{suffix}"
    elif n >= 1e3:
        return f"{prefix}{n / 1e3:.1f}K{suffix}"
    return f"{prefix}{n:.0f}{suffix}"


def get_item_color(item, color_by, all_items):
    """Get color for a cluster or geo_subgroup."""
    if color_by == "cluster":
        return CLUSTER_COLORS[int(item) % len(CLUSTER_COLORS)]
    else:
        # For geo_subgroups, hash to a color index
        idx = hash(str(item)) % len(CLUSTER_COLORS)
        return CLUSTER_COLORS[idx]


def get_top_waste_codes(row, n=2):
    """Get top N individual waste codes and their amounts for a facility."""
    # Exclude aggregate codes
    exclude_codes = ["PRIM", "SEC", "TOTAL", "TOT_X_MIN"]

    alloc_cols = [
        col for col in row.index if col.startswith("alloc_") and col.endswith("_tonnes")
    ]
    waste_amounts = []

    for col in alloc_cols:
        if pd.notna(row[col]) and row[col] > 0:
            # Extract waste code from column name (e.g., 'alloc_W124_tonnes' -> 'W124')
            waste_code = col.replace("alloc_", "").replace("_tonnes", "")

            # Skip aggregate codes, only include individual waste codes
            if waste_code not in exclude_codes:
                waste_amounts.append((waste_code, row[col]))

    # Sort by amount descending and return top N
    waste_amounts.sort(key=lambda x: x[1], reverse=True)
    return waste_amounts[:n]


def create_facility_map(df, selected_items, color_by, selected_subgroups=None):
    """Create Folium map with facility markers.

    Visibility rules:
    - No cluster selected: all facilities colored
    - Cluster selected, no subgroup filter: cluster facilities colored, rest hidden
    - Cluster + subgroup filter: cluster facilities visible; subgroup ones colored,
      rest of cluster grayed out; non-cluster hidden
    """
    if selected_subgroups is None:
        selected_subgroups = []

    # Center on Nordic region
    m = folium.Map(location=[59, 15], zoom_start=5, tiles="CartoDB positron")

    # Get unique items for coloring
    all_items = df[color_by].unique()

    # Calculate marker sizes based on log of total_tonnes
    df_valid = df[df["total_tonnes"] > 0].copy()
    if len(df_valid) > 0:
        log_tonnes = np.log10(df_valid["total_tonnes"].clip(lower=1))
        min_log = log_tonnes.min()
        max_log = log_tonnes.max()
    else:
        min_log, max_log = 0, 1

    has_cluster_selection = len(selected_items) > 0
    has_subgroup_filter = len(selected_subgroups) > 0

    for _, row in df.iterrows():
        item_value = row[color_by]
        in_selected_cluster = not has_cluster_selection or item_value in selected_items
        in_selected_subgroup = row["geo_subgroup"] in selected_subgroups

        # Skip facilities not in the selected cluster
        if has_cluster_selection and not in_selected_cluster:
            continue

        # Calculate radius from log scale (5-15 range)
        if row["total_tonnes"] > 0 and max_log > min_log:
            log_val = np.log10(max(row["total_tonnes"], 1))
            scaled_radius = 5 + 10 * (log_val - min_log) / (max_log - min_log)
        else:
            scaled_radius = 5

        # Determine color and opacity
        if has_subgroup_filter:
            # Subgroup filter active: color only matching facilities
            if in_selected_subgroup:
                color = get_item_color(item_value, color_by, all_items)
                fill_opacity = 0.7
            else:
                color = "#cccccc"
                fill_opacity = 0.3
                scaled_radius = scaled_radius * 0.7
        elif has_cluster_selection:
            # Cluster selected, no subgroup filter: all in cluster colored
            color = get_item_color(item_value, color_by, all_items)
            fill_opacity = 0.7
        else:
            # Nothing selected: all colored
            color = get_item_color(item_value, color_by, all_items)
            fill_opacity = 0.7

        # Build allocated waste breakdown
        waste_html = ""
        if (
            pd.notna(row.get("alloc_TOTAL_tonnes"))
            and row.get("alloc_TOTAL_tonnes", 0) > 0
        ):
            total_alloc = format_number(row["alloc_TOTAL_tonnes"], suffix=" t")
            waste_html = f"<b>Total allocated waste:</b> {total_alloc}<br>"

            # Get top 2 waste codes
            top_wastes = get_top_waste_codes(row, n=2)
            if len(top_wastes) > 0:
                waste_code, amount = top_wastes[0]
                waste_html += f"<b>Largest waste code ({waste_code}):</b> {format_number(amount, suffix=' t')}<br>"
            if len(top_wastes) > 1:
                waste_code, amount = top_wastes[1]
                waste_html += f"<b>2nd largest ({waste_code}):</b> {format_number(amount, suffix=' t')}<br>"
        else:
            waste_html = f"<b>Total waste:</b> {format_number(row['total_tonnes'], suffix=' t')}<br>"

        # Build technology and estimated waste section
        tech_html = ""
        if pd.notna(row.get("technology_regime")) or any(
            [
                pd.notna(row.get("estimated_production_min_t")),
                pd.notna(row.get("estimated_slag_min_t")),
                pd.notna(row.get("estimated_dust_min_t")),
            ]
        ):
            tech_html = "<hr style='margin: 5px 0;'>"
            if pd.notna(row.get("technology_regime")):
                tech_html += f"<b>Technology:</b> {row['technology_regime']}<br>"

            # Show estimated waste ranges if available
            if pd.notna(row.get("estimated_production_min_t")) and pd.notna(
                row.get("estimated_production_max_t")
            ):
                prod_min = format_number(row["estimated_production_min_t"], suffix=" t")
                prod_max = format_number(row["estimated_production_max_t"], suffix=" t")
                tech_html += f"<b>Est. Generated waste:</b> {prod_min} - {prod_max}<br>"

            if pd.notna(row.get("estimated_slag_min_t")) and pd.notna(
                row.get("estimated_slag_max_t")
            ):
                slag_min = format_number(row["estimated_slag_min_t"], suffix=" t")
                slag_max = format_number(row["estimated_slag_max_t"], suffix=" t")
                tech_html += f"<b>Est. Slag:</b> {slag_min} - {slag_max}<br>"

            if pd.notna(row.get("estimated_dust_min_t")) and pd.notna(
                row.get("estimated_dust_max_t")
            ):
                dust_min = format_number(row["estimated_dust_min_t"], suffix=" t")
                dust_max = format_number(row["estimated_dust_max_t"], suffix=" t")
                tech_html += f"<b>Est. Dust:</b> {dust_min} - {dust_max}<br>"
        else:
            tech_html = (
                "<hr style='margin: 5px 0;'><b>Technology/Estimates:</b> N/A<br>"
            )

        # Recovery maturity indicator
        recovery_html = ""
        if pd.notna(row.get("recovery_maturity_indicator")):
            rmi = row["recovery_maturity_indicator"]
            recovery_html = f"<hr style='margin: 5px 0;'><b>Recovery Maturity:</b> {rmi:.1f}"

        # Create popup content
        popup_html = f"""
        <div style="font-family: sans-serif; width: 280px; font-size: 12px;">
            <b style="font-size: 14px;">{row["facility_name"]}</b><br>
            <span style="color: #666;">{row["country"]}</span>
            <hr style="margin: 5px 0;">
            <b>NACE:</b> {row["nace"]} - {row["nace_description"]}<br>
            <b>IED:</b> {row["ied_activity"]} - {row["ied_description"]}<br>
            <b>Cluster:</b> {row["cluster"]} &nbsp;|&nbsp;
            <b>Subgroup:</b> {row["geo_subgroup"]}<br>
            <hr style="margin: 5px 0;">
            {tech_html}
            <hr style="margin: 5px 0;">
            {waste_html}
            {recovery_html}
        </div>
        """

        tooltip_text = f"{row['facility_name']} (Cluster: {row['cluster']}, Subgroup: {row['geo_subgroup']})"

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=scaled_radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=fill_opacity,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=tooltip_text,
        ).add_to(m)

    return m


def find_item_by_location(df, lat, lon, color_by, tolerance=0.3):
    """Find the cluster/subgroup of a facility by its approximate lat/lon."""
    for _, row in df.iterrows():
        if abs(row["lat"] - lat) < tolerance and abs(row["lon"] - lon) < tolerance:
            return row[color_by]
    return None


# Initialize session state
if "selected_items" not in st.session_state:
    st.session_state.selected_items = []
if "color_by" not in st.session_state:
    st.session_state.color_by = "cluster"
if "last_processed_click" not in st.session_state:
    st.session_state.last_processed_click = None
if "selected_facility" not in st.session_state:
    st.session_state.selected_facility = None

# Main app
st.title("🏭 Facility Waste Clusters")
st.markdown(
    "Interactive visualization of industrial facility waste profiles across Nordic countries."
)

# Load data
df = load_facility_clusters()
df_summary = load_facility_cluster_summary()
df_waste = load_facility_waste_allocated()
df_classified = load_facility_waste_classified()
nace_lookup = load_nace_lookup()

# Fix NACE descriptions using lookup table
df = fix_nace_descriptions(df, nace_lookup)

# Merge classified data with facility clusters to get technology and estimated waste info
tech_cols = [
    "facility_id",
    "technology_regime",
    "classification_confidence",
    "estimated_production_min_t",
    "estimated_production_max_t",
    "estimated_slag_min_t",
    "estimated_slag_max_t",
    "estimated_dust_min_t",
    "estimated_dust_max_t",
    # recovery_maturity_indicator already exists in facility_clusters.csv
]

# Get all allocation columns
alloc_cols = [
    col
    for col in df_classified.columns
    if col.startswith("alloc_") and col.endswith("_tonnes")
]
all_cols = tech_cols + alloc_cols

df_tech = (
    df_classified[all_cols].copy()
    if all(col in df_classified.columns for col in all_cols)
    else pd.DataFrame()
)

if not df_tech.empty:
    df = df.merge(df_tech, on="facility_id", how="left")

# Sidebar
st.sidebar.header("Filters & Options")

# Color by toggle
color_by = st.sidebar.radio(
    "Color by",
    ["cluster", "geo_subgroup"],
    format_func=lambda x: "Cluster" if x == "cluster" else "Geo Subgroup",
    key="color_by_radio",
)

# Update session state if color_by changed
if color_by != st.session_state.color_by:
    st.session_state.color_by = color_by
    st.session_state.selected_items = []  # Reset selection when switching

# Get all unique items for current color_by
all_items = sorted(
    df[color_by].unique(),
    key=lambda x: (str(x).split()[0] if isinstance(x, str) else x),
)


# Item selection
def on_item_change():
    """Callback when multiselect changes."""
    st.session_state.selected_items = st.session_state.item_multiselect


selected_items = st.sidebar.multiselect(
    f"Select {color_by.replace('_', ' ').title()}s",
    options=all_items,
    default=st.session_state.selected_items,
    format_func=lambda x: f"Cluster {x}" if color_by == "cluster" else str(x),
    key="item_multiselect",
    on_change=on_item_change,
)

# Quick buttons
col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("Select All", use_container_width=True):
        st.session_state.selected_items = list(all_items)
        st.rerun()
with col_btn2:
    if st.button("Clear All", use_container_width=True):
        st.session_state.selected_items = []
        st.rerun()

st.sidebar.markdown("---")

# Geo subgroup filter
all_subgroups = sorted(
    df["geo_subgroup"].unique(),
    key=lambda x: (str(x).split()[0] if isinstance(x, str) else x),
)
selected_subgroups = st.sidebar.multiselect(
    "Filter by Geo Subgroup", options=all_subgroups, default=[]
)

# Country filter
all_countries = sorted(df["country"].unique())
selected_countries = st.sidebar.multiselect(
    "Filter by Country", options=all_countries, default=[]
)

# IED activity filter
# Get unique IED codes from facility data, use detailed descriptions from ied_nace mapping
ied_codes = df["ied_activity"].dropna().astype(str).unique()
ied_options = sorted(ied_codes)
ied_format_func = lambda x: f"{x} - {get_ied_detailed_description(x)}"
selected_ied = st.sidebar.multiselect(
    "Filter by IED Activity",
    options=ied_options,
    default=[],
    format_func=ied_format_func,
)

# Apply filters (geo subgroup filter is applied separately — it does not affect the map)
df_filtered = df.copy()
if selected_countries:
    df_filtered = df_filtered[df_filtered["country"].isin(selected_countries)]
if selected_ied:
    df_filtered = df_filtered[
        df_filtered["ied_activity"].astype(str).isin(selected_ied)
    ]

# Summary statistics
st.sidebar.markdown("---")
st.sidebar.subheader("Summary")

# Calculate stats based on selection
if selected_items:
    df_stats = df_filtered[df_filtered[color_by].isin(selected_items)]
else:
    df_stats = df_filtered

st.sidebar.metric("Facilities", len(df_stats))
st.sidebar.metric(
    "Total Waste", format_number(df_stats["total_tonnes"].sum(), suffix=" t")
)

# Legend
st.sidebar.markdown("---")
st.sidebar.subheader("Legend")

# Show legend for current color_by
legend_items = df_filtered[color_by].value_counts().sort_index()
for item in sorted(
    legend_items.index, key=lambda x: (str(x).split()[0] if isinstance(x, str) else x)
):
    is_selected = len(selected_items) == 0 or item in selected_items
    color = get_item_color(item, color_by, all_items) if is_selected else "#cccccc"
    count = legend_items[item]
    selected_marker = "●" if is_selected else "○"
    label = f"Cluster {item}" if color_by == "cluster" else str(item)
    st.sidebar.markdown(
        f'<span style="color:{color}; font-size:18px;">{selected_marker}</span> {label} ({count})',
        unsafe_allow_html=True,
    )

# Main content - Map and Top Facilities
col1, col2 = st.columns([3, 1])

with col1:
    st.caption("Click on a facility marker to toggle its cluster/subgroup selection")
    m = create_facility_map(df_filtered, selected_items, color_by, selected_subgroups)
    map_data = st_folium(
        m, width=800, height=550, returned_objects=["last_object_clicked"]
    )

    # Handle map clicks
    if map_data and map_data.get("last_object_clicked"):
        clicked = map_data["last_object_clicked"]
        if clicked and "lat" in clicked and "lng" in clicked:
            click_key = (round(clicked["lat"], 4), round(clicked["lng"], 4))
            if click_key != st.session_state.last_processed_click:
                clicked_item = find_item_by_location(
                    df_filtered, clicked["lat"], clicked["lng"], color_by
                )
                if clicked_item is not None:
                    st.session_state.last_processed_click = click_key
                    current_selection = list(st.session_state.selected_items)
                    if clicked_item in current_selection:
                        if len(current_selection) > 1:
                            current_selection.remove(clicked_item)
                    else:
                        current_selection.append(clicked_item)
                    st.session_state.selected_items = current_selection
                    st.rerun()

with col2:
    if color_by == "cluster" and len(selected_items) == 1:
        st.subheader(f"Geo Subgroups in Cluster {selected_items[0]}")
        cluster_data = df_filtered[df_filtered["cluster"] == selected_items[0]]
        subgroup_stats = (
            cluster_data.groupby("geo_subgroup")
            .agg({"facility_id": "count", "total_tonnes": "sum"})
            .reset_index()
        )
        subgroup_stats.columns = ["Subgroup", "Facilities", "Total Tonnes"]
        subgroup_stats = subgroup_stats.sort_values("Total Tonnes", ascending=False)
        subgroup_stats["Total Tonnes"] = subgroup_stats["Total Tonnes"].apply(
            lambda x: format_number(x, suffix=" t")
        )
        st.dataframe(
            subgroup_stats, hide_index=True, use_container_width=True, height=480
        )

# Build facilities_filtered: apply cluster/subgroup selection + geo subgroup filter
if selected_items:
    facilities_filtered = df_filtered[df_filtered[color_by].isin(selected_items)]
else:
    facilities_filtered = df_filtered

# Apply geo subgroup filter to facilities table
if selected_subgroups:
    facilities_filtered = facilities_filtered[
        facilities_filtered["geo_subgroup"].isin(selected_subgroups)
    ]


def render_facilities_table():
    """Render the facilities table."""
    st.markdown("---")

    # Determine table title
    if selected_subgroups:
        sg_label = ", ".join(str(s) for s in selected_subgroups)
        table_title = f"Facilities in Geo Subgroup {sg_label}"
    elif selected_items:
        if color_by == "cluster" and len(selected_items) == 1:
            table_title = f"Facilities in Cluster {selected_items[0]}"
        elif color_by == "geo_subgroup" and len(selected_items) == 1:
            table_title = f"Facilities in {selected_items[0]}"
        elif len(selected_items) > 1:
            table_title = (
                f"Facilities in Selected {color_by.replace('_', ' ').title()}s"
            )
        else:
            table_title = "Facilities in Selection"
    else:
        table_title = "Top 50 Facilities"

    st.subheader(table_title)

    n_fac = min(50, len(facilities_filtered))
    top_facilities = facilities_filtered.nlargest(n_fac, "total_tonnes")
    top_display = top_facilities[
        [
            "facility_name",
            "country",
            "nace",
            "nace_description",
            "ied_activity",
            "ied_description",
            "total_tonnes",
            "cluster",
            "geo_subgroup",
        ]
    ].copy()
    top_display["total_tonnes"] = top_display["total_tonnes"].apply(
        lambda x: format_number(x, suffix=" t")
    )
    top_display.columns = [
        "Facility Name",
        "Country",
        "NACE",
        "NACE Description",
        "IED Activity",
        "IED Description",
        "Total Tonnes",
        "Cluster",
        "Subgroup",
    ]
    st.dataframe(top_display, hide_index=True, use_container_width=True, height=400)


def render_cluster_summary():
    """Render the cluster/subgroup summary table."""
    st.markdown("---")
    st.subheader(f"{'Cluster' if color_by == 'cluster' else 'Geo Subgroup'} Summary")

    if color_by == "cluster":
        summary_display = df_summary.copy()
        summary_display = summary_display.sort_values("total_tonnes", ascending=False)
        summary_display["total_tonnes"] = summary_display["total_tonnes"].apply(
            lambda x: format_number(x, suffix=" t")
        )

        def fix_multi_nace_desc(nace_str):
            if pd.isna(nace_str):
                return "Unknown"
            codes = [c.strip() for c in str(nace_str).split(",")]
            descriptions = [get_nace_description(c, nace_lookup) for c in codes]
            return "; ".join(descriptions)

        summary_display["nace_description"] = summary_display["dominant_nace"].apply(
            fix_multi_nace_desc
        )

        cluster_waste_types = compute_cluster_top_waste_types(df_classified, df)
        summary_display["top_waste_types"] = summary_display["cluster"].map(
            cluster_waste_types
        )
        summary_display["waste_description"] = summary_display["top_waste_types"].apply(
            get_waste_descriptions_from_top_types
        )

        summary_cols = [
            "cluster",
            "n_facilities",
            "total_tonnes",
            "dominant_nace",
            "nace_description",
            "dominant_ied",
            "ied_description",
            "top_waste_types",
            "waste_description",
        ]
        summary_display = summary_display[summary_cols]
        summary_display.columns = [
            "Cluster",
            "Facilities",
            "Total Tonnes",
            "Dominant NACE",
            "NACE Description",
            "Dominant IED",
            "IED Description",
            "Top Waste Types",
            "Waste Description",
        ]
    else:
        subgroup_summary = (
            df_filtered.groupby("geo_subgroup")
            .agg(
                {
                    "facility_id": "count",
                    "total_tonnes": "sum",
                    "nace": lambda x: x.mode().iloc[0]
                    if len(x.mode()) > 0
                    else "N/A",
                    "nace_description": lambda x: x.mode().iloc[0]
                    if len(x.mode()) > 0
                    else "N/A",
                    "ied_activity": lambda x: x.mode().iloc[0]
                    if len(x.mode()) > 0
                    else "N/A",
                    "ied_description": lambda x: x.mode().iloc[0]
                    if len(x.mode()) > 0
                    else "N/A",
                }
            )
            .reset_index()
        )
        subgroup_summary = subgroup_summary.sort_values(
            "total_tonnes", ascending=False
        )
        subgroup_summary["total_tonnes"] = subgroup_summary["total_tonnes"].apply(
            lambda x: format_number(x, suffix=" t")
        )
        subgroup_summary.columns = [
            "Subgroup",
            "Facilities",
            "Total Tonnes",
            "Dominant NACE",
            "NACE Description",
            "Dominant IED",
            "IED Description",
        ]
        summary_display = subgroup_summary

    st.dataframe(
        summary_display, hide_index=True, use_container_width=True, height=300
    )


# Render in order: geo subgroup selected → facilities first, otherwise summary first
if selected_subgroups:
    render_facilities_table()
    render_cluster_summary()
else:
    render_cluster_summary()
    render_facilities_table()

# Facility Detail Section
st.markdown("---")
st.subheader("Facility Waste Breakdown")

# Facility selector from filtered facilities
facility_options = facilities_filtered.sort_values("total_tonnes", ascending=False)[
    "facility_name"
].unique()

selected_facility = st.selectbox(
    "Select a facility to view waste breakdown",
    options=[""] + list(facility_options),
    format_func=lambda x: "Choose a facility..." if x == "" else x,
)

if selected_facility:
    # Get waste breakdown for selected facility
    facility_id = df[df["facility_name"] == selected_facility]["facility_id"].iloc[0]
    facility_waste = df_waste[df_waste["facility_id"] == facility_id].copy()

    if len(facility_waste) > 0:
        # Show facility info
        facility_info = df[df["facility_id"] == facility_id].iloc[0]
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Country", facility_info["country"])
        with col_info2:
            st.metric("Cluster", facility_info["cluster"])
        with col_info3:
            st.metric(
                "Total Waste", format_number(facility_info["total_tonnes"], suffix=" t")
            )

        # Show waste breakdown table
        waste_display = facility_waste[["waste_type", "allocated_tonnes"]].copy()
        waste_display = waste_display.sort_values("allocated_tonnes", ascending=False)
        waste_display["allocated_tonnes"] = waste_display["allocated_tonnes"].apply(
            lambda x: format_number(x, suffix=" t")
        )
        waste_display.columns = ["Waste Type", "Allocated Tonnes"]
        st.dataframe(waste_display, hide_index=True, use_container_width=True)
    else:
        st.info("No detailed waste data available for this facility.")
