"""Age histogram module.

Creates histogram visualization of deaths by age group.
"""

import logging
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def create_age_histogram(
    mortality_df: pd.DataFrame,
    find_column_func: callable
) -> go.Figure:
    """Create histogram of deaths by age group.
    
    Args:
        mortality_df: Mortality data DataFrame
        find_column_func: Function to find column names
        
    Returns:
        Plotly figure object
    """
    try:
        age_col = find_column_func(['GRUPO_EDAD1', 'EDAD', 'GRUPO_EDAD', 'RANGO_EDAD'], mortality_df)
        if age_col is None:
            return _create_error_figure("Age column not found")
        
        # Create histogram
        fig = px.histogram(
            mortality_df,
            x=age_col,
            title='Distribución de Muertes por Grupo de Edad - Colombia 2019',
            labels={age_col: 'Grupo de Edad', 'count': 'Total de Muertes'},
            color_discrete_sequence=['indianred']
        )
        
        fig.update_layout(height=500, showlegend=False)
        fig.update_xaxes(categoryorder='total descending')
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating age histogram: {e}")
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
