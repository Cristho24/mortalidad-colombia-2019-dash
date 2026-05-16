"""Gender by department chart module.

Creates stacked bar chart visualization of deaths by gender and department.
"""

import logging
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def create_gender_by_department_chart(
    mortality_df: pd.DataFrame,
    divipola_df: pd.DataFrame,
    find_column_func: callable
) -> go.Figure:
    """Create stacked bar chart of deaths by gender and department.
    
    Args:
        mortality_df: Mortality data DataFrame
        divipola_df: DIVIPOLA data DataFrame
        find_column_func: Function to find column names
        
    Returns:
        Plotly figure object
    """
    try:
        dept_col = find_column_func(['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'DEPTO', 'COD_DPTO'], mortality_df)
        gender_col = find_column_func(['SEXO', 'GENERO', 'SEX'], mortality_df)
        
        if dept_col is None or gender_col is None:
            return _create_error_figure("Required columns not found")
        
        # Aggregate by department code and gender
        gender_dept = mortality_df.groupby([dept_col, gender_col]).size().reset_index(name='Total')
        gender_dept.columns = ['COD_DEPARTAMENTO', 'Sexo', 'Total']
        
        # Merge with DIVIPOLA to get department names
        divipola_dept = divipola_df[['COD_DEPARTAMENTO', 'DEPARTAMENTO']].drop_duplicates()
        gender_dept = gender_dept.merge(divipola_dept, on='COD_DEPARTAMENTO', how='left')
        gender_dept['DEPARTAMENTO'] = gender_dept['DEPARTAMENTO'].fillna('Desconocido')
        
        # Create stacked bar chart with department names
        fig = px.bar(
            gender_dept,
            x='DEPARTAMENTO',
            y='Total',
            color='Sexo',
            title='Muertes por Sexo y Departamento - Colombia 2019',
            labels={'Total': 'Total de Muertes', 'DEPARTAMENTO': 'Departamento', 'Sexo': 'Sexo'},
            barmode='stack',
            hover_data={'COD_DEPARTAMENTO': True}
        )
        
        fig.update_layout(height=600, xaxis_tickangle=-45)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating gender by department chart: {e}")
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
