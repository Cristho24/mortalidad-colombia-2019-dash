"""Dash application for analyzing mortality data in Colombia (2019).

This application provides interactive visualizations for exploring mortality patterns
across Colombia, including geographic distribution, temporal trends, demographics,
and leading causes of death.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from dash.exceptions import PreventUpdate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path(__file__).parent / 'data'
MORTALITY_FILE = 'Anexo1.NoFetal2019_CE_15-03-23.xlsx'
CODES_FILE = 'Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx'
DIVIPOLA_FILE = 'Divipola_CE_.xlsx'
GEOJSON_FILE = 'colombia_departamentos.geojson'

# Homicide codes
HOMICIDE_CODES = ['X95']  # Assault by firearms


class DataLoader:
    """Handles loading and preprocessing of mortality data."""

    def __init__(self, data_dir: Path):
        """Initialize DataLoader with data directory path.
        
        Args:
            data_dir: Path to directory containing data files
        """
        self.data_dir = data_dir
        self.mortality_df: Optional[pd.DataFrame] = None
        self.codes_df: Optional[pd.DataFrame] = None
        self.divipola_df: Optional[pd.DataFrame] = None

    def load_data(self) -> None:
        """Load all required data files.
        
        Raises:
            FileNotFoundError: If any required data file is missing
            Exception: If data loading fails
        """
        try:
            logger.info("Loading mortality data...")
            self.mortality_df = pd.read_excel(
                self.data_dir / MORTALITY_FILE,
                engine='openpyxl'
            )
            
            logger.info("Loading death codes...")
            # Load codes file with header at row 8 (0-indexed)
            self.codes_df = pd.read_excel(
                self.data_dir / CODES_FILE,
                engine='openpyxl',
                header=8  # Header row is at index 8
            )
            
            logger.info("Loading DIVIPOLA data...")
            self.divipola_df = pd.read_excel(
                self.data_dir / DIVIPOLA_FILE,
                engine='openpyxl'
            )
            
            logger.info("Data loaded successfully")
            self._preprocess_data()
            
        except FileNotFoundError as e:
            logger.error(f"Data file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise

    def _preprocess_data(self) -> None:
        """Preprocess loaded data for analysis."""
        if self.mortality_df is None:
            return
            
        # Convert date columns if present
        date_columns = ['FECHA', 'FECHA_DEF', 'FEC_DEF']
        for col in date_columns:
            if col in self.mortality_df.columns:
                try:
                    self.mortality_df[col] = pd.to_datetime(
                        self.mortality_df[col],
                        errors='coerce'
                    )
                except Exception as e:
                    logger.warning(f"Could not convert {col} to datetime: {e}")
        
        # Clean string columns
        str_columns = self.mortality_df.select_dtypes(include=['str', 'object']).columns
        for col in str_columns:
            self.mortality_df[col] = self.mortality_df[col].astype(str).str.strip()
        
        # Preprocess codes dataframe - read with proper header row (row 8)
        if self.codes_df is not None:
            # The codes file has headers at row 8 (0-indexed)
            # We need to reload it with the correct header
            logger.info("Reloading codes file with correct header...")
            try:
                codes_file_path = Path(__file__).parent / 'data' / CODES_FILE
                self.codes_df = pd.read_excel(
                    codes_file_path,
                    engine='openpyxl',
                    header=8  # Header is at row 8 (0-indexed)
                )
                logger.info(f"Codes file reloaded. Columns: {self.codes_df.columns.tolist()}")
            except Exception as e:
                logger.error(f"Error reloading codes file: {e}")

    def get_mortality_data(self) -> pd.DataFrame:
        """Get mortality dataframe.
        
        Returns:
            Mortality dataframe
            
        Raises:
            ValueError: If data not loaded
        """
        if self.mortality_df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        return self.mortality_df

    def get_codes_data(self) -> pd.DataFrame:
        """Get death codes dataframe.
        
        Returns:
            Death codes dataframe
            
        Raises:
            ValueError: If data not loaded
        """
        if self.codes_df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        return self.codes_df

    def get_divipola_data(self) -> pd.DataFrame:
        """Get DIVIPOLA dataframe.
        
        Returns:
            DIVIPOLA dataframe
            
        Raises:
            ValueError: If data not loaded
        """
        if self.divipola_df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        return self.divipola_df


class MortalityAnalyzer:
    """Analyzes mortality data and generates visualizations."""

    def __init__(self, data_loader: DataLoader):
        """Initialize analyzer with data loader.
        
        Args:
            data_loader: DataLoader instance with loaded data
        """
        self.data_loader = data_loader
        self.mortality_df = data_loader.get_mortality_data()
        self.codes_df = data_loader.get_codes_data()
        self.divipola_df = data_loader.get_divipola_data()

    def create_department_bar_chart(self) -> go.Figure:
        """Create choropleth map of deaths by department.
        
        Returns:
            Plotly figure object
        """
        try:
            # Find department column in mortality data
            dept_col = self._find_column(['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'DEPTO', 'COD_DPTO'])
            if dept_col is None:
                logger.error("Department column not found")
                return self._create_error_figure("Department data not available")
            
            # Aggregate deaths by department code
            dept_deaths = self.mortality_df.groupby(dept_col).size().reset_index(name='Total_Muertes')
            dept_deaths.columns = ['COD_DEPARTAMENTO', 'Total_Muertes']
            
            # Merge with DIVIPOLA to get department names
            divipola_dept = self.divipola_df[['COD_DEPARTAMENTO', 'DEPARTAMENTO']].drop_duplicates()
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
            return self._create_error_figure(f"Error: {str(e)}")

def create_department_map(self) -> go.Figure:
    """Create choropleth map of deaths by department.

    Returns:
        Plotly figure object
    """
    try:
        dept_col = self._find_column(['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'DEPTO', 'COD_DPTO'])

        if dept_col is None:
            logger.error("Department column not found")
            return self._create_error_figure("No se encontró la columna de departamento")

        # Agrupar muertes por departamento
        dept_deaths = self.mortality_df.groupby(dept_col).size().reset_index(name='Total_Muertes')
        dept_deaths.columns = ['COD_DEPARTAMENTO', 'Total_Muertes']

        # Normalizar códigos de departamento a dos dígitos
        dept_deaths['COD_DEPARTAMENTO'] = (
            dept_deaths['COD_DEPARTAMENTO']
            .astype(str)
            .str.replace('.0', '', regex=False)
            .str.zfill(2)
        )

        # Preparar nombres de departamentos desde DIVIPOLA
        divipola_dept = self.divipola_df[['COD_DEPARTAMENTO', 'DEPARTAMENTO']].drop_duplicates()
        divipola_dept['COD_DEPARTAMENTO'] = (
            divipola_dept['COD_DEPARTAMENTO']
            .astype(str)
            .str.replace('.0', '', regex=False)
            .str.zfill(2)
        )

        dept_deaths = dept_deaths.merge(
            divipola_dept,
            on='COD_DEPARTAMENTO',
            how='left'
        )

        dept_deaths['DEPARTAMENTO'] = dept_deaths['DEPARTAMENTO'].fillna('Desconocido')

        # Cargar archivo GeoJSON
        geojson_path = self.data_loader.data_dir / GEOJSON_FILE

        with open(geojson_path, 'r', encoding='utf-8') as f:
            colombia_geojson = json.load(f)

        # Detectar columna del GeoJSON con el código de departamento
        possible_geojson_keys = [
            'COD_DEPARTAMENTO',
            'COD_DEPTO',
            'DPTO_CCDGO',
            'DPTO',
            'codigo',
            'Código',
            'CODIGO',
            'depto',
            'id'
        ]

        first_feature_props = colombia_geojson['features'][0]['properties']
        geojson_key = None

        for key in possible_geojson_keys:
            if key in first_feature_props:
                geojson_key = key
                break

        if geojson_key is None:
            logger.error(f"Propiedades disponibles en GeoJSON: {first_feature_props.keys()}")
            return self._create_error_figure(
                "No se encontró una propiedad compatible con el código de departamento en el GeoJSON"
            )

        # Normalizar códigos dentro del GeoJSON
        for feature in colombia_geojson['features']:
            value = feature['properties'].get(geojson_key)
            feature['properties'][geojson_key] = str(value).replace('.0', '').zfill(2)

        # Crear mapa coroplético
        fig = px.choropleth(
            dept_deaths,
            geojson=colombia_geojson,
            locations='COD_DEPARTAMENTO',
            featureidkey=f'properties.{geojson_key}',
            color='Total_Muertes',
            hover_name='DEPARTAMENTO',
            hover_data={
                'COD_DEPARTAMENTO': True,
                'Total_Muertes': ':,'
            },
            color_continuous_scale='Reds',
            title='Mapa de distribución total de muertes por departamento - Colombia 2019'
        )

        fig.update_geos(
            fitbounds="locations",
            visible=False
        )

        fig.update_layout(
            height=650,
            margin={"r": 0, "t": 60, "l": 0, "b": 0},
            coloraxis_colorbar_title="Total de muertes"
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating department map: {e}")
        return self._create_error_figure(f"Error al crear el mapa: {str(e)}")
    
    def create_monthly_line_chart(self) -> go.Figure:
        """Create line chart of deaths by month.
        
        Returns:
            Plotly figure object
        """
        try:
            # Find date column
            date_col = self._find_column(['MES', 'FECHA', 'FECHA_DEF', 'FEC_DEF'])
            if date_col is None:
                return self._create_error_figure("Date column not found")
            
            # Extract month
            if date_col == 'MES':
                monthly_data = self.mortality_df.groupby('MES').size().reset_index(name='Total_Muertes')
                monthly_data.columns = ['Mes', 'Total_Muertes']
            else:
                self.mortality_df['Mes'] = pd.to_datetime(
                    self.mortality_df[date_col],
                    errors='coerce'
                ).dt.month
                monthly_data = self.mortality_df.groupby('Mes').size().reset_index(name='Total_Muertes')
            
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
            return self._create_error_figure(f"Error: {str(e)}")

    def create_violent_cities_chart(self) -> go.Figure:
        """Create bar chart of top 5 most violent cities.
        
        Returns:
            Plotly figure object
        """
        try:
            # Find MANERA_MUERTE, city, and department columns
            manera_muerte_col = self._find_column(['MANERA_MUERTE', 'MANERA', 'TIPO_MUERTE'])
            city_col = self._find_column(['COD_MUNICIPIO', 'MUNICIPIO', 'CIUDAD', 'MUN', 'COD_MUN'])
            dept_col = self._find_column(['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'DEPTO', 'COD_DPTO'])
            
            if manera_muerte_col is None or city_col is None or dept_col is None:
                return self._create_error_figure("Required columns not found")
            
            # Filter homicides using MANERA_MUERTE = 'Homicidio'
            homicides = self.mortality_df[
                self.mortality_df[manera_muerte_col].astype(str).str.strip().str.upper() == 'HOMICIDIO'
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
            divipola_mun = self.divipola_df[['COD_DANE', 'MUNICIPIO', 'DEPARTAMENTO']].drop_duplicates()
            
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
            return self._create_error_figure(f"Error: {str(e)}")

    def create_lowest_mortality_pie(self) -> go.Figure:
        """Create pie chart of 10 cities with lowest mortality.
        
        Returns:
            Plotly figure object
        """
        try:
            city_col = self._find_column(['COD_MUNICIPIO', 'MUNICIPIO', 'CIUDAD', 'MUN', 'COD_MUN'])
            dept_col = self._find_column(['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'DEPTO', 'COD_DPTO'])
            
            if city_col is None or dept_col is None:
                return self._create_error_figure("Required columns not found")
            
            # Create COD_DANE for proper city identification
            mortality_with_dane = self.mortality_df.copy()
            mortality_with_dane['COD_DANE'] = (
                mortality_with_dane[dept_col].astype(str).str.zfill(2) + 
                mortality_with_dane[city_col].astype(str).str.zfill(3)
            ).astype(int)
            
            # Aggregate by COD_DANE
            city_deaths = mortality_with_dane.groupby('COD_DANE').size().reset_index(name='Total_Muertes')
            
            # Merge with DIVIPOLA to get city names
            divipola_mun = self.divipola_df[['COD_DANE', 'MUNICIPIO', 'DEPARTAMENTO']].drop_duplicates()
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
            return self._create_error_figure(f"Error: {str(e)}")

    def create_top_causes_table(self) -> go.Figure:
        """Create table of top 10 causes of death.
        
        Returns:
            Plotly figure object
        """
        try:
            cause_col = self._find_column(['COD_MUERTE', 'CAUSA', 'COD_CAUSA', 'C_MUERTE'])
            if cause_col is None:
                return self._create_error_figure("Cause column not found")
            
            # Aggregate by cause
            cause_deaths = self.mortality_df.groupby(cause_col).size().reset_index(name='Total')
            cause_deaths = cause_deaths.nlargest(10, 'Total')
            
            # Merge with codes if available
            if not self.codes_df.empty:
                # Use exact column names from the codes file (column indices 4 and 5)
                # Column 4: 'Código de la CIE-10 cuatro caracteres'
                # Column 5: 'Descripcion  de códigos mortalidad a cuatro caracteres'
                code_col_name = self.codes_df.columns[4]  # 4-character code column
                desc_col_name = self.codes_df.columns[5]  # Description column
                
                # Debug logging
                logger.info(f"Using code column: '{code_col_name}'")
                logger.info(f"Using description column: '{desc_col_name}'")
                
                # Clean the code columns before merging
                codes_clean = self.codes_df[[code_col_name, desc_col_name]].copy()
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
            return self._create_error_figure(f"Error: {str(e)}")

    def create_gender_by_department_chart(self) -> go.Figure:
        """Create stacked bar chart of deaths by gender and department.
        
        Returns:
            Plotly figure object
        """
        try:
            dept_col = self._find_column(['COD_DEPARTAMENTO', 'DEPARTAMENTO', 'DEPTO', 'COD_DPTO'])
            gender_col = self._find_column(['SEXO', 'GENERO', 'SEX'])
            
            if dept_col is None or gender_col is None:
                return self._create_error_figure("Required columns not found")
            
            # Aggregate by department code and gender
            gender_dept = self.mortality_df.groupby([dept_col, gender_col]).size().reset_index(name='Total')
            gender_dept.columns = ['COD_DEPARTAMENTO', 'Sexo', 'Total']
            
            # Merge with DIVIPOLA to get department names
            divipola_dept = self.divipola_df[['COD_DEPARTAMENTO', 'DEPARTAMENTO']].drop_duplicates()
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
            return self._create_error_figure(f"Error: {str(e)}")

    def create_age_histogram(self) -> go.Figure:
        """Create histogram of deaths by age group.
        
        Returns:
            Plotly figure object
        """
        try:
            age_col = self._find_column(['GRUPO_EDAD1', 'EDAD', 'GRUPO_EDAD', 'RANGO_EDAD'])
            if age_col is None:
                return self._create_error_figure("Age column not found")
            
            # Create histogram
            fig = px.histogram(
                self.mortality_df,
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
            return self._create_error_figure(f"Error: {str(e)}")

    def _find_column(self, possible_names: list, df: Optional[pd.DataFrame] = None) -> Optional[str]:
        """Find column name from list of possible names.
        
        Args:
            possible_names: List of possible column names
            df: DataFrame to search (defaults to mortality_df)
            
        Returns:
            Column name if found, None otherwise
        """
        if df is None:
            df = self.mortality_df
            
        for name in possible_names:
            if name in df.columns:
                return name
            # Try case-insensitive match
            for col in df.columns:
                if col.upper() == name.upper():
                    return col
            # Try partial match (e.g., 'DEPARTAMENTO' matches 'COD_DEPARTAMENTO')
            for col in df.columns:
                if name.upper() in col.upper() or col.upper() in name.upper():
                    return col
        return None

    def _create_error_figure(self, message: str) -> go.Figure:
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


def create_app() -> Dash:
    """Create and configure Dash application.
    
    Returns:
        Configured Dash application instance
    """
    # Initialize data loader
    data_loader = DataLoader(DATA_DIR)
    
    try:
        data_loader.load_data()
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    # Initialize analyzer
    analyzer = MortalityAnalyzer(data_loader)
    
    # Create Dash app
    app = Dash(
        __name__,
        title="Análisis de Mortalidad Colombia 2019",
        suppress_callback_exceptions=True
    )
    
    # Define layout
    app.layout = html.Div([
        html.H1(
            "Análisis de Mortalidad en Colombia - 2019",
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}
        ),
        
        html.Div([
    html.H2("Mapa de distribución total de muertes por departamento", style={'color': '#34495e'}),
    dcc.Graph(id='department-map', figure=analyzer.create_department_map())
], style={'marginBottom': '40px'}),

html.Div([
    html.H2("Comparación del total de muertes por departamento", style={'color': '#34495e'}),
    dcc.Graph(id='department-bar-chart', figure=analyzer.create_department_bar_chart())
], style={'marginBottom': '40px'}),
        
        html.Div([
            html.H2("Tendencia Mensual de Muertes", style={'color': '#34495e'}),
            dcc.Graph(id='monthly-line', figure=analyzer.create_monthly_line_chart())
        ], style={'marginBottom': '40px'}),
        
        html.Div([
            html.Div([
                html.H2("Ciudades Más Violentas", style={'color': '#34495e'}),
                dcc.Graph(id='violent-cities', figure=analyzer.create_violent_cities_chart())
            ], style={'width': '48%', 'display': 'inline-block'}),
            
            html.Div([
                html.H2("Ciudades con Menor Mortalidad", style={'color': '#34495e'}),
                dcc.Graph(id='lowest-mortality', figure=analyzer.create_lowest_mortality_pie())
            ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
        ], style={'marginBottom': '40px'}),
        
        html.Div([
            html.H2("Principales Causas de Muerte", style={'color': '#34495e'}),
            dcc.Graph(id='top-causes', figure=analyzer.create_top_causes_table())
        ], style={'marginBottom': '40px'}),
        
        html.Div([
            html.H2("Distribución por Sexo y Departamento", style={'color': '#34495e'}),
            dcc.Graph(id='gender-department', figure=analyzer.create_gender_by_department_chart())
        ], style={'marginBottom': '40px'}),
        
        html.Div([
            html.H2("Distribución por Grupo de Edad", style={'color': '#34495e'}),
            dcc.Graph(id='age-histogram', figure=analyzer.create_age_histogram())
        ], style={'marginBottom': '40px'}),
        
        html.Footer(
            "Análisis de Mortalidad Colombia 2019 - Datos oficiales",
            style={'textAlign': 'center', 'color': '#7f8c8d', 'marginTop': '50px', 'padding': '20px'}
        )
    ], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif'})
    
    return app


app = create_app()
server = app.server

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=8050)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
