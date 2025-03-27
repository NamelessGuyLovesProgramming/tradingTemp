import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_price_chart(df, symbol, show_sma=False, show_bb=False, show_volume=True):
    """
    Erstellt ein Preischart mit optionalen Indikatoren
    
    Args:
        df (pd.DataFrame): DataFrame mit OHLCV-Daten und Indikatoren
        symbol (str): Das Aktiensymbol
        show_sma (bool): Ob SMAs angezeigt werden sollen
        show_bb (bool): Ob Bollinger Bands angezeigt werden sollen
        show_volume (bool): Ob Volumen angezeigt werden soll
        
    Returns:
        go.Figure: Plotly-Figur mit dem Chart
    """
    # Bestimme die Anzahl der Zeilen für die Subplots
    row_heights = [0.7]
    if show_volume:
        row_heights.append(0.15)
    
    # Erstelle die Subplots
    fig = make_subplots(
        rows=len(row_heights),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=row_heights
    )
    
    # Füge Candlestick-Chart hinzu
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='OHLC',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Füge SMAs hinzu, wenn gewünscht
    if show_sma:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['sma_20'],
                name='SMA 20',
                line=dict(color='rgba(0, 150, 255, 0.8)', width=1.5),
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Füge Bollinger Bands hinzu, wenn gewünscht
    if show_bb:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['bb_upper'],
                name='BB Upper',
                line=dict(color='rgba(0, 255, 255, 0.8)', width=1),
                showlegend=True
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['bb_middle'],
                name='BB Middle',
                line=dict(color='rgba(0, 255, 255, 0.8)', width=1, dash='dash'),
                showlegend=True
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['bb_lower'],
                name='BB Lower',
                line=dict(color='rgba(0, 255, 255, 0.8)', width=1),
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Füge Volumen hinzu, wenn gewünscht
    if show_volume and len(row_heights) > 1:
        colors = ['rgba(0, 150, 0, 0.5)' if row['Close'] >= row['Open'] else 'rgba(255, 0, 0, 0.5)' for _, row in df.iterrows()]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker=dict(color=colors),
                showlegend=False
            ),
            row=2, col=1
        )
    
    # Aktualisiere das Layout
    fig.update_layout(
        title=f'{symbol} Chart',
        xaxis_title='Datum',
        yaxis_title='Preis',
        template='plotly_dark',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis_rangeslider_visible=False,
    )
    
    # Aktualisiere die Y-Achsen
    fig.update_yaxes(title_text='Preis', row=1, col=1)
    if show_volume and len(row_heights) > 1:
        fig.update_yaxes(title_text='Volumen', row=2, col=1)
    
    return fig

def create_volume_chart(df):
    """
    Erstellt ein Volumen-Chart
    
    Args:
        df (pd.DataFrame): DataFrame mit OHLCV-Daten
        
    Returns:
        go.Figure: Plotly-Figur mit dem Chart
    """
    fig = go.Figure()
    
    colors = ['rgba(0, 150, 0, 0.5)' if row['Close'] >= row['Open'] else 'rgba(255, 0, 0, 0.5)' for _, row in df.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            marker=dict(color=colors),
            showlegend=False
        )
    )
    
    fig.update_layout(
        title='Volume',
        xaxis_title='Datum',
        yaxis_title='Volumen',
        template='plotly_dark',
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    return fig

def create_indicator_chart(df, indicator_type):
    """
    Erstellt ein Chart für einen Indikator
    
    Args:
        df (pd.DataFrame): DataFrame mit OHLCV-Daten und Indikatoren
        indicator_type (str): Typ des Indikators ('rsi', 'macd')
        
    Returns:
        go.Figure: Plotly-Figur mit dem Chart
    """
    fig = go.Figure()
    
    if indicator_type == 'rsi':
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['rsi_14'],
                name='RSI (14)',
                line=dict(color='rgba(255, 165, 0, 0.8)', width=1.5),
                showlegend=True
            )
        )
        
        # Füge Überverkauft/Überkauft-Linien hinzu
        fig.add_shape(
            type="line",
            x0=df.index[0],
            y0=70,
            x1=df.index[-1],
            y1=70,
            line=dict(color="red", width=1, dash="dash"),
        )
        
        fig.add_shape(
            type="line",
            x0=df.index[0],
            y0=30,
            x1=df.index[-1],
            y1=30,
            line=dict(color="green", width=1, dash="dash"),
        )
        
        fig.update_layout(
            title='RSI (14)',
            xaxis_title='Datum',
            yaxis_title='RSI',
            template='plotly_dark',
            margin=dict(l=50, r=50, t=50, b=50),
            yaxis=dict(range=[0, 100]),
        )
    
    elif indicator_type == 'macd':
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['macd'],
                name='MACD',
                line=dict(color='rgba(0, 150, 255, 0.8)', width=1.5),
                showlegend=True
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['macdsignal'],
                name='Signal',
                line=dict(color='rgba(255, 165, 0, 0.8)', width=1.5),
                showlegend=True
            )
        )
        
        colors = ['rgba(0, 150, 0, 0.5)' if val >= 0 else 'rgba(255, 0, 0, 0.5)' for val in df['macdhist']]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['macdhist'],
                name='Histogram',
                marker=dict(color=colors),
                showlegend=True
            )
        )
        
        fig.update_layout(
            title='MACD (12, 26, 9)',
            xaxis_title='Datum',
            yaxis_title='MACD',
            template='plotly_dark',
            margin=dict(l=50, r=50, t=50, b=50),
        )
    
    return fig
