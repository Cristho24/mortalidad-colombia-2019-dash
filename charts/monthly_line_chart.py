"""Monthly line chart module.

Creates line chart visualization of deaths by month.
"""

import logging
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def create_monthly_line_chart(
    mortality_df: pd.DataFrame,
    find_column_func: callable
) -> go.Figure:
    """Create line chart of deaths by month.
    
    Args:
        mortality_df: Mortality data DataFrame
        find_column_func: Function to find column names
        
    Returns:
        Plotly figure object
    """
    try:
        # Find date column
        date_col = find_column_func(['MES', 'FECHA', 'FECHA_DEF', 'FEC_DEF'], mortality_df)
        if date_col is None:
            return _create_error_figure("Date column not found")
        
        # Extract month
        if date_col == 'MES':
            monthly_data = mortality_df.groupby('MES').size().reset_index(name='Total_Muertes')
            monthly_data.columns = ['Mes', 'Total_Muertes']
        else:
            mortality_df_copy = mortality_df.copy()
            mortality_df_copy['Mes'] = pd.to_datetime(
                mortality_df_copy[date_col],
                errors='coerce'
            ).dt.month
            monthly_data = mortality_df_copy.groupby('Mes').size().reset_index(name='Total_Muertes')
        
        # Create month names
        month_names = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        monthly_data['Mes_Nombre'] = monthly_data['Mes'].apply(
            lambda x: month_names[int(x) - 1] if pd.notna(x) and 1 <= x <= 12 else 'Desconocido'
        )
        
        # Create line chart
        fig = px.line(
            monthly_data,
            x='Mes',
            y='Total_Muertes',
            title='Total de Muertes por Mes - Colombia 2019',
            labels={'Mes': 'Mes', 'Total_Muertes': 'Total de Muertes'},
            markers=True
        )
        
        fig.update_xaxes(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=month_names
        )
        
        fig.update_layout(height=500)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating monthly chart: {e}")
        return _create_error_figure(f"Error: {str(e)}")


def _create_error_figure(message: str) -> go.Figure:
    """Create error figure with message.
    
    Args:
        message: Error message to display
        
    Returns:
        Plotly figure with error message
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="red")
    )
    fig.update_layout(height=400)
    return fig
