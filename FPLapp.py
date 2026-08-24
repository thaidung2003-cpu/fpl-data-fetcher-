import streamlit as st
import pandas as pd
import numpy as np
import requests
import json

st.set_page_config(layout="wide", page_title="FPL Advanced Analytics")

# --- Custom D3 Visualization Component ---
def FPLGraph(data, x_axis_name, y_axis_name, title_text, footnotes, width=1300, height=750):
    data_json = json.dumps(data)
    footnotes_json = json.dumps(footnotes)

    d3_code = f"""
    <!DOCTYPE html>
    <meta charset="utf-8">
    <style>
    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #121212; color: #f2f2f2; margin: 0; padding: 0; }}
    .axis-label {{ font-size: 16px; font-weight: 500; fill: #f2f2f2; }}
    .tick text {{ font-size: 14px; fill: #f2f2f2; }}
    .grid line {{ stroke: #555; stroke-opacity: 0.5; stroke-dasharray: 2, 2; }}
    .label {{ font-size: 13px; font-weight: 400; fill: #fff; text-shadow: 1px 1px 2px #000; }}
    .title {{ font-size: 20px; font-weight: 500; fill: #fff; text-anchor: middle; }}
    .footnote {{ font-size: 12px; fill: #999; font-style: italic; }}
    .dot-group text {{ pointer-events: none; }}
    .dot-circle {{ stroke: #ffffff; stroke-width: 1px; }}
    </style>
    <body>
    <div id="chart-container"></div>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
    const data = {data_json};
    const xName = '{x_axis_name}';
    const yName = '{y_axis_name}';
    const titleText = '{title_text}';
    const footnotes = {footnotes_json};
    const width = {width};
    const height = {height};
    const margin = {{top: 50, right: 100, bottom: 90, left: 80}};
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.select("#chart-container").append("svg")
        .attr("width", width)
        .attr("height", height);

    // --- 2026/27 Premier League Official Team Colors Mapping (Primary & Secondary) ---
    const teamColors = {{
        'ARS': {{p: '#EF0107', s: '#FFFFFF'}}, // Arsenal
        'AVL': {{p: '#670E36', s: '#95BFE5'}}, // Aston Villa
        'BOU': {{p: '#DA291C', s: '#000000'}}, // Bournemouth
        'BRE': {{p: '#E30613', s: '#FFFFFF'}}, // Brentford
        'BHA': {{p: '#0057B8', s: '#FFFFFF'}}, // Brighton
        'CHE': {{p: '#034694', s: '#FFFFFF'}}, // Chelsea
        'COV': {{p: '#00BFFF', s: '#FFFFFF'}}, // Coventry City
        'CRY': {{p: '#1B458F', s: '#C4122E'}}, // Crystal Palace
        'EVE': {{p: '#003399', s: '#FFFFFF'}}, // Everton
        'FUL': {{p: '#FFFFFF', s: '#000000'}}, // Fulham
        'HUL': {{p: '#F5A12D', s: '#000000'}}, // Hull City
        'IPS': {{p: '#0054A6', s: '#FFFFFF'}}, // Ipswich Town
        'LEE': {{p: '#FFFFFF', s: '#1D428A'}}, // Leeds United
        'LIV': {{p: '#C8102E', s: '#FFFFFF'}}, // Liverpool
        'MCI': {{p: '#6CABDD', s: '#FFFFFF'}}, // Man City
        'MUN': {{p: '#DA020E', s: '#000000'}}, // Man Utd
        'NEW': {{p: '#000000', s: '#FFFFFF'}}, // Newcastle
        'NFO': {{p: '#DD0000', s: '#FFFFFF'}}, // Nottingham Forest
        'SUN': {{p: '#FF0000', s: '#FFFFFF'}}, // Sunderland
        'TOT': {{p: '#FFFFFF', s: '#132257'}}  // Tottenham
    }};

    const defs = svg.append("defs");
    
    // Generate a diagonal split gradient for every team
    for (const [team, colors] of Object.entries(teamColors)) {{
        const grad = defs.append("linearGradient")
            .attr("id", `grad-${{team}}`)
            .attr("x1", "0%")
            .attr("x2", "100%")
            .attr("y1", "0%")
            .attr("y2", "100%");
            
        grad.append("stop").attr("offset", "50%").attr("stop-color", colors.p);
        grad.append("stop").attr("offset", "50%").attr("stop-color", colors.s);
    }}

    const chart = svg.append("g")
        .attr("transform", `translate(${{margin.left}}, ${{margin.top}})`);

    const xMin = d3.min(data, d => d[xName]);
    const xMax = d3.max(data, d => d[xName]);
    const yMin = d3.min(data, d => d[yName]);
    const yMax = d3.max(data, d => d[yName]);

    const xScale = d3.scaleLinear()
        .domain([xMin * 0.9, xMax * 1.1])
        .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
        .domain([yMin * 0.9, yMax * 1.1])
        .range([innerHeight, 0]);

    // Grid Lines (Tick formats remain empty so the lines don't print rogue numbers)
    chart.append("g")
        .attr("class", "grid")
        .attr("transform", `translate(0, ${{innerHeight}})`)
        .call(d3.axisBottom(xScale).tickSize(-innerHeight).tickFormat(""));

    chart.append("g")
        .attr("class", "grid")
        .call(d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat(""));

    // Axes (Manual string formatting removed, allowing D3 to auto-scale decimals correctly)
    chart.append("g")
        .attr("transform", `translate(0, ${{innerHeight}})`)
        .call(d3.axisBottom(xScale).ticks(10));

    chart.append("g")
        .call(d3.axisLeft(yScale).ticks(10));

    svg.append("text")
        .attr("class", "title")
        .attr("x", width / 2)
        .attr("y", 30)
        .text(titleText);

    chart.append("text")
        .attr("class", "axis-label")
        .attr("x", innerWidth / 2)
        .attr("y", innerHeight + 50)
        .attr("text-anchor", "middle")
        .text(`${{xName}}`);

    chart.append("text")
        .attr("class", "axis-label")
        .attr("transform", "rotate(-90)")
        .attr("x", -innerHeight / 2)
        .attr("y", -50)
        .attr("text-anchor", "middle")
        .text(`${{yName}}`);

    const dots = chart.selectAll(".dot-group")
        .data(data)
        .enter().append("g")
        .attr("class", "dot-group")
        .attr("transform", d => `translate(${{xScale(d[xName])}}, ${{yScale(d[yName])}})`);

    // Apply the 2-color gradient to the circles
    dots.append("circle")
        .attr("class", "dot-circle")
        .attr("r", 10)
        .attr("fill", d => teamColors[d.Team] ? `url(#grad-${{d.Team}})` : '#2196F3')
        .attr("opacity", 0.95);

    // Label graph dots with the FPL Web Name
    dots.append("text")
        .attr("class", "label")
        .attr("x", 13)
        .attr("y", 4)
        .text(d => d['Web Name']);

    const footnoteGroup = svg.append("g")
        .attr("transform", `translate(${{margin.left}}, ${{height - 35}})`);

    footnotes.forEach((note, i) => {{
        const text = footnoteGroup.append("text")
            .attr("class", "footnote")
            .attr("x", i % 2 === 0 ? 0 : innerWidth)
            .attr("y", Math.floor(i / 2) * 20)
            .attr("text-anchor", i % 2 === 0 ? "start" : "end")
            .text(note);
    }});
    </script>
    </body>
    </html>
    """
    st.components.v1.html(d3_code, width=width, height=height, scrolling=False)


# --- Data Fetching and Processing ---
@st.cache_data
def get_fpl_data():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    data = requests.get(url).json()
    
    players = pd.DataFrame(data['elements'])
    teams = pd.DataFrame(data['teams'])
    positions = pd.DataFrame(data['element_types'])
    
    df = players.merge(teams[['id', 'short_name']], left_on='team', right_on='id', how='left')
    df = df.merge(positions[['id', 'singular_name_short']], left_on='element_type', right_on='id', how='left')
    
    for col in df.columns:
        if df[col].dtype == 'object' and col not in ['first_name', 'second_name', 'web_name', 'short_name', 'singular_name_short', 'photo', 'status', 'news']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    base_cols = [
        'first_name', 'second_name', 'web_name', 'short_name', 'singular_name_short', 'now_cost', 
        'total_points', 'selected_by_percent', 'form', 'points_per_game', 'minutes', 'starts',
        'goals_scored', 'assists', 'clean_sheets', 'goals_conceded', 'own_goals', 
        'yellow_cards', 'red_cards', 'saves', 'bonus', 'bps', 'influence', 'creativity', 'threat', 'ict_index', 
        'expected_goals', 'expected_assists', 'expected_goal_involvements', 'expected_goals_conceded',
        'defensive_contribution'
    ]
    
    native_per_90_cols = [c for c in df.columns if str(c).endswith('_per_90')]
    cols_to_keep = list(set(base_cols + native_per_90_cols))
    
    df = df[[c for c in cols_to_keep if c in df.columns]]
    
    rename_dict = {
        'first_name': 'First Name', 'second_name': 'Last Name', 'web_name': 'Web Name', 'short_name': 'Team', 'singular_name_short': 'Position', 
        'now_cost': 'Cost (M)', 'total_points': 'Total Points', 'selected_by_percent': 'Selected By (%)',
        'points_per_game': 'PPG', 'goals_scored': 'Goals', 'clean_sheets': 'Clean Sheets', 'goals_conceded': 'GC',
        'expected_goals': 'xG', 'expected_assists': 'xA', 'expected_goal_involvements': 'xGI', 
        'expected_goals_conceded': 'xGC', 'ict_index': 'ICT Index', 'bps': 'BPS', 'minutes': 'Minutes Played',
        'defensive_contribution': 'Defcons', 'starts': 'Starts',
        'expected_goals_per_90': 'xG90', 'expected_assists_per_90': 'xA90', 'expected_goal_involvements_per_90': 'xGI90',
        'expected_goals_conceded_per_90': 'xGC90', 'goals_conceded_per_90': 'GC90', 'saves_per_90': 'Saves90',
        'starts_per_90': 'Starts90', 'clean_sheets_per_90': 'Clean Sheets90', 'defensive_contribution_per_90': 'Defcons90'
    }
    df.rename(columns=rename_dict, inplace=True)
    df.columns = [col.replace('_', ' ').title() if col.islower() else col for col in df.columns]
    
    if 'Cost (M)' in df.columns:
        df['Cost (M)'] = df['Cost (M)'] / 10 

    if 'Minutes Played' in df.columns:
        df['Minutes Played'] = pd.to_numeric(df['Minutes Played'], errors='coerce').fillna(0)

    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    skip_90 = ['Cost (M)', 'Minutes Played', 'Chance Of Playing Next Round', 'Chance Of Playing This Round']
    
    for col in numeric_cols:
        if col not in skip_90 and not str(col).endswith('90'):
            new_col_90 = f"{col}90"
            if new_col_90 not in df.columns:
                df[new_col_90] = np.where(df['Minutes Played'] > 0, (df[col] / df['Minutes Played']) * 90, 0)
                df[new_col_90] = df[new_col_90].round(2)

    return df

df = get_fpl_data()

# --- Main App Interface ---
st.title("FPL Advanced Player Explorer")

# --- Sidebar Filters ---
st.sidebar.header("Filter Players")
search_name = st.sidebar.text_input("Look up by Name (separate by commas)")
selected_teams = st.sidebar.multiselect("Categorize by Team", sorted(df['Team'].unique()))
selected_positions = st.sidebar.multiselect("Categorize by Position", df['Position'].unique(), default=["DEF"])

max_mins_played = int(df['Minutes Played'].max()) if not df.empty and df['Minutes Played'].max() > 0 else 90
default_mins = min(1500, max_mins_played)

min_minutes = st.sidebar.number_input(
    "Minimum Minutes Played", 
    min_value=0, 
    max_value=max_mins_played, 
    value=default_mins, 
    step=10 if max_mins_played < 200 else 100
)

min_cost, max_cost = st.sidebar.slider(
    "Cost (M)", 
    float(df['Cost (M)'].min()), float(df['Cost (M)'].max()), 
    (float(df['Cost (M)'].min()), float(df['Cost (M)'].max())), 
    step=0.1
)

filtered_df = df.copy()

if search_name:
    # Multi-search: Split by commas, clear whitespace, build Regex pattern
    search_terms = [term.strip() for term in search_name.split(',') if term.strip()]
    search_pattern = '|'.join(search_terms)
    
    filtered_df = filtered_df[
        filtered_df['Last Name'].str.contains(search_pattern, case=False, na=False) |
        filtered_df['Web Name'].str.contains(search_pattern, case=False, na=False)
    ]

if selected_teams:
    filtered_df = filtered_df[filtered_df['Team'].isin(selected_teams)]
if selected_positions:
    filtered_df = filtered_df[filtered_df['Position'].isin(selected_positions)]

filtered_df = filtered_df[(filtered_df['Cost (M)'] >= min_cost) & (filtered_df['Cost (M)'] <= max_cost)]
filtered_df = filtered_df[filtered_df['Minutes Played'] >= min_minutes]

# --- Sidebar Display Options ---
st.sidebar.header("Display Options")

# Force logical column order: Core info first, then alphabetized stats
core_cols = ['First Name', 'Last Name', 'Web Name', 'Team', 'Position', 'Cost (M)', 'Total Points', 'Minutes Played']
other_cols = sorted([c for c in filtered_df.columns if c not in core_cols])
logical_columns = core_cols + other_cols

default_cols = ['Web Name', 'Team', 'Position', 'Cost (M)', 'Total Points', 'xGI90', 'Defcons90', 'Minutes Played']
selected_columns = st.sidebar.multiselect("Select Table Columns", logical_columns, default=[c for c in default_cols if c in logical_columns])
display_df = filtered_df[selected_columns]

# --- Graph Options & Axis Selection ---
st.sidebar.header("Graph Options")
show_graph = st.sidebar.toggle("Show Data Graph", value=True, key="show_data_graph_toggle")

graph_data = pd.DataFrame()
if show_graph:
    # Alphabetized graph axis selectors
    all_numeric_cols = sorted(filtered_df.select_dtypes(include=['float64', 'int64']).columns.tolist())
    
    st.sidebar.subheader("Select Graph Axes")
    x_axis = st.sidebar.selectbox("X-Axis", all_numeric_cols, index=all_numeric_cols.index('xGI90') if 'xGI90' in all_numeric_cols else 0, key="x_axis_select")
    y_axis = st.sidebar.selectbox("Y-Axis", all_numeric_cols, index=all_numeric_cols.index('Defcons90') if 'Defcons90' in all_numeric_cols else 1, key="y_axis_select")

    graph_cols_needed = list(set(['First Name', 'Last Name', 'Web Name', 'Position', 'Team'] + [x_axis, y_axis]))
    graph_base_df = filtered_df[[c for c in graph_cols_needed if c in filtered_df.columns]]

    col1, col2 = st.columns(2)
    with col1:
        x_min_val, x_max_val = float(graph_base_df[x_axis].min()), float(graph_base_df[x_axis].max())
        if x_min_val == x_max_val:
            x_max_val += 0.01
        x_step = 0.01 if (x_max_val - x_min_val) < 50 else 1.0
        x_range = st.slider(f"{x_axis} Range", x_min_val, x_max_val, (x_min_val, x_max_val), step=x_step)
    
    with col2:
        y_min_val, y_max_val = float(graph_base_df[y_axis].min()), float(graph_base_df[y_axis].max())
        if y_min_val == y_max_val:
            y_max_val += 1.0
        y_step = 0.01 if (y_max_val - y_min_val) < 50 else 1.0
        y_range = st.slider(f"{y_axis} Range", y_min_val, y_max_val, (y_min_val, y_max_val), step=y_step)
        
    graph_data = graph_base_df[(graph_base_df[x_axis] >= x_range[0]) & (graph_base_df[x_axis] <= x_range[1]) & (graph_base_df[y_axis] >= y_range[0]) & (graph_base_df[y_axis] <= y_range[1])]

# --- Data Table Rendering ---
st.write(f"Showing **{len(display_df)}** players after primary filters.")
st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- Graph Rendering ---
if show_graph and not graph_data.empty:
    st.header("Graph Data")
    filtered_pos_text = selected_positions[0] if len(selected_positions) == 1 else "Various"
    chart_title = f"£{min_cost:.1f}m-£{max_cost:.1f}m {filtered_pos_text} Data"
    
    footnotes_list = [
        f"Filtered by position: {', '.join(selected_positions) if selected_positions else 'ALL'}",
        f"Filtered by minute range: {min_minutes}+",
        f"Filtered by price range: £{min_cost:.1f}m - £{max_cost:.1f}m",
        f"Players in graph range: {len(graph_data)}"
    ]
    
    FPLGraph(graph_data.to_dict('records'), x_axis, y_axis, chart_title, footnotes_list, width=1300, height=750)
elif show_graph and graph_data.empty:
    st.info("No players match the combined table and graph axis filters. Try widening your slider ranges.")
