import plotly.graph_objects as go

def create_gauge_chart(value: float, title: str = "Score") -> go.Figure:
    """Farmer-friendly gauge chart with traffic light colors."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 22, 'family': 'Inter'}},
        number={'font': {'size': 56, 'family': 'Inter', 'weight': 700}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "#ccc"},
            'bar': {'color': "#2c5f2d", 'thickness': 0.25},
            'bgcolor': "white",
            'borderwidth': 3,
            'bordercolor': "#e0e0e0",
            'steps': [
                {'range': [0, 40], 'color': '#ffebee'},
                {'range': [40, 70], 'color': '#fff9c4'},
                {'range': [70, 100], 'color': '#e8f5e9'}
            ],
            'threshold': {
                'line': {'color': "#2c5f2d", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "#333", 'family': "Inter"},
        height=320,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig

def create_progress_line_chart(data: list[dict]) -> go.Figure:
    """Simple line chart showing ESG score over time."""
    years = [d['year'] for d in data]
    scores = [d['esg_score'] for d in data]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=years,
        y=scores,
        mode='lines+markers+text',
        name='ESG Score',
        line=dict(color='#28a745', width=4),
        marker=dict(size=14, color='#28a745', symbol='circle',
                   line=dict(width=2, color='white')),
        text=[f"{s:.0f}" for s in scores],
        textposition="top center",
        textfont=dict(size=14, color='#28a745', family='Inter', weight=700),
        fill='tozeroy',
        fillcolor='rgba(40, 167, 69, 0.15)',
        hovertemplate='<b>Year %{x}</b><br>ESG Score: %{y:.1f}/100<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text="Your ESG Score Progress", font=dict(size=20, family='Inter', weight=600)),
        xaxis_title="Year",
        yaxis_title="ESG Score",
        yaxis=dict(range=[0, 100], gridcolor='#e0e0e0'),
        xaxis=dict(gridcolor='#e0e0e0'),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter", size=14),
        hovermode='x unified',
        height=380,
        margin=dict(l=50, r=30, t=60, b=50)
    )
    
    fig.update_xaxes(showgrid=True, showline=True, linewidth=2, linecolor='#e0e0e0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e0e0e0')
    
    return fig

def create_score_breakdown_pie(e_score: float, s_score: float, g_score: float) -> go.Figure:
    """Pie chart showing ESG component breakdown."""
    labels = ['Environment', 'Social', 'Governance']
    values = [e_score, s_score, g_score]
    colors = ['#4caf50', '#2196f3', '#ff9800']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color='white', width=3)),
        textinfo='label+percent',
        textfont=dict(size=16, family='Inter', weight=600),
        hovertemplate='<b>%{label}</b><br>Score: %{value:.1f}/100<br>%{percent}<extra></extra>',
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
            font=dict(size=14, family='Inter')
        ),
        paper_bgcolor="white",
        font=dict(family="Inter"),
        height=350,
        margin=dict(l=20, r=20, t=40, b=80)
    )
    
    return fig

def create_emissions_donut(fertilizer: float, diesel: float, electricity: float) -> go.Figure:
    """Donut chart showing emissions by source."""
    labels = ['Fertilizer', 'Diesel', 'Electricity']
    values = [fertilizer, diesel, electricity]
    colors = ['#ff6b6b', '#4ecdc4', '#ffe66d']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors, line=dict(color='white', width=3)),
        textinfo='label+percent',
        textfont=dict(size=15, family='Inter', weight=600),
        hovertemplate='<b>%{label}</b><br>Emissions: %{value:.0f} kg CO₂e<br>%{percent}<extra></extra>'
    )])
    
    # Add center text
    fig.add_annotation(
        text=f"<b>{sum(values):.0f}</b><br>kg CO₂e",
        x=0.5, y=0.5,
        font=dict(size=20, family='Inter', weight=700),
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
            font=dict(size=13, family='Inter')
        ),
        paper_bgcolor="white",
        font=dict(family="Inter"),
        height=350,
        margin=dict(l=20, r=120, t=40, b=20)
    )
    
    return fig

def create_comparison_bar(my_farm: dict, all_farms_df) -> go.Figure:
    """Simple bar chart comparing farm to average."""
    avg_esg = all_farms_df['esg_score'].mean()
    avg_e = all_farms_df['e_score'].mean()
    avg_s = all_farms_df['s_score'].mean()
    avg_g = all_farms_df['g_score'].mean()
    
    categories = ['Overall ESG', 'Environment', 'Social', 'Governance']
    my_scores = [my_farm['esg_score'], my_farm['e_score'], my_farm['s_score'], my_farm['g_score']]
    avg_scores = [avg_esg, avg_e, avg_s, avg_g]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Your Farm',
        x=categories,
        y=my_scores,
        marker_color='#28a745',
        text=[f"{s:.0f}" for s in my_scores],
        textposition='outside',
        textfont=dict(size=14, weight=700),
        hovertemplate='<b>Your Farm</b><br>%{x}: %{y:.1f}/100<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        name='Average Farm',
        x=categories,
        y=avg_scores,
        marker_color='#b0bec5',
        text=[f"{s:.0f}" for s in avg_scores],
        textposition='outside',
        textfont=dict(size=14, weight=700),
        hovertemplate='<b>Average</b><br>%{x}: %{y:.1f}/100<extra></extra>'
    ))
    
    fig.update_layout(
        barmode='group',
        yaxis=dict(range=[0, 110], title="Score", gridcolor='#e0e0e0'),
        xaxis=dict(title=""),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter", size=13),
        height=350,
        margin=dict(l=50, r=30, t=40, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_xaxes(showgrid=False, showline=True, linewidth=2, linecolor='#e0e0e0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#e0e0e0')
    
    return fig
