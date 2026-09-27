import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from database import get_db_connection


# ==========================================================
# CUSTOMER INQUIRIES
# ==========================================================

def render(user):

    # ======================================================
    # PAGE TITLE
    # ======================================================

    st.header("💬 Customer Inquiries")

    # ======================================================
    # ROLE
    # ======================================================

    role = user.get("role", "")

    allowed_roles = [
        "Administrator",
        "Pharmacist",
        "Staff"
    ]

    if role not in allowed_roles:

        st.error(
            "🚫 Access Denied. "
            "Only Administrator, Pharmacist, and Staff "
            "can access Customer Inquiries."
        )

        return

    # ======================================================
    # DATABASE
    # ======================================================

    conn = get_db_connection()

    # ======================================================
    # REFRESH
    # ======================================================

    refresh_col, info_col = st.columns(
        [1, 4],
        gap="small"
    )

    with refresh_col:

        if st.button(
            "🔄 Refresh",
            use_container_width=True
        ):

            st.rerun()

    with info_col:

        st.caption(
            "Customer questions and AI responses submitted "
            "through the Gemini Pharmacy Assistant."
        )

    # ======================================================
    # CUSTOMER INQUIRIES
    # ======================================================

    try:

        df = pd.read_sql_query(
            """
            SELECT

                ci.id,

                ci.user_query,

                ci.bot_response,

                m.name AS matched_medicine,

                ci.timestamp

            FROM customer_inquiries ci

            LEFT JOIN medicines m
                ON ci.matched_medicine_id = m.id

            ORDER BY ci.timestamp DESC
            """,
            conn
        )

    except Exception as e:

        st.error(
            f"Unable to load customer inquiries: {e}"
        )

        df = pd.DataFrame()

    # ======================================================
    # INQUIRY HISTORY
    # ======================================================

    st.subheader(
        "📋 Inquiry History"
    )

    if not df.empty:

        # ==================================================
        # RENAME COLUMNS
        # ==================================================

        display_df = df.rename(
            columns={
                "user_query": "Customer Question",
                "bot_response": "AI Response",
                "matched_medicine": "Medicine",
                "timestamp": "Date & Time"
            }
        )

        # ==================================================
        # DISPLAY WITHOUT ID
        # ==================================================

        st.dataframe(
            display_df[
                [
                    "Customer Question",
                    "AI Response",
                    "Medicine",
                    "Date & Time"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No customer inquiries have been recorded yet."
        )

    # ======================================================
    # COMMON QUESTIONS
    # ======================================================

    if not df.empty:

        st.markdown("---")

        st.subheader(
            "❓ Common Questions"
        )

        questions = (
            df["user_query"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        questions = questions[
            questions != ""
        ]

        if not questions.empty:

            common_questions = (
                questions
                .value_counts()
                .head(7)
                .reset_index()
            )

            common_questions.columns = [
                "Question",
                "Count"
            ]

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=common_questions[
                        "Count"
                    ],

                    y=common_questions[
                        "Question"
                    ],

                    orientation="h",

                    marker=dict(
                        color="#E91E63"
                    ),

                    text=common_questions[
                        "Count"
                    ],

                    textposition="outside",

                    hovertemplate=
                    "<b>%{y}</b><br>"
                    "Asked: %{x} times"
                    "<extra></extra>"
                )
            )

            fig.update_layout(

                height=350,

                margin=dict(
                    l=20,
                    r=60,
                    t=10,
                    b=20
                ),

                plot_bgcolor="#FFFFFF",

                paper_bgcolor="#FFFFFF",

                showlegend=False,

                xaxis=dict(

                    title="Number of Questions",

                    showgrid=True,

                    gridcolor="#EEEEEE",

                    zeroline=False,

                    dtick=1
                ),

                yaxis=dict(

                    title=None,

                    autorange="reversed"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                    "responsive": True
                }
            )

    # ======================================================
    # MOST ASKED MEDICINES
    # ======================================================

    if not df.empty:

        matched = (
            df["matched_medicine"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        matched = matched[
            matched != ""
        ]

        if not matched.empty:

            st.markdown("---")

            st.subheader(
                "💊 Most Inquired Medicines"
            )

            medicine_counts = (
                matched
                .value_counts()
                .head(5)
                .reset_index()
            )

            medicine_counts.columns = [
                "Medicine",
                "Inquiries"
            ]

            fig_medicine = go.Figure()

            fig_medicine.add_trace(
                go.Bar(

                    x=medicine_counts[
                        "Inquiries"
                    ],

                    y=medicine_counts[
                        "Medicine"
                    ],

                    orientation="h",

                    marker=dict(
                        color="#9C6ADE"
                    ),

                    text=medicine_counts[
                        "Inquiries"
                    ],

                    textposition="outside",

                    hovertemplate=
                    "<b>%{y}</b><br>"
                    "Inquiries: %{x}"
                    "<extra></extra>"
                )
            )

            fig_medicine.update_layout(

                height=280,

                margin=dict(
                    l=20,
                    r=60,
                    t=10,
                    b=20
                ),

                plot_bgcolor="#FFFFFF",

                paper_bgcolor="#FFFFFF",

                showlegend=False,

                xaxis=dict(

                    title="Number of Inquiries",

                    showgrid=True,

                    gridcolor="#EEEEEE",

                    zeroline=False,

                    dtick=1
                ),

                yaxis=dict(

                    title=None,

                    autorange="reversed"
                )
            )

            st.plotly_chart(
                fig_medicine,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                    "responsive": True
                }
            )

    # ======================================================
    # CLOSE DATABASE
    # ======================================================

    conn.close()