"""Top causes table module.

Creates table visualization of top 10 causes of death.
"""

import logging
from typing import Optional

import pandas as pd
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def create_top_causes_table(
    mortality_df: pd.DataFrame,
    codes_df: pd.DataFrame,
    find_column_func: callable
) -> go.Figure:
    """Create table of top 10 causes of death.
    
    Args:
        mortality_df: Mortality data DataFrame
        codes_df: Death codes DataFrame
        find_column_func: Function to find column names
        
    Returns:
        Plotly figure object
    """
    try:
        cause_col = find_column_func(['COD_MUERTE', 'CAUSA', 'COD_CAUSA', 'C_MUERTE'], mortality_df)
        if cause_col is None:
            return _create_error_figure("Cause column not found")
        
        # Aggregate by cause
        cause_deaths = mortality_df.groupby(cause_col).size().reset_index(name='Total')
        cause_deaths = cause_deaths.nlargest(10, 'Total')
        
        # Merge with codes if available
        if not codes_df.empty:
            # Use exact column names from the codes file (column indices 4 and 5)
            # Column 4: 'Código de la CIE-10 cuatro caracteres'
            # Column 5: 'Descripcion  de códigos mortalidad a cuatro caracteres'
            code_col_name = codes_df.columns[4]  # 4-character code column
            desc_col_name = codes_df.columns[5]  # Description column
            
            # Debug logging
            logger.info(f"Using code column: '{code_col_name}'")
            logger.info(f"Using description column: '{desc_col_name}'")
            
            # Clean the code columns before merging
            codes_clean = codes_df[[code_col_name, desc_col_name]].copy()
            codes_clean[code_col_name] = codes_clean[code_col_name].astype(str).str.strip()
            cause_deaths[cause_col] = cause_deaths[cause_col].astype(str).str.strip()
            
            # Create a mapping column that handles both 3-character and 4-character codes
            # The codes file has codes like 'C61X' but mortality data has 'C61'
            # We'll create a lookup key by removing trailing 'X' if present
            codes_clean['lookup_key'] = codes_clean[code_col_name].astype(str).str.strip().str.replace(r'X$', '', regex=True)
            
            # Also create lookup key for mortality codes
            cause_deaths['lookup_key'] = cause_deaths[cause_col].astype(str).str.strip().str.replace(r'X$', '', regex=True)
            
            # Perform the merge using the lookup keys
            cause_deaths = cause_deaths.merge(
                codes_clean[['lookup_key', desc_col_name]].drop_duplicates(subset=['lookup_key']),
                on='lookup_key',
                how='left'
            )
            
            # Create the Nombre column from the description
            cause_deaths['Nombre'] = cause_deaths[desc_col_name].fillna('Desconocido')
            logger.info(f"Merge successful. Sample names: {cause_deaths['Nombre'].head().tolist()}")
        else:
            logger.warning("Codes DataFrame is empty")
            cause_deaths['Nombre'] = 'Desconocido'
        
        # Create final dataframe with only needed columns
        result_df = pd.DataFrame({
            'Código': cause_deaths[cause_col],
            'Nombre': cause_deaths['Nombre'],
            'Total': cause_deaths['Total']
        })
        
        # Create table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['Código', 'Nombre', 'Total de Casos'],
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=[
                    result_df['Código'],
                    result_df['Nombre'],
                    result_df['Total']
                ],
                fill_color='lavender',
                align='left',
                font=dict(size=11)
            )
        )])
        
        fig.update_layout(
            title='Top 10 Causas de Muerte - Colombia 2019',
            height=500
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating causes table: {e}")
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
