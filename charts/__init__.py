"""Charts package for mortality data visualizations.

This package contains individual modules for each chart type used in the
mortality analysis dashboard.
"""

from .department_map import create_department_map
from .monthly_line_chart import create_monthly_line_chart
from .violent_cities_chart import create_violent_cities_chart
from .lowest_mortality_pie import create_lowest_mortality_pie
from .top_causes_table import create_top_causes_table
from .gender_by_department_chart import create_gender_by_department_chart
from .age_histogram import create_age_histogram

__all__ = [
    'create_department_map',
    'create_monthly_line_chart',
    'create_violent_cities_chart',
    'create_lowest_mortality_pie',
    'create_top_causes_table',
    'create_gender_by_department_chart',
    'create_age_histogram',
]
