"""Violent cities chart module.

Creates bar chart visualization of top 5 most violent cities.
"""

import logging
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def create_violent_cities_chart(
    mortality_df: pd.DataFrame,
    divipola_df: pd.DataFrame,
    find_column_func: callable
) -> go.Figure:
    """Create bar chart of top 5 most violent cities.
    
    Args:
        mortality_df: Mortality data DataFrame
        divipola_df: DIVIPOLA data DataFrame
        find_column_func: Function to find column names
        
    Returns:
        Plotly figure object
    """
    try:
        # Find MANERA_MUERTE, city, and department columns
        manera_muerte_col = find_column_func(['MANERA_MUERTE', 'MANERA', 'TIPO_MUERTE'], mortality_df)
        city_col = find_column_func(['COD_MUNICIPIO', 'MUNICIPIO', 'CIUDAD', 'MUN', 'COD_MUN'], mortality_df)
        dept_col = find_column_func(['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'DEPTO', 'COD_DPTO'], mortality_df)
        
        if manera_muerte_col is None or city_col is None or dept_col is None:
            return _create_error_figure("Required columns not found")
        
        # Filter homicides using MANERA_MUERTE = 'Homicidio'
        homicides = mortality_df[
            mortality_df[manera_muerte_col].astype(str).str.strip().str.upper() == 'HOMICIDIO'
        ].copy()
        
        # Create full DIVIPOLA code (COD_DANE) by combining department and municipality codes
        # Format: DDDMM where DDD is department (2 digits) and MM is municipality (3 digits)
        # Example: Department 5, Municipality 1 = 05001
        homicides['COD_DANE'] = (
            homicides[dept_col].astype(str).str.zfill(2) + 
            homicides[city_col].astype(str).str.zfill(3)
        ).astype(int)
        
        # Aggregate by COD_DANE
        city_homicides = homicides.groupby('COD_DANE').size().reset_index(name='Total_Homicidios')
        
        # Merge with DIVIPOLA to get city names using COD_DANE
        divipola_mun = divipola_df[['COD_DANE', 'MUNICIPIO', 'DEPARTAMENTO']].drop_duplicates()
        
        city_homicides = city_homicides.merge(
            divipola_mun, 
            on='COD_DANE', 
            how='left'
        )
        city_homicides['MUNICIPIO'] = city_homicides['MUNICIPIO'].fillna('Desconocido')
        city_homicides['DEPARTAMENTO'] = city_homicides['DEPARTAMENTO'].fillna('Desconocido')
        
        # Create full city name with department for clarity
        city_homicides['Ciudad_Completa'] = city_homicides['MUNICIPIO'] + ' (' + city_homicides['DEPARTAMENTO'] + ')'
        
        # Get top 5 most violent cities
        city_homicides = city_homicides.nlargest(5, 'Total_Homicidios')
        
        # Create bar chart with city names
        fig = px.bar(
            city_homicides,
            x='Ciudad_Completa',
            y='Total_Homicidios',
            title='Top 5 Ciudades Más Violentas - Colombia 2019',
            labels={'Ciudad_Completa': 'Ciudad', 'Total_Homicidios': 'Total de Homicidios'},
            color='Total_Homicidios',
            color_continuous_scale='Reds',
            hover_data={'COD_DANE': True, 'MUNICIPIO': True, 'DEPARTAMENTO': True}
        )
        
        fig.update_layout(height=500, showlegend=False, xaxis_tickangle=-45)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating violent cities chart: {e}")
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
