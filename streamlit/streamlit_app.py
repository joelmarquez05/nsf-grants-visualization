
import streamlit as st
import charts as charts

st.set_page_config(layout="wide", page_title="NSF Grants Visualization")

st.title("NSF Grants Visualization (2021-2025)")

st.markdown("""
### Objective
This project presents an exploratory data visualization analysis of National Science Foundation (NSF) grants from the last 5 years (2021-2025). 
The main aspects treated are the distribution of grants across different states and directorates, the temporal evolution of funding amounts, 
and the impact of cancelled grants during the Trump administration.
""")

st.markdown("---")

# Load Data Functions
@st.cache_data
def load_mappings():
    return charts.get_mappings()

@st.cache_data
def load_award_data(mappings):
    return charts.get_award_data(mappings)

@st.cache_data
def load_state_grants_data(df_complete, mappings):
    return charts.get_state_grants_data(df_complete, mappings)

@st.cache_data
def load_q5_cancellation_data(mappings):
    return charts.get_q5_cancellation_data(mappings)

@st.cache_data
def load_q1(df_state_grants, mappings):
    return charts.get_q1_data(df_state_grants, mappings)

@st.cache_data
def load_q2():
    return charts.get_q2_data()

# CONSTANTS

# --- Chart Dimensions ---
MAP_WIDTH = 450
MAP_HEIGHT = 300
MAP_SCALE = int(1.25 * MAP_WIDTH)

BAR_WIDTH = 250
BAR_HEIGHT = 330
BAR_CHART_TOP_PADDING = 36

Q5_BAR_HEIGHT = 150
Q5_WIDTH = BAR_WIDTH + MAP_WIDTH
Q5_2_WIDTH = MAP_WIDTH + BAR_WIDTH - 20

LINE_CHART_WIDTH = 300
LINE_CHART_HEIGHT = 275

# Legend
LEGEND_WIDTH = MAP_WIDTH - 50
LEGEND_SPACER_WIDTH = (MAP_WIDTH - LEGEND_WIDTH) / 2
LEGEND_TEXT_HEIGHT = 20
LEGEND_BAR_HEIGHT = 15
LEGEND_STEPS = 300
LEGEND_TICK_COUNT = 6

# Q2 Bubble & Bar
CHART_WIDTH_BUBBLE = 450
CHART_HEIGHT_BUBBLE = 400
CHART_WIDTH_BAR = 275
CHART_WIDTH_LABEL = 40
CHART_HEIGHT_BAR = 350
HEADER_HEIGHT = 30
FOOTER_HEIGHT = 20
BUBBLE_HEADER_OFFSET = 4
BUTTERFLY_HEADER_OFFSET = 2

# --- Colors ---
COLOR_DEMOCRAT = "#377eb8"
COLOR_REPUBLICAN = "#e41a1c"
COLOR_DEMOCRAT_DARK = "#12129E"
COLOR_REPUBLICAN_DARK = "#8B0000"
COLOR_STROKE_BLACK = "black"
COLOR_STROKE_WHITE = "white"
COLOR_BACKGROUND_MAP = "#e0e0e0"
COLOR_SCHEME_RATE = "teals"
COLOR_ALL_PARTY = "#7B1FA2"

# --- Styling ---
STROKE_WIDTH_THIN = 0.5
STROKE_WIDTH_THICK = 4
STROKE_WIDTH_SYMBOL = 5

OPACITY_ACTIVE = 1.0
OPACITY_INACTIVE = 0.0
OPACITY_CIRCLE = 0.9
OPACITY_RULE_OUTLINE = 0.8
OPACITY_LINE = 0.6
OPACITY_YEAR_RULE = 0.7

CIRCLE_SIZE = 50
POINT_SIZE_DEFAULT = 80
POINT_SIZE_SELECTED = 100
POINT_SIZE_UNSELECTED = 50

# --- Offsets ---
PARTY_LEGEND_OFFSET_Y = -40
MEAN_LEGEND_OFFSET = -30
Q4_HEIGHT_OFFSET = 52

# --- Interaction Defaults ---
TOP_N_MIN = 5
TOP_N_MAX = 15
TOP_N_STEP = 1
DEFAULT_TOP_N = 10

YEARS_LIST = [2021, 2022, 2023, 2024, 2025]
YEAR_DEFAULT = 2025  # Default year shown when "All Years" is selected

VCONCAT_SPACING = 20
HCONCAT_SPACING = 30
BOTTOM_SPACING = 40
DASHBOARD_TITLE_FONT_SIZE = 20
DASHBOARD_SUBTITLE_FONT_SIZE = 12
DASHBOARD_TITLE_OFFSET = 20

PALETTE_DIRECTORATES = [
    '#E69F00', '#56B4E9', '#8D6E63', '#F0E442', '#0072B2',
    '#D55E00', '#CC79A7', '#999999', '#000000'
]
COLOR_VOLUME = '#00897B'
COLOR_IMPACT = '#AD1457'
COLOR_GRAY = 'lightgray'

OPACITY_DIM = 0.1
LEGEND_TITLE_FONT_SIZE = 14
LEGEND_LABEL_FONT_SIZE = 12
LEGEND_SYMBOL_SIZE = 60
LEGEND_ROW_PADDING = 5

STEP_BUBBLE_X = 200
STEP_BAR_X = 500
STEP_RATE = 2
MIN_BAR_GRANTS = 25
MIN_BAR_RATE = 0
YEAR_ALL_INDICATOR = 0

CHART_CONFIG = {
    'MAP_WIDTH': MAP_WIDTH,
    'MAP_HEIGHT': MAP_HEIGHT,
    'MAP_SCALE': MAP_SCALE,
    'BAR_WIDTH': BAR_WIDTH,
    'BAR_HEIGHT': BAR_HEIGHT,
    'BAR_CHART_TOP_PADDING': BAR_CHART_TOP_PADDING,
    'Q5_BAR_HEIGHT': Q5_BAR_HEIGHT,
    'Q5_WIDTH': Q5_WIDTH,
    'Q5_2_WIDTH': Q5_2_WIDTH,
    'LINE_CHART_WIDTH': LINE_CHART_WIDTH,
    'LINE_CHART_HEIGHT': LINE_CHART_HEIGHT,
    'LEGEND_WIDTH': LEGEND_WIDTH,
    'LEGEND_SPACER_WIDTH': LEGEND_SPACER_WIDTH,
    'LEGEND_TEXT_HEIGHT': LEGEND_TEXT_HEIGHT,
    'LEGEND_BAR_HEIGHT': LEGEND_BAR_HEIGHT,
    'LEGEND_STEPS': LEGEND_STEPS,
    'LEGEND_TICK_COUNT': LEGEND_TICK_COUNT,
    'CHART_WIDTH_BUBBLE': CHART_WIDTH_BUBBLE,
    'CHART_HEIGHT_BUBBLE': CHART_HEIGHT_BUBBLE,
    'CHART_WIDTH_BAR': CHART_WIDTH_BAR,
    'CHART_WIDTH_LABEL': CHART_WIDTH_LABEL,
    'CHART_HEIGHT_BAR': CHART_HEIGHT_BAR,
    'HEADER_HEIGHT': HEADER_HEIGHT,
    'FOOTER_HEIGHT': FOOTER_HEIGHT,
    'BUBBLE_HEADER_OFFSET': BUBBLE_HEADER_OFFSET,
    'BUTTERFLY_HEADER_OFFSET': BUTTERFLY_HEADER_OFFSET,
    'COLOR_DEMOCRAT': COLOR_DEMOCRAT,
    'COLOR_REPUBLICAN': COLOR_REPUBLICAN,
    'COLOR_DEMOCRAT_DARK': COLOR_DEMOCRAT_DARK,
    'COLOR_REPUBLICAN_DARK': COLOR_REPUBLICAN_DARK,
    'COLOR_STROKE_BLACK': COLOR_STROKE_BLACK,
    'COLOR_STROKE_WHITE': COLOR_STROKE_WHITE,
    'COLOR_BACKGROUND_MAP': COLOR_BACKGROUND_MAP,
    'COLOR_SCHEME_RATE': COLOR_SCHEME_RATE,
    'COLOR_ALL_PARTY': COLOR_ALL_PARTY,
    'COLOR_VOLUME': COLOR_VOLUME,
    'COLOR_IMPACT': COLOR_IMPACT,
    'COLOR_GRAY': COLOR_GRAY,
    'PALETTE_DIRECTORATES': PALETTE_DIRECTORATES,
    'STROKE_WIDTH_THIN': STROKE_WIDTH_THIN,
    'STROKE_WIDTH_THICK': STROKE_WIDTH_THICK,
    'STROKE_WIDTH_SYMBOL': STROKE_WIDTH_SYMBOL,
    'OPACITY_ACTIVE': OPACITY_ACTIVE,
    'OPACITY_DIM': OPACITY_DIM,
    'OPACITY_INACTIVE': OPACITY_INACTIVE,
    'OPACITY_CIRCLE': OPACITY_CIRCLE,
    'OPACITY_RULE_OUTLINE': OPACITY_RULE_OUTLINE,
    'OPACITY_LINE': OPACITY_LINE,
    'OPACITY_YEAR_RULE': OPACITY_YEAR_RULE,
    'CIRCLE_SIZE': CIRCLE_SIZE,
    'POINT_SIZE_DEFAULT': POINT_SIZE_DEFAULT,
    'POINT_SIZE_SELECTED': POINT_SIZE_SELECTED,
    'POINT_SIZE_UNSELECTED': POINT_SIZE_UNSELECTED,
    'PARTY_LEGEND_OFFSET_Y': PARTY_LEGEND_OFFSET_Y,
    'MEAN_LEGEND_OFFSET': MEAN_LEGEND_OFFSET,
    'LEGEND_TITLE_FONT_SIZE': LEGEND_TITLE_FONT_SIZE,
    'LEGEND_LABEL_FONT_SIZE': LEGEND_LABEL_FONT_SIZE,
    'LEGEND_SYMBOL_SIZE': LEGEND_SYMBOL_SIZE,
    'LEGEND_ROW_PADDING': LEGEND_ROW_PADDING,
    'Q4_HEIGHT_OFFSET': Q4_HEIGHT_OFFSET,
    'TOP_N_MIN': TOP_N_MIN,
    'TOP_N_MAX': TOP_N_MAX,
    'TOP_N_STEP': TOP_N_STEP,
    'DEFAULT_TOP_N': DEFAULT_TOP_N,
    'YEARS_LIST': YEARS_LIST,
    'YEAR_DEFAULT': YEAR_DEFAULT,
    'YEAR_ALL_INDICATOR': YEAR_ALL_INDICATOR,
    'VCONCAT_SPACING': VCONCAT_SPACING,
    'HCONCAT_SPACING': HCONCAT_SPACING,
    'BOTTOM_SPACING': BOTTOM_SPACING,
    'DASHBOARD_TITLE_FONT_SIZE': DASHBOARD_TITLE_FONT_SIZE,
    'DASHBOARD_SUBTITLE_FONT_SIZE': DASHBOARD_SUBTITLE_FONT_SIZE,
    'DASHBOARD_TITLE_OFFSET': DASHBOARD_TITLE_OFFSET,
    'STEP_BUBBLE_X': STEP_BUBBLE_X,
    'STEP_BAR_X': STEP_BAR_X,
    'STEP_RATE': STEP_RATE,
    'MIN_BAR_GRANTS': MIN_BAR_GRANTS,
    'MIN_BAR_RATE': MIN_BAR_RATE
}

# Execute Data Loading
mappings = load_mappings()
df_complete = load_award_data(mappings)
df_state_grants = load_state_grants_data(df_complete, mappings)
q1_combined = load_q1(df_state_grants, mappings)
df_scatter, df_div = load_q2()
cancelled_by_state_year = load_q5_cancellation_data(mappings)

@st.cache_data
def load_visualization(df_complete, df_state_grants, df_scatter, df_div, q1_combined, cancelled_by_state_year, config):
    return charts.get_visualization(df_complete, df_state_grants, df_scatter, df_div, q1_combined, cancelled_by_state_year, config)

visualization = load_visualization(df_complete, df_state_grants, df_scatter, df_div, q1_combined, cancelled_by_state_year, CHART_CONFIG)

# CSS to hide chart during initial render, then fade in after delay

# JUSTIFICATION (IMANOL)
# Vega-Lite charts render asynchronously; without this delay, users see
# a brief flicker as the chart initializes. The animation delay allows
# the visualization to fully render before becoming visible.

st.markdown("""
<style>
    /* Hide vega-embed initially, then fade in after 5 seconds */
    .vega-embed {
        opacity: 0;
        animation: fadeIn 0.5s ease-in-out 22s forwards;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Loading message styling */
    .loading-msg {
        text-align: center;
        padding: 20px;
        font-size: 18px;
        color: #666;
        animation: hideLoading 0s 22s forwards;
    }
    
    @keyframes hideLoading {
        to { display: none; visibility: hidden; height: 0; padding: 0; }
    }
    
    /* Hide expander until chart is loaded */
    [data-testid="stExpander"] {
        opacity: 0;
        animation: fadeIn 0.5s ease-in-out 22s forwards;
    }
</style>
<div class="loading-msg">⏳ Loading visualization...</div>
""", unsafe_allow_html=True)

st.altair_chart(visualization, width='content')

with st.expander("ℹ️ Authors", expanded=False):
    st.markdown(
        """
        - **Pau Balaguer Coll**
        - **Joel Márquez Álvarez**
        """
    )