import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import difflib

st.set_page_config(layout="wide", page_title="FPL Advanced Analytics")

# --- Custom D3 Visualization Component ---
def FPLGraph(data, x_axis_name, y_axis_name, title_text, footnotes, show_labels=True, x_order="Ascending", y_order="Ascending", width=1300, height=750):
    data_json = json.dumps(data)
    footnotes_json = json.dumps(footnotes)
    show_labels_js = "true" if show_labels else "false"
    
    x_asc_js = "true" if x_order == "Ascending" else "false"
    y_asc_js = "true" if y_order == "Ascending" else "false"

    d3_code = f"""
    <!DOCTYPE html>
    <meta charset="utf-8">
    <style>
    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #121212; color: #f2f2f2; margin: 0; padding: 0; overflow: auto; }}
    
    ::-webkit-scrollbar {{ width: 14px; height: 14px; }}
    ::-webkit-scrollbar-track {{ background: #121212; }}
    ::-webkit-scrollbar-thumb {{ background: #444; border-radius: 10px; border: 4px solid #121212; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #666; }}
    * {{ scrollbar-width: thin; scrollbar-color: #444 #121212; }}

    .axis-label {{ font-size: 16px; font-weight: 500; fill: #f2f2f2; }}
    .tick text {{ font-size: 14px; fill: #f2f2f2; }}
    .grid line {{ stroke: #555; stroke-opacity: 0.5; stroke-dasharray: 2, 2; }}
    .title {{ font-size: 20px; font-weight: 500; fill: #fff; text-anchor: middle; }}
    .footnote {{ font-size: 12px; fill: #999; font-style: italic; }}
    .dot-circle {{ stroke: #ffffff; stroke-width: 1px; cursor: pointer; transition: stroke-width 0.1s; }}
    
    .label {{ 
        font-size: 12px; 
        font-weight: 500; 
        fill: #ffffff; 
        paint-order: stroke; 
        stroke: #121212; 
        stroke-width: 3px; 
        stroke-opacity: 0.9; 
        pointer-events: none; 
    }}

    .tooltip {{
        position: absolute;
        text-align: left;
        padding: 10px 14px;
        font-size: 14px;
        background: rgba(25, 25, 25, 0.95);
        color: #fff;
        border: 1px solid #555;
        border-radius: 6px;
        pointer-events: none;
        opacity: 0;
        z-index: 100;
        box-shadow: 2px 4px 10px rgba(0,0,0,0.6);
        line-height: 1.5;
    }}
    .tooltip-name {{ font-weight: bold; font-size: 17px; color: #FFEB3B; margin-bottom: 5px; border-bottom: 1px solid #555; padding-bottom: 3px; }}
    </style>
    <body>
    <div id="chart-container"></div>
    <div id="tooltip" class="tooltip"></div>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
    const data = {data_json};
    const xName = '{x_axis_name}';
    const yName = '{y_axis_name}';
    const titleText = '{title_text}';
    const footnotes = {footnotes_json};
    const width = {width};
    const height = {height};
    const showLabels = {show_labels_js};
    const xAsc = {x_asc_js};
    const yAsc = {y_asc_js};
    
    const margin = {{top: 50, right: 60, bottom: 90, left: 80}};
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.select("#chart-container").append("svg")
        .attr("width", width)
        .attr("height", height);
        
    const tooltip = d3.select("#tooltip");

    const teamColors = {{
        'ARS': {{p: '#EF0107', s: '#FFFFFF'}}, 'AVL': {{p: '#670E36', s: '#95BFE5'}},
        'BOU': {{p: '#DA291C', s: '#000000'}}, 'BRE': {{p: '#E30613', s: '#FFFFFF'}},
        'BHA': {{p: '#0057B8', s: '#FFFFFF'}}, 'CHE': {{p: '#034694', s: '#FFFFFF'}},
        'COV': {{p: '#00BFFF', s: '#FFFFFF'}}, 'CRY': {{p: '#1B458F', s: '#C4122E'}},
        'EVE': {{p: '#003399', s: '#FFFFFF'}}, 'FUL': {{p: '#FFFFFF', s: '#000000'}},
        'HUL': {{p: '#F5A12D', s: '#000000'}}, 'IPS': {{p: '#0054A6', s: '#FFFFFF'}},
        'LEE': {{p: '#FFFFFF', s: '#1D428A'}}, 'LIV': {{p: '#C8102E', s: '#FFFFFF'}},
        'MCI': {{p: '#6CABDD', s: '#FFFFFF'}}, 'MUN': {{p: '#DA020E', s: '#000000'}},
        'NEW': {{p: '#000000', s: '#FFFFFF'}}, 'NFO': {{p: '#DD0000', s: '#FFFFFF'}},
        'SUN': {{p: '#FF0000', s: '#FFFFFF'}}, 'TOT': {{p: '#FFFFFF', s: '#132257'}}
    }};

    const defs = svg.append("defs");
    for (const [team, colors] of Object.entries(teamColors)) {{
        const grad = defs.append("linearGradient").attr("id", `grad-${{team}}`).attr("x1", "0%").attr("x2", "100%").attr("y1", "0%").attr("y2", "100%");
        grad.append("stop").attr("offset", "50%").attr("stop-color", colors.p);
        grad.append("stop").attr("offset", "50%").attr("stop-color", colors.s);
    }}

    const chart = svg.append("g").attr("transform", `translate(${{margin.left}}, ${{margin.top}})`);

    const xMin = d3.min(data, d => d[xName]);
    const xMax = d3.max(data, d => d[xName]);
    const yMin = d3.min(data, d => d[yName]);
    const yMax = d3.max(data, d => d[yName]);

    const xDomain = xAsc ? [xMin * 0.95, xMax * 1.05] : [xMax * 1.05, xMin * 0.95];
    const yDomain = yAsc ? [yMin * 0.95, yMax * 1.05] : [yMax * 1.05, yMin * 0.95];

    const xScale = d3.scaleLinear().domain(xDomain).range([0, innerWidth]);
    const yScale = d3.scaleLinear().domain(yDomain).range([innerHeight, 0]);

    chart.append("g").attr("class", "grid").attr("transform", `translate(0, ${{innerHeight}})`).call(d3.axisBottom(xScale).tickSize(-innerHeight).tickFormat(""));
    chart.append("g").attr("class", "grid").call(d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat(""));
    chart.append("g").attr("transform", `translate(0, ${{innerHeight}})`).call(d3.axisBottom(xScale).ticks(10));
    chart.append("g").call(d3.axisLeft(yScale).ticks(10));

    svg.append("text").attr("class", "title").attr("x", width / 2).attr("y", 30).text(titleText);
    chart.append("text").attr("class", "axis-label").attr("x", innerWidth / 2).attr("y", innerHeight + 45).attr("text-anchor", "middle").text(`${{xName}}`);
    chart.append("text").attr("class", "axis-label").attr("transform", "rotate(-90)").attr("x", -innerHeight / 2).attr("y", -45).attr("text-anchor", "middle").text(`${{yName}}`);

    const dots = chart.selectAll(".dot-group")
        .data(data)
        .enter().append("g")
        .attr("class", "dot-group")
        .attr("transform", d => `translate(${{xScale(d[xName])}}, ${{yScale(d[yName])}})`);

    dots.append("circle")
        .attr("class", "dot-circle")
        .attr("r", 9)
        .attr("fill", d => teamColors[d.Team] ? `url(#grad-${{d.Team}})` : '#2196F3')
        .attr("opacity", 0.9)
        .on("mouseover", function(event, d) {{
            d3.select(this).attr("stroke", "#FFEB3B").attr("stroke-width", 3).attr("opacity", 1);
            tooltip.style("opacity", 1)
                   .html(`<div class='tooltip-name'>${{d['Web Name']}}</div>
                          Team: <b>${{d.Team}}</b> | Pos: <b>${{d.Position}}</b><br>
                          Cost: <b>£${{d['Cost (M)']}}m</b><br><br>
                          ${{xName}}: <b>${{d[xName]}}</b><br>
                          ${{yName}}: <b>${{d[yName]}}</b>`);
        }})
        .on("mousemove", function(event) {{
            const tooltipWidth = tooltip.node().offsetWidth;
            const tooltipHeight = tooltip.node().offsetHeight;
            let xPos = event.pageX + 20;
            let yPos = event.pageY - 20;
            
            if (xPos + tooltipWidth > window.innerWidth) {{ xPos = event.pageX - tooltipWidth - 20; }}
            if (yPos + tooltipHeight > window.innerHeight) {{ yPos = event.pageY - tooltipHeight - 10; }}
            if (yPos < 0) {{ yPos = event.pageY + 20; }}
            
            tooltip.style("left", xPos + "px")
                   .style("top", yPos + "px");
        }})
        .on("mouseout", function(event, d) {{
            d3.select(this).attr("stroke", "#ffffff").attr("stroke-width", 1).attr("opacity", 0.9);
            tooltip.style("opacity", 0);
        }});

    if (showLabels) {{
        dots.append("text")
            .attr("class", "label")
            .attr("x", 13)
            .attr("y", 4)
            .text(d => d['Web Name']);
    }}

    const footnoteGroup = svg.append("g").attr("transform", `translate(${{margin.left}}, ${{height - 35}})`);
    footnotes.forEach((note, i) => {{
        footnoteGroup.append("text").attr("class", "footnote").attr("x", i % 2 === 0 ? 0 : innerWidth).attr("y", Math.floor(i / 2) * 20).attr("text-anchor", i % 2 === 0 ? "start" : "end").text(note);
    }});
    </script>
    </body>
    </html>
    """
    st.components.v1.html(d3_code, height=height, scrolling=True)

# --- Data Fetching and Processing ---
@st.cache_data(ttl=3600)
def get_fpl_data():
    # 1. Fetch Official FPL Data Online
    try:
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        fpl_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        fpl_response = requests.get(url, headers=fpl_headers)
        fpl_response.raise_for_status() 
        data = fpl_response.json()
        
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
            'goals_scored', 'assists', 'clean_sheets', 'goals_conceded'
        ]
        
        df = df[[c for c in base_cols if c in df.columns]]
        
        rename_dict = {
            'first_name': 'First Name', 'second_name': 'Last Name', 'web_name': 'Web Name', 'short_name': 'Team', 'singular_name_short': 'Position', 
            'now_cost': 'Cost (M)', 'total_points': 'Total Points', 'selected_by_percent': 'Selected By (%)',
            'points_per_game': 'PPG', 'goals_scored': 'Goals', 'clean_sheets': 'Clean Sheets', 'goals_conceded': 'GC',
            'minutes': 'Minutes Played', 'starts': 'Starts'
        }
        df.rename(columns=rename_dict, inplace=True)
        
        if 'Cost (M)' in df.columns:
            df['Cost (M)'] = df['Cost (M)'] / 10 
        if 'Minutes Played' in df.columns:
            df['Minutes Played'] = pd.to_numeric(df['Minutes Played'], errors='coerce').fillna(0)

    except Exception as e:
        st.sidebar.error(f"Failed to fetch FPL base data. Error: {e}")
        return pd.DataFrame()

    # 2. Read Local JSON File directly from repository
    try:
        npxg_df = pd.read_json("league-players.json")
        
        df['Full Name'] = df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)
        fpl_full_names = df['Full Name'].tolist()
        fpl_web_names = df['Web Name'].tolist()
        web_to_full_map = df.set_index('Web Name')['Full Name'].to_dict()
        
        match_dict = {}
        for custom_name in npxg_df['player']:
            clean_name = str(custom_name).strip()
            matches = difflib.get_close_matches(clean_name, fpl_full_names, n=1, cutoff=0.65)
            if matches:
                match_dict[custom_name] = matches[0]
            else:
                web_matches = difflib.get_close_matches(clean_name, fpl_web_names, n=1, cutoff=0.6)
                if web_matches:
                    match_dict[custom_name] = web_to_full_map[web_matches[0]]
                    
        npxg_df['matched_full_name'] = npxg_df['player'].map(match_dict)
        npxg_clean = npxg_df.dropna(subset=['matched_full_name']).drop_duplicates(subset=['matched_full_name'])
        
        df = df.merge(npxg_clean[['matched_full_name', 'NPxG', 'NPxG90']], left_on='Full Name', right_on='matched_full_name', how='left')
        
        df['NPxG'] = df['NPxG'].fillna(0.0)
        df['NPxG90'] = df['NPxG90'].fillna(0.0)
        df.drop(columns=['matched_full_name', 'Full Name'], inplace=True)
            
    except Exception as e:
        st.sidebar.warning(f"Could not load league-players.json. Error: {e}")

    return df 
# --- Main App Interface ---
st.title("FPL Advanced Player Explorer")

# Safe handling if data failed to load or returned None
if not isinstance(df, pd.DataFrame) or df.empty:
    st.warning("Data failed to load. Please check the error messages in the sidebar.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filter Players")
search_name = st.sidebar.text_input("Look up by Web Name (separate by commas)")

safe_teams = sorted([str(x) for x in df['Team'].dropna().unique()]) if 'Team' in df.columns else []
selected_teams = st.sidebar.multiselect("Categorize by Team", safe_teams)

safe_positions = sorted([str(x) for x in df['Position'].dropna().unique()]) if 'Position' in df.columns else []
selected_positions = st.sidebar.multiselect("Categorize by Position", safe_positions, default=safe_positions)

max_mins_played = int(df['Minutes Played'].max()) if not df.empty and df['Minutes Played'].max() > 0 else 90
min_minutes = st.sidebar.number_input(
    "Minimum Minutes Played", 
    min_value=0, 
    max_value=max_mins_played, 
    value=0, 
    step=10 if max_mins_played < 200 else 100
)

min_cost, max_cost = st.sidebar.slider(
    "Cost (M)", 
    float(df['Cost (M)'].min()) if not df.empty else 0.0, 
    float(df['Cost (M)'].max()) if not df.empty else 15.0, 
    (float(df['Cost (M)'].min()) if not df.empty else 0.0, float(df['Cost (M)'].max()) if not df.empty else 15.0), 
    step=0.1
)

filtered_df = df.copy()

if search_name:
    search_terms = [term.strip() for term in search_name.split(',') if term.strip()]
    search_pattern = '|'.join(search_terms)
    filtered_df = filtered_df[filtered_df['Web Name'].str.contains(search_pattern, case=False, na=False)]

if selected_teams:
    filtered_df = filtered_df[filtered_df['Team'].isin(selected_teams)]
if selected_positions:
    filtered_df = filtered_df[filtered_df['Position'].isin(selected_positions)]

if not filtered_df.empty and 'Cost (M)' in filtered_df.columns:
    filtered_df = filtered_df[(filtered_df['Cost (M)'] >= min_cost) & (filtered_df['Cost (M)'] <= max_cost)]
if not filtered_df.empty and 'Minutes Played' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Minutes Played'] >= min_minutes]

# --- Sidebar Display Options ---
st.sidebar.header("Display Options")

core_cols = ['First Name', 'Last Name', 'Web Name', 'Team', 'Position', 'Cost (M)', 'Total Points', 'Minutes Played']
other_cols = sorted([c for c in filtered_df.columns if c not in core_cols])
logical_columns = [c for c in core_cols if c in filtered_df.columns] + other_cols

# Dynamically pick up the custom NPxG columns to show in the table automatically
x_cols_pulled = [c for c in other_cols if c.lower().startswith('x') or 'npxg' in c.lower()]
default_cols = [c for c in ['Web Name', 'Team', 'Position', 'Cost (M)', 'Total Points', 'Minutes Played'] if c in logical_columns] + x_cols_pulled
selected_columns = st.sidebar.multiselect("Select Table Columns", logical_columns, default=default_cols)
display_df = filtered_df[selected_columns]

# --- Graph Options & Axis Selection ---
st.sidebar.header("Graph Options")
show_graph = st.sidebar.toggle("Show Data Graph", value=True, key="show_data_graph_toggle")
show_labels = st.sidebar.toggle("Show Player Labels on Graph", value=True, key="show_labels_toggle")

graph_width = st.sidebar.slider("Chart Width (px)", min_value=800, max_value=4000, value=1300, step=100)
graph_height = st.sidebar.slider("Chart Height (px)", min_value=500, max_value=3000, value=750, step=50)

if show_graph:
    all_numeric_cols = sorted(filtered_df.select_dtypes(include=['float64', 'int64']).columns.tolist())
    
    if all_numeric_cols:
        st.sidebar.subheader("Select Graph Axes")
        
        default_x = 'Cost (M)' if 'Cost (M)' in all_numeric_cols else all_numeric_cols[0]
        # Automatically make the Y-Axis NPxG if successfully parsed
        default_y = 'NPxG' if 'NPxG' in all_numeric_cols else ('Total Points' if 'Total Points' in all_numeric_cols else all_numeric_cols[-1])
        
        x_axis = st.sidebar.selectbox("X-Axis", all_numeric_cols, index=all_numeric_cols.index(default_x), key="x_axis_select")
        x_order = st.sidebar.radio("X-Axis Order", ["Ascending", "Descending"], horizontal=True, key="x_axis_order")
        
        y_axis = st.sidebar.selectbox("Y-Axis", all_numeric_cols, index=all_numeric_cols.index(default_y), key="y_axis_select")
        y_order = st.sidebar.radio("Y-Axis Order", ["Ascending", "Descending"], horizontal=True, key="y_axis_order")

# --- Data Table Rendering ---
st.write(f"Showing **{len(display_df)}** players after primary filters.")
st.dataframe(display_df.style.format(precision=2), use_container_width=True, hide_index=True)

# --- Graph Rendering ---
if show_graph and all_numeric_cols:
    st.divider()
    st.header("Graph Data")
    
    graph_cols_needed = list(set(['First Name', 'Last Name', 'Web Name', 'Position', 'Team', 'Cost (M)'] + [x_axis, y_axis]))
    graph_base_df = filtered_df[[c for c in graph_cols_needed if c in filtered_df.columns]]

    st.markdown("##### Adjust Axis Ranges to Zoom")
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

    if not graph_data.empty:
        filtered_pos_text = selected_positions[0] if len(selected_positions) == 1 else "Various"
        chart_title = f"£{min_cost:.1f}m-£{max_cost:.1f}m {filtered_pos_text} Data"
        
        footnotes_list = [
            f"Filtered by position: {', '.join(selected_positions) if selected_positions else 'ALL'}",
            f"Filtered by minute range: {min_minutes}+",
            f"Filtered by price range: £{min_cost:.1f}m - £{max_cost:.1f}m",
            f"Players in graph range: {len(graph_data)}"
        ]
        
        FPLGraph(
            graph_data.to_dict('records'), 
            x_axis, 
            y_axis, 
            chart_title, 
            footnotes_list, 
            show_labels=show_labels, 
            x_order=x_order, 
            y_order=y_order, 
            width=graph_width, 
            height=graph_height
        )
    else:
        st.info("No players match the combined table and graph axis filters. Try widening your slider ranges.")
