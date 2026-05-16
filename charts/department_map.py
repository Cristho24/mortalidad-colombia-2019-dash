"""Department map chart module.

Creates choropleth visualization of deaths by department.
"""

import logging
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def create_department_map(
    mortality_df: pd.DataFrame,
    divipola_df: pd.DataFrame,
    find_column_func: callable
) -> go.Figure:
    """Create choropleth map of deaths by department.
    
    Args:
        mortality_df: Mortality data DataFrame
        divipola_df: DIVIPOLA data DataFrame
        find_column_func: Function to find column names
        
    Returns:
        Plotly figure object
    """
    try:
        # Find department column in mortality data
        dept_col = find_column_func(['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'DEPTO', 'COD_DPTO'], mortality_df)
        if dept_col is None:
            logger.error("Department column not found")
            return _create_error_figure("Department data not available")
        
        # Aggregate deaths by department code
        dept_deaths = mortality_df.groupby(dept_col).size().reset_index(name='Total_Muertes')
        dept_deaths.columns = ['COD_DEPARTAMENTO', 'Total_Muertes']
        
        # Merge with DIVIPOLA to get department names
        divipola_dept = divipola_df[['COD_DEPARTAMENTO', 'DEPARTAMENTO']].drop_duplicates()
        dept_deaths = dept_deaths.merge(divipola_dept, on='COD_DEPARTAMENTO', how='left')
        dept_deaths['DEPARTAMENTO'] = dept_deaths['DEPARTAMENTO'].fillna('Desconocido')
        
        # Sort by total deaths for better visualization
        dept_deaths = dept_deaths.sort_values('Total_Muertes', ascending=False)
        
        # Create bar chart instead of choropleth (since we don't have GeoJSON)
        fig = px.bar(
            dept_deaths,
            x='DEPARTAMENTO',
            y='Total_Muertes',
            title='Distribución de Muertes por Departamento - Colombia 2019',
            labels={'DEPARTAMENTO': 'Departamento', 'Total_Muertes': 'Total de Muertes'},
            color='Total_Muertes',
            color_continuous_scale='Reds',
            hover_data={'Total_Muertes': ':,', 'COD_DEPARTAMENTO': True}
        )
        
        fig.update_layout(
            height=600,
            xaxis_tickangle=-45,
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating department map: {e}")
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
