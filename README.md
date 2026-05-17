# Análisis de Mortalidad en Colombia 2019

Aplicación web interactiva desarrollada con Plotly y Dash para analizar datos de mortalidad en Colombia durante el año 2019.

## Características

La aplicación incluye los siguientes elementos visuales:

1. **Mapa**: Visualización de la distribución total de muertes por departamento en Colombia
2. **Gráfico de Líneas**: Representación del total de muertes por mes mostrando variaciones a lo largo del año
3. **Gráfico de Barras**: Top 5 ciudades más violentas considerando homicidios (código X95)
4. **Gráfico Circular**: 10 ciudades con menor índice de mortalidad
5. **Tabla**: Listado de las 10 principales causas de muerte con código, nombre y total de casos
6. **Gráfico de Barras Apiladas**: Comparación del total de muertes por sexo en cada departamento
7. **Histograma**: Distribución de muertes por grupo de edad (GRUPO_EDAD1)

## Requisitos

- Python 3.9 o superior
- Archivos de datos:
  - `Anexo1.NoFetal2019_CE_15-03-23.xlsx` (Datos de mortalidad)
  - `Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx` (Códigos de causas de muerte)
  - `Divipola_CE_.xlsx` (División político-administrativa de Colombia)

## Instalación

### Local

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd analytics
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Verificar que los archivos de datos estén en la carpeta `data/`

5. Ejecutar la aplicación:
```bash
python app.py
```

6. Abrir navegador en `http://localhost:8050`

## Despliegue en Azure

### Opción 1: Azure App Service

1. **Crear App Service**:
```bash
az login
az group create --name mortality-analysis-rg --location eastus
az appservice plan create --name mortality-plan --resource-group mortality-analysis-rg --sku B1 --is-linux
az webapp create --resource-group mortality-analysis-rg --plan mortality-plan --name colombia-mortality-2019 --runtime "PYTHON:3.9"
```

2. **Configurar despliegue**:
```bash
az webapp config appsettings set --resource-group mortality-analysis-rg --name colombia-mortality-2019 --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

3. **Desplegar**:
```bash
az webapp up --resource-group mortality-analysis-rg --name colombia-mortality-2019 --runtime "PYTHON:3.9"
```

### Opción 2: Azure Container Instances

1. **Crear archivo Dockerfile** (ver sección Dockerfile abajo)

2. **Construir y subir imagen**:
```bash
az acr create --resource-group mortality-analysis-rg --name mortalityregistry --sku Basic
az acr build --registry mortalityregistry --image mortality-app:v1 .
```

3. **Desplegar contenedor**:
```bash
az container create --resource-group mortality-analysis-rg --name mortality-container --image mortalityregistry.azurecr.io/mortality-app:v1 --dns-name-label colombia-mortality --ports 8050
```

## Dockerfile

Crear archivo `Dockerfile` en la raíz del proyecto:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

CMD ["gunicorn", "-b", "0.0.0.0:8050", "app:server"]
```

## Estructura del Proyecto

```
analytics/
├── app.py                 # Aplicación principal Dash
├── requirements.txt       # Dependencias Python
├── README.md             # Documentación
├── .gitignore            # Archivos ignorados por Git
├── Dockerfile            # Configuración Docker
└── data/                 # Datos de entrada
    ├── Anexo1.NoFetal2019_CE_15-03-23.xlsx
    ├── Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx
    └── Divipola_CE_.xlsx
```

## Arquitectura

### DataLoader
Clase responsable de cargar y preprocesar los datos desde archivos Excel:
- Carga de datos de mortalidad
- Carga de códigos de causas de muerte
- Carga de datos DIVIPOLA
- Preprocesamiento y limpieza de datos

### MortalityAnalyzer
Clase que genera todas las visualizaciones:
- Mapa coroplético por departamento
- Gráfico de líneas temporal
- Gráficos de barras de violencia
- Gráfico circular de baja mortalidad
- Tabla de causas principales
- Gráfico apilado por género
- Histograma de edad

## Seguridad

- No se exponen datos sensibles en el código
- Validación de entrada de datos
- Manejo de errores robusto
- Logging de operaciones

## Rendimiento

- Carga de datos optimizada con pandas
- Visualizaciones eficientes con Plotly
- Caché de datos en memoria

## Testing

Ejecutar pruebas:
```bash
pytest tests/ -v --cov=app
```
## Interpretación resultados

## Mapa coroplético de mortalidad por departamento – Colombia 2019

<img width="1770" height="761" alt="image" src="https://github.com/user-attachments/assets/b1790b9d-c97b-45bf-8f12-851e43b21aee" />

El mapa coroplético evidencia la distribución total de muertes por departamento en Colombia durante 2019, mostrando mayores concentraciones en los territorios con tonalidades rojas más intensas, especialmente en departamentos con alta densidad poblacional y fuerte actividad urbana. Esto sugiere que el número absoluto de muertes puede estar relacionado con factores como el tamaño de la población, la urbanización, la movilidad y el acceso a servicios de salud. En contraste, los departamentos con colores más claros registran menores niveles de mortalidad. En conjunto, el mapa permite identificar diferencias territoriales importantes y resalta la necesidad de analizar la mortalidad desde una perspectiva regional.


<img width="921" height="406" alt="image" src="https://github.com/user-attachments/assets/33772c41-9b06-40b3-a859-27bc490c6be2" />


### Muertes por sexo y departamento – Colombia 2019
La distribución territorial evidencia una fuerte concentración de mortalidad en Bogotá D.C., Antioquia y Valle del Cauca, lo que resulta consistente con su densidad poblacional y nivel de urbanización. En prácticamente todos los departamentos se observa una mayor proporción de muertes masculinas frente a femeninas, sugiriendo una incidencia más alta de factores de riesgo asociados a violencia, enfermedades cardiovasculares y accidentes en hombres. Departamentos con menor población presentan volúmenes considerablemente inferiores, manteniendo una relación proporcional estable entre ambos sexos.

<img width="921" height="313" alt="image" src="https://github.com/user-attachments/assets/b007c671-76ec-4514-ac37-efc68ac291e9" />


### Top 10 causas de muerte – Colombia 2019
  Las principales causas de mortalidad están dominadas por enfermedades cardiovasculares y respiratorias, destacándose el infarto agudo de miocardio como la causa más representativa con amplia diferencia sobre las demás. La presencia recurrente de enfermedades pulmonares, neumonía e hipertensión refleja una alta carga de enfermedades crónicas no transmisibles y afecciones respiratorias. Adicionalmente, la inclusión de agresiones con armas de fuego dentro del top 10 evidencia que la violencia continúa siendo un componente relevante dentro de la mortalidad nacional. Esta distribución permite comprender que la mortalidad en Colombia durante 2019 no respondió a una única causa dominante, sino a una combinación de problemáticas de salud pública y factores sociales. La alta presencia de enfermedades cardiovasculares y respiratorias señala la importancia de fortalecer acciones preventivas relacionadas con el control de factores de riesgo, la atención temprana y el seguimiento médico de enfermedades crónicas.

<img width="921" height="562" alt="image" src="https://github.com/user-attachments/assets/1246c699-4210-463c-9147-a6dfdaf2d215" />


### Top 10 ciudades con menor mortalidad – Colombia 2019
Las ciudades identificadas presentan una participación homogénea dentro del gráfico, lo que sugiere niveles de mortalidad muy similares y relativamente bajos entre sí. La mayoría corresponde a municipios pequeños o de baja densidad poblacional ubicados en regiones periféricas como Amazonas, Chocó y Bolívar, donde el reducido tamaño poblacional influye directamente en el menor número absoluto de defunciones registradas.

<img width="921" height="672" alt="image" src="https://github.com/user-attachments/assets/84c67e71-f250-45a7-8807-85d2d0a3edc5" />


### Top 5 ciudades más violentas – Colombia 2019
Santiago de Cali y Bogotá D.C. concentran el mayor número de homicidios, posicionándose significativamente por encima del resto de ciudades analizadas. Medellín mantiene una incidencia considerable, aunque menor respecto a los dos primeros casos, mientras Barranquilla y Cúcuta muestran cifras moderadas. El comportamiento evidencia una concentración de violencia letal en grandes centros urbanos, posiblemente asociada a dinámicas de criminalidad, desigualdad social y densidad poblacional.

<img width="921" height="348" alt="image" src="https://github.com/user-attachments/assets/5071f718-5e3f-42d7-b91a-82c928b6d265" />


### Total de muertes por mes – Colombia 2019
La serie temporal evidencia el comportamiento mensual de las muertes registradas en Colombia durante 2019. En términos generales, la mortalidad presenta una dinámica relativamente estable, aunque con variaciones importantes entre algunos meses. Febrero registra el valor más bajo del año, mientras que diciembre alcanza el punto más alto, lo que permite identificar un aumento hacia el cierre del periodo analizado. También se observa un incremento progresivo entre mayo y julio, seguido de una leve disminución en agosto y septiembre, antes de un nuevo repunte en el último trimestre. Estas fluctuaciones permiten reconocer posibles patrones temporales en la mortalidad nacional; Para explicar con mayor profundidad sus causas sería necesario complementar el análisis con variables adicionales, como edad, causa de muerte, departamento, condiciones epidemiológicas, movilidad o factores estacionales. En este sentido, el gráfico constituye una herramienta útil para identificar meses críticos y orientar análisis posteriores sobre los momentos del año con mayor concentración de defunciones.

<img width="921" height="343" alt="image" src="https://github.com/user-attachments/assets/5bd6d856-ed54-42e4-84f4-b42d49da917a" />


### Distribución de muertes por grupo de edad – Colombia 2019
El histograma muestra la distribución de las muertes registradas en Colombia durante 2019 según los grupos de edad codificados en la base de datos. Se observa que la mortalidad tiende a concentrarse en los grupos de edad más avanzados, especialmente en los rangos superiores de la clasificación, lo que evidencia un aumento progresivo de las defunciones conforme avanza el ciclo de vida. Los grupos asociados a edades jóvenes presentan una frecuencia considerablemente menor, mientras que los mayores registros se ubican en las categorías correspondientes a adultez avanzada, vejez y longevidad. Este comportamiento es coherente con el incremento del riesgo de muerte en edades mayores, asociado al deterioro natural de la salud, la presencia de enfermedades crónicas y la acumulación de condiciones de vulnerabilidad.

## Contribución

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

MIT License

## Contacto

Para preguntas o soporte, contactar al equipo de desarrollo.

## Notas Adicionales

- Los datos deben estar en formato Excel (.xlsx)
- La aplicación requiere conexión a internet para cargar mapas
- Se recomienda usar navegadores modernos (Chrome, Firefox, Edge)
- Para producción, configurar variables de entorno para credenciales
