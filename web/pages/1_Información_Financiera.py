import datetime
import time

import plotly.graph_objects as go
import streamlit as st
from quant_drl.data.stock_data import StockData

from web.commons.session import check_login
from web.commons.style_utils import add_logo
from web.pages.commons.database_connectors import (
    fetch_companies,
    fetch_favorite_portfolios,
    save_favorite_portfolio,
)

# change_theme_toogle()
add_logo(with_name=False, sidebar=True)
check_login()

# st.set_page_config(page_title="Información Financiera", layout="wide")
# Cargar modelos en Streamlit
st.title("📊 Información Financiera")

# 🔹 Sidebar: Selección de empresas
st.sidebar.header("⚙️ Configuración del Análisis")


# --- Fetch Data ---
companies = fetch_companies()
# print(companies)
companies_dict = {k: v for _, k, v, _ in companies}

favorite_portfolios = fetch_favorite_portfolios(st.session_state.get("user_id", 1))

# --- Selection Mode ---
selection_mode = st.sidebar.radio(
    "Selecciona el modo de búsqueda:",
    ["Empresas", "Portafolios Favoritos"],
    horizontal=True,
)

selected_companies_names = []
selected_companies_abv = []

if selection_mode == "Empresas":
    # --- Sidebar: Select Companies ---
    selected_companies_names = st.sidebar.multiselect(
        "Selecciona activos", list(companies_dict.keys())
    )
    selected_companies_abv = [companies_dict[name] for name in selected_companies_names]

    # --- Save Portfolio as Favorite ---
    portfolio_name = st.sidebar.text_input(
        "Asignar nombre al portafolio:",
        placeholder="Alias para el portfolio.",
    )
    if (
        st.sidebar.button("⭐ Guardar como favorito")
        and selected_companies_abv
        and portfolio_name
    ):
        save_favorite_portfolio(portfolio_name, selected_companies_abv)

elif selection_mode == "Portafolios Favoritos":
    # --- Favorite Portfolio Selection ---
    favorite_selected = st.sidebar.selectbox(
        "Cargar Portafolio Favorito", list(favorite_portfolios.keys())
    )
    if favorite_selected:
        selected_companies_abv = favorite_portfolios[favorite_selected]
        selected_companies_abv.remove("CASH")
        selected_companies_names = [
            name
            for name, abv in companies_dict.items()
            if abv in selected_companies_abv
        ]

# --- Date Selection ---
today = datetime.date.today()
fecha_final = st.sidebar.date_input("Fecha Final", today, max_value=today)
fecha_inicio = fecha_final - datetime.timedelta(days=365 * 20 + 5)
st.sidebar.write(f"Analizando datos desde: {fecha_inicio}")


# --- Update Button ---
if st.sidebar.button("Actualizar Datos"):
    st.rerun()
    time.sleep(0.5)

# --- Plotting Section ---
# st.header("Evolución del Precio de Cierre de las Empresas")


if selected_companies_names:
    stockdata = StockData(
        comp_abv=selected_companies_abv,
        comp_names=selected_companies_names,
        start_date=fecha_inicio,
        end_date=fecha_final,
        winsorize=True,
        percentile=0.001,
    )

    multi_index_df = stockdata.multi_index_df

    gross_return_df = stockdata.extract_return_data_as_df(return_type="gross")
    gross_return_winsorized_df = stockdata.extract_return_data_as_df(
        return_type="gross", normalized="winsorized"
    )
    gross_return_standardized_df = stockdata.extract_return_data_as_df(
        return_type="gross", normalized="standard"
    )

    if stockdata:
        with st.expander("Selección de Características", expanded=True):
            selected_features = st.multiselect(
                "Selecciona las características a analizar",
                ["Close", "High", "Low", "Open"]
                + [
                    "SMA",
                    "EMA",
                    "RSI",
                    "MACD",
                    "Bollinger_High",
                    "Bollinger_Low",
                    "ATR",
                ],
                placeholder="Selecciona una o más características",
            )

    if not selected_features:
        st.warning("Por favor, selecciona al menos una característica.")
        st.stop()

    tab1, tab2 = st.tabs(["Vista Separada", "Vista Unificada"])

    with tab1:
        col1, col2 = st.columns(2)

        for i, empresa in enumerate(selected_companies_names):
            company_abv = companies_dict[empresa]
            fig = go.Figure()

            for feature in selected_features:
                feature_data = multi_index_df.get((company_abv, feature))
                if feature_data is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=feature_data.index,
                            y=feature_data.values,
                            mode="lines",
                            name=f"{empresa} - {feature}",
                        )
                    )

            candle_data = multi_index_df.get(
                company_abv, ["Open", "High", "Low", "Close"]
            )

            fig.add_trace(
                go.Candlestick(
                    x=candle_data.index,
                    open=candle_data["Open"],
                    high=candle_data["High"],
                    low=candle_data["Low"],
                    close=candle_data["Close"],
                    name=f"{empresa} - Candlestick",
                    visible=False,  # Oculto por defecto
                )
            )

            for feature in selected_features:
                feature_data = multi_index_df.get((company_abv, feature))
                if feature_data is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=feature_data.index,
                            y=feature_data.values,
                            mode="lines",
                            fill="tozeroy",
                            name=f"{empresa} - {feature} (Mountain)",
                            visible=False,  # Oculto por defecto
                        )
                    )

            # Dropdown para cambiar vistas
            fig.update_layout(
                updatemenus=[
                    {
                        "buttons": [
                            {
                                "label": "Line",
                                "method": "update",
                                "args": [{"visible": [True, False, False]}],
                            },
                            {
                                "label": "Candle",
                                "method": "update",
                                "args": [{"visible": [False, True, False]}],
                            },
                            {
                                "label": "Mountain",
                                "method": "update",
                                "args": [{"visible": [False, False, True]}],
                            },
                        ],
                        "direction": "down",
                        "showactive": True,
                    }
                ],
            )

            fig.update_layout(
                dragmode="zoom",  # Habilita zoom en ambas direcciones (X e Y)
                xaxis=dict(
                    rangeslider=dict(
                        visible=True
                    ),  # Mantiene el selector de rango en X
                    fixedrange=False,  # Permite zoom en X
                ),
                yaxis=dict(
                    fixedrange=False  # Permite zoom en Y
                ),
            )

            fig.update_xaxes(
                rangeslider_visible=True,
                rangeselector=dict(
                    buttons=list(
                        [
                            dict(
                                count=1, label="1m", step="month", stepmode="backward"
                            ),
                            dict(
                                count=6, label="6m", step="month", stepmode="backward"
                            ),
                            dict(count=1, label="YTD", step="year", stepmode="todate"),
                            dict(count=1, label="1y", step="year", stepmode="backward"),
                            dict(step="all"),
                        ]
                    )
                ),
            )

            fig.add_annotation(
                align="right",
                text=f"<b>{empresa}</b>",
                xref="paper",
                yref="paper",
                x=0.5,
                y=1.3,
                showarrow=False,
                font=dict(size=20),
            )

            fig.update_xaxes(minor=dict(ticks="inside", showgrid=True))

            (col1 if i % 2 == 0 else col2).plotly_chart(fig, use_container_width=True)

    with tab2:
        selected_companies_unified = st.multiselect(
            "Selecciona empresas para visualizar en el gráfico unificado:",
            selected_companies_names,
            default=selected_companies_names,
        )

        fig_unificado = go.Figure()
        for empresa in selected_companies_unified:
            company_abv = companies_dict[empresa]

            for feature in selected_features:
                feature_data = multi_index_df.get((company_abv, feature))
                if feature_data is not None:
                    fig_unificado.add_trace(
                        go.Scatter(
                            x=feature_data.index,
                            y=feature_data.values,
                            mode="lines",
                            name=f"{empresa} - {feature}",
                        )
                    )

                f_gross_data = gross_return_df.query(f"Stock == '{company_abv}'")[
                    feature
                ]

                if f_gross_data is not None:
                    fig_unificado.add_trace(
                        go.Scatter(
                            x=f_gross_data.index,
                            y=f_gross_data.values,
                            mode="lines",
                            name=f"{empresa} - {feature} Gross Return",
                            visible=False,
                        )
                    )

                f_gross_win_data = gross_return_winsorized_df.query(
                    f"Stock == '{company_abv}'"
                )[feature]

                if f_gross_win_data is not None:
                    fig_unificado.add_trace(
                        go.Scatter(
                            x=f_gross_win_data.index,
                            y=f_gross_win_data.values,
                            mode="lines",
                            name=f"{empresa} - {feature} Gross Return (Winsorized)",
                            visible=False,
                        )
                    )

                f_gross_std_data = gross_return_standardized_df.query(
                    f"Stock == '{company_abv}'"
                )[feature]

                if f_gross_std_data is not None:
                    fig_unificado.add_trace(
                        go.Scatter(
                            x=f_gross_std_data.index,
                            y=f_gross_std_data.values,
                            mode="lines",
                            name=f"{empresa} - {feature} Gross Return (Standardized)",
                            visible=False,
                        )
                    )

        fig_unificado.update_layout(
            updatemenus=[
                {
                    "buttons": [
                        {
                            "label": "Original",
                            "method": "update",
                            "args": [{"visible": [True, False, False, False]}],
                        },
                        {
                            "label": "Gross",
                            "method": "update",
                            "args": [{"visible": [False, True, False, False]}],
                        },
                        {
                            "label": "Gross Winsorized",
                            "method": "update",
                            "args": [{"visible": [False, False, True, False]}],
                        },
                        {
                            "label": "Gross Standardized",
                            "method": "update",
                            "args": [{"visible": [False, False, False, True]}],
                        },
                    ],
                    "direction": "down",
                    "showactive": True,
                }
            ],
        )

        fig_unificado.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
        )

        fig_unificado.update_layout(
            dragmode="zoom",  # Habilita zoom en ambas direcciones (X e Y)
            xaxis=dict(
                rangeslider=dict(visible=True),  # Mantiene el selector de rango en X
                fixedrange=False,  # Permite zoom en X
            ),
            yaxis=dict(
                fixedrange=False  # Permite zoom en Y
            ),
        )

        st.plotly_chart(fig_unificado, use_container_width=True)


else:
    st.warning("Por favor, selecciona al menos una empresa.")
