import os
import io

import altair as alt
import pandas as pd
import streamlit as st


# -------------------------------------------------
# Page setup
# -------------------------------------------------
st.set_page_config(
    page_title="Civic Indicators – Reporting Tool",
    layout="wide",
    page_icon="📊",
)

st.title("📊 Civic Indicators – Domain-based Reporting Tool")
st.markdown(
    """
    **Explore domain-based indicators over time.**
    
    Use the sidebar to filter data and customize the visualization.
    """
)


# -------------------------------------------------
# Embed info content (replacing info_content.py)
# -------------------------------------------------
# -------------------------------------------------
# Embed info content (replacing info_content.py)
# NOTE: Definitions are now loaded from 'Indicator_Definitions.xlsx'.
# -------------------------------------------------
variable_info_md = "" # Deprecated, keeping empty variable just in case until full cleanup

# -------------------------------------------------
# Load Indicator Definitions (External Excel)
# -------------------------------------------------
@st.cache_data
def load_definitions():
    """
    Loads schema and item descriptions from 'Indicator_Definitions.xlsx'.
    Returns:
        schema (dict): {Variable: {col: val, ...}}
        item_descs (dict): {Code: Description}
    """
    # Resolve path relative to this script file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_dir, "Indicator_Definitions.xlsx")
    
    # Check if file exists
    if not os.path.exists(filename):
        # Fallback: Try just the filename in CWD (useful if __file__ is weird in some envs)
        if os.path.exists("Indicator_Definitions.xlsx"):
            filename = "Indicator_Definitions.xlsx"
        else:
             return {}, {}

    try:
        # Load Schema
        df_schema = pd.read_excel(filename, sheet_name="Schema")
        df_schema["Variable"] = df_schema["Variable"].astype(str).str.strip()
        
        # Convert to dict keyed by Variable
        # orient='index' gives {index: {col: val}}, so we set index first
        schema = df_schema.set_index("Variable").to_dict(orient="index")

        # Load Items
        df_items = pd.read_excel(filename, sheet_name="Items")
        df_items["Code"] = df_items["Code"].astype(str).str.strip()
        df_items["Description"] = df_items["Description"].astype(str).str.strip()
        
        # Convert to dict {Code: Description}
        item_descs = dict(zip(df_items["Code"], df_items["Description"]))
        
        return schema, item_descs
        
    except Exception as e:
        return {}, {}

def get_schema_dict():
    """Wrapper to return schema dict from cached loader."""
    s, _ = load_definitions()
    return s

def get_item_descriptions():
    """Wrapper to return items dict from cached loader."""
    _, i = load_definitions()
    return i

# -------------------------------------------------
# Load & reshape data (ResultswithSE.xlsx style)
# -------------------------------------------------
@st.cache_data
def load_long_data(file_input, sheet: str = "Sheet1") -> pd.DataFrame:
    """
    Reads ResultswithSE.xlsx, where:
    - col 0: Domain
    - col 1: Question
    - cols 2+: numeric triplets with 3 header rows:
        row 1: Country
        row 2: Year
        row 3: 'Mean' / 'Standard Error of Mean' / 'Count'

    Returns one row per (Domain, Question, Country, Year) with:
        value = mean, se = standard error, n = sample size
    """
    try:
        # Read without header; we’ll build headers manually
        df = pd.read_excel(file_input, sheet_name=sheet, header=None)

        # Header rows for numeric columns (starting from column index 2)
        # Search for the header row containing "DOMAIN" in the first column
        header_idx = -1
        for i in range(min(20, len(df))):
            val = str(df.iloc[i, 0]).strip().upper()
            if val == "DOMAIN":
                header_idx = i
                break
        
        if header_idx == -1:
            # Fallback for flexibility: try to find "Standard Error" or "Count" in any row
            for i in range(min(20, len(df))):
                row_vals = df.iloc[i].astype(str).str.lower().tolist()
                if any("standard error" in x for x in row_vals) or any("count" in x for x in row_vals):
                    header_idx = i
                    break
        
        if header_idx < 2:
            st.error("Could not detect header rows (Country/Year/Stats) correctly.")
            return pd.DataFrame()

        # Define offsets relative to the main header row
        # Row [header_idx]: DOMAIN | Question | ... Stats ...
        # Row [header_idx - 1]: Years
        # Row [header_idx - 2]: Countries
        
        stat_row = df.iloc[header_idx, 2:]
        year_row = df.iloc[header_idx - 1, 2:]
        country_row = df.iloc[header_idx - 2, 2:]
        
        # Data starts immediately after the header row
        data = df.iloc[header_idx + 1:].reset_index(drop=True)
        data = data.rename(columns={0: "Domain", 1: "Question"})

        # Melt numeric columns
        value_cols = data.columns[2:]
        long = data.melt(
            id_vars=["Domain", "Question"],
            value_vars=value_cols,
            var_name="col_idx",
            value_name="raw_value",
        )

        # Map each column index to (Country, Year, stat label)
        def map_meta(col_idx):
            c = country_row[col_idx]
            y = year_row[col_idx]
            s = stat_row[col_idx]
            return c, y, s

        meta = long["col_idx"].apply(map_meta)
        meta_df = pd.DataFrame(meta.tolist(), columns=["Country", "Year", "stat_label"])
        long = pd.concat([long, meta_df], axis=1)

        # Normalise stat labels → mean / se / n
        def normalize_stat(label):
            if isinstance(label, str):
                l = label.lower()
                if "standard error" in l:
                    return "se"
                if "count" in l:
                    return "n"
                if "mean" in l:
                    return "mean"
            return "value"

        long["stat"] = long["stat_label"].apply(normalize_stat)

        # Clean labels
        long["Domain"] = long["Domain"].astype(str).str.strip()
        long["Question"] = long["Question"].astype(str).str.strip()

        # Convert value to numeric, coercing errors (like strings) to NaN
        long["raw_value"] = pd.to_numeric(long["raw_value"], errors='coerce')

        # Drop rows with no data
        long = long.dropna(subset=["raw_value"])

        # Pivot stats to columns
        wide = (
            long.pivot_table(
                index=["Domain", "Question", "Country", "Year"],
                columns="stat",
                values="raw_value",
                aggfunc="first",
            )
            .reset_index()
        )

        # Flatten column index
        wide.columns = [str(c) for c in wide.columns]

        # Rename mean column to value
        if "mean" in wide.columns:
            wide = wide.rename(columns={"mean": "value"})

        # Drop rows where value is missing (crucial for line charts)
        if "value" in wide.columns:
            wide = wide.dropna(subset=["value"])

        # Ensure Year is numeric
        wide["Year"] = wide["Year"].astype(int)
        
        # Sort by Year to ensure line order
        wide = wide.sort_values(by=["Country", "Year"])

        return wide

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


# Check if default file exists (case-insensitive search)
default_filename = "ResultswithSE.xlsx"
data_source = None

# Try exact match first
if os.path.exists(default_filename):
    data_source = default_filename
else:
    # Try case-insensitive match in current directory
    files = [f for f in os.listdir(".") if os.path.isfile(f)]
    for f in files:
        if f.lower() == default_filename.lower():
            data_source = f
            break

if not data_source:
    st.warning(
        f"⚠️ '{default_filename}' not found in the current directory. Please upload the data file."
    )
    uploaded_file = st.sidebar.file_uploader("Upload Data File", type=["xlsx"])
    if uploaded_file:
        data_source = uploaded_file

if data_source:
    long_df = load_long_data(data_source)
    if long_df.empty:
        st.error("Data loading failed or returned empty dataset.")
        st.stop()
else:
    st.info("Waiting for data file...")
    st.stop()


# -------------------------------------------------
# Sidebar controls
# -------------------------------------------------
st.sidebar.header("⚙️ Configuration")

# --- Data Selection ---
with st.sidebar.expander("1. Data Selection", expanded=True):
    # Domain
    domains = sorted(long_df["Domain"].unique())
    selected_domain = st.selectbox("Domain", domains)

    dom_df = long_df[long_df["Domain"] == selected_domain]

    # Show availability info
    avail_years = sorted(dom_df["Year"].unique())
    if avail_years:
        st.caption(f"📅 Data available: {min(avail_years)} - {max(avail_years)}")

    # Questions within domain
    questions = sorted(dom_df["Question"].unique())

    # --- Select All / Clear All Buttons ---
    c_all, c_clear = st.columns(2)

    # Session state key for selection
    if "selected_questions_key" not in st.session_state:
        st.session_state.selected_questions_key = [questions[0]] if questions else []

    if c_all.button("Select All"):
        st.session_state.selected_questions_key = questions
        st.rerun()

    if c_clear.button("Clear All"):
        st.session_state.selected_questions_key = []
        st.rerun()

    # Requires Streamlit 1.38+ for st.pills; fall back if missing
    if hasattr(st, "pills"):
        selected_questions = st.pills(
            "Indicators (questions)",
            questions,
            selection_mode="multi",
            key="selected_questions_key",
        )
    else:
        selected_questions = st.multiselect(
            "Indicators (questions)",
            questions,
            default=st.session_state.selected_questions_key,
            key="selected_questions_key",
        )

    # Countries
    countries = sorted(dom_df["Country"].unique())
    selected_countries = st.multiselect(
        "Countries",
        countries,
        default=countries,
    )

    # Year range
    years = sorted(dom_df["Year"].unique())
    if years:
        y_min, y_max = int(min(years)), int(max(years))
        selected_year_range = st.slider(
            "Year range",
            y_min,
            y_max,
            (y_min, y_max),
        )
    else:
        selected_year_range = (0, 0)

# --- Visual Settings ---
with st.sidebar.expander("2. Visual Settings", expanded=False):
    # Chart Type
    chart_type = st.selectbox(
        "Chart Type",
        ["Line Chart", "Bar Chart"],
        index=0,
    )

    # Layout
    layout = st.radio(
        "Plot layout",
        ["Single figure (all countries)", "Country panels"],
        index=0,
    )

    # Show column control if we are faceting (either by country or by indicator)
    show_grid_control = (layout == "Country panels") or (
        layout == "Single figure (all countries)" and len(selected_questions) > 1
    )

    grid_columns = 2
    if show_grid_control:
        grid_columns = st.slider("Grid columns (width)", 1, 6, 2)

    # Graph style
    graph_style = st.selectbox(
        "Graph style",
        [
            "Colorblind-safe (default)",
            "Vibrant (Tableau 10)",
            "Pastel (Soft)",
            "Earth Tones (Muted)",
            "Monochrome (blue shades)",
            "Black & white (line styles)",
            "Highlight focal country",
        ],
        index=0,
    )

    # Theme presets
    theme = st.selectbox(
        "Theme preset",
        [
            "Academic (light)",
            "OECD grey",
            "Dark dashboard",
            "Pastel report",
            "The Economist",
            "Financial Times",
        ],
        index=0,
    )

    # Focal country
    focal_country = None
    if graph_style == "Highlight focal country":
        focal_country = st.selectbox(
            "Focal country",
            countries,
            index=0,
        )

    # Error Bar Settings
    error_bar_type = st.selectbox(
        "Error Bars / Confidence Intervals",
        ["95% Confidence Interval", "Standard Error", "None"],
        index=0
    )


# -------------------------------------------------
# Filtered data for plotting
# -------------------------------------------------
if not selected_questions or not selected_countries:
    st.warning("Please select at least one indicator and one country.")
    st.stop()

plot_df = dom_df[
    (dom_df["Question"].isin(selected_questions))
    & (dom_df["Country"].isin(selected_countries))
    & (dom_df["Year"].between(selected_year_range[0], selected_year_range[1]))
]

if plot_df.empty:
    st.warning("No data for this combination. Try widening the year range or adding countries.")
    st.stop()

# Calculate error bars / CI
if "se" in plot_df.columns:
    if error_bar_type == "95% Confidence Interval":
        z_mult = 1.96
    elif error_bar_type == "Standard Error":
        z_mult = 1.0
    else:
        z_mult = 0.0
        
    if error_bar_type != "None":
        plot_df["ci_low"] = plot_df["value"] - z_mult * plot_df["se"]
        plot_df["ci_high"] = plot_df["value"] + z_mult * plot_df["se"]
    else:
        plot_df["ci_low"] = pd.NA
        plot_df["ci_high"] = pd.NA
else:
    plot_df["ci_low"] = pd.NA
    plot_df["ci_high"] = pd.NA

# Check for missing countries
present_countries = set(plot_df["Country"].unique())
missing_countries = set(selected_countries) - present_countries
if missing_countries:
    st.warning(
        "⚠️ The following countries have no data for the selected period and are not shown: "
        + ", ".join(sorted(missing_countries))
    )


# -------------------------------------------------
# Main Content: Dashboard Layout
# -------------------------------------------------
tab1 = st.container()

with tab1:
    # --- 1. KPI Metrics ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Countries", len(selected_countries))
    m2.metric("Indicators", len(selected_questions))
    m3.metric("Years", f"{selected_year_range[0]} - {selected_year_range[1]}")
    m4.metric("Data Points", len(plot_df))

    st.divider()

    # --- 2. Chart Section ---
    st.subheader(f"📈 Analysis: {selected_domain}")

    # --- Style helpers ---
    def get_country_color_encoding():
        """Color mapping for countries, depending on graph style."""
        if graph_style == "Colorblind-safe (default)":
            palette = [
                "#1b9e77",
                "#d95f02",
                "#7570b3",
                "#e7298a",
                "#66a61e",
                "#e6ab02",
                "#a6761d",
                "#666666",
            ]
            return alt.Color(
                "Country:N",
                title="Country",
                scale=alt.Scale(range=palette),
            )

        if graph_style == "Vibrant (Tableau 10)":
            # Tableau 10 standard
            palette = [
                "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
                "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"
            ]
            return alt.Color("Country:N", title="Country", scale=alt.Scale(range=palette))

        if graph_style == "Pastel (Soft)":
            # Brewer Pastel1 + Pastel2 mix
            palette = [
                "#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4", "#fed9a6",
                "#ffffcc", "#e5d8bd", "#fddaec", "#f2f2f2"
            ]
            return alt.Color("Country:N", title="Country", scale=alt.Scale(range=palette))

        if graph_style == "Earth Tones (Muted)":
            # Muted earth tones
            palette = [
                "#8c564b", "#c49c94", "#7f7f7f", "#c7c7c7", "#bcbd22",
                "#dbdb8d", "#17becf", "#9edae5"
            ]
            return alt.Color("Country:N", title="Country", scale=alt.Scale(range=palette))

        if graph_style == "Monochrome (blue shades)":
            return alt.Color(
                "Country:N",
                title="Country",
                scale=alt.Scale(scheme="blues"),
            )

        if graph_style == "Highlight focal country" and focal_country is not None:
            return alt.condition(
                alt.datum.Country == focal_country,
                alt.value("#1f77b4"),  # highlight
                alt.value("#CCCCCC"),  # others
            )

        return alt.value("black")

    def get_stroke_dash_encoding():
        """Line style mapping (used for black & white)."""
        if graph_style == "Black & white (line styles)":
            return alt.StrokeDash(
                "Country:N",
                title="Country",
                sort=selected_countries,
            )
        return alt.value([1, 0])

    def style_chart(chart: alt.Chart) -> alt.Chart:
        """Apply theme preset: fonts, fill, grid, legend, etc."""
        chart = (
            chart.configure_axis(labelFontSize=13, titleFontSize=15)
            .configure_legend(titleFontSize=14, labelFontSize=12)
            .configure_title(fontSize=18, anchor="start")
        )

        if theme == "Academic (light)":
            chart = chart.configure_view(strokeWidth=0, fill="white").configure_axis(
                grid=True, gridColor="#DDDDDD"
            )
        elif theme == "OECD grey":
            chart = chart.configure_view(
                stroke="#CCCCCC", strokeWidth=1, fill="white"
            ).configure_axis(grid=True, gridColor="#E0E0E0")
        elif theme == "Dark dashboard":
            chart = (
                chart.configure_view(strokeWidth=0, fill="#111111")
                .configure_axis(
                    labelColor="white",
                    titleColor="white",
                    grid=True,
                    gridColor="#333333",
                )
                .configure_legend(titleColor="white", labelColor="white")
                .configure_title(color="white")
            )
        elif theme == "Pastel report":
            chart = chart.configure_view(strokeWidth=0, fill="#FAFAFA").configure_axis(
                grid=True, gridColor="#F0F0F0"
            )
        elif theme == "The Economist":
            chart = chart.configure_view(strokeWidth=0, fill="#d5e4eb").configure_axis(
                grid=True,
                gridColor="white",
                labelFont="Verdana",
                titleFont="Verdana",
            ).configure_title(font="Verdana", fontSize=20).configure_legend(
                labelFont="Verdana", titleFont="Verdana"
            )
        elif theme == "Financial Times":
            chart = chart.configure_view(strokeWidth=0, fill="#fff1e0").configure_axis(
                grid=True,
                gridColor="#e3cbb0",
                labelFont="Georgia",
                titleFont="Georgia",
            ).configure_title(font="Georgia", fontSize=20).configure_legend(
                labelFont="Georgia", titleFont="Georgia"
            )

        return chart

    color_encoding = get_country_color_encoding()
    stroke_dash_encoding = get_stroke_dash_encoding()

    # --- Plotting Logic ---
    def create_single_chart(
        data: pd.DataFrame,
        title_text: str,
        x_axis_title: str = "Year",
        y_axis_title: str = "Value",
        color_enc=None,
        dash_enc=None,
        x_off=None,
        show_ci_flag: bool = True,
        height: int = 450,
    ) -> alt.Chart:
        base = alt.Chart(data)

        # Main layer: bar or line
        if chart_type == "Bar Chart":
            main_mark = base.mark_bar()
        else:
            main_mark = base.mark_line(point=True)

        main = main_mark.encode(
            x=alt.X("Year:Q", title=x_axis_title, axis=alt.Axis(format="d")),
            y=alt.Y("value:Q", title=y_axis_title),
            color=color_enc,
            strokeDash=dash_enc,
            xOffset=x_off,
            tooltip=[
                "Country",
                "Year",
                "Question",
                alt.Tooltip("value:Q", title="Mean"),
                alt.Tooltip("se:Q", title="SE", format=".3f"),
                alt.Tooltip("n:Q", title="N"),
                alt.Tooltip("ci_low:Q", title="CI low", format=".3f"),
                alt.Tooltip("ci_high:Q", title="CI high", format=".3f"),
            ],
            order="Year",
        )

        layers = [main]

        # Optional CI layer
        if (
            show_ci_flag
            and "ci_low" in data.columns
            and "ci_high" in data.columns
            and data["ci_low"].notna().any()
        ):
            if chart_type == "Bar Chart":
                err = base.mark_errorbar().encode(
                    x=alt.X("Year:Q", title=x_axis_title, axis=alt.Axis(format="d")),
                    y=alt.Y("ci_low:Q", title=y_axis_title),
                    y2="ci_high:Q",
                    color=color_enc,
                    xOffset=x_off,
                )
            else:
                err = base.mark_errorband(opacity=0.2).encode(
                    x=alt.X("Year:Q", title=x_axis_title, axis=alt.Axis(format="d")),
                    y=alt.Y("ci_low:Q", title=y_axis_title),
                    y2="ci_high:Q",
                    color=color_enc,
                )
            layers.insert(0, err)

        chart = alt.layer(*layers).properties(
            title=title_text,
            height=height,  # Dynamic height
        )
        return style_chart(chart)

    # Layouts
    if layout == "Single figure (all countries)":
        if len(selected_questions) > 1:
            # Multiple indicators -> grid of charts, one per indicator
            cols = st.columns(grid_columns)
            for i, q in enumerate(selected_questions):
                q_data = plot_df[plot_df["Question"] == q]
                chart = create_single_chart(
                    q_data,
                    title_text=f"{q}",
                    y_axis_title="Value",
                    color_enc=color_encoding,
                    dash_enc=stroke_dash_encoding
                    if chart_type == "Line Chart"
                    else alt.value([0, 0]),
                    x_off="Country:N" if chart_type == "Bar Chart" else alt.value(0),
                    show_ci_flag=(error_bar_type != "None"),
                )
                with cols[i % grid_columns]:
                    st.altair_chart(chart, width="stretch")
        else:
            # One indicator -> single chart
            chart = create_single_chart(
                plot_df,
                title_text=f"{selected_questions[0]} – {selected_domain}",
                y_axis_title=selected_questions[0],
                color_enc=color_encoding,
                dash_enc=stroke_dash_encoding
                if chart_type == "Line Chart"
                else alt.value([0, 0]),
                x_off="Country:N" if chart_type == "Bar Chart" else alt.value(0),
                show_ci_flag=(error_bar_type != "None"),
                height=600,  # Increased height
            )
            
            # Left aligned, narrower (approx 60% width)
            c_chart, _ = st.columns([3, 2])
            with c_chart:
                st.altair_chart(chart, width="stretch")
    else:
        # Country panels -> grid of charts, one per country
        if graph_style == "Black & white (line styles)":
            panel_color = alt.value("black")
            panel_dash = alt.StrokeDash("Question:N", title="Indicator")
        else:
            panel_color = alt.Color("Question:N", title="Indicator")
            panel_dash = alt.value([1, 0])

        cols = st.columns(grid_columns)
        for i, country in enumerate(selected_countries):
            c_data = plot_df[plot_df["Country"] == country]
            if c_data.empty:
                continue
            chart = create_single_chart(
                c_data,
                title_text=f"{country}",
                y_axis_title="Value",
                color_enc=panel_color,
                dash_enc=panel_dash
                if chart_type == "Line Chart"
                else alt.value([0, 0]),
                x_off="Question:N" if chart_type == "Bar Chart" else alt.value(0),
                show_ci_flag=(error_bar_type != "None"),
            )
            with cols[i % grid_columns]:
                st.altair_chart(chart, width="stretch")

    # --- 3. Footer / Export ---
    st.divider()

    # --- Selected Indicator Definitions ---
    if selected_questions:
        st.subheader("📖 Indicator Definitions")
        # from info_content import get_schema_dict, get_item_descriptions # MERGED

        schema = get_schema_dict()
        item_descs = get_item_descriptions()

        for q in selected_questions:
            info = schema.get(q)
            if info:
                with st.expander(f"ℹ️ {q}", expanded=False):
                    items_used = info.get("Items Used", "N/A")
                    st.markdown(
                        f"""
                        - **Interpretation**: {info.get('Interpretation', 'N/A')}
                        - **Method**: {info.get('Method', 'N/A')}
                        - **Items Used**: {items_used}
                        - **Domain**: {info.get('Domain', 'N/A')}
                        """
                    )

                    # Try to find relevant item descriptions
                    import re

                    relevant_items = []
                    for code, desc in item_descs.items():
                        # 1) Exact substring match
                        if code in items_used:
                            relevant_items.append(f"- **{code}**: {desc}")
                        else:
                            # 2) Range parsing, e.g. A065–A074
                            ranges = re.findall(
                                r"([A-Z]\d+)[-–—]([A-Z]\d+)", items_used
                            )
                            for start, end in ranges:
                                if start[0] == end[0] == code[0]:
                                    try:
                                        s_num = int(start[1:])
                                        e_num = int(end[1:])
                                        c_num = int(code[1:])
                                        if s_num <= c_num <= e_num:
                                            relevant_items.append(
                                                f"- **{code}**: {desc}"
                                            )
                                            break
                                    except Exception:
                                        pass

                    if relevant_items:
                        st.markdown("**Constituent Items:**")
                        relevant_items = sorted(list(set(relevant_items)))
                        for item_txt in relevant_items:
                            st.markdown(item_txt)

    st.divider()
    with st.expander("📥 Export & Data View", expanded=False):
        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown("### Download")
            csv = plot_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                csv,
                "filtered_data.csv",
                "text/csv",
                key="download-csv",
                use_container_width=True,
            )

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                plot_df.to_excel(writer, sheet_name="Data", index=False)

            st.download_button(
                "Download Excel",
                buffer.getvalue(),
                "filtered_data.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download-excel",
                use_container_width=True,
            )

        with c2:
            st.markdown("### Raw Data Preview")
            # Optional quick summary of SE / N
            if "se" in plot_df.columns and "n" in plot_df.columns:
                se_valid = plot_df["se"].dropna()
                n_valid = plot_df["n"].dropna()
                if not se_valid.empty and not n_valid.empty:
                    st.markdown(
                        f"- Median SE: **{se_valid.median():.3f}** "
                        f"(min: {se_valid.min():.3f}, max: {se_valid.max():.3f})  \n"
                        f"- Median N: **{int(n_valid.median())}** "
                        f"(min: {int(n_valid.min())}, max: {int(n_valid.max())})"
                    )
            st.dataframe(plot_df, height=200, use_container_width=True)
