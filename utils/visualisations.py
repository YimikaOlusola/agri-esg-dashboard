import plotly.graph_objects as go

def create_gauge_chart(value: float, title: str = "Score") -> go.Figure:
    """
    Farmer-friendly gauge chart with tooltip (invisible hover trigger).
    """
    fig = go.Figure()

    # 1. The Gauge Indicator
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 22, 'family': 'Inter', 'color': '#32CD32'}},
        number={'font': {'size': 56, 'family': 'Inter', 'weight': 700, 'color': '#2d5016'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "#32CD32"},
            'bar': {'color': "#2d5016", 'thickness': 0.25},
            'bgcolor': "white",
            'borderwidth': 3,
            'bordercolor': "#e0e0e0",
            'steps': [
                {'range': [0, 40], 'color': "#fcc0c9"},  
                {'range': [40, 70], 'color': "#f8eecc"},  
                {'range': [70, 100], 'color': "#bef8c3"}  
            ],
            'threshold': {
                'line': {'color': "#295e06", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    # 2. Invisible Scatter Trace for Tooltip
    # This creates a hidden point in the center that triggers the tooltip on hover
    fig.add_trace(go.Scatter(
        x=[0.5], y=[0.2], # Positioned near the bottom center of the gauge
        mode='markers',
        marker=dict(opacity=0, size=150), # Invisible (opacity 0) but large enough to hit
        hoverinfo='text',
        text=(
            "<b>What this means:</b><br>" +
            "This summarizes your environmental impact,<br>" +
            "worker safety, and paperwork compliance."
        )
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "#32CD32", 'family': "Inter"},
        height=320,
        margin=dict(l=20, r=20, t=60, b=20),
        # We need to fix the axes for the invisible scatter point to work
        xaxis={'range': [0, 1], 'visible': False, 'fixedrange': True},
        yaxis={'range': [0, 1], 'visible': False, 'fixedrange': True},
        showlegend=False
    )
    
    return fig

def create_progress_line_chart(data: list[dict]) -> go.Figure:
    """Line chart with plain English tooltip"""
    years = [d['year'] for d in data]
    scores = [d['esg_score'] for d in data]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=years,
        y=scores,
        mode='lines+markers+text',
        name='ESG Score',
        line=dict(color='#4a7c29', width=4),
        marker=dict(size=14, color='#2d5016', symbol='circle',
                   line=dict(width=2, color='white')),
        text=[f"{s:.0f}" for s in scores],
        textposition="top center",
        textfont=dict(size=14, color='#2d5016', family='Inter', weight=700),
        fill='tozeroy',
        fillcolor='rgba(74, 124, 41, 0.15)',
        # Enhanced Tooltip
        hovertemplate=(
            '<b>Year %{x}</b><br>' +
            'Score: %{y:.1f}/100<br>' +
            '<i>What this means: Tracking if your farm is getting<br>more sustainable over time.</i><extra></extra>'
        ),
        cliponaxis=False 
    ))
    
    fig.update_layout(
        title=dict(text="Your ESG Score Progress", font=dict(size=20, family='Inter', weight=600, color='#5d4037')),
        xaxis_title="Year",
        yaxis_title="ESG Score",
        yaxis=dict(range=[0, 115], gridcolor='#e0e0e0'),
        xaxis=dict(gridcolor='#e0e0e0'),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter", size=14, color='#5d4037'),
        hovermode='x unified',
        height=380,
        margin=dict(l=60, r=60, t=60, b=50) 
    )
    
    if len(years) > 0:
        min_y, max_y = min(years), max(years)
        padding = 1 if min_y == max_y else (max_y - min_y) * 0.1
        fig.update_xaxes(range=[min_y - padding, max_y + padding])
        
    fig.update_xaxes(showgrid=True, showline=True, linewidth=2, linecolor='#e0e0e0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e0e0e0')
    
    return fig

def create_score_breakdown_pie(e_score: float, s_score: float, g_score: float) -> go.Figure:
    """Pie chart with plain English tooltip"""
    labels = ['Environment', 'Social', 'Governance']
    values = [e_score, s_score, g_score]
    colors = ['#4a7c29', '#8d6e63', '#f9a825']
    
    # Plain english descriptions for the tooltip
    descriptions = [
        "Nature (Chemicals, Soil, Water)",
        "People (Safety, Fair Pay)",
        "Records (Compliance, SFI)"
    ]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        customdata=descriptions,
        marker=dict(colors=colors, line=dict(color='white', width=3)),
        textinfo='label+percent',
        textfont=dict(size=16, family='Inter', weight=600),
        # Enhanced Tooltip
        hovertemplate=(
            '<b>%{label}</b><br>' +
            'Score: %{value:.1f}/100<br>' +
            '<i>What this means: %{customdata}</i><extra></extra>'
        ),
        pull=[0.05, 0, 0]
    )])
    
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=14, family='Inter', color='#5d4037'),
        ),
        paper_bgcolor="white",
        font=dict(family="Inter"),
        height=350,
        margin=dict(l=20, r=20, t=40, b=80)
    )
    
    return fig

def create_emissions_donut(fertilizer: float, diesel: float, electricity: float) -> go.Figure:
    """Donut chart with plain English tooltip"""
    labels = ['Fertilizer', 'Diesel', 'Electricity']
    values = [fertilizer, diesel, electricity]
    colors = ['#c62828', '#f9a825', '#8d6e63']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors, line=dict(color='white', width=3)),
        textinfo='label+percent',
        textfont=dict(size=15, family='Inter', weight=600),
        # Enhanced Tooltip
        hovertemplate=(
            '<b>%{label}</b><br>' +
            'Emissions: %{value:.0f} kg CO₂e<br>' +
            '<i>What this means: How much greenhouse gas comes<br>from using this input.</i><extra></extra>'
        )
    )])
    
    fig.add_annotation(
        text=f"<b>{sum(values):.0f}</b><br>kg CO₂e",
        x=0.5, y=0.5,
        font=dict(size=20, family='Inter', weight=700, color='#5d4037'),
        showarrow=False
    )
    
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=13, family='Inter', color='#5d4037')
        ),
        paper_bgcolor="white",
        font=dict(family="Inter"),
        height=350,
        margin=dict(l=20, r=120, t=40, b=20)
    )
    
    return fig

def create_comparison_bar(my_farm: dict, all_farms_df) -> go.Figure:
    """Bar chart with plain English tooltip and fixed text colors for Dark Mode"""
    
    if len(all_farms_df) < 2:
        avg_esg, avg_e, avg_s, avg_g = 60.0, 55.0, 50.0, 65.0
        comparison_label = "Industry Standard"
        desc = "Based on typical industry targets."
    else:
        avg_esg = all_farms_df['esg_score'].mean()
        avg_e = all_farms_df['e_score'].mean()
        avg_s = all_farms_df['s_score'].mean()
        avg_g = all_farms_df['g_score'].mean()
        comparison_label = "Average Farm"
        desc = "Based on the average of all uploaded farms."
    
    categories = ['Overall ESG', 'Environment', 'Social', 'Governance']
    my_scores = [my_farm['esg_score'], my_farm['e_score'], my_farm['s_score'], my_farm['g_score']]
    avg_scores = [avg_esg, avg_e, avg_s, avg_g]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Your Farm',
        x=categories,
        y=my_scores,
        marker_color='#4a7c29',
        text=[f"{s:.0f}" for s in my_scores],
        textposition='outside',
        textfont=dict(size=14, weight=700, color='#5d4037'), 
        hovertemplate=(
            '<b>Your Farm</b><br>%{x}: %{y:.1f}/100<br>' +
            '<i>What this means: Your specific performance.</i><extra></extra>'
        ),
        cliponaxis=False
    ))
    
    fig.add_trace(go.Bar(
        name=comparison_label,
        x=categories,
        y=avg_scores,
        marker_color='#a1887f',
        text=[f"{s:.0f}" for s in avg_scores],
        textposition='outside',
        textfont=dict(size=14, weight=700, color='#5d4037'),
        hovertemplate=(
            f'<b>{comparison_label}</b><br>%{{x}}: %{{y:.1f}}/100<br>' +
            f'<i>What this means: {desc}</i><extra></extra>'
        ),
        cliponaxis=False
    ))
    
    fig.update_layout(
        barmode='group',
        yaxis=dict(
            range=[0, 115], 
            # FIXED: Use nested dictionary for title font
            title=dict(text="Score", font=dict(color='#5d4037')),
            gridcolor='#e0e0e0',
            tickfont=dict(color='#5d4037')
        ),
        xaxis=dict(
            title="",
            tickfont=dict(color='#5d4037')
        ),
        plot_bgcolor="white",
        font=dict(family="Inter", size=13, color='#5d4037'),
        height=350,
        margin=dict(l=40, r=30, t=50, b=50),
        legend=dict(
        orientation="h",
        yanchor="top",
        y=1.02,          
        xanchor="right",
        x=1.01,
        bgcolor="#dfcfcb",  
        bordercolor='#e0e0e0',
        borderwidth=1,
    )

    )
    fig.update_xaxes(showgrid=False, showline=True, linewidth=2, linecolor='#e0e0e0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e0e0e0')
    
    return fig