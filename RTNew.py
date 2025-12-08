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
variable_info_md = """
# Operationalisation Table

| Variable | Domain | Items Used | Method | Interpretation |
|---------|--------|------------|--------|----------------|
| D1_Justification | Citizenship, Rights, Responsibilities, Obligation | F115–F117 | REVERSE MEAN | Justification of Existing System |
| D1_Participation | Citizenship, Rights, Responsibilities, Obligation | E025–E029 | COUNT/5 | Unconventional Political Participation |
| D1_Political Interest | Citizenship, Rights, Responsibilities, Obligation | E023, E150 | MEAN | Political Interest |
| D2_Membership | Relation btw. Citizens and State | A065–A074 | COUNT | Civic Participation |
| D2_Proud of Nationality | Relation btw. Citizens and State | G006 | Raw | Pride in Nationality |
| D3_Confidence in Institutions | Legitimacy | E069_01–E069_17 (Selected) | Factor Analysis | Confidence in Institutions |
| D3_Confidence in the EU | Legitimacy | E069_18 | Raw | Confidence in the EU |
| D3_Support for Technocray&Authoritarianism | Legitimacy | E114–E116 | Factor Analysis | Support for authoritarian models |
| D3_Support for Democracy | Legitimacy | E117 | Raw | Support for democracy |
| Concern for Everyone | Social Cohesion & Mutual Regard | E154–E158 | Factor Analysis | Concern for Everyone |
| Concern for Everyone | Social Cohesion & Mutual Regard | E154–E158 | Factor Analysis (Reversed) | Concern for Everyone |
| Concern for Vulnerable | Social Cohesion & Mutual Regard | E159–E162 | Raw | Concern for Vulnerable |
| D04_Autonomy-oriented child qualities | Social Cohesion & Mutual Regard | A029, A030, A034 | Count | Autonomy |
| D04_Conformity-oriented child qualities | Social Cohesion & Mutual Regard | A038, A040, A042 | Count | Conformity |
| D04_Prosocial/communal child qualities | Social Cohesion & Mutual Regard | A032, A035, A041, A039 | Count | Prosocial |
| D4_Gender Discrimination | Social Cohesion & Mutual Regard | D059, D060 | Factor Analysis | Gender Discrimination |
| D4_AntiImmigrant | Social Cohesion & Mutual Regard | C002, A124_02 | Recoded | Anti-Immigrant Attitudes |
| D4_Intolerance | Social Cohesion & Mutual Regard | A124_05, 06, 10 | Count | Intolerance |
| D4_Moral_Intolerance | Social Cohesion & Mutual Regard | A124_03, 08, 09 | Count | Moral Intolerance |
| D4_Generalized Trust | Social Cohesion & Mutual Regard | A165 | Raw | Generalized Trust |
| D5_Belief in Democracy | Justice & Fairness | E120–E123 | Factor Analysis (Reversed) | Support for Democracy |
| D5_ProMarket | Justice & Fairness | E035–E039 | Factor Analysis (Reversed) | ProMarket Attitudes |
| D6_Protestant Ethic | Justice & Fairness | C036–C039 | Factor Analysis (Reversed) | Protestant Ethic |
| Agency | Legitimacy/Resilience | A173 | Raw | Perceived freedom/control |
| Satisfaction with Life | Resilience | A170 | Raw | Subjective well-being |
| Post-Materialist index 4-item | Values | Y002 | Index | Post-materialist values |
| Autonomy Index | Values | Y003 | Index | Autonomy Index |

# Item-Level Descriptions

## Citizenship & Participation
- F115 — Justifiable: Avoiding a fare on public transport
- F116 — Justifiable: Cheating on taxes
- F117 — Justifiable: Someone accepting a bribe
- E025 — Political action: signing a petition
- E026 — Political action: joining in boycotts
- E027 — Political action: attending lawful/peaceful demonstrations
- E028 — Political action: joining unofficial strikes
- E029 — Political action: occupying buildings or factories
- E023 — Interest in politics
- E150 — How often follows politics in the news

## Group Membership (A065–A074)
- A065 — Member: Belong to religious organization
- A066 — Member: Belong to education, arts, music or cultural activities
- A067 — Member: Belong to labour unions
- A068 — Member: Belong to political parties
- A069 — Member: Belong to local political actions
- A070 — Member: Belong to human rights
- A071 — Member: Belong to conservation, the environment, ecology, animal rights
- A072 — Member: Belong to professional associations
- A073 — Member: Belong to youth work
- A074 — Member: Belong to sports or recreation

## National Identity
- G006 — How proud of nationality

## Institutions (E069)
- E069_01 — Confidence: Churches
- E069_02 — Confidence: Armed Forces
- E069_04 — Confidence: The Press
- E069_05 — Confidence: Labour Unions
- E069_06 — Confidence: The Police
- E069_07 — Confidence: Parliament
- E069_08 — Confidence: The Civil Services
- E069_17 — Confidence: Justice System/Courts
- E069_18 — Confidence: The European Union

## Political Systems (E114–E117)
- E114 — Political system: Having a strong leader
- E115 — Political system: Having experts make decisions
- E116 — Political system: Having the army rule
- E117 — Political system: Having a democratic political system

## Social Concern (E154–E162)
- E154 — Feel concerned about people in the neighbourhood
- E155 — Feel concerned about people in the region
- E156 — Feel concerned about fellow countrymen
- E157 — Feel concerned about Europeans
- E158 — Feel concerned about human kind
- E159 — Feel concerned about elderly people
- E160 — Feel concerned about unemployed people
- E161 — Feel concerned about immigrants
- E162 — Feel concerned about sick and disabled people

## Child Qualities (A029–A042)
- A029 — Important child qualities: independence
- A030 — Important child qualities: hard work
- A032 — Important child qualities: feeling of responsibility
- A034 — Important child qualities: imagination
- A035 — Important child qualities: tolerance and respect for other people
- A038 — Important child qualities: thrift saving money and things
- A039 — Important child qualities: determination perseverance
- A040 — Important child qualities: religious faith
- A041 — Important child qualities: unselfishness
- A042 — Important child qualities: obedience

## Gender & Discrimination
- D059 — Men make better political leaders than women do
- D060 — University is more important for a boy than for a girl
- C002 — Jobs scarce: Employers should give priority to (nation) people than immigrants

## Intolerance / Neighbors (A124)
- A124_02 — Neighbours: People of a different race
- A124_03 — Neighbours: Heavy drinkers
- A124_05 — Neighbours: Muslims
- A124_06 — Neighbours: Immigrants/foreign workers
- A124_08 — Neighbours: Drug addicts
- A124_09 — Neighbours: Homosexuals
- A124_10 — Neighbours: Jews

## Trust
- A165 — Most people can be trusted

## Democratic Performance (E120–E123)
- E120 — In democracy, the economic system runs badly
- E121 — Democracies are indecisive and have too much squabbling
- E122 — Democracies aren´t good at maintaining order
- E123 — Democracy may have problems but is better

## Economic & Work Values
- E035 — Income equality
- E036 — Private vs state ownership of business
- E037 — Government responsibility
- E038 — Job taking of the unemployed
- E039 — Competition good or harmful
- C036 — To develop talents you need to have a job
- C037 — Humiliating to receive money without having to work for it
- C038 — People who don´t work turn lazy
- C039 — Work is a duty towards society
"""

def get_schema_dict():
    """Parses the markdown table into a dictionary keyed by Variable name."""
    lines = variable_info_md.strip().splitlines()
    
    # Find table start
    table_lines = []
    in_table = False
    for line in lines:
        if line.strip().startswith('| Variable |'):
            in_table = True
        if in_table:
            if line.strip() == '' or line.startswith('#'):
                if len(table_lines) > 2: # End of table
                    break
            if line.strip() != "":
                table_lines.append(line)
            
    if not table_lines:
        return {}

    # Parse headers
    headers = [h.strip() for h in table_lines[0].split('|') if h.strip()]
    
    schema = {}
    # Skip header and separator
    for line in table_lines[2:]:
        if not line.strip(): continue
        if line.strip().startswith("|---"): continue
        
        row = [cell.strip() for cell in line.split('|') if cell.strip()]
        # Handle pipe at start/end
        # Split puts '' at start/end if pipe is there
        row = [cell.strip() for cell in line.strip().strip('|').split('|')]
        
        if len(row) >= len(headers):
            # Create a dict for this row
            row_dict = {headers[i]: row[i].strip() for i in range(len(headers))}
            # Key by Variable name
            var_name = row_dict.get('Variable')
            if var_name:
                schema[var_name] = row_dict
                # Duplicate entry handling? Currently overwrites.
                
    return schema

def get_item_descriptions():
    """Parses the item-level descriptions into a dictionary {ItemCode: Description}."""
    lines = variable_info_md.strip().splitlines()
    
    items = {}
    import re
    # Regex to match "- CODE — Description"
    # Handles codes like G006, E069_01
    pattern = re.compile(r'-\s+([A-Z0-9_]+)\s+[—–-]\s+(.+)')
    
    for line in lines:
        line = line.strip()
        match = pattern.match(line)
        if match:
            code = match.group(1).strip()
            desc = match.group(2).strip()
            items[code] = desc
            
    return items

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

        # Ensure Year is numeric
        wide["Year"] = wide["Year"].astype(int)

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
    ) -> alt.Chart:
        base = alt.Chart(data)

        # Main layer: bar or line
        if chart_type == "Bar Chart":
            main_mark = base.mark_bar()
        else:
            main_mark = base.mark_line(point=True)

        main = main_mark.encode(
            x=alt.X("Year:O", title=x_axis_title),
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
                    x=alt.X("Year:O", title=x_axis_title),
                    y=alt.Y("ci_low:Q", title=y_axis_title),
                    y2="ci_high:Q",
                    color=color_enc,
                    xOffset=x_off,
                )
            else:
                err = base.mark_errorband(opacity=0.2).encode(
                    x=alt.X("Year:O", title=x_axis_title),
                    y=alt.Y("ci_low:Q", title=y_axis_title),
                    y2="ci_high:Q",
                    color=color_enc,
                )
            layers.insert(0, err)

        chart = alt.layer(*layers).properties(
            title=title_text,
            height=450,  # Fixed height, width responsive
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
            )
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
