
import pandas as pd
import numpy as np
import altair as alt
import math
from vega_datasets import data as vega_data


def get_mappings():
    df_states = pd.read_csv('clean_data/us_states.csv')
    return {
        'state_party_2020': dict(zip(df_states['StateCode'], df_states['Party2020'])),
        'state_party_2025': dict(zip(df_states['StateCode'], df_states['Party2025'])),
        'state_name': dict(zip(df_states['StateCode'], df_states['StateName'])),
        'state_fips': dict(zip(df_states['StateCode'], df_states['Id'])),
        'state_lat': dict(zip(df_states['StateCode'], df_states['Latitude'])),
        'state_lon': dict(zip(df_states['StateCode'], df_states['Longitude']))
    }

def get_award_data(mappings):
    df_awards = pd.read_csv('clean_data/nsf_awards_full.csv')
    df_cancellations = pd.read_csv('clean_data/nsf_cancellations.csv')

    state_party_2020_map = mappings['state_party_2020']
    state_party_2025_map = mappings['state_party_2025']
    state_name_map = mappings['state_name']

    # Check how many cancelled grants are already in the main dataset
    cancelled_ids = set(df_cancellations['AwardID'].astype(str))
    main_ids = set(df_awards['AwardID'].astype(str))
    missing = cancelled_ids - main_ids

    # Filter missing cancellations that have valid Year (2021-2025) and StateCode
    missing_cancellations = df_cancellations[
        (df_cancellations['AwardID'].astype(str).isin(missing)) &
        (df_cancellations['Year'].notna()) &
        (df_cancellations['Year'].between(2021, 2025)) &  # Only years in our dataset range
        (df_cancellations['StateCode'].notna())
    ][['AwardID', 'StateCode', 'Year', 'EstimatedBudget']].copy()

    # Get StateName from df_states
    missing_cancellations['StateName'] = missing_cancellations['StateCode'].map(state_name_map)
    missing_cancellations['Year'] = missing_cancellations['Year'].astype(int)

    # Add missing cancelled grants to all the awards
    df_complete = pd.concat([
        df_awards[['AwardID', 'StateCode', 'StateName', 'Year', 'EstimatedBudget']],
        missing_cancellations[['AwardID', 'StateCode', 'StateName', 'Year', 'EstimatedBudget']]
    ], ignore_index=True)

    # Add governing party in each grant State
    df_complete['Party'] = df_complete.apply(  # Political party based on the year
        lambda row: state_party_2020_map.get(row['StateCode'], 'Unknown') if row['Year'] <= 2024
        else state_party_2025_map.get(row['StateCode'], 'Unknown'), axis=1
    )

    return df_complete

def get_state_grants_data(df_complete, mappings):
    state_party_2020_map = mappings['state_party_2020']
    state_party_2025_map = mappings['state_party_2025']
    state_fips_map = mappings['state_fips']
    state_lat_map = mappings['state_lat']
    state_lon_map = mappings['state_lon']

    # Grant Share (%) of all grants correspoding to each state
    df_state_grants = df_complete.groupby(['StateCode', 'StateName', 'Year']).size().reset_index(name='GrantCount')
    year_totals = df_state_grants.groupby('Year')['GrantCount'].sum().to_dict()
    df_state_grants['GrantRate'] = df_state_grants.apply(
        lambda row: (row['GrantCount'] / year_totals[row['Year']]) * 100, axis=1
    )

    # Add map topology data
    df_state_grants['id'] = df_state_grants['StateCode'].map(state_fips_map)
    df_state_grants['latitude'] = df_state_grants['StateCode'].map(state_lat_map)
    df_state_grants['longitude'] = df_state_grants['StateCode'].map(state_lon_map)

    df_state_grants['Party'] = df_state_grants.apply(  # Political party based on the year
        lambda row: state_party_2020_map.get(row['StateCode'], 'Unknown') if row['Year'] <= 2024
        else state_party_2025_map.get(row['StateCode'], 'Unknown'), axis=1
    )
    return df_state_grants



def get_q1_data(df_state_grants, mappings):
    # All Years Average
    state_party_2020_map = mappings['state_party_2020']
    q1_all_years = df_state_grants.groupby(['StateCode', 'StateName', 'id']).agg({
        'GrantCount': 'sum',
        'latitude': 'first',
        'longitude': 'first'
    }).reset_index()

    total_all_grants = q1_all_years['GrantCount'].sum()
    q1_all_years['GrantRate'] = (q1_all_years['GrantCount'] / total_all_grants) * 100

    YEAR_ALL_INDICATOR = 0 # Used to represent the average of All Years

    q1_all_years['Year'] = YEAR_ALL_INDICATOR
    q1_all_years['Party'] = q1_all_years['StateCode'].map(state_party_2020_map)
    q1_combined = pd.concat([df_state_grants, q1_all_years], ignore_index=True)
    return q1_combined 


def get_q5_cancellation_data(mappings):
    df_cancellations = pd.read_csv('clean_data/nsf_cancellations.csv')
    state_name_map = mappings['state_name']
    state_party_2020_map = mappings['state_party_2020']
    state_party_2025_map = mappings['state_party_2025']

    df_cancellations['StateName'] = df_cancellations['StateCode'].map(state_name_map)
    cancelled_by_state_year = df_cancellations.groupby(['Year', 'StateCode', 'StateName', 'Status']).agg(
        Count=('AwardID', 'count')
    ).reset_index()
    cancelled_by_state_year['Year'] = cancelled_by_state_year['Year'].astype(int)
    cancelled_by_state_year['StateName'] = cancelled_by_state_year['StateCode'].map(state_name_map)
    cancelled_by_state_year['Party'] = cancelled_by_state_year.apply(  # Political party based on the year
        lambda row: state_party_2020_map.get(row['StateCode'], 'Unknown') if row['Year'] <= 2024
        else state_party_2025_map.get(row['StateCode'], 'Unknown'), axis=1
    )
    return cancelled_by_state_year

def get_q2_data():
    YEAR_ALL_INDICATOR = 0
    NUM_YEARS = 5

    df_awards = pd.read_csv('clean_data/nsf_awards_full.csv')
    df_cancellations = pd.read_csv('clean_data/nsf_cancellations.csv')
    df_terminated = df_cancellations[df_cancellations['Status'] == 'Terminated'].copy()
    df_reinstated = df_cancellations[df_cancellations['Status'] == 'Reinstated'].copy()


    # Directorate aggregation (All years, yearly average)
    dir_full_all = df_awards.groupby(['DirectorateAbbr', 'Directorate'])['AwardID'].count().reset_index(name='TotalGrants')
    dir_term_all = df_terminated.groupby('DirectorateAbbr')['AwardID'].count().reset_index(name='Terminated')
    dir_reinst_all = df_reinstated.groupby('DirectorateAbbr')['AwardID'].count().reset_index(name='Reinstated')

    df_dir_all = dir_full_all.merge(dir_term_all, on='DirectorateAbbr', how='left')
    df_dir_all = df_dir_all.merge(dir_reinst_all, on='DirectorateAbbr', how='left')

    df_dir_all['Terminated'] = df_dir_all['Terminated'].fillna(0)
    df_dir_all['Reinstated'] = df_dir_all['Reinstated'].fillna(0)
    df_dir_all['Cancelled'] = df_dir_all['Terminated'] + df_dir_all['Reinstated']
    df_dir_all['TotalGrants'] = df_dir_all['TotalGrants'] / NUM_YEARS
    df_dir_all['CancelRate'] = (df_dir_all['Cancelled'] / (df_dir_all['TotalGrants'] * NUM_YEARS)) * 100
    df_dir_all['TerminationRate'] = df_dir_all.apply(
        lambda r: (r['Terminated'] / r['Cancelled'] * 100) if r['Cancelled'] > 0 else 0, axis=1
    )

    df_dir_all['Year'] = YEAR_ALL_INDICATOR

    # Directorate aggregation (By year)
    dir_full_year = df_awards.groupby(['DirectorateAbbr', 'Directorate', 'Year'])['AwardID'].count().reset_index(name='TotalGrants')
    dir_term_year = df_terminated.groupby(['DirectorateAbbr', 'Year'])['AwardID'].count().reset_index(name='Terminated')
    dir_reinst_year = df_reinstated.groupby(['DirectorateAbbr', 'Year'])['AwardID'].count().reset_index(name='Reinstated')

    df_dir_year = dir_full_year.merge(dir_term_year, on=['DirectorateAbbr', 'Year'], how='left')
    df_dir_year = df_dir_year.merge(dir_reinst_year, on=['DirectorateAbbr', 'Year'], how='left')

    df_dir_year['Terminated'] = df_dir_year['Terminated'].fillna(0)
    df_dir_year['Reinstated'] = df_dir_year['Reinstated'].fillna(0)
    df_dir_year['Cancelled'] = df_dir_year['Terminated'] + df_dir_year['Reinstated']
    df_dir_year['CancelRate'] = (df_dir_year['Cancelled'] / df_dir_year['TotalGrants']) * 100
    df_dir_year['TerminationRate'] = df_dir_year.apply(
        lambda r: (r['Terminated'] / r['Cancelled'] * 100) if r['Cancelled'] > 0 else 0, axis=1
    )

    # Major directorates (>=100 grants)
    df_scatter = pd.concat([df_dir_all, df_dir_year], ignore_index=True)
    major_dirs = df_awards.groupby('DirectorateAbbr')['AwardID'].count()
    major_dirs = major_dirs[major_dirs >= 100].index.tolist()
    df_scatter = df_scatter[df_scatter['DirectorateAbbr'].isin(major_dirs)]

    # Division aggregation (All years, yearly average)
    div_full_all = df_awards.groupby(['DirectorateAbbr', 'Directorate', 'DivisionAbbr', 'Division'])['AwardID'].count().reset_index(name='TotalGrants')
    div_term_all = df_terminated.groupby(['DirectorateAbbr', 'DivisionAbbr'])['AwardID'].count().reset_index(name='Terminated')
    div_reinst_all = df_reinstated.groupby(['DirectorateAbbr', 'DivisionAbbr'])['AwardID'].count().reset_index(name='Reinstated')

    df_div_all = div_full_all.merge(div_term_all, on=['DirectorateAbbr', 'DivisionAbbr'], how='left')
    df_div_all = df_div_all.merge(div_reinst_all, on=['DirectorateAbbr', 'DivisionAbbr'], how='left')

    df_div_all['Terminated'] = df_div_all['Terminated'].fillna(0)
    df_div_all['Reinstated'] = df_div_all['Reinstated'].fillna(0)
    df_div_all['Cancelled'] = df_div_all['Terminated'] + df_div_all['Reinstated']
    df_div_all['TotalGrants'] = df_div_all['TotalGrants'] / NUM_YEARS
    df_div_all['CancelRate'] = (df_div_all['Cancelled'] / (df_div_all['TotalGrants'] * NUM_YEARS)) * 100
    df_div_all['TerminationRate'] = df_div_all.apply(
        lambda r: (r['Terminated'] / r['Cancelled'] * 100) if r['Cancelled'] > 0 else 0, axis=1
    )
    df_div_all['Year'] = YEAR_ALL_INDICATOR

    # Division aggregation (By year)
    div_full_year = df_awards.groupby(['DirectorateAbbr', 'Directorate', 'DivisionAbbr', 'Division', 'Year'])['AwardID'].count().reset_index(name='TotalGrants')
    div_term_year = df_terminated.groupby(['DirectorateAbbr', 'DivisionAbbr', 'Year'])['AwardID'].count().reset_index(name='Terminated')
    div_reinst_year = df_reinstated.groupby(['DirectorateAbbr', 'DivisionAbbr', 'Year'])['AwardID'].count().reset_index(name='Reinstated')

    df_div_year = div_full_year.merge(div_term_year, on=['DirectorateAbbr', 'DivisionAbbr', 'Year'], how='left')
    df_div_year = df_div_year.merge(div_reinst_year, on=['DirectorateAbbr', 'DivisionAbbr', 'Year'], how='left')

    df_div_year['Terminated'] = df_div_year['Terminated'].fillna(0)
    df_div_year['Reinstated'] = df_div_year['Reinstated'].fillna(0)
    df_div_year['Cancelled'] = df_div_year['Terminated'] + df_div_year['Reinstated']
    df_div_year['CancelRate'] = (df_div_year['Cancelled'] / df_div_year['TotalGrants']) * 100
    df_div_year['TerminationRate'] = df_div_year.apply(
        lambda r: (r['Terminated'] / r['Cancelled'] * 100) if r['Cancelled'] > 0 else 0, axis=1
    )

    # Combine divisions
    df_div = pd.concat([df_div_all, df_div_year], ignore_index=True)
    df_div = df_div[df_div['DirectorateAbbr'].isin(major_dirs)]

    return df_scatter, df_div

def get_visualization(df_complete, df_state_grants, df_scatter, df_div, q1_combined, cancelled_by_state_year, config):

    # CONSTANTS

    # --- Chart Dimensions ---
    MAP_WIDTH = config['MAP_WIDTH']
    MAP_HEIGHT = config['MAP_HEIGHT']
    MAP_SCALE = config['MAP_SCALE']

    BAR_WIDTH = config['BAR_WIDTH']
    BAR_HEIGHT = config['BAR_HEIGHT']
    BAR_CHART_TOP_PADDING = config['BAR_CHART_TOP_PADDING']

    Q5_BAR_HEIGHT = config['Q5_BAR_HEIGHT']
    Q5_WIDTH = config['Q5_WIDTH']
    Q5_2_WIDTH = config['Q5_2_WIDTH']

    LINE_CHART_WIDTH = config['LINE_CHART_WIDTH']
    LINE_CHART_HEIGHT = config['LINE_CHART_HEIGHT']

    # Legend
    LEGEND_WIDTH = config['LEGEND_WIDTH']
    LEGEND_SPACER_WIDTH = config['LEGEND_SPACER_WIDTH']
    LEGEND_TEXT_HEIGHT = config['LEGEND_TEXT_HEIGHT']
    LEGEND_BAR_HEIGHT = config['LEGEND_BAR_HEIGHT']
    LEGEND_STEPS = config['LEGEND_STEPS']
    LEGEND_TICK_COUNT = config['LEGEND_TICK_COUNT']

    # Q2 Bubble & Bar
    CHART_WIDTH_BUBBLE = config['CHART_WIDTH_BUBBLE']
    CHART_HEIGHT_BUBBLE = config['CHART_HEIGHT_BUBBLE']
    CHART_WIDTH_BAR = config['CHART_WIDTH_BAR']
    CHART_WIDTH_LABEL = config['CHART_WIDTH_LABEL']
    CHART_HEIGHT_BAR = config['CHART_HEIGHT_BAR']
    HEADER_HEIGHT = config['HEADER_HEIGHT']
    FOOTER_HEIGHT = config['FOOTER_HEIGHT']
    BUBBLE_HEADER_OFFSET = config['BUBBLE_HEADER_OFFSET']
    BUTTERFLY_HEADER_OFFSET = config['BUTTERFLY_HEADER_OFFSET']

    # --- Colors ---
    COLOR_DEMOCRAT = config['COLOR_DEMOCRAT']
    COLOR_REPUBLICAN = config['COLOR_REPUBLICAN']
    COLOR_DEMOCRAT_DARK = config['COLOR_DEMOCRAT_DARK']
    COLOR_REPUBLICAN_DARK = config['COLOR_REPUBLICAN_DARK']
    COLOR_STROKE_BLACK = config['COLOR_STROKE_BLACK']
    COLOR_STROKE_WHITE = config['COLOR_STROKE_WHITE']
    COLOR_BACKGROUND_MAP = config['COLOR_BACKGROUND_MAP']
    COLOR_SCHEME_RATE = config['COLOR_SCHEME_RATE']
    COLOR_ALL_PARTY = config['COLOR_ALL_PARTY']
    COLOR_VOLUME = config['COLOR_VOLUME']
    COLOR_IMPACT = config['COLOR_IMPACT']
    COLOR_GRAY = config['COLOR_GRAY']
    PALETTE_DIRECTORATES = config['PALETTE_DIRECTORATES']

    # --- Styling ---
    STROKE_WIDTH_THIN = config['STROKE_WIDTH_THIN']
    STROKE_WIDTH_THICK = config['STROKE_WIDTH_THICK']
    STROKE_WIDTH_SYMBOL = config['STROKE_WIDTH_SYMBOL']

    OPACITY_ACTIVE = config['OPACITY_ACTIVE']
    OPACITY_INACTIVE = config['OPACITY_INACTIVE']
    OPACITY_CIRCLE = config['OPACITY_CIRCLE']
    OPACITY_RULE_OUTLINE = config['OPACITY_RULE_OUTLINE']
    OPACITY_LINE = config['OPACITY_LINE']
    OPACITY_YEAR_RULE = config['OPACITY_YEAR_RULE']

    CIRCLE_SIZE = config['CIRCLE_SIZE']
    POINT_SIZE_DEFAULT = config['POINT_SIZE_DEFAULT']
    POINT_SIZE_SELECTED = config['POINT_SIZE_SELECTED']
    POINT_SIZE_UNSELECTED = config['POINT_SIZE_UNSELECTED']

    # --- Offsets ---
    PARTY_LEGEND_OFFSET_Y = config['PARTY_LEGEND_OFFSET_Y']
    MEAN_LEGEND_OFFSET = config['MEAN_LEGEND_OFFSET']
    Q4_HEIGHT_OFFSET = config['Q4_HEIGHT_OFFSET']

    # --- Interaction Defaults ---
    TOP_N_MIN = config['TOP_N_MIN']
    TOP_N_MAX = config['TOP_N_MAX']
    TOP_N_STEP = config['TOP_N_STEP']
    DEFAULT_TOP_N = config['DEFAULT_TOP_N']

    # --- Data Values ---
    YEARS_LIST = config['YEARS_LIST']
    YEAR_DEFAULT = config['YEAR_DEFAULT']
    YEAR_ALL_INDICATOR = config['YEAR_ALL_INDICATOR']

    # --- Dashboard Layout ---
    VCONCAT_SPACING = config['VCONCAT_SPACING']
    HCONCAT_SPACING = config['HCONCAT_SPACING']
    BOTTOM_SPACING = config['BOTTOM_SPACING']
    DASHBOARD_TITLE_FONT_SIZE = config['DASHBOARD_TITLE_FONT_SIZE']
    DASHBOARD_SUBTITLE_FONT_SIZE = config['DASHBOARD_SUBTITLE_FONT_SIZE']
    DASHBOARD_TITLE_OFFSET = config['DASHBOARD_TITLE_OFFSET']

    # --- Chart Scales ---
    STEP_BUBBLE_X = config['STEP_BUBBLE_X']
    STEP_BAR_X = config['STEP_BAR_X']
    STEP_RATE = config['STEP_RATE']
    MIN_BAR_GRANTS = config['MIN_BAR_GRANTS']
    MIN_BAR_RATE = config['MIN_BAR_RATE']
    

    # SHARED INTERACTION PARAMETERS

    # Year dropdown
    year_input = alt.binding_select(
        options=[YEAR_ALL_INDICATOR] + YEARS_LIST,
        labels=['All Years (Total)'] + [str(y) for y in YEARS_LIST],
        name='Fiscal Year: '
    )
    year_param = alt.param(name='year_select', value=YEAR_ALL_INDICATOR, bind=year_input)

    # Top N slider
    topn_slider = alt.binding_range(
        min=TOP_N_MIN, max=TOP_N_MAX, step=TOP_N_STEP, name='Top N States: '
    )
    topn_param = alt.param(name='topn', value=DEFAULT_TOP_N, bind=topn_slider)

    # Party dropdown
    party_input = alt.binding_select(
        options=['All', 'Republican', 'Democrat'],
        name='Party Filter: '
    )
    party_param = alt.param(name='party_filter', value='All', bind=party_input)

    # State selection (map click + dropdown)
    state_list = q1_combined['StateName'].unique().tolist()
    state_input = alt.binding_select(
        options=[None] + state_list,
        labels=['No State Selected'] + state_list,
        name='State: '
    )
    state_selection = alt.selection_point(
        fields=['StateName'],
        name='state_click',
        bind=state_input,
        on='click',
        clear='dblclick'
    )

    # Directorate selection (Q2 drill-down)
    dir_selection = alt.selection_point(fields=['DirectorateAbbr'], name='dir_select')

    # COLOR SCALES

    max_rate = q1_combined['GrantRate'].max()

    viridis_scale = alt.Scale(scheme=COLOR_SCHEME_RATE, domain=[0, max_rate])

    party_color_scale = alt.Scale(
        domain=["Democrat", "Republican"],
        range=[COLOR_DEMOCRAT, COLOR_REPUBLICAN]
    )

    party_legend_colors = alt.Scale(
        domain=["Democrat", "Republican"],
        range=[COLOR_DEMOCRAT_DARK, COLOR_REPUBLICAN_DARK]
    )

    q5_color_scale = alt.Scale(
        domain=['All', 'Democrat', 'Republican'],
        range=['#7B1FA2', COLOR_DEMOCRAT, COLOR_REPUBLICAN]
    )

    status_color_scale = alt.Scale(
        domain=['Terminated', 'Reinstated'],
        range=['#424242', '#FF8A65']
    )


    # Q1: BAR CHART + MAP

    # Bar Chart
    base_bars = alt.Chart(q1_combined).transform_filter(
        alt.datum.Year == year_param
    ).transform_filter(
        "(party_filter == 'All') || (datum.Party == party_filter)"
    ).transform_window(
        rank='rank(GrantRate)',
        sort=[alt.SortField('GrantRate', order='descending')]
    ).transform_filter(
        alt.datum.rank <= topn_param
    )

    y_axis_config = alt.Y(
        'StateName:N',
        title=None,
        sort=alt.EncodingSortField(field="rank", op="min", order="ascending")
    )

    bars = base_bars.mark_bar(
        stroke=COLOR_STROKE_BLACK,
        strokeWidth=STROKE_WIDTH_THIN
    ).encode(
        x=alt.X('GrantRate:Q', title='Grant Share (%)', scale=alt.Scale(domain=[0, max_rate])),
        y=y_axis_config,
        color=alt.Color('Party:N', scale=party_color_scale, legend=None),
        opacity=alt.condition(state_selection, alt.value(OPACITY_ACTIVE), alt.value(0.2)),
        tooltip=['StateName:N', 'Party:N', alt.Tooltip('GrantRate:Q', format='.2f'), alt.Tooltip('GrantCount:Q', format=',')]
    ).properties(width=BAR_WIDTH, height=BAR_HEIGHT)

    # Mean rules
    rule_base = alt.Chart(q1_combined).transform_filter(
        alt.datum.Year == year_param
    ).transform_filter(
        "(party_filter == 'All') || (datum.Party == party_filter)"
    ).transform_aggregate(
        GrantRate='mean(GrantRate)', groupby=['Party']
    )

    rule_outline = rule_base.mark_rule(strokeWidth=STROKE_WIDTH_THICK, opacity=OPACITY_RULE_OUTLINE).encode(
        x='GrantRate:Q',
        stroke=alt.value(COLOR_STROKE_BLACK),
        tooltip=[alt.Tooltip('Party:N'), alt.Tooltip('GrantRate:Q', format='.2f', title='Mean')]
    )

    rule_color = rule_base.mark_rule(strokeWidth=STROKE_WIDTH_SYMBOL).encode(
        x='GrantRate:Q',
        stroke=alt.Stroke('Party:N', scale=party_legend_colors,
            legend=alt.Legend(
                title='Mean by Party',
                orient='top',
                direction='horizontal',
                offset=MEAN_LEGEND_OFFSET,
                symbolStrokeWidth=STROKE_WIDTH_SYMBOL
            ))
    )

    bar_chart = (bars + rule_outline + rule_color)

    # Map
    us_states_geo = alt.topo_feature(vega_data.us_10m.url, "states")

    background = alt.Chart(us_states_geo).mark_geoshape(
        fill=COLOR_BACKGROUND_MAP,
        stroke=COLOR_STROKE_WHITE,
        strokeWidth=STROKE_WIDTH_THIN
    ).project(
        'albersUsa',
        scale=MAP_SCALE,
        translate=(MAP_WIDTH // 2, MAP_HEIGHT // 2)
    )

    layers = []
    year_list = [YEAR_ALL_INDICATOR] + YEARS_LIST

    for i, year in enumerate(year_list):
        yd = q1_combined[q1_combined['Year'] == year].copy()

        is_visible_year = f"year_select == '{year}'" if isinstance(year, str) else f"year_select == {year}"

        map_shape = alt.Chart(us_states_geo).mark_geoshape(
            stroke=COLOR_STROKE_WHITE,
            strokeWidth=STROKE_WIDTH_THIN
        ).transform_lookup(
            lookup='id',
            from_=alt.LookupData(yd, 'id', ['GrantCount', 'GrantRate', 'StateName', 'Party'])
        ).transform_filter(
            "(party_filter == 'All') || (datum.Party == party_filter)"
        ).transform_filter(
            is_visible_year
        ).encode(
            color=alt.Color('GrantRate:Q', scale=viridis_scale, legend=None),
            opacity=alt.condition(state_selection, alt.value(OPACITY_ACTIVE), alt.value(0.1)),
            tooltip=[
                'StateName:N',
                'Party:N',
                alt.Tooltip('GrantRate:Q', format='.2f'),
                alt.Tooltip('GrantCount:Q', format=',')
            ]
        ).project(
            'albersUsa',
            scale=MAP_SCALE,
            translate=(MAP_WIDTH // 2, MAP_HEIGHT // 2)
        )

        layers.append(map_shape)

        show_legend = alt.Legend(title='Party', orient='top-left', direction='horizontal', offset=PARTY_LEGEND_OFFSET_Y) if i == 0 else None

        map_dots = alt.Chart(yd).mark_circle(
            size=CIRCLE_SIZE,
            stroke=COLOR_STROKE_BLACK,
            strokeWidth=STROKE_WIDTH_THIN
        ).transform_filter(
            "(party_filter == 'All') || (datum.Party == party_filter)"
        ).transform_filter(
            is_visible_year
        ).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            color=alt.Color('Party:N', scale=party_color_scale, legend=show_legend),
            opacity=alt.condition(state_selection, alt.value(OPACITY_CIRCLE), alt.value(0.1)),
            tooltip=[
                'StateName:N',
                'Party:N',
                alt.Tooltip('GrantRate:Q', format='.2f'),
                alt.Tooltip('GrantCount:Q', format=',')
            ]
        ).project(
            'albersUsa',
            scale=MAP_SCALE,
            translate=(MAP_WIDTH // 2, MAP_HEIGHT // 2)
        )

        layers.append(map_dots)

    map_main = (background + alt.layer(*layers)).add_params(
        state_selection
    ).properties(width=MAP_WIDTH, height=MAP_HEIGHT)

    # --- Legend ---
    legend_values = np.linspace(0, max_rate if max_rate > 0 else 1, LEGEND_STEPS)
    legend_df = pd.DataFrame({"value": legend_values, "y": 1})

    l_title = alt.Chart(pd.DataFrame({'text': ['Grant Share (%)']})).mark_text(fontWeight='bold', dy=-5).encode(text='text').properties(width=LEGEND_WIDTH, height=LEGEND_TEXT_HEIGHT)

    l_rect = alt.Chart(legend_df).mark_rect().encode(
        x=alt.X("value:Q", bin=alt.Bin(maxbins=LEGEND_STEPS), axis=None, scale=alt.Scale(domain=[0, max_rate])),
        y=alt.Y("y:O", axis=None),
        color=alt.Color("value:Q", scale=viridis_scale, legend=None)
    ).properties(width=LEGEND_WIDTH, height=LEGEND_BAR_HEIGHT)

    l_ticks = alt.Chart(pd.DataFrame({"value": np.linspace(0, max_rate, LEGEND_TICK_COUNT)})).mark_text(dy=5).encode(
        x=alt.X("value:Q", scale=alt.Scale(domain=[0, max_rate]), axis=None),
        text=alt.Text("value:Q", format=".1f")
    ).properties(width=LEGEND_WIDTH, height=LEGEND_BAR_HEIGHT)

    legend_col = alt.vconcat(l_title, l_rect, l_ticks, spacing=2)
    spacer = alt.Chart(pd.DataFrame({'x': [0]})).mark_point(opacity=0).encode().properties(width=LEGEND_SPACER_WIDTH, height=1)
    legend_centered = alt.hconcat(spacer, legend_col, spacer, spacing=0)

    # --- Assembly ---
    right_side = alt.vconcat(map_main, legend_centered, spacing=10).resolve_scale(color='independent')
    q1_row = alt.hconcat(bar_chart, right_side, spacing=0).resolve_scale(color='independent')


    # Q5.2: CANCELLED GRANTS BAR CHART

    Q5_WIDTH = BAR_WIDTH + MAP_WIDTH + 20

    max_cancelled_count = cancelled_by_state_year.groupby(['Year', 'StateName'])['Count'].sum().max()
    q5_2_x_domain = [0, max_cancelled_count * 1.1 if max_cancelled_count > 0 else 5]

    q5_2_chart = alt.Chart(cancelled_by_state_year).mark_bar().encode(
        y=alt.Y('Year:O', title='Year', axis=alt.Axis(labelAngle=0)),
        x=alt.X('mean(Count):Q',
                title='Cancelled Grants (Average per State)',
                stack='zero',
                scale=alt.Scale(domain=q5_2_x_domain)),
        color=alt.Color(
            'Status:N',
            scale=status_color_scale,
            legend=alt.Legend(title='Status', orient='top')
        ),
        tooltip=[
            alt.Tooltip('Year:O', title='Year'),
            alt.Tooltip('StateName:N', aggregate='min', title='State'),
            alt.Tooltip('Status:N', title='Status'),
            alt.Tooltip('mean(Count):Q', title='Count (Avg/Actual)', format='.1f')
        ]
    ).transform_filter(
        state_selection
    ).transform_filter(
        f"(year_select == '{YEAR_ALL_INDICATOR}') || (datum.Year == year_select)"
    ).transform_filter(
        "(party_filter == 'All') || (datum.Party == party_filter)"
    ).properties(
        title={
            'text': 'Cancelled Grants Details',
            'subtitle': 'Average count (All States) or actual (State selected)',
            'anchor': 'start',
            'fontSize': 16
        },
        width=Q5_WIDTH,
        height=Q5_BAR_HEIGHT
    )

    # Q2: BUBBLE CHART + BUTTERFLY BAR CHART

    df_dummy = pd.DataFrame({'dummy': [1]})

    # --- Domain Setup ---
    max_grants_global = df_scatter['TotalGrants'].max()
    max_domain_bubble = math.ceil(max_grants_global / STEP_BUBBLE_X) * STEP_BUBBLE_X

    cancel_rate_max = df_scatter['CancelRate'].max()
    max_domain_rate_bubble = cancel_rate_max + (cancel_rate_max - df_scatter['CancelRate'].min()) * 0.25

    max_domain_vol_bar = max_domain_bubble
    max_rate_global = max(df_scatter['CancelRate'].max(), df_div['CancelRate'].max())
    max_domain_rate_bar = math.ceil(max_rate_global / 2) * 2

    ticks_vol = list(range(0, int(max_domain_vol_bar) + 1, STEP_BAR_X))
    ticks_rate = list(range(0, int(max_domain_rate_bar) + 1, STEP_RATE))
    ticks_bubble_y = [i for i in range(0, int(max_domain_rate_bubble) + 1, 2)]

    sort_order = alt.EncodingSortField(field='TotalGrants', op='max', order='descending')
    MODE_DEFAULT = "!length(data('dir_select_store'))"
    MODE_DRILLDOWN = "length(data('dir_select_store'))"

    # --- Bubble Chart ---
    bubble_layer = alt.Chart(df_scatter).mark_circle(
        opacity=0.8,
        stroke='white',
        strokeWidth=2
    ).encode(
        x=alt.X(
            'TotalGrants:Q', 
            title=None, 
            scale=alt.Scale(domainMin=0, domainMax=max_domain_bubble, nice=False)
        ),
        y=alt.Y(
            'CancelRate:Q', 
            title='Cancellation Rate (%)', 
            scale=alt.Scale(domain=[-2, max_domain_rate_bubble], nice=False), 
            axis=alt.Axis(values=ticks_bubble_y)
        ),
        size=alt.Size(
            'TerminationRate:Q', 
            scale=alt.Scale(domain=[0, 100], range=[150, 1500]),
            legend=alt.Legend(
                orient='none', 
                legendX=CHART_WIDTH_BUBBLE + 20, 
                legendY=1025, 
                title=['Termination Rate (%)'], 
                symbolFillColor='gray', 
                padding=10, 
                cornerRadius=5
            )
        ),
        color=alt.condition(
            dir_selection,
            alt.Color(
                'DirectorateAbbr:N', 
                legend=None, 
                scale=alt.Scale(range=PALETTE_DIRECTORATES), 
                sort=sort_order
            ),
            alt.value(COLOR_GRAY)
        ),
        tooltip=[
            alt.Tooltip('Directorate:N'),
            alt.Tooltip('TotalGrants:Q', format='.1f'),
            alt.Tooltip('CancelRate:Q', format='.1f'),
            alt.Tooltip('TerminationRate:Q', format='.1f')
        ]
    ).add_params(
        dir_selection
    ).transform_filter(
        alt.datum.Year == year_param
    ).properties(
        width=CHART_WIDTH_BUBBLE, 
        height=CHART_HEIGHT_BUBBLE
    )

    bubble_title_avg = alt.Chart(df_dummy).mark_text(
        dy=35, 
        fontSize=13,
        fontWeight='normal',
        text='Total Grants (Yearly Avg)'
    ).encode(
        x=alt.value(CHART_WIDTH_BUBBLE / 2), 
        y=alt.value(CHART_HEIGHT_BUBBLE)
    ).transform_filter(
        f"year_select == '{YEAR_ALL_INDICATOR}'"
    )

    bubble_title_norm = alt.Chart(df_dummy).mark_text(
        dy=35, 
        fontSize=13,
        fontWeight='normal', 
        text='Total Grants'
    ).encode(
        x=alt.value(CHART_WIDTH_BUBBLE / 2), 
        y=alt.value(CHART_HEIGHT_BUBBLE)
    ).transform_filter(
        f"year_select != '{YEAR_ALL_INDICATOR}'"
    )

    legend_directorate = alt.Chart(df_scatter).mark_circle(size=100).encode(
        y=alt.Y(
            'DirectorateAbbr:N', 
            axis=alt.Axis(orient='right', title=None, domain=False, ticks=False), 
            sort=sort_order, 
            scale=alt.Scale(padding=0)
        ),
        color=alt.Color(
            'DirectorateAbbr:N', 
            legend=None, 
            scale=alt.Scale(range=PALETTE_DIRECTORATES), 
            sort=sort_order
        )
    ).transform_filter(
        alt.datum.Year == year_param
    ).properties(
        width=50, 
        height=150, 
        title=alt.TitleParams(text='Directorate', anchor='start', fontSize=11, dx=10)
    )

    bubble_header = alt.Chart(df_dummy).mark_text(opacity=0).properties(
        width=CHART_WIDTH_BUBBLE + 65, 
        height=BUBBLE_HEADER_OFFSET
    )

    bubble_footer_avg = alt.Chart(df_dummy).mark_text( 
        fontSize=13,
        fontWeight='normal',
        color='#666',
        dy=-15, 
        text='Total Grants (Yearly Avg)'
    ).transform_filter(
        f"year_select == '{YEAR_ALL_INDICATOR}'"
    )
    
    bubble_footer_norm = alt.Chart(df_dummy).mark_text(
        fontSize=13,
        fontWeight='normal',
        color='#666',
        dy=-15, 
        text='Total Grants'
    ).transform_filter(
        f"year_select != '{YEAR_ALL_INDICATOR}'"
    )
    
    bubble_footer = alt.layer(
        bubble_footer_avg, 
        bubble_footer_norm
    ).properties(
        width=CHART_WIDTH_BUBBLE + 65, 
        height=FOOTER_HEIGHT
    )

    bubble_chart_layer = alt.hconcat(
        bubble_layer, 
        legend_directorate, 
        spacing=15
    ).resolve_scale(color='shared')
    
    q2_left_part = alt.vconcat(
        bubble_header, 
        bubble_chart_layer, 
        bubble_footer
    )

    # --- Butterfly Bar Chart ---
    head_vol_dir = alt.Chart(df_dummy).mark_text(
        fontWeight='bold', fontSize=12, dy=10, text='Volume (Directorates)'
    ).transform_filter(
        MODE_DEFAULT
    )
    
    head_vol_div = alt.Chart(df_dummy).mark_text(
        fontWeight='bold', fontSize=12, dy=10, text='Volume (Divisions)'
    ).transform_filter(
        MODE_DRILLDOWN
    )
    
    header_vol_layer = alt.layer(
        head_vol_dir, 
        head_vol_div
    ).properties(
        width=CHART_WIDTH_BAR, 
        height=HEADER_HEIGHT + BUTTERFLY_HEADER_OFFSET
    )

    head_risk_dir = alt.Chart(df_dummy).mark_text(
        fontWeight='bold', fontSize=12, dy=10, text='Impact (Directorates)'
    ).transform_filter(
        MODE_DEFAULT
    )
    
    head_risk_div = alt.Chart(df_dummy).mark_text(
        fontWeight='bold', fontSize=12, dy=10, text='Impact (Divisions)'
    ).transform_filter(
        MODE_DRILLDOWN
    )
    
    header_risk_layer = alt.layer(
        head_risk_dir, 
        head_risk_div
    ).properties(
        width=CHART_WIDTH_BAR, 
        height=HEADER_HEIGHT + BUTTERFLY_HEADER_OFFSET
    )

    header_spacer = alt.Chart(df_dummy).mark_text(text='').properties(
        width=CHART_WIDTH_LABEL, 
        height=HEADER_HEIGHT + BUTTERFLY_HEADER_OFFSET
    )

    # Default view (Directorates)
    base_def = alt.Chart(df_scatter).transform_filter(
        alt.datum.Year == year_param
    ).transform_filter(MODE_DEFAULT)

    def_left = base_def.mark_bar(color=COLOR_VOLUME).encode(
        y=alt.Y('DirectorateAbbr:N', axis=None, sort=sort_order),
        x=alt.X(
            'TotalGrants:Q', 
            sort='descending', 
            scale=alt.Scale(domainMin=0, domainMax=max_domain_vol_bar, nice=False), 
            axis=alt.Axis(values=ticks_vol, title=None)
        ),
        tooltip=[alt.Tooltip('Directorate:N'), alt.Tooltip('TotalGrants:Q', format='.1f')]
    ).properties(
        width=CHART_WIDTH_BAR, 
        height=CHART_HEIGHT_BUBBLE
    )

    def_mid = base_def.mark_text().encode(
        y=alt.Y('DirectorateAbbr:N', axis=None, sort=sort_order), 
        text='DirectorateAbbr:N'
    ).properties(
        width=CHART_WIDTH_LABEL, 
        height=CHART_HEIGHT_BUBBLE
    )

    def_right = base_def.mark_bar(color=COLOR_IMPACT).encode(
        y=alt.Y('DirectorateAbbr:N', axis=None, sort=sort_order),
        x=alt.X(
            'CancelRate:Q', 
            title='Cancellation Rate (%)', 
            scale=alt.Scale(domainMin=0, domainMax=max_domain_rate_bar, nice=False), 
            axis=alt.Axis(values=ticks_rate, titlePadding=21)
        ),
        tooltip=[alt.Tooltip('Directorate:N'), alt.Tooltip('CancelRate:Q', format='.1f')]
    ).properties(
        width=CHART_WIDTH_BAR, 
        height=CHART_HEIGHT_BUBBLE
    )

    # Drilldown view (Divisions)
    base_drill = alt.Chart(df_div).transform_filter(
        alt.datum.Year == year_param
    ).transform_filter(
        MODE_DRILLDOWN
    ).transform_filter(
        dir_selection
    ).transform_filter(
        alt.datum.TotalGrants > 0
    ).transform_calculate(
        TotalGrantsDisplay=f"max(datum.TotalGrants, {MIN_BAR_GRANTS})",
        CancelRateDisplay=f"max(datum.CancelRate, {MIN_BAR_RATE})"
    )

    drill_left = base_drill.mark_bar(color=COLOR_VOLUME).encode(
        y=alt.Y('DivisionAbbr:N', axis=None, sort=sort_order),
        x=alt.X(
            'TotalGrantsDisplay:Q', 
            sort='descending', 
            scale=alt.Scale(domainMin=0, domainMax=max_domain_vol_bar, nice=False), 
            axis=alt.Axis(values=ticks_vol, title=None)
        ),
        tooltip=[alt.Tooltip('Division:N'), alt.Tooltip('TotalGrants:Q', format='.1f')]
    ).properties(
        width=CHART_WIDTH_BAR, 
        height=CHART_HEIGHT_BUBBLE
    )

    drill_mid = base_drill.mark_text().encode(
        y=alt.Y('DivisionAbbr:N', axis=None, sort=sort_order), 
        text='DivisionAbbr:N'
    ).properties(
        width=CHART_WIDTH_LABEL, 
        height=CHART_HEIGHT_BUBBLE
    )

    drill_right = base_drill.mark_bar(color=COLOR_IMPACT).encode(
        y=alt.Y('DivisionAbbr:N', axis=None, sort=sort_order),
        x=alt.X(
            'CancelRateDisplay:Q', 
            scale=alt.Scale(domainMin=0, domainMax=max_domain_rate_bar, nice=False), 
            axis=alt.Axis(values=ticks_rate, title='Cancellation Rate (%)', titlePadding=21)
        ),
        tooltip=[alt.Tooltip('Division:N'), alt.Tooltip('CancelRate:Q', format='.1f')]
    ).properties(
        width=CHART_WIDTH_BAR, 
        height=CHART_HEIGHT_BUBBLE
    )

    # Footers
    footer_text_avg = alt.Chart(df_dummy).mark_text(
        fontSize=13,fontWeight='normal', color='#666', dy=-15, text='Total Grants (Yearly Avg)'
    ).transform_filter(f"year_select == '{YEAR_ALL_INDICATOR}'")
    
    footer_text_norm = alt.Chart(df_dummy).mark_text(
        fontSize=13,fontWeight='normal', color='#666', dy=-15, text='Total Grants'
    ).transform_filter(f"year_select != '{YEAR_ALL_INDICATOR}'")
    
    footer_vol = alt.layer(
        footer_text_avg, 
        footer_text_norm
    ).properties(
        width=CHART_WIDTH_BAR, 
        height=FOOTER_HEIGHT
    )
    
    footer_impact = alt.Chart(df_dummy).mark_text(opacity=0).properties(
        width=CHART_WIDTH_BAR, 
        height=FOOTER_HEIGHT
    )
    
    footer_center = alt.Chart(df_dummy).mark_text(opacity=0).properties(
        width=CHART_WIDTH_LABEL, 
        height=FOOTER_HEIGHT
    )

    # Assembly
    q2_right_part = alt.hconcat(
        alt.vconcat(
            header_vol_layer, 
            alt.layer(def_left, drill_left), 
            footer_vol
        ).resolve_scale(x='shared'),
        alt.vconcat(
            header_spacer, 
            alt.layer(def_mid, drill_mid), 
            footer_center
        ),
        alt.vconcat(
            header_risk_layer, 
            alt.layer(def_right, drill_right), 
            footer_impact
        ),
        spacing=10
    ).resolve_scale(y='independent')

    q2_chart = alt.hconcat(
        q2_left_part, 
        q2_right_part, 
        spacing=HCONCAT_SPACING
    ).resolve_scale(color='independent').properties(
        title=alt.TitleParams(
            text='Grant Distribution and Cancellation Rate by Directorate',
            subtitle='Click a directorate bubble to drill-down into divisions. Only major directorates (≥100 total grants across 2021-2025)',
            fontSize=16, offset=-10
        )
    )

    # Q4 LINE CHART

    # 2025 Annotation data
    df_annotation_2025 = pd.DataFrame({'Year': [2025]})
    
    q4_color_scale = alt.Scale(
    domain=['All', 'Democrat', 'Republican'],
    range=['#2E7D32', '#4A90D9', '#E8843C']
    )

    yearly_totals = df_complete.groupby('Year').agg(
    TotalBudget=('EstimatedBudget', 'sum')
    ).reset_index()
    yearly_totals['Group'] = 'All'

    yearly_party_totals = df_complete.groupby(['Year', 'Party']).agg(
        TotalBudget=('EstimatedBudget', 'sum')
    ).reset_index()
    
    yearly_party_totals['Group'] = yearly_party_totals['Party']
    combined_q4 = pd.concat([yearly_totals, yearly_party_totals], ignore_index=True)

    # Q4 & Q5.1 LINE CHARTS (FINAL VERSION)

    # --- Q4: Budget Evolution ---
    q4_y_max = combined_q4['TotalBudget'].max() * 1.05
    q4_color_scale = alt.Scale(domain=['All', 'Democrat', 'Republican'], range=[COLOR_ALL_PARTY, COLOR_DEMOCRAT, COLOR_REPUBLICAN])

    q4_base = alt.Chart(combined_q4).transform_filter(
        "(party_filter == 'All' && datum.Group == 'All') || (datum.Group == party_filter)"
    ).transform_calculate(TotalBudgetBillions='datum.TotalBudget / 1000000000')

    q4_line = q4_base.mark_line(strokeWidth=2).encode(
        x=alt.X('Year:O', axis=alt.Axis(labelAngle=0, title='Fiscal Year')),
        y=alt.Y('TotalBudgetBillions:Q', title='Budget ($B)', scale=alt.Scale(domain=[0, q4_y_max // 1000000000])),
        color=alt.Color('Group:N', scale=q4_color_scale, legend=alt.Legend(title='Party', orient='right')),
        opacity=alt.value(OPACITY_LINE)
    )

    q4_points = q4_base.mark_circle(size=POINT_SIZE_DEFAULT).encode(
        x='Year:O', y='TotalBudgetBillions:Q',
        color=alt.Color('Group:N', scale=q4_color_scale, legend=None),
        tooltip=['Year:O', 'Group:N', alt.Tooltip('TotalBudget:Q', format='$,.0f')]
    )

    q4_year_rule = alt.Chart(pd.DataFrame({'Year': YEARS_LIST})).mark_rule(
        strokeDash=[5, 5], strokeWidth=2, color='gray', opacity=OPACITY_YEAR_RULE
    ).encode(x='Year:O').transform_filter(f"year_select != '{YEAR_ALL_INDICATOR}'").transform_filter("datum.Year == year_select")

    q4_chart = (q4_line + q4_points + q4_year_rule).properties(
        title='Grants Total Budget Evolution Over Time',
        width=LINE_CHART_WIDTH, height=BAR_HEIGHT - Q4_HEIGHT_OFFSET
    )

    # --- Q5.1: State Grants Evolution ---
    q5_all_avg = df_state_grants.groupby('Year').agg(GrantCount=('GrantCount', 'mean')).reset_index()
    q5_all_avg['Group'] = 'All'
    q5_all_avg['StateName'] = 'All States (Avg)'

    q5_by_state = df_state_grants.copy()
    q5_by_state['Group'] = q5_by_state['Party']

    combined_q5_with_states = pd.concat([
        q5_all_avg[['Year', 'Group', 'GrantCount', 'StateName']],
        q5_by_state[['Year', 'Group', 'GrantCount', 'StateName', 'StateCode', 'Party']]
    ], ignore_index=True)

    def create_segments(df):
        segments = []
        for state in df['StateName'].unique():
            state_df = df[df['StateName'] == state].sort_values('Year')
            years = state_df['Year'].values
            counts = state_df['GrantCount'].values
            groups = state_df['Group'].values
            for i in range(len(years) - 1):
                segments.append({
                    'StateName': state, 'Year_from': years[i], 'Year_to': years[i + 1],
                    'Count_from': counts[i], 'Count_to': counts[i + 1], 'Group': groups[i + 1]
                })
        return pd.DataFrame(segments)

    q5_segments = create_segments(combined_q5_with_states)
    q5_y_max = combined_q5_with_states['GrantCount'].max() * 1.05
    q5_color_scale_grouped = alt.Scale(domain=['All', 'Democrat', 'Republican'], range=[COLOR_ALL_PARTY, COLOR_DEMOCRAT, COLOR_REPUBLICAN])

    q5_line_base = alt.Chart(q5_segments).transform_filter(
        "!length(data('state_click_store')) ? datum.Group == 'All' : true"
    ).transform_filter(state_selection).transform_filter(
        "(party_filter == 'All') || (datum.Group == 'All') || (datum.Group == party_filter)"
    )

    q5_part1_line = q5_line_base.mark_rule(strokeWidth=2, opacity=OPACITY_LINE).encode(
        x=alt.X('Year_from:O', title='Fiscal Year', axis=alt.Axis(labelAngle=0)), x2='Year_to:O',
        y=alt.Y('Count_from:Q', title='Grant Count (Avg/Actual)', scale=alt.Scale(domain=[0, q5_y_max])), y2='Count_to:Q',
        color=alt.Color('Group:N', scale=q5_color_scale_grouped, legend=None)
    )

    q5_points_base = alt.Chart(combined_q5_with_states).transform_filter(
        "!length(data('state_click_store')) ? datum.Group == 'All' : true"
    ).transform_filter(state_selection).transform_filter(
        "(party_filter == 'All') || (datum.Group == 'All') || (datum.Group == party_filter)"
    )

    q5_part1_points = q5_points_base.mark_circle(size=POINT_SIZE_DEFAULT).encode(
        x='Year:O', y=alt.Y('mean(GrantCount):Q', scale=alt.Scale(domain=[0, q5_y_max])),
        color=alt.Color('Group:N', scale=q5_color_scale_grouped),
        tooltip=[alt.Tooltip('Year:O', title='Year'), alt.Tooltip('StateName:N', aggregate='min', title='State'),
                alt.Tooltip('Group:N', title='Category'), alt.Tooltip('mean(GrantCount):Q', title='Count', format='.0f')]
    )

    q5_year_rule = alt.Chart(pd.DataFrame({'Year': YEARS_LIST})).mark_rule(
        strokeDash=[5, 5], strokeWidth=2, color='gray', opacity=OPACITY_YEAR_RULE
    ).encode(x='Year:O').transform_filter(f"year_select != '{YEAR_ALL_INDICATOR}'").transform_filter("datum.Year == year_select")

    q5_part1_chart = (q5_part1_line + q5_part1_points + q5_year_rule).properties(
        title={'text': 'State Grants Evolution (Average/Selected)'},
        width=LINE_CHART_WIDTH, height=LINE_CHART_HEIGHT
    )

    # FINAL DASHBOARD ASSEMBLY

    left_side = alt.vconcat(q1_row, q5_2_chart, spacing=VCONCAT_SPACING).resolve_scale(color='independent')

    right_side = alt.vconcat(q4_chart, q5_part1_chart, spacing=VCONCAT_SPACING).resolve_scale(x='shared')

    middle_row = alt.hconcat(left_side, right_side, spacing=HCONCAT_SPACING).resolve_scale(color='independent')

    final_dashboard = alt.vconcat(middle_row, q2_chart, spacing=BOTTOM_SPACING).add_params(
        year_param, topn_param, party_param
    ).properties(
        title=alt.TitleParams(
            text='NSF Grant Dashboard (2021-2025)',
            subtitle='Overview of grants and 2025 cancellations. Filter by Year/Party or click Map/Bubble to explore.',
            anchor='middle',
            fontSize=DASHBOARD_TITLE_FONT_SIZE,
            subtitleFontSize=DASHBOARD_SUBTITLE_FONT_SIZE,
            offset=DASHBOARD_TITLE_OFFSET
        )
    ).configure_view(stroke=None)

    return final_dashboard