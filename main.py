import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import requests
import time
import logging
from typing import Dict, List, Any
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('BlockchainInfoAPI')

class BlockchainInfoAPI:
    BASE_URL = "https://api.blockchain.info"

    def __init__(self, duracion_cache: int = 3600):
        self.headers = {
            'accept': '*/*',
            'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
            'origin': 'https://www.blockchain.com',
            'referer': 'https://www.blockchain.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

        self.parametros_predeterminados = {
            'timespan': '1year',
            'sampled': 'true',
            'metadata': 'false',
            'daysAverageString': '1d',
            'cors': 'true',
            'format': 'json',
        }

        self.cache = {}
        self.duracion_cache = duracion_cache

        self.nombres_descriptivos = {
            'market-price': 'Precio de Mercado (USD)',
            'market-cap': 'Capitalización de Mercado',
            'trade-volume': 'Volumen de Comercio USD',
            'blocks-size': 'Tamaño de Blockchain (MB)',
            'avg-block-size': 'Tamaño Promedio de Bloque (MB)',
            'n-transactions-per-block': 'Transacciones por Bloque',
            'n-payments-per-block': 'Pagos por Bloque',
            'n-transactions-total': 'Número Total de Transacciones',
            'median-confirmation-time': 'Tiempo Mediano de Confirmación',
            'avg-confirmation-time': 'Tiempo Promedio de Confirmación',
            'hash-rate': 'Tasa de Hash (TH/s)',
            'difficulty': 'Dificultad de Minería',
            'miners-revenue': 'Ingresos de Mineros (USD)',
            'transaction-fees': 'Comisiones Totales (BTC)',
            'transaction-fees-usd': 'Comisiones Totales (USD)',
            'cost-per-transaction': 'Costo por Transacción',
            'cost-per-transaction-percent': 'Costo por Transacción (%)',
            'n-unique-addresses': 'Direcciones Únicas Usadas',
            'n-transactions': 'Transacciones Confirmadas por Día',
            'n-payments': 'Pagos Confirmados por Día',
            'transactions-per-second': 'Transacciones por Segundo',
            'output-volume': 'Valor de Salida por Día',
            'mempool-count': 'Conteo de Transacciones Mempool',
            'mempool-growth': 'Crecimiento del Mempool',
            'mempool-size': 'Tamaño del Mempool (Bytes)',
            'mempool-state-by-fee-level': 'Estado del Mempool por Nivel de Comisión',
            'utxo-count': 'Salidas No Gastadas (UTXO)',
            'n-transactions-excluding-popular': 'Transacciones (Excluyendo Populares)',
            'estimated-transaction-volume': 'Valor de Transacción Estimado (BTC)',
            'estimated-transaction-volume-usd': 'Valor de Transacción Estimado (USD)',
            'mvrv': 'MVRV - Valor de Mercado a Valor Realizado',
            'nvt': 'NVT - Valor de Red a Transacciones',
            'nvts': 'Señal NVT',
            'total-bitcoins': 'Bitcoins en Circulación',
        }

    def _hacer_solicitud(self, endpoint: str, params: Dict[str, Any] = None, usar_cache: bool = True) -> Dict[str, Any]:
        if params is None:
            params = {}

        if 'charts' in endpoint:
            new_params = self.parametros_predeterminados.copy()
            new_params.update(params)
            params = new_params

        clave_cache = f"{endpoint}_{str(params)}"
        ahora = time.time()

        if usar_cache and clave_cache in self.cache:
            datos_cache, timestamp = self.cache[clave_cache]
            if ahora - timestamp < self.duracion_cache:
                return datos_cache

        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            respuesta = requests.get(url, params=params, headers=self.headers)
            respuesta.raise_for_status()
            datos = respuesta.json()

            if usar_cache:
                self.cache[clave_cache] = (datos, ahora)

            return datos

        except requests.exceptions.RequestException as e:
            logger.error(f"Error en {url}: {str(e)}")
            raise

    def _procesar_datos_grafico(self, datos: Dict[str, Any]) -> pd.DataFrame:
        df = pd.DataFrame(datos['values'])

        if 'x' in df.columns:
            df = df.set_index('x')
            df.index = pd.to_datetime(df.index, unit='s')
        
        if 'y' not in df.columns and len(df.columns) > 0:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                df = df.rename(columns={numeric_cols[0]: 'y'})

        return df

    def obtener_grafico(self, nombre_grafico: str, **params) -> pd.DataFrame:
        try:
            if nombre_grafico == 'mempool-state-by-fee-level':
                endpoint = 'charts/mempool-state-by-fee-level/interval'
                params = {'cors': 'true'}
            else:
                endpoint = f"charts/{nombre_grafico}"
            
            datos = self._hacer_solicitud(endpoint, params)
            
            if not datos or 'values' not in datos or not datos['values']:
                return pd.DataFrame()
            
            return self._procesar_datos_grafico(datos)
            
        except Exception as e:
            logger.error(f"Error al obtener {nombre_grafico}: {str(e)}")
            return pd.DataFrame()

    def obtener_pools(self, **params) -> pd.DataFrame:
        try:
            if 'timespan' not in params:
                params['timespan'] = '4days'
            params['cors'] = 'true'

            endpoint = "pools"
            datos = self._hacer_solicitud(endpoint, params)

            df = pd.DataFrame(columns=['relativeSize'])

            if isinstance(datos, dict):
                for pool, info in datos.items():
                    if isinstance(info, dict) and 'relativeSize' in info:
                        df.at[pool, 'relativeSize'] = info['relativeSize']
                    elif isinstance(info, (int, float)):
                        df.at[pool, 'relativeSize'] = info

            return df.sort_values('relativeSize', ascending=False) if not df.empty else df

        except Exception as e:
            logger.error(f"Error al obtener pools: {str(e)}")
            return pd.DataFrame(columns=['relativeSize'])

    def obtener_categorias_graficos(self) -> Dict[str, List[str]]:
        return {
            'Mercado': ['market-price', 'market-cap', 'trade-volume'],
            'Detalles de Bloques': [
                'blocks-size', 'avg-block-size', 'n-transactions-per-block',
                'n-payments-per-block', 'n-transactions-total',
                'median-confirmation-time', 'avg-confirmation-time'
            ],
            'Información de Minería': [
                'hash-rate', 'difficulty', 'miners-revenue',
                'transaction-fees', 'transaction-fees-usd',
                'cost-per-transaction', 'cost-per-transaction-percent'
            ],
            'Actividad de Red': [
                'n-unique-addresses', 'n-transactions', 'n-payments',
                'transactions-per-second', 'output-volume', 'mempool-count',
                'mempool-growth', 'mempool-size', 'mempool-state-by-fee-level',
                'utxo-count', 'n-transactions-excluding-popular',
                'estimated-transaction-volume', 'estimated-transaction-volume-usd'
            ],
            'Señales de Mercado': ['mvrv', 'nvt', 'nvts'],
            'Suministro': ['total-bitcoins']
        }

    def obtener_precio_mercado(self, **params) -> pd.DataFrame:
        return self.obtener_grafico('market-price', **params)

    def obtener_cap_mercado(self, **params) -> pd.DataFrame:
        return self.obtener_grafico('market-cap', **params)

    def obtener_volumen_comercio(self, **params) -> pd.DataFrame:
        return self.obtener_grafico('trade-volume', **params)

    def obtener_transacciones(self, **params) -> pd.DataFrame:
        return self.obtener_grafico('n-transactions', **params)

st.set_page_config(
    page_title="Bitcoin Analytics Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        margin: 10px 0;
    }
    .gradient-text {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
    }
    .subtitle {
        color: #a8b2d1;
        text-align: center;
        font-size: 1.2em;
        margin-bottom: 40px;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: bold;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    [data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.8);
        backdrop-filter: blur(10px);
    }
    .info-box {
        background: rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        color: #a8b2d1;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #a8b2d1;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_api():
    return BlockchainInfoAPI()

api = init_api()

def crear_grafico_plotly(df, titulo, y_label="Valor"):
    fig = go.Figure()
    
    for col in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col],
            mode='lines',
            name=col,
            line=dict(width=2),
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Valor: %{y:,.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=20, color='#e6e6e6')),
        xaxis_title="Fecha",
        yaxis_title=y_label,
        template="plotly_dark",
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#a8b2d1'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        height=500
    )
    
    return fig

st.markdown('<h1 class="gradient-text">₿ Bitcoin Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Análisis profesional de datos de blockchain en tiempo real</p>', unsafe_allow_html=True)

timespan_options = {
    "1 día": "1days",
    "1 semana": "1weeks",
    "1 mes": "1months",
    "3 meses": "3months",
    "6 meses": "6months",
    "1 año": "1year",
    "2 años": "2years",
    "3 años": "3years",
    "5 años": "5years",
    "Todo": "all"
}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/1200px-Bitcoin.svg.png", width=100)
    st.markdown("## 🎯 Navegación")
    
    seccion = st.radio(
        "Selecciona una sección:",
        ["🏠 Inicio", "📊 Visualización", "📈 Comparación", "🔍 Explorador", "📥 Exportar Datos"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuración")
    
    timespan_label = st.selectbox("📅 Período de tiempo", list(timespan_options.keys()), index=6)
    timespan = timespan_options[timespan_label]
    
    st.markdown("---")
    
    categorias = api.obtener_categorias_graficos()
    total_metricas = sum(len(graficos) for graficos in categorias.values())
    
    st.markdown(f"""
    <div class="info-box">
    <b>📊 {total_metricas} métricas</b> disponibles<br>
    <b>💡 Tip:</b> Explora diferentes métricas para obtener insights profundos sobre Bitcoin.
    </div>
    """, unsafe_allow_html=True)

if seccion == "🏠 Inicio":
    st.markdown("### 📊 Métricas Clave en Tiempo Real")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with st.spinner("Cargando datos..."):
        try:
            precio_df = api.obtener_precio_mercado(timespan='30days')
            if len(precio_df) > 0:
                valor_col = 'y' if 'y' in precio_df.columns else precio_df.columns[0]
                precio_actual = precio_df[valor_col].iloc[-1]
                precio_anterior = precio_df[valor_col].iloc[-2] if len(precio_df) > 1 else precio_actual
                delta_precio = ((precio_actual - precio_anterior) / precio_anterior) * 100
                with col1:
                    st.metric("💰 Precio Bitcoin", f"${precio_actual:,.2f}", f"{delta_precio:+.2f}%")
            else:
                with col1:
                    st.metric("💰 Precio Bitcoin", "N/A")
            
            cap_df = api.obtener_cap_mercado(timespan='30days')
            if len(cap_df) > 0:
                valor_col = 'y' if 'y' in cap_df.columns else cap_df.columns[0]
                cap_actual = cap_df[valor_col].iloc[-1]
                with col2:
                    st.metric("📈 Cap. de Mercado", f"${cap_actual/1e9:.2f}B")
            else:
                with col2:
                    st.metric("📈 Cap. de Mercado", "N/A")
            
            volumen_df = api.obtener_volumen_comercio(timespan='30days')
            if len(volumen_df) > 0:
                valor_col = 'y' if 'y' in volumen_df.columns else volumen_df.columns[0]
                volumen_actual = volumen_df[valor_col].iloc[-1]
                with col3:
                    st.metric("💹 Volumen 24h", f"${volumen_actual/1e6:.2f}M")
            else:
                with col3:
                    st.metric("💹 Volumen 24h", "N/A")
            
            tx_df = api.obtener_transacciones(timespan='30days')
            if len(tx_df) > 0:
                valor_col = 'y' if 'y' in tx_df.columns else tx_df.columns[0]
                tx_actual = tx_df[valor_col].iloc[-1]
                with col4:
                    st.metric("🔄 Transacciones 24h", f"{tx_actual:,.0f}")
            else:
                with col4:
                    st.metric("🔄 Transacciones 24h", "N/A")
        
        except Exception as e:
            st.error(f"Error al cargar métricas: {str(e)}")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📈 Evolución del Precio")
        try:
            precio_df = api.obtener_precio_mercado(timespan=timespan)
            if not precio_df.empty:
                fig = crear_grafico_plotly(precio_df, "Precio de Bitcoin (USD)", "Precio (USD)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ No hay datos disponibles")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with col2:
        st.markdown("### ℹ️ Acerca de")
        st.markdown("""
        <div class="metric-card">
        <p><b>Bitcoin Analytics Dashboard</b> te permite:</p>
        <ul>
            <li>📊 Visualizar métricas clave</li>
            <li>📈 Comparar indicadores</li>
            <li>🔍 Explorar datos históricos</li>
            <li>📥 Exportar en CSV/Excel</li>
        </ul>
        <p style="margin-top: 20px; color: #667eea;">
        <b>Datos en tiempo real</b> desde blockchain.info
        </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Categorías")
        for cat, graficos in categorias.items():
            with st.expander(f"📁 {cat}"):
                st.write(f"**{len(graficos)} métricas**")

elif seccion == "📊 Visualización":
    st.markdown("### 📊 Visualización de Métricas")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        categorias = api.obtener_categorias_graficos()
        categoria_seleccionada = st.selectbox("🏷️ Categoría", list(categorias.keys()))
        
        graficos_categoria = categorias[categoria_seleccionada]
        nombres_mostrar = [api.nombres_descriptivos.get(g, g) for g in graficos_categoria]
        metrica_mostrar = st.selectbox("📈 Métrica", nombres_mostrar)
        
        indice = nombres_mostrar.index(metrica_mostrar)
        metrica_seleccionada = graficos_categoria[indice]
        
        tipo_grafico = st.selectbox("📊 Tipo de gráfico", ["Línea", "Área"])
    
    with col2:
        st.markdown(f"<div class='metric-card'><h4>{metrica_mostrar}</h4><code>{metrica_seleccionada}</code></div>", unsafe_allow_html=True)
    
    if st.button("🚀 Cargar Datos", type="primary"):
        with st.spinner("Obteniendo datos..."):
            try:
                df = api.obtener_grafico(metrica_seleccionada, timespan=timespan)
                
                if df.empty:
                    st.error("❌ No hay datos disponibles")
                    st.info("💡 Intenta con otro período o métrica")
                else:
                    fig = go.Figure()
                    
                    if tipo_grafico == "Línea":
                        for col in df.columns:
                            fig.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=col, line=dict(width=2)))
                    else:
                        for col in df.columns:
                            fig.add_trace(go.Scatter(x=df.index, y=df[col], fill='tozeroy', name=col))
                    
                    fig.update_layout(
                        title=dict(text=metrica_mostrar, font=dict(size=20, color='#e6e6e6')),
                        xaxis_title="Fecha",
                        yaxis_title="Valor",
                        template="plotly_dark",
                        hovermode='x unified',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#a8b2d1'),
                        height=600
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("### 📊 Estadísticas")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    valor_col = 'y' if 'y' in df.columns else df.columns[0]
                    
                    with col1:
                        st.metric("Máximo", f"{df[valor_col].max():,.2f}")
                    with col2:
                        st.metric("Mínimo", f"{df[valor_col].min():,.2f}")
                    with col3:
                        st.metric("Promedio", f"{df[valor_col].mean():,.2f}")
                    with col4:
                        st.metric("Último Valor", f"{df[valor_col].iloc[-1]:,.2f}")
                    
                    with st.expander("📋 Ver datos en tabla"):
                        st.dataframe(df.tail(50), use_container_width=True)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif seccion == "📈 Comparación":
    st.markdown("### 📈 Comparación de Múltiples Métricas")
    
    # Inicializar session state para métricas seleccionadas
    if 'metricas_comparacion' not in st.session_state:
        st.session_state.metricas_comparacion = []
    
    # Sugerencias de combinaciones
    combinaciones_sugeridas = {
        "💰 Precio y Mercado": ['market-price', 'market-cap', 'trade-volume'],
        "⛏️ Minería": ['hash-rate', 'difficulty', 'miners-revenue'],
        "📊 Actividad de Red": ['n-transactions', 'n-unique-addresses', 'transactions-per-second'],
        "💸 Comisiones": ['transaction-fees', 'transaction-fees-usd', 'cost-per-transaction'],
        "🧠 Mempool": ['mempool-count', 'mempool-size', 'mempool-growth'],
        "📈 Señales de Mercado": ['mvrv', 'nvt', 'nvts'],
        "🔗 Blockchain": ['blocks-size', 'avg-block-size', 'n-transactions-per-block'],
        "⚡ Rendimiento": ['avg-confirmation-time', 'median-confirmation-time', 'transactions-per-second']
    }
    
    st.markdown("#### 🎯 Combinaciones Sugeridas")
    st.info("💡 Selecciona una combinación predefinida haciendo clic en el botón correspondiente")
    
    cols = st.columns(4)
    for idx, (nombre, metricas) in enumerate(combinaciones_sugeridas.items()):
        with cols[idx % 4]:
            if st.button(nombre, key=f"combo_{idx}", use_container_width=True):
                st.session_state.metricas_comparacion = metricas.copy()
    
    st.markdown("---")
    
    categorias = api.obtener_categorias_graficos()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📋 Selección Manual de Métricas")
        
        # Botón para limpiar selección
        if st.button("🗑️ Limpiar Selección"):
            st.session_state.metricas_comparacion = []
        
        # Si hay métricas en session state, mostrarlas
        if st.session_state.metricas_comparacion:
            st.success(f"✅ {len(st.session_state.metricas_comparacion)} métricas seleccionadas")
            for m in st.session_state.metricas_comparacion:
                st.write(f"• {api.nombres_descriptivos.get(m, m)}")
        
        # Selección manual con checkboxes
        for categoria, graficos in categorias.items():
            with st.expander(f"📁 {categoria} ({len(graficos)})"):
                for grafico in graficos:
                    nombre_desc = api.nombres_descriptivos.get(grafico, grafico)
                    # Verificar si está en session state
                    is_checked = grafico in st.session_state.metricas_comparacion
                    
                    if st.checkbox(nombre_desc, value=is_checked, key=f"check_{grafico}"):
                        if grafico not in st.session_state.metricas_comparacion:
                            st.session_state.metricas_comparacion.append(grafico)
                    else:
                        if grafico in st.session_state.metricas_comparacion:
                            st.session_state.metricas_comparacion.remove(grafico)
    
    with col2:
        st.markdown("#### ⚙️ Opciones de Comparación")
        
        tipo_grafico = st.radio("📊 Tipo de gráfico", ["Línea", "Área"], horizontal=True)
        normalizar = st.checkbox("📊 Normalizar datos (100 = valor inicial)", value=False)
        
        st.markdown("---")
        
        if st.session_state.metricas_comparacion:
            st.success(f"✅ {len(st.session_state.metricas_comparacion)} métricas listas para comparar")
        else:
            st.info("👆 Selecciona métricas manualmente o usa una combinación sugerida")
    
    st.markdown("---")
    
    # Usar directamente el session state para el botón
    if st.button("🔄 Generar Comparación", type="primary", disabled=len(st.session_state.metricas_comparacion) == 0, use_container_width=True):
        # Ahora sí asignamos a una variable local para usar en el bucle
        metricas_seleccionadas = st.session_state.metricas_comparacion
        with st.spinner("Generando comparación..."):
            fig = go.Figure()
            metricas_exitosas = []
            metricas_fallidas = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, metrica in enumerate(metricas_seleccionadas):
                try:
                    status_text.text(f"Cargando {idx+1}/{len(metricas_seleccionadas)}: {api.nombres_descriptivos.get(metrica, metrica)}")
                    
                    df = api.obtener_grafico(metrica, timespan=timespan)
                    
                    if df.empty:
                        metricas_fallidas.append((api.nombres_descriptivos.get(metrica, metrica), "Sin datos"))
                        continue
                    
                    if normalizar:
                        df = (df / df.iloc[0]) * 100
                    
                    nombre_desc = api.nombres_descriptivos.get(metrica, metrica)
                    valor_col = 'y' if 'y' in df.columns else df.columns[0]
                    
                    if tipo_grafico == "Línea":
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=df[valor_col],
                            mode='lines',
                            name=nombre_desc,
                            line=dict(width=2)
                        ))
                    else:  # Área
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=df[valor_col],
                            fill='tonexty',
                            name=nombre_desc,
                            mode='lines',
                            line=dict(width=1)
                        ))
                    
                    metricas_exitosas.append(nombre_desc)
                    
                except Exception as e:
                    error_msg = str(e)
                    metricas_fallidas.append((api.nombres_descriptivos.get(metrica, metrica), error_msg))
                    logger.error(f"Error en comparación con {metrica}: {error_msg}")
                finally:
                    progress_bar.progress((idx + 1) / len(metricas_seleccionadas))
            
            progress_bar.empty()
            status_text.empty()
            
            if metricas_exitosas:
                fig.update_layout(
                    title=dict(text="Comparación de Métricas de Bitcoin", font=dict(size=20, color='#e6e6e6')),
                    xaxis_title="Fecha",
                    yaxis_title="Valor normalizado (%)" if normalizar else "Valor",
                    template="plotly_dark",
                    hovermode='x unified',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#a8b2d1'),
                    height=600,
                    legend=dict(
                        bgcolor='rgba(0,0,0,0.5)',
                        bordercolor='rgba(255,255,255,0.2)',
                        borderwidth=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if metricas_exitosas:
                        st.success(f"✅ {len(metricas_exitosas)} métricas graficadas correctamente")
                        with st.expander("📊 Ver métricas graficadas"):
                            for m in metricas_exitosas:
                                st.write(f"• {m}")
                
                with col2:
                    if metricas_fallidas:
                        st.warning(f"⚠️ {len(metricas_fallidas)} métricas fallaron")
                        with st.expander("❌ Ver métricas con error"):
                            for m, error in metricas_fallidas:
                                st.write(f"• {m}")
                                st.caption(f"Error: {error[:100]}")
            else:
                st.error("❌ No se pudo obtener ninguna de las métricas seleccionadas")
                st.info("💡 Detalles de los errores:")
                for m, error in metricas_fallidas:
                    with st.expander(f"❌ {m}"):
                        st.code(error)
                st.info("🔧 Intenta con otras métricas o un período de tiempo diferente")

elif seccion == "🔍 Explorador":
    st.markdown("### 🔍 Explorador Avanzado de Datos")
    
    tab1, tab2 = st.tabs(["📊 Todas las Métricas", "⛏️ Pools de Minería"])
    
    with tab1:
        st.markdown("#### 📋 Catálogo Completo")
        
        categorias = api.obtener_categorias_graficos()
        
        for categoria, graficos in categorias.items():
            with st.expander(f"📁 {categoria} ({len(graficos)} métricas)"):
                for grafico in graficos:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{api.nombres_descriptivos.get(grafico, grafico)}**")
                        st.caption(f"ID: `{grafico}`")
                    with col2:
                        if st.button("Ver", key=f"ver_{grafico}"):
                            with st.spinner("Cargando..."):
                                try:
                                    df = api.obtener_grafico(grafico, timespan=timespan)
                                    if not df.empty:
                                        fig = crear_grafico_plotly(df, api.nombres_descriptivos.get(grafico, grafico))
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.warning("⚠️ No hay datos disponibles")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
    
    with tab2:
        st.markdown("#### ⛏️ Distribución de Pools")
        
        periodos_pools = {
            "24 horas": "24hours",
            "48 horas": "48hours",
            "4 días": "4days",
            "1 semana": "1weeks",
            "1 mes": "1months"
        }
        
        periodo = st.selectbox("Período", list(periodos_pools.keys()), index=2)
        
        if st.button("🔍 Cargar Pools", type="primary"):
            with st.spinner("Obteniendo datos..."):
                try:
                    df_pools = api.obtener_pools(timespan=periodos_pools[periodo])
                    
                    if not df_pools.empty:
                        fig = go.Figure(data=[go.Pie(
                            labels=df_pools.index,
                            values=df_pools['relativeSize'],
                            hole=0.4,
                            marker=dict(colors=px.colors.qualitative.Set3)
                        )])
                        
                        fig.update_layout(
                            title=dict(text=f"Distribución de Pools ({periodo})", font=dict(size=20, color='#e6e6e6')),
                            template="plotly_dark",
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#a8b2d1'),
                            height=600
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.markdown("#### 📊 Tabla de Distribución")
                        df_pools['Porcentaje'] = df_pools['relativeSize'].apply(lambda x: f"{x:.2f}%")
                        st.dataframe(df_pools[['Porcentaje']], use_container_width=True)
                    else:
                        st.warning("No hay datos disponibles")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")

elif seccion == "📥 Exportar Datos":
    st.markdown("### 📥 Exportar Datos")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Exportación Simple")
        
        categorias = api.obtener_categorias_graficos()
        categoria = st.selectbox("Categoría", list(categorias.keys()), key="export_cat")
        graficos_cat = categorias[categoria]
        nombres_desc = [api.nombres_descriptivos.get(g, g) for g in graficos_cat]
        metrica_desc = st.selectbox("Métrica", nombres_desc, key="export_metric")
        indice = nombres_desc.index(metrica_desc)
        metrica = graficos_cat[indice]
        
        formato = st.radio("Formato", ["CSV", "Excel"])
        
        if st.button("📥 Exportar", type="primary"):
            with st.spinner("Exportando..."):
                try:
                    df = api.obtener_grafico(metrica, timespan=timespan)
                    
                    if df.empty:
                        st.error("❌ No hay datos disponibles")
                    else:
                        if formato == "CSV":
                            csv = df.to_csv().encode('utf-8')
                            st.download_button(
                                label="⬇️ Descargar CSV",
                                data=csv,
                                file_name=f"{metrica}_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        else:
                            buffer = BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df.to_excel(writer, sheet_name=metrica[:31])
                            
                            st.download_button(
                                label="⬇️ Descargar Excel",
                                data=buffer.getvalue(),
                                file_name=f"{metrica}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        st.success("✅ Datos listos para descargar")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        st.markdown("#### Exportación Múltiple")
        st.info("Selecciona múltiples métricas para exportar en Excel")
        
        metricas_export = []
        for cat, graficos in categorias.items():
            with st.expander(f"📁 {cat}"):
                for grafico in graficos:
                    nombre = api.nombres_descriptivos.get(grafico, grafico)
                    if st.checkbox(nombre, key=f"export_multi_{grafico}"):
                        metricas_export.append(grafico)
        
        if metricas_export:
            st.success(f"✅ {len(metricas_export)} métricas seleccionadas")
            
            if st.button("📥 Exportar Múltiples", type="primary"):
                with st.spinner("Generando Excel..."):
                    try:
                        buffer = BytesIO()
                        metricas_exportadas = 0
                        
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            for metrica in metricas_export:
                                try:
                                    df = api.obtener_grafico(metrica, timespan=timespan)
                                    if not df.empty:
                                        nombre_hoja = api.nombres_descriptivos.get(metrica, metrica)[:31]
                                        df.to_excel(writer, sheet_name=nombre_hoja)
                                        metricas_exportadas += 1
                                except:
                                    continue
                        
                        if metricas_exportadas > 0:
                            st.download_button(
                                label="⬇️ Descargar Excel Completo",
                                data=buffer.getvalue(),
                                file_name=f"bitcoin_metrics_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            
                            st.success(f"✅ {metricas_exportadas}/{len(metricas_export)} métricas exportadas")
                        else:
                            st.error("❌ No se pudo exportar ninguna métrica")
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #667eea; padding: 20px;">
    <p><b>Bitcoin Analytics Dashboard</b> | Datos en tiempo real desde blockchain.info</p>
    <p style="font-size: 0.9em; color: #a8b2d1; margin-top: 10px;">
        Desarrollado por <a href="https://x.com/Gsnchez" target="_blank" style="color: #667eea; text-decoration: none; font-weight: bold;">@Gsnchez</a> | 
        <a href="https://bquantfinance.com" target="_blank" style="color: #764ba2; text-decoration: none; font-weight: bold;">bquantfinance.com</a>
    </p>
    <p style="font-size: 0.8em; color: #a8b2d1;">Creado con ❤️ usando Streamlit y Python</p>
</div>
""", unsafe_allow_html=True)
