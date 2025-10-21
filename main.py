import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from blockchain_wrapper import BlockchainInfoAPI

# Configuración de la página
st.set_page_config(
    page_title="Bitcoin Analytics Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para modo oscuro elegante
st.markdown("""
    <style>
    /* Modo oscuro global */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Tarjetas con efecto glassmorphism */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        margin: 10px 0;
    }
    
    /* Títulos con degradado */
    .gradient-text {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Subtítulos */
    .subtitle {
        color: #a8b2d1;
        text-align: center;
        font-size: 1.2em;
        margin-bottom: 40px;
    }
    
    /* Mejora de selectbox */
    .stSelectbox {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    /* Botones personalizados */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar mejorado */
    [data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.8);
        backdrop-filter: blur(10px);
    }
    
    /* Textos en sidebar */
    [data-testid="stSidebar"] .stMarkdown {
        color: #e6e6e6;
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        color: #a8b2d1;
    }
    
    /* Tabs personalizados */
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

# Inicializar la API
@st.cache_resource
def init_api():
    return BlockchainInfoAPI()

api = init_api()

# Header principal
st.markdown('<h1 class="gradient-text">₿ Bitcoin Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Análisis profesional de datos de blockchain en tiempo real</p>', unsafe_allow_html=True)

# Sidebar
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
    
    # Período de tiempo global
    timespan_options = {
        "1 día": "1days",
        "1 semana": "1weeks",
        "1 mes": "1months",
        "3 meses": "3months",
        "6 meses": "6months",
        "1 año": "1year",
        "2 años": "2years",
        "3 años": "3years",
        "Todo": "all"
    }
    
    timespan_label = st.selectbox("📅 Período de tiempo", list(timespan_options.keys()), index=4)
    timespan = timespan_options[timespan_label]
    
    st.markdown("---")
    st.markdown("""
    <div class="info-box">
    <b>💡 Tip:</b> Explora diferentes métricas para obtener insights profundos sobre Bitcoin.
    </div>
    """, unsafe_allow_html=True)

# Función para crear gráficos con Plotly
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
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            showline=True,
            linecolor='rgba(255,255,255,0.2)'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)',
            showline=True,
            linecolor='rgba(255,255,255,0.2)'
        ),
        height=500
    )
    
    return fig

# Sección: INICIO
if seccion == "🏠 Inicio":
    # Métricas clave en tiempo real
    st.markdown("### 📊 Métricas Clave en Tiempo Real")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with st.spinner("Cargando datos..."):
        try:
            # Precio de mercado
            precio_df = api.obtener_precio_mercado(timespan='1days')
            precio_actual = precio_df['y'].iloc[-1]
            precio_anterior = precio_df['y'].iloc[-2] if len(precio_df) > 1 else precio_actual
            delta_precio = ((precio_actual - precio_anterior) / precio_anterior) * 100
            
            with col1:
                st.metric(
                    label="💰 Precio Bitcoin",
                    value=f"${precio_actual:,.2f}",
                    delta=f"{delta_precio:+.2f}%"
                )
            
            # Capitalización de mercado
            cap_df = api.obtener_cap_mercado(timespan='1days')
            cap_actual = cap_df['y'].iloc[-1]
            
            with col2:
                st.metric(
                    label="📈 Cap. de Mercado",
                    value=f"${cap_actual/1e9:.2f}B"
                )
            
            # Volumen de comercio
            volumen_df = api.obtener_volumen_comercio(timespan='1days')
            volumen_actual = volumen_df['y'].iloc[-1]
            
            with col3:
                st.metric(
                    label="💹 Volumen 24h",
                    value=f"${volumen_actual/1e6:.2f}M"
                )
            
            # Transacciones
            tx_df = api.obtener_transacciones(timespan='1days')
            tx_actual = tx_df['y'].iloc[-1]
            
            with col4:
                st.metric(
                    label="🔄 Transacciones 24h",
                    value=f"{tx_actual:,.0f}"
                )
        
        except Exception as e:
            st.error(f"Error al cargar métricas: {str(e)}")
    
    st.markdown("---")
    
    # Gráfico destacado
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📈 Evolución del Precio")
        try:
            precio_df = api.obtener_precio_mercado(timespan=timespan)
            fig = crear_grafico_plotly(precio_df, "Precio de Bitcoin (USD)", "Precio (USD)")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar gráfico: {str(e)}")
    
    with col2:
        st.markdown("### ℹ️ Acerca de")
        st.markdown("""
        <div class="metric-card">
        <p><b>Bitcoin Analytics Dashboard</b> te permite:</p>
        <ul>
            <li>📊 Visualizar métricas clave de Bitcoin</li>
            <li>📈 Comparar múltiples indicadores</li>
            <li>🔍 Explorar datos históricos</li>
            <li>📥 Exportar datos en CSV/Excel</li>
        </ul>
        <p style="margin-top: 20px; color: #667eea;">
        <b>Datos en tiempo real</b> desde blockchain.info
        </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Categorías Disponibles")
        categorias = api.obtener_categorias_graficos()
        for cat, graficos in categorias.items():
            with st.expander(f"📁 {cat}"):
                st.write(f"{len(graficos)} métricas disponibles")

# Sección: VISUALIZACIÓN
elif seccion == "📊 Visualización":
    st.markdown("### 📊 Visualización de Métricas")
    
    # Seleccionar categoría y métrica
    col1, col2 = st.columns([1, 2])
    
    with col1:
        categorias = api.obtener_categorias_graficos()
        categoria_seleccionada = st.selectbox("🏷️ Categoría", list(categorias.keys()))
        
        graficos_categoria = categorias[categoria_seleccionada]
        
        # Mostrar nombres descriptivos
        nombres_mostrar = [api.nombres_descriptivos.get(g, g) for g in graficos_categoria]
        metrica_mostrar = st.selectbox("📈 Métrica", nombres_mostrar)
        
        # Obtener el nombre técnico de la métrica
        indice = nombres_mostrar.index(metrica_mostrar)
        metrica_seleccionada = graficos_categoria[indice]
        
        tipo_grafico = st.selectbox("📊 Tipo de gráfico", ["Línea", "Área"])
    
    with col2:
        st.markdown(f"<div class='metric-card'><h4>{metrica_mostrar}</h4></div>", unsafe_allow_html=True)
    
    # Botón para cargar datos
    if st.button("🚀 Cargar Datos", type="primary"):
        with st.spinner("Obteniendo datos..."):
            try:
                df = api.obtener_grafico(metrica_seleccionada, timespan=timespan)
                
                # Crear gráfico según el tipo seleccionado
                fig = go.Figure()
                
                if tipo_grafico == "Línea":
                    for col in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=df[col],
                            mode='lines',
                            name=col,
                            line=dict(width=2)
                        ))
                else:  # Área
                    for col in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=df[col],
                            fill='tozeroy',
                            name=col
                        ))
                
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
                
                # Mostrar estadísticas
                st.markdown("### 📊 Estadísticas")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Máximo", f"{df['y'].max():,.2f}")
                with col2:
                    st.metric("Mínimo", f"{df['y'].min():,.2f}")
                with col3:
                    st.metric("Promedio", f"{df['y'].mean():,.2f}")
                with col4:
                    st.metric("Último Valor", f"{df['y'].iloc[-1]:,.2f}")
                
                # Mostrar datos en tabla
                with st.expander("📋 Ver datos en tabla"):
                    st.dataframe(df.tail(50), use_container_width=True)
                
            except Exception as e:
                st.error(f"Error al cargar datos: {str(e)}")

# Sección: COMPARACIÓN
elif seccion == "📈 Comparación":
    st.markdown("### 📈 Comparación de Múltiples Métricas")
    
    categorias = api.obtener_categorias_graficos()
    
    # Selección múltiple de métricas
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Selecciona métricas para comparar")
        metricas_seleccionadas = []
        
        for categoria, graficos in categorias.items():
            with st.expander(f"📁 {categoria}"):
                for grafico in graficos:
                    nombre_desc = api.nombres_descriptivos.get(grafico, grafico)
                    if st.checkbox(nombre_desc, key=grafico):
                        metricas_seleccionadas.append(grafico)
    
    with col2:
        st.markdown("#### Opciones de comparación")
        normalizar = st.checkbox("📊 Normalizar datos (100 = valor inicial)", value=False)
        
        if metricas_seleccionadas:
            st.success(f"✅ {len(metricas_seleccionadas)} métricas seleccionadas")
            for m in metricas_seleccionadas:
                st.write(f"• {api.nombres_descriptivos.get(m, m)}")
        else:
            st.info("👆 Selecciona al menos una métrica de las categorías")
    
    # Botón para comparar
    if st.button("🔄 Comparar Métricas", type="primary", disabled=len(metricas_seleccionadas) == 0):
        with st.spinner("Generando comparación..."):
            try:
                fig = go.Figure()
                
                for metrica in metricas_seleccionadas:
                    df = api.obtener_grafico(metrica, timespan=timespan)
                    
                    # Normalizar si se solicita
                    if normalizar and len(df) > 0:
                        df = (df / df.iloc[0]) * 100
                    
                    nombre_desc = api.nombres_descriptivos.get(metrica, metrica)
                    
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['y'],
                        mode='lines',
                        name=nombre_desc,
                        line=dict(width=2)
                    ))
                
                fig.update_layout(
                    title=dict(
                        text="Comparación de Métricas de Bitcoin",
                        font=dict(size=20, color='#e6e6e6')
                    ),
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
                
            except Exception as e:
                st.error(f"Error al comparar métricas: {str(e)}")

# Sección: EXPLORADOR
elif seccion == "🔍 Explorador":
    st.markdown("### 🔍 Explorador Avanzado de Datos")
    
    tab1, tab2 = st.tabs(["📊 Todas las Métricas", "⛏️ Pools de Minería"])
    
    with tab1:
        st.markdown("#### 📋 Catálogo Completo de Métricas")
        
        categorias = api.obtener_categorias_graficos()
        
        for categoria, graficos in categorias.items():
            with st.expander(f"📁 {categoria} ({len(graficos)} métricas)"):
                for grafico in graficos:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{api.nombres_descriptivos.get(grafico, grafico)}**")
                        st.caption(f"ID técnico: `{grafico}`")
                    with col2:
                        if st.button("Ver", key=f"ver_{grafico}"):
                            with st.spinner("Cargando..."):
                                try:
                                    df = api.obtener_grafico(grafico, timespan=timespan)
                                    fig = crear_grafico_plotly(
                                        df,
                                        api.nombres_descriptivos.get(grafico, grafico)
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
    
    with tab2:
        st.markdown("#### ⛏️ Distribución de Pools de Minería")
        
        periodos_pools = {
            "24 horas": "24hours",
            "48 horas": "48hours",
            "1 semana": "1weeks",
            "1 mes": "1months",
            "3 meses": "3months"
        }
        
        periodo = st.selectbox("Selecciona período", list(periodos_pools.keys()))
        
        if st.button("🔍 Cargar Pools", type="primary"):
            with st.spinner("Obteniendo datos de pools..."):
                try:
                    df_pools = api.obtener_pools(timespan=periodos_pools[periodo])
                    
                    if not df_pools.empty:
                        # Gráfico de pastel
                        fig = go.Figure(data=[go.Pie(
                            labels=df_pools.index,
                            values=df_pools['relativeSize'],
                            hole=0.4,
                            marker=dict(
                                colors=px.colors.qualitative.Set3
                            )
                        )])
                        
                        fig.update_layout(
                            title=dict(
                                text=f"Distribución de Pools de Minería ({periodo})",
                                font=dict(size=20, color='#e6e6e6')
                            ),
                            template="plotly_dark",
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#a8b2d1'),
                            height=600
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabla de pools
                        st.markdown("#### 📊 Tabla de Distribución")
                        df_pools['Porcentaje'] = df_pools['relativeSize'].apply(lambda x: f"{x:.2f}%")
                        st.dataframe(df_pools[['Porcentaje']], use_container_width=True)
                    else:
                        st.warning("No se encontraron datos de pools para este período")
                        
                except Exception as e:
                    st.error(f"Error al cargar pools: {str(e)}")

# Sección: EXPORTAR
elif seccion == "📥 Exportar Datos":
    st.markdown("### 📥 Exportar Datos de Bitcoin")
    
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
                    
                    if formato == "CSV":
                        csv = df.to_csv().encode('utf-8')
                        st.download_button(
                            label="⬇️ Descargar CSV",
                            data=csv,
                            file_name=f"{metrica}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        # Para Excel necesitamos usar un buffer
                        from io import BytesIO
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
                    st.error(f"Error al exportar: {str(e)}")
    
    with col2:
        st.markdown("#### Exportación Múltiple")
        st.info("Selecciona múltiples métricas para exportar en un solo archivo Excel")
        
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
                with st.spinner("Generando archivo Excel..."):
                    try:
                        from io import BytesIO
                        buffer = BytesIO()
                        
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            for metrica in metricas_export:
                                df = api.obtener_grafico(metrica, timespan=timespan)
                                nombre_hoja = api.nombres_descriptivos.get(metrica, metrica)[:31]
                                df.to_excel(writer, sheet_name=nombre_hoja)
                        
                        st.download_button(
                            label="⬇️ Descargar Excel Completo",
                            data=buffer.getvalue(),
                            file_name=f"bitcoin_metrics_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                        st.success("✅ Archivo Excel generado correctamente")
                        
                    except Exception as e:
                        st.error(f"Error al exportar: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #667eea; padding: 20px;">
    <p><b>Bitcoin Analytics Dashboard</b> | Datos en tiempo real desde blockchain.info</p>
    <p style="font-size: 0.8em; color: #a8b2d1;">Desarrollado con ❤️ usando Streamlit y Python</p>
</div>
""", unsafe_allow_html=True)
