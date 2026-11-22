
import datetime
from typing import ClassVar

import plotly.express as px
import streamlit as st


class Dashboard:
    """Displays financial summaries and spending trends."""

    CATEGORY_ICONS: ClassVar[dict[str, str]] = {
        "Food": "🍔",
        "Groceries": "🛒",
        "Shopping": "🛍️",
        "Transportation": "🚗",
        "Housing": "🏠",
        "Entertainment": "🎮",
        "Health": "💊",
        "Utilities": "💡",
        "Education": "📚",
        "Uncategorized": "📌",
    }


    def __init__(self, summary_service, budget_monitor):
        self.summary_service = summary_service
        self.budget_monitor = budget_monitor

    
    def render(self, transactions):
        self._apply_styles()

        financial_summary = self.summary_service.income_and_expenses()
        monthly_totals = self.summary_service.monthly_cash_flow()

        st.markdown("## Financial Overview")
        st.caption("Your personal finance activity at a glance.")

        self._render_metrics(financial_summary)

        st.divider()

        selected_date = st.date_input(
            "Select month for spending and budget tracking",
            value=datetime.date.today(),
            key="dashboard_month",
        )

        selected_month = selected_date.strftime("%Y-%m")

        category_totals = self.summary_service.spending_by_category(
            selected_month
        )

        budget_status = self.budget_monitor.get_budget_status(
            selected_month
        )

        st.markdown("## Financial Analytics")

        chart_column, category_column = st.columns(
            [1.6, 1],
            gap="large",
        )

        with chart_column:
            self._render_cash_flow_chart(monthly_totals)

        with category_column:
            self._render_category_breakdown(category_totals)

        st.divider()

        self._render_budget_progress(budget_status, selected_month)

        st.divider()

        self._render_recent_transactions(transactions)



    def _apply_styles(self):
        st.markdown(
            """
            <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            [data-testid="stProgressBar"] {
                height: 9px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


    def _render_metrics(self, summary):
        income = summary["income"]
        expenses = summary["expenses"]
        net_cash_flow = summary["net_cash_flow"]

        if net_cash_flow >= 0:
            cash_flow_color = "#55CDAA"
            cash_flow_background = "rgba(85, 205, 170, 0.10)"
            cash_flow_border = "rgba(85, 205, 170, 0.30)"
            cash_flow_icon = "↑"
            cash_flow_status = "Positive cash flow"
        else:
            cash_flow_color = "#F17C91"
            cash_flow_background = "rgba(241, 124, 145, 0.10)"
            cash_flow_border = "rgba(241, 124, 145, 0.30)"
            cash_flow_icon = "↓"
            cash_flow_status = "Negative cash flow"

        cards = [
            {
                "title": "Total Income",
                "amount": f"${income:,.2f}",
                "color": "#55CDAA",
                "background": "rgba(85, 205, 170, 0.10)",
                "border": "rgba(85, 205, 170, 0.30)",
                "icon": "↗",
                "status": "Money coming in",
            },
            {
                "title": "Total Expenses",
                "amount": f"${expenses:,.2f}",
                "color": "#F17C91",
                "background": "rgba(241, 124, 145, 0.10)",
                "border": "rgba(241, 124, 145, 0.30)",
                "icon": "↘",
                "status": "Money going out",
            },
            {
                "title": "Net Cash Flow",
                "amount": f"${net_cash_flow:,.2f}",
                "color": cash_flow_color,
                "background": cash_flow_background,
                "border": cash_flow_border,
                "icon": cash_flow_icon,
                "status": cash_flow_status,
            },
        ]

        columns = st.columns(3, gap="medium")

        for column, card in zip(columns, cards):
            with column:
                st.markdown(
                    f"""
                    <div style="
                        background: {card['background']};
                        border: 1px solid {card['border']};
                        border-radius: 12px;
                        padding: 22px;
                        min-height: 145px;
                    ">
                        <div style="
                            color: {card['color']};
                            font-size: 14px;
                            font-weight: 600;
                            margin-bottom: 12px;
                        ">
                            {card['title']}
                        </div>
                        <div style="
                            color: #FFFFFF;
                            font-size: 30px;
                            font-weight: 700;
                            margin-bottom: 10px;
                        ">
                            {card['amount']}
                        </div>
                        <div style="
                            color: {card['color']};
                            font-size: 13px;
                        ">
                            {card['icon']} {card['status']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


    def _render_cash_flow_chart(self, monthly_totals):
        with st.container(border=True):
            st.markdown("### Monthly Cash Flow")
            st.caption("Compare your income and expenses over time.")

            if not monthly_totals:
                st.info("Add transactions to see your cash flow.")
                return

            chart_data = [
                {
                    "month": datetime.datetime.strptime(
                        item["month"], "%Y-%m"
                    ).strftime("%b %Y"),
                    "Income": item["income"],
                    "Expenses": item["expenses"],
                }
                for item in monthly_totals
            ]

            chart = px.bar(
                chart_data,
                x="month",
                y=["Income", "Expenses"],
                barmode="group",
                color_discrete_map={
                    "Income": "#55CDAA",
                    "Expenses": "#F17C91",
                },
                labels={
                    "month": "Month",
                    "value": "Amount ($)",
                    "variable": "Transaction Type",
                },
            )

            chart.update_traces(
                hovertemplate=(
                    "%{x}<br>"
                    "$%{y:,.2f}<extra>%{fullData.name}</extra>"
                ),
            )

            chart.update_layout(
                template="plotly_dark",
                height=350,
                margin={"t": 20, "b": 35, "l": 15, "r": 15},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis_title="Amount ($)",
                xaxis_title=None,
                legend_title=None,
            )

            st.plotly_chart(
                chart,
                use_container_width=True,
            )


    def _render_category_breakdown(self, category_totals):
        with st.container(border=True):
            st.markdown("### Spending Breakdown")
            st.caption("Distribution of your expenses by category.")

            if not category_totals:
                st.info("No expense categories to display.")
                return

            chart = px.pie(
                category_totals,
                names="category",
                values="total",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )

            chart.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "$%{value:,.2f}<br>"
                    "%{percent}<extra></extra>"
                ),
            )

            chart.update_layout(
                template="plotly_dark",
                height=350,
                margin={"t": 15, "b": 15, "l": 10, "r": 10},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend_title=None,
            )

            st.plotly_chart(
                chart,
                use_container_width=True,
            )


 
    def _render_budget_progress(self, budgets, selected_month):
        month_label = datetime.datetime.strptime(
        selected_month,
            "%Y-%m",
        ).strftime("%B %Y")

        st.markdown(f"## Monthly Budgets — {month_label}")
        st.caption(
            "Track your spending against your saved monthly category limits."
        )

        if not budgets:
            st.info(
                "No budgets have been created yet. "
                "Visit Manage Budgets to set your first spending limit."
            )
            return

        columns = st.columns(2, gap="large")

        for index, budget in enumerate(budgets):
            with columns[index % 2], st.container(border=True):
                category = budget["category"]
                spent = budget["spent"]
                limit = budget["limit"]
                percentage = budget["percentage_used"]
                remaining = budget["remaining"]
                status = budget["status"]

                icon = self.CATEGORY_ICONS.get(category, "📁")

                st.markdown(f"### {icon} {category}")

                st.markdown(
                    f"**${spent:,.2f}** spent "
                    f"of **${limit:,.2f}**"
                    )

                st.progress(
                    min(percentage / 100, 1.0)
                    )

                st.caption(
                    f"{percentage:.1f}% of monthly budget used"
                    )

                if status == "over_limit":
                    st.error(
                        f"Over budget by ${spent - limit:,.2f}."
                        )
                elif status == "limit_reached":
                    st.warning("You've reached your budget limit.")
                elif status == "approaching_limit":
                    st.warning(
                        f"Approaching your limit. "
                        f"${remaining:,.2f} remaining."
                        )
                else:                        
                    st.success(
                        f"${remaining:,.2f} remaining."
                        )



    def _render_recent_transactions(self, transactions):
        st.markdown("## Recent Activity")
        st.caption("Your five most recent transactions.")

        if not transactions:
            st.info("No transactions yet. Add your first transaction!")
            return

        recent = sorted(
            transactions,
            key=lambda item: (item["date"], item["id"]),
            reverse=True,
        )[:5]

        st.dataframe(
            [
                {
                    "Date": item["date"],
                    "Type": item["transaction_type"].capitalize(),
                    "Merchant": item["merchant"],
                    "Category": item["category"] or "Uncategorized",
                    "Amount": (
                        f"+${item['amount']:,.2f}"
                        if item["transaction_type"] == "income"
                        else f"-${item['amount']:,.2f}"
                    ),
                }
                for item in recent
            ],
            use_container_width=True,
            hide_index=True,
        )
