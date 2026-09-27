import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from datetime import date

from database import (
    get_db_connection,
    get_medicine_stock_summary
)


# ==========================================================
# REPORTS & ANALYTICS
# ==========================================================

def render(user):

    # ======================================================
    # PAGE TITLE
    # ======================================================

    st.header("📈 Reports & Analytics")


    # ======================================================
    # ANALYTICS CSS
    # ======================================================

    st.markdown(
        """
        <style>

        /* ==================================================
           ANALYTICS COLUMN
           ================================================== */

        div[data-testid="column"] {
            overflow: visible;
        }


        /* ==================================================
           ANALYTICS CARD TITLE
           ================================================== */

        .analytics-card {

            background: #FFFFFF;

            border: 2px solid #F8D0E1;

            border-bottom: none;

            border-radius: 12px 12px 0 0;

            min-height: 48px;

            padding: 0;

            margin: 0;

            position: relative;

            z-index: 2;

            overflow: hidden;
        }


        .analytics-title {

            color: #222222;

            font-size: 16px;

            font-weight: 500;

            padding-left: 14px;

            line-height: 48px;

            text-align: left;
        }


        /* ==================================================
           PLOTLY CHART
           ================================================== */

        div[data-testid="stPlotlyChart"] {

            background: #FFFFFF !important;

            border-left: 2px solid #F8D0E1;

            border-right: 2px solid #F8D0E1;

            border-bottom: 2px solid #F8D0E1;

            border-radius: 0 0 12px 12px;

            padding: 0 5px 5px 5px;

            margin-top: 0;

            overflow: hidden;
        }


        div[data-testid="stPlotlyChart"] iframe {

            border-radius: 0 0 12px 12px;
        }


        /* ==================================================
           METRIC CARDS
           ================================================== */

        div[data-testid="stMetric"] {

            background: #FFFFFF;

            border: 1px solid #F8D0E1;

            border-left: 4px solid #FF1493;

            border-radius: 12px;

            padding: 15px;

            box-shadow:
                0 3px 10px
                rgba(255, 20, 147, 0.08);
        }


        /* ==================================================
           DOWNLOAD BUTTON
           ================================================== */

        div[data-testid="stDownloadButton"] button {

            background: #FF1493;

            color: #FFFFFF;

            border: none;

            border-radius: 10px;

            font-weight: 600;
        }


        div[data-testid="stDownloadButton"] button:hover {

            background: #D41472;

            color: #FFFFFF;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # ======================================================
    # DATABASE
    # ======================================================

    conn = get_db_connection()


    # ======================================================
    # GET MEDICINE DATA
    # ======================================================

    medicines = get_medicine_stock_summary()

    if medicines is None:

        medicines = pd.DataFrame()


    # ======================================================
    # PREPARE MEDICINE DATA
    # ======================================================

    if not medicines.empty:

        medicines = medicines.copy()


        # ----------------------------------------------
        # STOCK
        # ----------------------------------------------

        if "total_stock" in medicines.columns:

            medicines["total_stock"] = (
                pd.to_numeric(
                    medicines["total_stock"],
                    errors="coerce"
                )
                .fillna(0)
            )

        else:

            medicines["total_stock"] = 0


        # ----------------------------------------------
        # PRICE
        # ----------------------------------------------

        if "price" in medicines.columns:

            medicines["price"] = (
                pd.to_numeric(
                    medicines["price"],
                    errors="coerce"
                )
                .fillna(0)
            )

        else:

            medicines["price"] = 0


    # ======================================================
    # TWO CHART COLUMNS
    # ======================================================

    chart_left, chart_right = st.columns(
        [1, 1],
        gap="medium"
    )


    # ======================================================
    # INVENTORY OVERVIEW
    # ======================================================

    with chart_left:

        st.html(
            """
            <div class="analytics-card">
                <div class="analytics-title">
                    Inventory Overview
                </div>
            </div>
            """
        )


        # ==================================================
        # INVENTORY HISTORY
        # ==================================================

        try:

            history = pd.read_sql_query(
                """
                SELECT

                    DATE(timestamp)
                    AS transaction_date,

                    SUM(

                        CASE

                            WHEN transaction_type = 'IN'
                            THEN quantity

                            WHEN transaction_type = 'OUT'
                            THEN -quantity

                            ELSE 0

                        END

                    ) AS movement

                FROM stock_transactions

                GROUP BY DATE(timestamp)

                ORDER BY transaction_date
                """,
                conn
            )

        except Exception:

            history = pd.DataFrame()


        # ==================================================
        # LINE CHART
        # ==================================================

        if not history.empty:

            history["movement"] = (
                pd.to_numeric(
                    history["movement"],
                    errors="coerce"
                )
                .fillna(0)
            )


            # Cumulative inventory movement

            history["inventory"] = (
                history["movement"].cumsum()
            )


            history["transaction_date"] = (
                pd.to_datetime(
                    history["transaction_date"]
                )
            )


            fig_inventory = go.Figure()


            fig_inventory.add_trace(
                go.Scatter(

                    x=history[
                        "transaction_date"
                    ],

                    y=history[
                        "inventory"
                    ],

                    mode="lines+markers",

                    line=dict(
                        color="#FF1493",
                        width=3,
                        shape="spline"
                    ),

                    marker=dict(
                        color="#FF1493",
                        size=5
                    ),

                    hovertemplate=
                    "<b>%{x|%b %Y}</b><br>"
                    "Inventory: %{y}"
                    "<extra></extra>"
                )
            )


            fig_inventory.update_layout(

                height=230,

                margin=dict(
                    l=35,
                    r=10,
                    t=10,
                    b=35
                ),

                plot_bgcolor="#FFFFFF",

                paper_bgcolor="#FFFFFF",

                showlegend=False,

                xaxis=dict(

                    title=None,

                    showgrid=False,

                    tickformat="%b %Y",

                    tickfont=dict(
                        size=9,
                        color="#444444"
                    ),

                    linecolor="#EEEEEE"
                ),

                yaxis=dict(

                    title=None,

                    showgrid=True,

                    gridcolor="#EEEEEE",

                    zeroline=False,

                    tickfont=dict(
                        size=9,
                        color="#444444"
                    )
                )
            )


            st.plotly_chart(
                fig_inventory,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                    "responsive": True
                }
            )


        else:

            # ==================================================
            # FALLBACK USING CURRENT STOCK
            # ==================================================

            if not medicines.empty:

                inventory_values = (
                    medicines[
                        "total_stock"
                    ]
                    .sort_values()
                    .reset_index(drop=True)
                )


                if len(inventory_values) > 0:

                    fig_inventory = go.Figure()


                    fig_inventory.add_trace(
                        go.Scatter(

                            x=list(
                                range(
                                    1,
                                    len(
                                        inventory_values
                                    ) + 1
                                )
                            ),

                            y=inventory_values,

                            mode="lines+markers",

                            line=dict(
                                color="#FF1493",
                                width=3,
                                shape="spline"
                            ),

                            marker=dict(
                                color="#FF1493",
                                size=5
                            ),

                            hovertemplate=
                            "Medicine: %{x}<br>"
                            "Stock: %{y}"
                            "<extra></extra>"
                        )
                    )


                    fig_inventory.update_layout(

                        height=230,

                        margin=dict(
                            l=35,
                            r=10,
                            t=10,
                            b=35
                        ),

                        plot_bgcolor="#FFFFFF",

                        paper_bgcolor="#FFFFFF",

                        showlegend=False,

                        xaxis=dict(
                            title=None,
                            showgrid=False
                        ),

                        yaxis=dict(
                            title=None,
                            showgrid=True,
                            gridcolor="#EEEEEE"
                        )
                    )


                    st.plotly_chart(
                        fig_inventory,
                        use_container_width=True,
                        config={
                            "displayModeBar": False,
                            "responsive": True
                        }
                    )


                else:

                    st.info(
                        "No inventory data available."
                    )


            else:

                st.info(
                    "No inventory data available."
                )


    # ======================================================
    # MEDICINE CATEGORIES
    # ======================================================

    with chart_right:

        st.html(
            """
            <div class="analytics-card">
                <div class="analytics-title">
                    Medicine Categories
                </div>
            </div>
            """
        )


        # ==================================================
        # CATEGORY DATA
        # ==================================================

        if (
            not medicines.empty
            and "category" in medicines.columns
        ):

            category_data = medicines.copy()


            category_data["category"] = (
                category_data["category"]
                .fillna("Others")
                .astype(str)
                .str.strip()
            )


            category_data.loc[
                category_data["category"] == "",
                "category"
            ] = "Others"


            categories = (
                category_data
                .groupby("category")
                .size()
                .reset_index(
                    name="count"
                )
                .sort_values(
                    "count",
                    ascending=False
                )
            )


        else:

            categories = pd.DataFrame()


        # ==================================================
        # DONUT CHART
        # ==================================================

        if not categories.empty:

            fig_category = go.Figure()


            fig_category.add_trace(
                go.Pie(

                    labels=categories[
                        "category"
                    ],

                    values=categories[
                        "count"
                    ],

                    hole=0.55,

                    textinfo="percent",

                    textposition="outside",

                    textfont=dict(
                        size=9,
                        color="#333333"
                    ),

                    marker=dict(

                        colors=[
                            "#FF1493",
                            "#9B7DEB",
                            "#4A7FF5",
                            "#55C9D1",
                            "#FFB347",
                            "#E57373"
                        ],

                        line=dict(
                            color="#FFFFFF",
                            width=2
                        )
                    ),

                    sort=False,

                    hovertemplate=
                    "<b>%{label}</b><br>"
                    "Medicines: %{value}<br>"
                    "Percentage: %{percent}"
                    "<extra></extra>"
                )
            )


            fig_category.update_layout(

                height=230,

                margin=dict(
                    l=5,
                    r=100,
                    t=5,
                    b=5
                ),

                paper_bgcolor="#FFFFFF",

                plot_bgcolor="#FFFFFF",

                showlegend=True,

                legend=dict(

                    orientation="v",

                    x=1.0,

                    y=0.5,

                    xanchor="left",

                    yanchor="middle",

                    font=dict(
                        size=11,
                        color="#333333"
                    )
                )
            )


            st.plotly_chart(
                fig_category,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                    "responsive": True
                }
            )


        else:

            st.info(
                "No medicine categories available."
            )


    # ======================================================
    # SUMMARY
    # ======================================================

    st.markdown("---")


    summary1, summary2, summary3 = st.columns(3)


    # ======================================================
    # TOTAL MEDICINES
    # ======================================================

    with summary1:

        total_medicines = (
            len(medicines)
            if not medicines.empty
            else 0
        )


        st.metric(
            "Total Medicines",
            total_medicines
        )


    # ======================================================
    # TOTAL STOCK
    # ======================================================

    with summary2:

        total_stock = (

            medicines[
                "total_stock"
            ].sum()

            if not medicines.empty

            else 0
        )


        st.metric(
            "Total Stock",
            int(total_stock)
        )


    # ======================================================
    # TOTAL STOCK VALUE
    # ======================================================

    with summary3:

        if not medicines.empty:

            total_value = (
                medicines["price"]
                *
                medicines["total_stock"]
            ).sum()

        else:

            total_value = 0


        st.metric(
            "Total Stock Value",
            f"₱{total_value:,.2f}"
        )


    # ======================================================
    # DOWNLOAD REPORT
    # ======================================================

    st.markdown("---")


    st.subheader(
        "📄 Inventory Report"
    )


    if not medicines.empty:

        report_data = medicines.copy()


        report_data["total_value"] = (
            report_data["price"]
            *
            report_data["total_stock"]
        )


        csv = (
            report_data
            .to_csv(
                index=False
            )
            .encode("utf-8")
        )


        st.download_button(

            label="⬇️ Download Inventory Report",

            data=csv,

            file_name=(
                f"inventory_report_"
                f"{date.today()}.csv"
            ),

            mime="text/csv"
        )


    else:

        st.info(
            "No inventory data available for download."
        )


    # ======================================================
    # CLOSE DATABASE
    # ======================================================

    conn.close()