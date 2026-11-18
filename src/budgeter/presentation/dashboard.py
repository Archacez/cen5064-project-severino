
import plotly.express as px
import streamlit as st


class Dashboard:
    """Displays spending trends and category breakdowns to the user."""

    def __init__(self, summary_service):
        self.summary_service = summary_service

    def render(self, transactions):
        st.markdown(
            """
            <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            [data-testid="stMetric"] {
                background: #242631;
                border: 1px solid #353846;
                padding: 20px;
                border-radius: 12px;
            }

            [data-testid="stMetricLabel"] {
                color: #A7AAB8;
            }

            [data-testid="stMetricValue"] {
                color: #FFFFFF;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        category_totals = self.summary_service.spending_by_category()
        monthly_totals = self.summary_service.spending_by_month()

        total_spending = sum(item["amount"] for item in transactions)
        transaction_count = len(transactions)

        average_transaction = (
            total_spending / transaction_count
            if transaction_count
            else 0
        )

        st.markdown("## Financial Overview")
        st.caption("A snapshot of your spending activity.")

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Total Spending",
            f"${total_spending:,.2f}",
        )
        metric2.metric(
            "Total Transactions",
            transaction_count,
        )
        metric3.metric(
            "Average Transaction",
            f"${average_transaction:,.2f}",
        )

        st.divider()

        st.markdown("## Spending Analytics")

        category_column, monthly_column = st.columns(2)

        with category_column, st.container(border=True):
            st.markdown("### Spending by Category")

            if category_totals:
                category_chart = px.pie(
                    category_totals,
                    names="category",
                    values="total",
                    hole=0.65,
                    color_discrete_sequence=[
                        "#78A9FF",
                        "#9B8AFB",
                        "#55CDAA",
                        "#F5B95F",
                        "#F17C91",
                        "#A7AAB8",
                    ],
                )

                category_chart.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    hovertemplate=(
                        "%{label}<br>"
                        "Spent: $%{value:,.2f}<br>"
                        "%{percent}<extra></extra>"
                    ),
                )

                category_chart.update_layout(
                    template="plotly_dark",
                    height=340,
                    margin={"t":15, "b":15, "l":15, "r":15},
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend={
                        "orientation": "h",
                        "yanchor": "bottom",
                        "y": -0.15,
                        "xanchor": "center",
                        "x": 0.5,
                    },
                )

                st.plotly_chart(
                    category_chart,
                    use_container_width=True,
                )
            else:
                st.info("No category spending data available.")

        with monthly_column, st.container(border=True):
            st.markdown("### Monthly Spending")

            if monthly_totals:
                monthly_chart = px.bar(
                    monthly_totals,
                    x="month",
                    y="total",
                    text_auto=".2f",
                )

                monthly_chart.update_traces(
                    marker_color="#78A9FF",
                    texttemplate="$%{y:,.2f}",
                    textposition="outside",
                    hovertemplate=(
                        "%{x}<br>"
                        "Spent: $%{y:,.2f}<extra></extra>"
                    ),
                )

                monthly_chart.update_layout(
                    template="plotly_dark",
                    height=340,
                    margin={"t": 35, "b": 35, "l": 15, "r": 15},
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Month",
                    yaxis_title="Amount ($)",
                    showlegend=False,
                )

                st.plotly_chart(
                    monthly_chart,
                    use_container_width=True,
                )
            else:
                st.info("No monthly spending data available.")

        st.divider()

        st.markdown("## Recent Transactions")

        if transactions:
            recent = sorted(
                transactions,
                key=lambda item: (item["date"], item["id"]),
                reverse=True,
            )[:5]

            st.dataframe(
                [
                    {
                        "Date": item["date"],
                        "Merchant": item["merchant"],
                        "Category": item["category"] or "Uncategorized",
                        "Amount": f"${item['amount']:,.2f}",
                    }
                    for item in recent
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No transactions yet. Add your first transaction!")
