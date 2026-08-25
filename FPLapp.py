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
def fetch_fpl_data():
    # 1. Fetch Official FPL Data Online with a spoofed User-Agent
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

    # 2. Integrate Custom Scraped NPxG Data
    try:
        custom_npxg_json = """[{"player":"Jack Hinshelwood","team":"Brighton","NPxG":1.4,"NPxG90":1.83},{"player":"Martin Odegaard","team":"Arsenal","NPxG":0.23,"NPxG90":0.27},{"player":"Semi Ajayi","team":"Hull","NPxG":0.71,"NPxG90":0.96},{"player":"Kai Havertz","team":"Arsenal","NPxG":0.1,"NPxG90":0.1},{"player":"Joe Willock","team":"Newcastle United","NPxG":0.07,"NPxG90":0.2},{"player":"Bukayo Saka","team":"Arsenal","NPxG":0.78,"NPxG90":1},{"player":"Marc Guehi","team":"Manchester City","NPxG":0.65,"NPxG90":0.65},{"player":"João Pedro","team":"Chelsea","NPxG":0.67,"NPxG90":0.67},{"player":"Cole Palmer","team":"Chelsea","NPxG":0.57,"NPxG90":0.61},{"player":"Anthony Elanga","team":"Newcastle United","NPxG":0.28,"NPxG90":0.33},{"player":"Vitaly Janelt","team":"Brentford","NPxG":0.49,"NPxG90":0.49},{"player":"Kiernan Dewsbury-Hall","team":"Everton","NPxG":0.19,"NPxG90":0.19},{"player":"Dominik Szoboszlai","team":"Liverpool","NPxG":0.07,"NPxG90":0.07},{"player":"Josko Gvardiol","team":"Manchester City","NPxG":0.41,"NPxG90":0.41},{"player":"Anton Stach","team":"Leeds","NPxG":0.11,"NPxG90":0.11},{"player":"Marcus Tavernier","team":"Bournemouth","NPxG":0.48,"NPxG90":0.48},{"player":"Keane Lewis-Potter","team":"Brentford","NPxG":0.58,"NPxG90":0.58},{"player":"Michael Kayode","team":"Brentford","NPxG":0.82,"NPxG90":0.95},{"player":"Cody Gakpo","team":"Liverpool","NPxG":0.23,"NPxG90":0.23},{"player":"Gonzalo García","team":"Fulham","NPxG":0.8,"NPxG90":0.8},{"player":"Nobel Mendy","team":"Hull","NPxG":0.53,"NPxG90":0.72},{"player":"Joshua King","team":"Fulham","NPxG":0.12,"NPxG90":0.12},{"player":"Morgan Rogers","team":"Chelsea","NPxG":0.56,"NPxG90":0.6},{"player":"Thierno Barry","team":"Everton","NPxG":0.59,"NPxG90":0.64},{"player":"Jack Clarke","team":"Ipswich","NPxG":0.1,"NPxG90":0.5},{"player":"Maxim De Cuyper","team":"Brighton","NPxG":1.38,"NPxG90":1.5},{"player":"Emersonn","team":"Ipswich","NPxG":0.61,"NPxG90":0.81},{"player":"Nilson Angulo","team":"Sunderland","NPxG":0.12,"NPxG90":0.17},{"player":"Fabian Schär","team":"Newcastle United","NPxG":0,"NPxG90":0},{"player":"Bernd Leno","team":"Fulham","NPxG":0,"NPxG90":0},{"player":"Granit Xhaka","team":"Sunderland","NPxG":0,"NPxG90":0},{"player":"Pascal Groß","team":"Brighton","NPxG":0,"NPxG90":0},{"player":"Callum Wilson","team":"Brentford","NPxG":0.08,"NPxG90":1.27},{"player":"Alex Iwobi","team":"Fulham","NPxG":0,"NPxG90":0},{"player":"Marcus Rashford","team":"Manchester United","NPxG":0,"NPxG90":0},{"player":"Paddy McNair","team":"Hull","NPxG":0,"NPxG90":0},{"player":"Ross Barkley","team":"Aston Villa","NPxG":0.1,"NPxG90":0.11},{"player":"Jack Grealish","team":"Manchester City","NPxG":0,"NPxG90":0},{"player":"Ola Aina","team":"Nottingham Forest","NPxG":0.04,"NPxG90":0.04},{"player":"Jordan Pickford","team":"Everton","NPxG":0,"NPxG90":0},{"player":"Adam Smith","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Virgil van Dijk","team":"Liverpool","NPxG":0.12,"NPxG90":0.12},{"player":"Matt Targett","team":"Hull","NPxG":0,"NPxG90":0},{"player":"Luke Shaw","team":"Manchester United","NPxG":0,"NPxG90":0},{"player":"Tyrone Mings","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Matt Grimes","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Gianluigi Donnarumma","team":"Manchester City","NPxG":0,"NPxG90":0},{"player":"Bruno Fernandes","team":"Manchester United","NPxG":0.04,"NPxG90":0.04},{"player":"Alisson","team":"Liverpool","NPxG":0,"NPxG90":0},{"player":"Sasa Lukic","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"James Tarkowski","team":"Everton","NPxG":0.05,"NPxG90":0.05},{"player":"Dominic Solanke","team":"Tottenham","NPxG":0.04,"NPxG90":0.18},{"player":"Harry Maguire","team":"Manchester United","NPxG":0.06,"NPxG90":0.06},{"player":"Andrew Robertson","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Oliver McBurnie","team":"Hull","NPxG":0.44,"NPxG90":0.44},{"player":"Lewis Cook","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Chuba Akpom","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Emiliano Buendía","team":"Aston Villa","NPxG":0.12,"NPxG90":0.12},{"player":"Mateo Kovacic","team":"Manchester City","NPxG":0,"NPxG90":0},{"player":"Issa Diop","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Olivier Boscagli","team":"Brighton","NPxG":0,"NPxG90":0},{"player":"Chris Wood","team":"Nottingham Forest","NPxG":0.06,"NPxG90":0.2},{"player":"Alexander Isak","team":"Liverpool","NPxG":1.41,"NPxG90":1.41},{"player":"Mikel Merino","team":"Arsenal","NPxG":0.14,"NPxG90":1.08},{"player":"Declan Rice","team":"Arsenal","NPxG":0.04,"NPxG90":0.05},{"player":"Dominic Calvert-Lewin","team":"Leeds","NPxG":0.16,"NPxG90":0.16},{"player":"Harry Wilson","team":"Leeds","NPxG":0,"NPxG90":0},{"player":"Gabriel","team":"Arsenal","NPxG":0.03,"NPxG90":0.03},{"player":"Thomas Meunier","team":"Sunderland","NPxG":0.05,"NPxG90":0.05},{"player":"Ibrahim Sangare","team":"Nottingham Forest","NPxG":0.01,"NPxG90":0.01},{"player":"Jean-Philippe Mateta","team":"Crystal Palace","NPxG":1.32,"NPxG90":1.77},{"player":"Yoane Wissa","team":"Newcastle United","NPxG":0.97,"NPxG90":0.97},{"player":"Boubacar Kamara","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Youri Tielemans","team":"Manchester United","NPxG":0.03,"NPxG90":0.04},{"player":"Richarlison","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Lewis Dunk","team":"Brighton","NPxG":0,"NPxG90":0},{"player":"Phil Foden","team":"Manchester City","NPxG":0.1,"NPxG90":0.11},{"player":"Jacob Murphy","team":"Newcastle United","NPxG":0,"NPxG90":0},{"player":"Victor Lindelöf","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Rodrigo Bentancur","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Daichi Kamada","team":"Crystal Palace","NPxG":0,"NPxG90":0},{"player":"Timothy Castagne","team":"Fulham","NPxG":0.07,"NPxG90":0.07},{"player":"Nikola Milenkovic","team":"Nottingham Forest","NPxG":0.12,"NPxG90":0.12},{"player":"Pau Torres","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Ethan Ampadu","team":"Leeds","NPxG":0,"NPxG90":0},{"player":"Joe Rodon","team":"Leeds","NPxG":0.03,"NPxG90":0.03},{"player":"Pedro Neto","team":"Chelsea","NPxG":0.06,"NPxG90":0.41},{"player":"Eddie Nketiah","team":"Crystal Palace","NPxG":0.31,"NPxG90":0.46},{"player":"Bryan Mbeumo","team":"Manchester United","NPxG":0.55,"NPxG90":0.55},{"player":"Harvey Barnes","team":"Newcastle United","NPxG":0.06,"NPxG90":0.06},{"player":"Dwight McNeil","team":"Crystal Palace","NPxG":0.02,"NPxG90":0.03},{"player":"Jaka Bijol","team":"Leeds","NPxG":0.08,"NPxG90":0.08},{"player":"James Maddison","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Ryan Sessegnon","team":"Fulham","NPxG":0.04,"NPxG90":0.23},{"player":"Morgan Gibbs-White","team":"Nottingham Forest","NPxG":0.14,"NPxG90":0.14},{"player":"Matz Sels","team":"Nottingham Forest","NPxG":0,"NPxG90":0},{"player":"Georginio Rutter","team":"Brighton","NPxG":0.07,"NPxG90":0.07},{"player":"Justin Kluivert","team":"Bournemouth","NPxG":0.08,"NPxG90":0.09},{"player":"Sean Longstaff","team":"Leeds","NPxG":0,"NPxG90":0},{"player":"Matheus Cunha","team":"Manchester United","NPxG":0.19,"NPxG90":0.2},{"player":"Wilson Isidor","team":"Sunderland","NPxG":0,"NPxG90":0},{"player":"Mathias Jensen","team":"Brentford","NPxG":0.09,"NPxG90":0.12},{"player":"Ryan John Giles","team":"Hull","NPxG":0.03,"NPxG90":0.03},{"player":"Diogo Dalot","team":"Manchester United","NPxG":0,"NPxG90":0},{"player":"Ben White","team":"Arsenal","NPxG":0.13,"NPxG90":0.13},{"player":"Tyler Adams","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Reinildo","team":"Sunderland","NPxG":0,"NPxG90":0},{"player":"James Garner","team":"Everton","NPxG":0,"NPxG90":0},{"player":"Martín Zubimendi","team":"Arsenal","NPxG":0,"NPxG90":0},{"player":"Dean Henderson","team":"Crystal Palace","NPxG":0,"NPxG90":0},{"player":"John Egan","team":"Hull","NPxG":0,"NPxG90":0},{"player":"John McGinn","team":"Aston Villa","NPxG":0.03,"NPxG90":0.04},{"player":"James Justin","team":"Leeds","NPxG":0,"NPxG90":0},{"player":"Xaver Schlager","team":"Nottingham Forest","NPxG":0,"NPxG90":0},{"player":"Taiwo Awoniyi","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Caoimhin Kelleher","team":"Brentford","NPxG":0,"NPxG90":0},{"player":"Takehiro Tomiyasu","team":"Crystal Palace","NPxG":0,"NPxG90":0},{"player":"Sandro Tonali","team":"Tottenham","NPxG":0.03,"NPxG90":0.03},{"player":"Evann Guessand","team":"Crystal Palace","NPxG":0.04,"NPxG90":0.16},{"player":"Arnaud Kalimuendo Muinga","team":"Nottingham Forest","NPxG":0,"NPxG90":0},{"player":"Reece James","team":"Chelsea","NPxG":0.08,"NPxG90":0.08},{"player":"Ronald Araújo","team":"Liverpool","NPxG":0,"NPxG90":0},{"player":"Mathis Cherki","team":"Manchester City","NPxG":0,"NPxG90":0},{"player":"Riccardo Calafiori","team":"Arsenal","NPxG":0.08,"NPxG90":0.09},{"player":"Neco Williams","team":"Nottingham Forest","NPxG":0,"NPxG90":0},{"player":"Tyrick Mitchell","team":"Crystal Palace","NPxG":0,"NPxG90":0},{"player":"Erling Haaland","team":"Manchester City","NPxG":0.75,"NPxG90":0.75},{"player":"Sander Berge","team":"Fulham","NPxG":0.04,"NPxG90":0.04},{"player":"Malick Thiaw","team":"Newcastle United","NPxG":0,"NPxG90":0},{"player":"Alexis Mac Allister","team":"Liverpool","NPxG":0,"NPxG90":0},{"player":"Florian Wirtz","team":"Liverpool","NPxG":0.23,"NPxG90":0.32},{"player":"Luca Netz","team":"Nottingham Forest","NPxG":0,"NPxG90":0},{"player":"Chris Richards","team":"Crystal Palace","NPxG":0,"NPxG90":0},{"player":"Jarrad Branthwaite","team":"Everton","NPxG":0,"NPxG90":0},{"player":"Bobby Thomas","team":"Coventry","NPxG":0.01,"NPxG90":0.01},{"player":"Jorge Cuenca","team":"Fulham","NPxG":0,"NPxG90":0},{"player":"Ellis Simms","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Sven Botman","team":"Newcastle United","NPxG":0,"NPxG90":0},{"player":"Adrien Truffert","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Enzo Le Fée","team":"Sunderland","NPxG":0,"NPxG90":0},{"player":"Dan Ndoye","team":"Nottingham Forest","NPxG":0,"NPxG90":0},{"player":"Eberechi Eze","team":"Arsenal","NPxG":0.04,"NPxG90":0.28},{"player":"Dara O&#039;Shea","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Iyenoma Destiny Udogie","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Maxence Lacroix","team":"Chelsea","NPxG":0,"NPxG90":0},{"player":"Mikkel Damsgaard","team":"Brentford","NPxG":0,"NPxG90":0},{"player":"Matthew Cash","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Matteo Ruggeri","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Leif Davis","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Antonee Robinson","team":"Fulham","NPxG":0.2,"NPxG90":0.22},{"player":"Jacob Ramsey","team":"Newcastle United","NPxG":0.09,"NPxG90":0.25},{"player":"Aaron Hickey","team":"Brentford","NPxG":0,"NPxG90":0},{"player":"Rúben Dias","team":"Manchester City","NPxG":0,"NPxG90":0},{"player":"Omar Alderete","team":"Sunderland","NPxG":0,"NPxG90":0},{"player":"Malo Gusto","team":"Chelsea","NPxG":0,"NPxG90":0},{"player":"Yeremi Pino","team":"Crystal Palace","NPxG":0.05,"NPxG90":0.14},{"player":"Conor Gallagher","team":"Tottenham","NPxG":0.02,"NPxG90":0.03},{"player":"James Trafford","team":"Leeds","NPxG":0,"NPxG90":0},{"player":"Robert Sánchez","team":"Chelsea","NPxG":0,"NPxG90":0},{"player":"Elliot Anderson","team":"Manchester City","NPxG":0,"NPxG90":0},{"player":"Kevin Schade","team":"Brentford","NPxG":0.44,"NPxG90":0.44},{"player":"Jayden Bogle","team":"Leeds","NPxG":0,"NPxG90":0},{"player":"Iliman Ndiaye","team":"Everton","NPxG":0.22,"NPxG90":0.22},{"player":"Jeremie Frimpong","team":"Liverpool","NPxG":0.01,"NPxG90":0.01},{"player":"Cody Drameh","team":"Hull","NPxG":0.04,"NPxG90":0.21},{"player":"Daniel Jebbison","team":"Bournemouth","NPxG":0.08,"NPxG90":0.57},{"player":"William Osula","team":"Newcastle United","NPxG":0.06,"NPxG90":0.09},{"player":"Marco Bizot","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Dango Ouattara","team":"Brentford","NPxG":0.03,"NPxG90":0.04},{"player":"David Raya","team":"Arsenal","NPxG":0,"NPxG90":0},{"player":"Kristoffer Ajer","team":"Brentford","NPxG":0.08,"NPxG90":0.08},{"player":"Frank Onyeka","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Nathan Collins","team":"Brentford","NPxG":0.5,"NPxG90":0.5},{"player":"Christos Tzolis","team":"Arsenal","NPxG":0.24,"NPxG90":0.27},{"player":"Habib Diarra","team":"Sunderland","NPxG":0.02,"NPxG90":0.17},{"player":"Mathys Tel","team":"Tottenham","NPxG":0.06,"NPxG90":0.06},{"player":"Brian Brobbey","team":"Sunderland","NPxG":0.64,"NPxG90":0.83},{"player":"Piero Hincapié","team":"Arsenal","NPxG":0,"NPxG90":0},{"player":"Kjell Scherpen","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Loum Tchaouna","team":"Coventry","NPxG":0.05,"NPxG90":0.05},{"player":"Beto","team":"Everton","NPxG":0.07,"NPxG90":0.84},{"player":"Romeo Lavia","team":"Chelsea","NPxG":0.59,"NPxG90":0.79},{"player":"Cristhian Mosquera","team":"Arsenal","NPxG":0,"NPxG90":0},{"player":"Lamare Bogarde","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"James McAtee","team":"Nottingham Forest","NPxG":0,"NPxG90":0},{"player":"Kasey McAteer","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Archie Gray","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Lewis Hall","team":"Newcastle United","NPxG":0,"NPxG90":0},{"player":"Vitalii Mykolenko","team":"Everton","NPxG":0,"NPxG90":0},{"player":"Guemissongui Ouattara","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Alejandro Garnacho","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Noussair Mazraoui","team":"Manchester United","NPxG":0.09,"NPxG90":0.1},{"player":"Ryan Gravenberch","team":"Liverpool","NPxG":0.06,"NPxG90":0.06},{"player":"Rodrigo Muniz","team":"Fulham","NPxG":0.02,"NPxG90":0.23},{"player":"Jaidon Anthony","team":"Brentford","NPxG":0.02,"NPxG90":0.07},{"player":"James Hill","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Brenden Aaronson","team":"Leeds","NPxG":0.02,"NPxG90":0.02},{"player":"Brennan Johnson","team":"Everton","NPxG":0,"NPxG90":0},{"player":"Levi Colwill","team":"Chelsea","NPxG":0.05,"NPxG90":0.05},{"player":"Jan Paul van Hecke","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Rico Lewis","team":"Manchester City","NPxG":0.35,"NPxG90":0.53},{"player":"Marcos Senesi","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Matheus Nunes","team":"Manchester City","NPxG":0,"NPxG90":0},{"player":"Julio Enciso","team":"Ipswich","NPxG":0.2,"NPxG90":0.25},{"player":"Jørgen Strand Larsen","team":"Crystal Palace","NPxG":0.14,"NPxG90":0.56},{"player":"Pep Chavarría","team":"Chelsea","NPxG":0,"NPxG90":0},{"player":"Chadi Riad","team":"Crystal Palace","NPxG":0,"NPxG90":0},{"player":"Kobbie Mainoo","team":"Manchester United","NPxG":0.03,"NPxG90":0.11},{"player":"Ben Doak","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Carlos Alcaraz","team":"Everton","NPxG":0.06,"NPxG90":5.34},{"player":"Merlin Röhl","team":"Everton","NPxG":0,"NPxG90":0},{"player":"Enzo Fernández","team":"Chelsea","NPxG":0,"NPxG90":0},{"player":"Noni Madueke","team":"Arsenal","NPxG":0,"NPxG90":0},{"player":"Antoine Semenyo","team":"Manchester City","NPxG":0.05,"NPxG90":0.05},{"player":"João Gomes","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Yasin Ayari","team":"Brighton","NPxG":0.08,"NPxG90":0.11},{"player":"Lewis Miley","team":"Newcastle United","NPxG":0.05,"NPxG90":0.06},{"player":"Jérémy Jacquet","team":"Liverpool","NPxG":0,"NPxG90":0},{"player":"Nico O&#039;Reilly","team":"Manchester City","NPxG":0.16,"NPxG90":0.23},{"player":"Shea Charles","team":"Fulham","NPxG":0,"NPxG90":0},{"player":"Milos Kerkez","team":"Liverpool","NPxG":0.04,"NPxG90":0.04},{"player":"Bart Verbruggen","team":"Brighton","NPxG":0,"NPxG90":0},{"player":"Calvin Bassey","team":"Fulham","NPxG":0.02,"NPxG90":0.02},{"player":"Abduqodir Khusanov","team":"Manchester City","NPxG":0,"NPxG90":0},{"player":"Yehor Yarmolyuk","team":"Brentford","NPxG":0.03,"NPxG90":0.11},{"player":"Ian Maatsen","team":"Aston Villa","NPxG":0.03,"NPxG90":0.03},{"player":"Andrey Santos","team":"Manchester United","NPxG":0,"NPxG90":0},{"player":"Gustavo Hamer","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Oscar Bobb","team":"Fulham","NPxG":0,"NPxG90":0},{"player":"Patrick Dorgu","team":"Manchester United","NPxG":0.62,"NPxG90":1.17},{"player":"Noah Okafor","team":"Leeds","NPxG":0,"NPxG90":0},{"player":"Benjamin Sesko","team":"Manchester United","NPxG":0.04,"NPxG90":0.17},{"player":"Djordje Petrovic","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Murillo","team":"Nottingham Forest","NPxG":0,"NPxG90":0},{"player":"Alex Scott","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Myles Lewis-Skelly","team":"Arsenal","NPxG":0.05,"NPxG90":0.05},{"player":"Daniel Muñoz","team":"Crystal Palace","NPxG":0.33,"NPxG90":0.5},{"player":"Adam Wharton","team":"Crystal Palace","NPxG":0,"NPxG90":0},{"player":"Lewis Koumas","team":"Liverpool","NPxG":0.05,"NPxG90":0.43},{"player":"Josh Acheampong","team":"Chelsea","NPxG":0,"NPxG90":0},{"player":"Tyrique George","team":"Everton","NPxG":0.24,"NPxG90":0.25},{"player":"Mikey Moore","team":"Tottenham","NPxG":0.61,"NPxG90":0.8},{"player":"Jacob Greaves","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Harrison Armstrong","team":"Everton","NPxG":0,"NPxG90":0},{"player":"Mats Wieffer","team":"Brighton","NPxG":0.08,"NPxG90":0.09},{"player":"Carl Rushworth","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Abdul Fatawu","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Lucas Bergvall","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Mateus Fernandes","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Aurèle Amenda","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Evanilson","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Ayden Heaven","team":"Manchester United","NPxG":0.13,"NPxG90":0.13},{"player":"Jaydee Canvot","team":"Crystal Palace","NPxG":0.02,"NPxG90":0.02},{"player":"Aladji Bamba","team":"Newcastle United","NPxG":0,"NPxG90":0},{"player":"Thiago","team":"Brentford","NPxG":0.15,"NPxG90":0.16},{"player":"Víctor Muñoz","team":"Liverpool","NPxG":0.11,"NPxG90":0.38},{"player":"Antonín Kinsky","team":"Tottenham","NPxG":0,"NPxG90":0},{"player":"Diego Gómez","team":"Brighton","NPxG":0.23,"NPxG90":0.23},{"player":"Amar Dedic","team":"Newcastle United","NPxG":0.06,"NPxG90":0.06},{"player":"Rio Ngumoha","team":"Liverpool","NPxG":0.05,"NPxG90":0.07},{"player":"Robin Roefs","team":"Sunderland","NPxG":0,"NPxG90":0},{"player":"Trai Hume","team":"Sunderland","NPxG":0.05,"NPxG90":0.06},{"player":"Dan Ballard","team":"Sunderland","NPxG":0,"NPxG90":0},{"player":"Noah Sadiki","team":"Sunderland","NPxG":0.29,"NPxG90":0.29},{"player":"Chemsdine Talbi","team":"Sunderland","NPxG":0,"NPxG90":0},{"player":"Chris Rigg","team":"Sunderland","NPxG":0,"NPxG90":0},{"player":"Luka Vuskovic","team":"Brighton","NPxG":0.37,"NPxG90":0.37},{"player":"Estêvão","team":"Chelsea","NPxG":0,"NPxG90":0},{"player":"Jorrel Hato","team":"Chelsea","NPxG":0.03,"NPxG90":0.05},{"player":"Igor Jesus","team":"Nottingham Forest","NPxG":0.28,"NPxG90":0.28},{"player":"Jair","team":"Nottingham Forest","NPxG":0,"NPxG90":0},{"player":"Ibrahim Osman","team":"Brighton","NPxG":0,"NPxG90":0},{"player":"Tarik Muharemovic","team":"Leeds","NPxG":0.06,"NPxG90":0.06},{"player":"Mamadou Sangaré","team":"Brentford","NPxG":0.04,"NPxG90":0.05},{"player":"Kevin","team":"Fulham","NPxG":0,"NPxG90":0},{"player":"Senne Lammens","team":"Manchester United","NPxG":0,"NPxG90":0},{"player":"Luke O&#039;Nien","team":"Sunderland","NPxG":0.02,"NPxG90":0.03},{"player":"Charalampos Kostoulas","team":"Brighton","NPxG":0.34,"NPxG90":1.45},{"player":"George Hemmings","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Shea Lacey","team":"Manchester United","NPxG":0,"NPxG90":0},{"player":"César Palacios","team":"Fulham","NPxG":0.16,"NPxG90":0.19},{"player":"Alex Tóth","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Rayan","team":"Bournemouth","NPxG":0.07,"NPxG90":0.07},{"player":"Alysson Edward","team":"Aston Villa","NPxG":0,"NPxG90":0},{"player":"Milan van Ewijk","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Jay Dasilva","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Caleb Yirenkyi","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Brandon Thomas-Asante","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Victor Torp","team":"Coventry","NPxG":0,"NPxG90":0},{"player":"Jack Rudoni","team":"Coventry","NPxG":0.51,"NPxG90":2.53},{"player":"Konstantinos Tzolakis","team":"Hull","NPxG":0,"NPxG90":0},{"player":"Lewie Coyle","team":"Hull","NPxG":0,"NPxG90":0},{"player":"Mohamed Belloumi","team":"Hull","NPxG":0.05,"NPxG90":0.05},{"player":"Matt Crooks","team":"Hull","NPxG":0,"NPxG90":0},{"player":"Regan Slater","team":"Hull","NPxG":0,"NPxG90":0},{"player":"Elliot Stroud","team":"Hull","NPxG":0,"NPxG90":0},{"player":"Liam Millar","team":"Hull","NPxG":0,"NPxG90":0},{"player":"Lucas Herrington","team":"Hull","NPxG":0,"NPxG90":0},{"player":"Hayden Hackney","team":"Everton","NPxG":0.04,"NPxG90":0.04},{"player":"Anan Khalaili","team":"Crystal Palace","NPxG":0,"NPxG90":0},{"player":"Marcelino Núñez","team":"Ipswich","NPxG":0.06,"NPxG90":0.06},{"player":"Daizen Maeda","team":"Ipswich","NPxG":0.62,"NPxG90":0.68},{"player":"Sindre Egeli","team":"Ipswich","NPxG":0,"NPxG90":0},{"player":"Costinha","team":"Brighton","NPxG":0.05,"NPxG90":0.22},{"player":"Zadok Yohanna","team":"Brighton","NPxG":0,"NPxG90":0},{"player":"Malick Yalcouyé","team":"Brighton","NPxG":0,"NPxG90":0},{"player":"António Silva","team":"Bournemouth","NPxG":0,"NPxG90":0},{"player":"Lukás Hornícek","team":"Newcastle United","NPxG":0,"NPxG90":0},{"player":"Sean Steur","team":"Newcastle United","NPxG":0,"NPxG90":0},{"player":"Geovany Quenda","team":"Chelsea","NPxG":0,"NPxG90":0}]"""
        
        npxg_data = json.loads(custom_npxg_json)
        npxg_df = pd.DataFrame(npxg_data)
        
        # Merge mapping using existing app logic 
        df['Full Name'] = df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)
        fpl_full_names = df['Full Name'].tolist()
        fpl_web_names = df['Web Name'].tolist()
        web_to_full_map = df.set_index('Web Name')['Full Name'].to_dict()
        
        match_dict = {}
        for custom_name in npxg_df['player']:
            clean_name = str(custom_name).strip()
            # 1. Try matching the full name exactly/closely
            matches = difflib.get_close_matches(clean_name, fpl_full_names, n=1, cutoff=0.65)
            if matches:
                match_dict[custom_name] = matches[0]
            else:
                # 2. Try matching their Web Name as a backup
                web_matches = difflib.get_close_matches(clean_name, fpl_web_names, n=1, cutoff=0.6)
                if web_matches:
                    match_dict[custom_name] = web_to_full_map[web_matches[0]]
                    
        npxg_df['matched_full_name'] = npxg_df['player'].map(match_dict)
        npxg_clean = npxg_df.dropna(subset=['matched_full_name']).drop_duplicates(subset=['matched_full_name'])
        
        # Merge the two new columns into your main table
        df = df.merge(npxg_clean[['matched_full_name', 'NPxG', 'NPxG90']], left_on='Full Name', right_on='matched_full_name', how='left')
        
        # Clean up missing data points for players not in your list
        df['NPxG'] = df['NPxG'].fillna(0.0)
        df['NPxG90'] = df['NPxG90'].fillna(0.0)
        df.drop(columns=['matched_full_name', 'Full Name'], inplace=True)
            
    except Exception as e:
        st.sidebar.warning(f"Could not parse custom NPxG data. Error: {e}")

    return df

df = fetch_fpl_data()

# --- Main App Interface ---
st.title("FPL Advanced Player Explorer")

# Safe handling if data failed to load
if df.empty:
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
