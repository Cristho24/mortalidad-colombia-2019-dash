"""Lowest mortality pie chart module.

Creates pie chart visualization of 10 cities with lowest mortality.
"""

import logging
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def create_lowest_mortality_pie(
    mortality_df: pd.DataFrame,
    divipola_df: pd.DataFrame,
    find_column_func: callable
) -> go.Figure:
    """Create pie chart of 10 cities with lowest mortality.
    
    Args:
        mortality_df: Mortality data DataFrame
        divipola_df: DIVIPOLA data DataFrame
        find_column_func: Function to find column names
        
    Returns:
        Plotly figure object
    """
    try:
        city_col = find_column_func(['COD_MUNICIPIO', 'MUNICIPIO', 'CIUDAD', 'MUN', 'COD_MUN'], mortality_df)
        dept_col = find_column_func(['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'DEPTO', 'COD_DPTO'], mortality_df)
        
        if city_col is None or dept_col is None:
            return _create_error_figure("Required columns not found")
        
        # Create COD_DANE for proper city identification
        mortality_with_dane = mortality_df.copy()
        mortality_with_dane['COD_DANE'] = (
            mortality_with_dane[dept_col].astype(str).str.zfill(2) + 
            mortality_with_dane[city_col].astype(str).str.zfill(3)
        ).astype(int)
        
        # Aggregate by COD_DANE
        city_deaths = mortality_with_dane.groupby('COD_DANE').size().reset_index(name='Total_Muertes')
        
        # Merge with DIVIPOLA to get city names
        divipola_mun = divipola_df[['COD_DANE', 'MUNICIPIO', 'DEPARTAMENTO']].drop_duplicates()
        city_deaths = city_deaths.merge(divipola_mun, on='COD_DANE', how='left')
        city_deaths['MUNICIPIO'] = city_deaths['MUNICIPIO'].fillna('Desconocido')
        city_deaths['DEPARTAMENTO'] = city_deaths['DEPARTAMENTO'].fillna('Desconocido')
        
        # Create full city name with department
        city_deaths['Ciudad_Completa'] = city_deaths['MUNICIPIO'] + ' (' + city_deaths['DEPARTAMENTO'] + ')'
        
        # Get 10 cities with lowest mortality
        city_deaths = city_deaths.nsmallest(10, 'Total_Muertes')
        
        # Create pie chart with city names
        fig = px.pie(
            city_deaths,
            values='Total_Muertes',
            names='Ciudad_Completa',
            title='Top 10 Ciudades con Menor Mortalidad - Colombia 2019',
            hover_data={'COD_DANE': True, 'Total_Muertes': True}
        )
        
        # Update hover template to show formatted values
        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>Total Muertes: %{value:,}<br>Código DANE: %{customdata[0]}<extra></extra>'
        )
        
        fig.update_layout(height=500)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating lowest mortality pie: {e}")
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
