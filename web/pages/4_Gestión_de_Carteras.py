import plotly.graph_objects as go
import streamlit as st
from quant_drl.data.stock_data import StockData

from web.commons.session import check_login
from web.commons.style_utils import add_logo
from web.pages.commons.database_connectors import (
    check_if_portfolio_has_assets_weights,
    fetch_companies,
    get_companies_from_portfolio,
    get_portfolios_from_user,
    get_weights_for_portfolio,
    save_favorite_portfolio,
    save_weights_for_portfolio,
)

## Funciones auxiliares


def plot_weights_pie_chart(weights_dict):
    weights = list(weights_dict.items())
    values = list(map(lambda x: x[1], weights))
    labels = list(map(lambda x: x[0], weights))

    custom_text = [f"<br>{value:.4f} (USD)" for label, value in zip(labels, values)]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                hovertext=custom_text,
                hoverinfo="label+text",
                textinfo="percent",
            ),
        ]
    )

    fig.update_layout(title_text="Resumen de inversión")
    return fig


def add_portolio_weights_page(
    selected_companies_dict,
    selected_companies_abv,
    new_porfolio=False,
    new_portfolio_name="",
    is_correct=False,
    portfolio_id=None,
    total_invested=100.0,
):
    method = st.radio(
        "Método de selección de pesos", ["Porcentual", "Manual"], horizontal=True
    )

    if method == "Porcentual":
        st.markdown("#### Pesos Iniciales")
        initial_weights = {}

        total_invested = st.number_input(
            "Total a invertir:", min_value=0.0, value=100.0
        )

        col1, col2, col3 = st.columns(3)

        default_weight = 1 / (len(selected_companies_dict))

        cash_id = None
        for i, (company_id, name) in enumerate(selected_companies_dict.items()):
            if name != "Cash":
                col = col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3
                weight = col.slider(
                    f"Peso para {name}", 0.0, 1.0, default_weight, 0.01, format="%.4f"
                )
                initial_weights[company_id] = weight
            else:
                cash_id = company_id

        suma_pesos_pre_cash = sum(initial_weights.values())
        if suma_pesos_pre_cash > 1:
            st.error("La suma de los pesos debe ser 1")
            is_correct = False
            st.stop()

        # initial_weights[search_cash_company()] = weight
        # selected_companies_dict[search_cash_company()] = "Cash"
        weight = st.slider(
            "Peso para Cash",
            0.0,
            1.0,
            value=1 - suma_pesos_pre_cash,
            step=0.01,
            format="%.4f",
        )
        initial_weights[cash_id] = weight

        # check sum of weights is 1
        if sum(initial_weights.values()) != 1:
            is_correct = False
            st.error(
                f"La suma de los pesos debe ser 1. Suma actual: {sum(initial_weights.values())}"
            )
        else:
            weights_dict = {k: v * total_invested for k, v in initial_weights.items()}
            weight_dict_names = {
                selected_companies_dict[k]: v
                for k, v in weights_dict.items()
                if k in selected_companies_dict
            }
            is_correct = True

    else:
        st.subheader("Inversión Inicial")
        initial_investment = {}
        # cash_id = search_cash_company()
        # selected_companies_dict[cash_id] = "Cash"

        col1, col2, col3 = st.columns(3)

        for i, (company_id, name) in enumerate(selected_companies_dict.items()):
            col = col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3
            investment = col.number_input(
                f"Inversión para {name}:", min_value=0.0, value=100.0
            )
            initial_investment[company_id] = investment

        # Check sum of investments is not 0 and all are positive

        if sum(initial_investment.values()) == 0:
            st.error("La inversión total no puede ser 0")
            is_correct = False
        elif any(v < 0 for v in initial_investment.values()):
            is_correct = False
            st.error("La inversión no puede ser negativa")
        else:
            # transorm investment to weights
            total_invested = sum(initial_investment.values())
            initial_weights = {
                k: v / total_invested for k, v in initial_investment.items()
            }
            weight_dict_names = {
                selected_companies_dict[k]: v
                for k, v in initial_weights.items()
                if k in selected_companies_dict
            }
            is_correct = True

    fig = plot_weights_pie_chart(weight_dict_names)
    fig.update_layout(title_text="Resumen de inversión")
    st.plotly_chart(fig)

    if new_porfolio:
        new_portfolio_name = st.text_input("Nombre del nuevo portafolio:", "")
        if is_correct:
            if st.button("💾 Guardar Portafolio"):
                # Crear portafolio
                portfolio_id = save_favorite_portfolio(
                    new_portfolio_name,
                    selected_companies_abv,
                    total_invested,
                )

                corrected_saved = save_weights_for_portfolio(
                    portfolio_id,
                    initial_weights,
                )

                if corrected_saved:
                    st.success("Portafolio guardado correctamente")
                else:
                    st.error("Error al guardar el portafolio")
    elif portfolio_id:
        if is_correct:
            if st.button("💾 Guardar Portafolio"):
                corrected_saved = save_weights_for_portfolio(
                    portfolio_id,
                    initial_weights,
                )

                if corrected_saved:
                    st.success("Portafolio guardado correctamente")
                else:
                    st.error("Error al guardar el portafolio")
    else:
        st.error("Error al guardar el portafolio")


##
# change_theme_toogle()
add_logo(with_name=False, sidebar=True)
check_login()


st.title("💼 Gestión de Carteras")


tab_selection = st.radio(
    "Selecciona una sección",
    ["Mis Portafolios", "Nuevo Portafolio"],
    horizontal=True,
)

if tab_selection == "Mis Portafolios":
    portfolios = get_portfolios_from_user(st.session_state.get("user_id", 1))
    if portfolios:
        st.subheader("⭐ Mis Portafolios Favoritos")
        selected_portfolio = st.selectbox(
            "Selecciona un portafolio:", portfolios, format_func=lambda x: x[2]
        )

        if selected_portfolio:
            portfolio_id = selected_portfolio[0]

            # Mostrar pesos si existen
            if check_if_portfolio_has_assets_weights(portfolio_id):
                st.subheader("📊 Pesos actuales:")
                weights = get_weights_for_portfolio(portfolio_id)

                weights_dict = {k: v for _, k, v, _, _, _ in weights}

                recorded_date = weights[0][3]
                portfolio_value = weights[0][4]
                st.write(f"Fecha de registro: {recorded_date}")

                # Add a wait message and a spinner
                with st.spinner("Cargando datos..."):
                    stockdata = StockData(
                        comp_abv=[t for _, t, _, _, _, _ in weights],
                        comp_names=[n for n, _, _, _, _, _ in weights],
                        difference_start_end=5,
                    )

                new_portfolio_value, new_weights, previous_values, new_values = (
                    stockdata.calculate_portfolio_value(
                        weights_dict, recorded_date, portfolio_value
                    )
                )

                investement_dict = new_values

                fig = plot_weights_pie_chart(investement_dict)
                fig.update_layout(
                    title_text=f"Resumen de inversión. Nuevo valor del portafolio: ${new_portfolio_value:.5f}"
                )
                st.plotly_chart(fig)

                # Indicar el cambio en el valor del portafolio
                st.write(
                    f"El valor del portafolio ha cambiado en: ${(float(new_portfolio_value) - float(portfolio_value)):.5f} (Precio de cierre)"
                )

            else:
                st.warning("No hay pesos registrados para este portafolio")
                # 2️⃣ Modificar pesos de un portafolio
                st.subheader("Añadir Pesos")
                new_weights = {}

                # Obtener empresas en el portafolio
                companies = get_companies_from_portfolio(portfolio_id)

                subdict = {k: v for k, v, _, _, _ in companies}

                selected_abv = [t for _, _, t, _, _ in companies]

                add_portolio_weights_page(
                    subdict,
                    selected_companies_abv=selected_abv,
                    new_porfolio=False,
                    portfolio_id=portfolio_id,
                )

    # 4️⃣ Crear un nuevo portafolio
else:
    st.subheader("➕ Crear Nuevo Portafolio")

    st.session_state.creating_portfolio = True

    is_correct = False
    companies = fetch_companies()
    companies_dict = {k: v for k, v, _, _ in companies}
    selected_companies_names = st.multiselect(
        "Selecciona empresas", list(companies_dict.values())
    )

    subdict = {
        k: v
        for k, v in companies_dict.items()
        if v in selected_companies_names or v == "Cash"
    }

    selected_abv = [
        ticker for _, name, ticker, _ in companies if name in selected_companies_names
    ]

    if subdict:
        add_portolio_weights_page(
            subdict, selected_companies_abv=selected_abv, new_porfolio=True
        )
