# streamlit_tracker.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from generate_data import generate_expense_data

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# ---------- Custom CSS ----------
st.markdown("""
<style>
.main-title {
    font-size: 2.5rem;
    background: linear-gradient(90deg, #2ecc71, #3498db);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: bold;
    text-align: center;
}
.kpi {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------- Load Data ----------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('expenses.csv', parse_dates=['date'])
    except FileNotFoundError:
        df = generate_expense_data()
        df.to_csv('expenses.csv', index=False)
    return df

df = load_data()

# ---------- Sidebar ----------
st.sidebar.image("https://img.icons8.com/color/96/000000/money-bag.png", width=80)
st.sidebar.title("💰 Expense Tracker")

page = st.sidebar.radio("Navigate", [
    "📊 Dashboard",
    "💸 Transactions",
    "📈 Trends & Insights",
    "🔮 Forecast",
    "🎯 Budget Manager",
    "➕ Add Expense"
])

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filters")

# Date range
min_date = df['date'].min().date()
max_date = df['date'].max().date()
date_range = st.sidebar.date_input(
    "Date Range", [min_date, max_date],
    min_value=min_date, max_value=max_date
)

# Category filter
all_cats = sorted(df['category'].unique())
sel_cats = st.sidebar.multiselect("Categories", all_cats, default=all_cats)

# Payment filter
all_pay = sorted(df['payment_method'].unique())
sel_pay = st.sidebar.multiselect("Payment Methods", all_pay, default=all_pay)

# Apply filters
if len(date_range) == 2:
    filtered = df[
        (df['date'].dt.date >= date_range[0]) &
        (df['date'].dt.date <= date_range[1]) &
        (df['category'].isin(sel_cats)) &
        (df['payment_method'].isin(sel_pay))
    ]
else:
    filtered = df[df['category'].isin(sel_cats) & df['payment_method'].isin(sel_pay)]

# ============================================
# PAGE 1: DASHBOARD
# ============================================
if page == "📊 Dashboard":
    st.markdown('<h1 class="main-title">💰 Expense Dashboard</h1>',
                unsafe_allow_html=True)
    
    if len(filtered) == 0:
        st.warning("No data matches the filters.")
        st.stop()
    
    # KPIs
    total = filtered['amount'].sum()
    avg_txn = filtered['amount'].mean()
    n_txn = len(filtered)
    days = (filtered['date'].max() - filtered['date'].min()).days + 1
    daily_avg = total / days
    monthly_avg = total / filtered['month'].nunique()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💵 Total Spent", f"${total:,.0f}")
    col2.metric("📊 Transactions", f"{n_txn:,}")
    col3.metric("💳 Avg Transaction", f"${avg_txn:.2f}")
    col4.metric("📅 Daily Average", f"${daily_avg:.2f}")
    col5.metric("📆 Monthly Average", f"${monthly_avg:,.0f}")
    
    st.markdown("---")
    
    # Top row: Category pie + monthly trend
    col1, col2 = st.columns([1, 2])
    
    with col1:
        cat_totals = filtered.groupby('category')['amount'].sum().sort_values(ascending=False)
        fig = px.pie(values=cat_totals.values, names=cat_totals.index,
                     title='Spending by Category', hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textposition='inside', textinfo='percent')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        monthly = filtered.groupby('month')['amount'].sum().reset_index()
        fig = px.bar(monthly, x='month', y='amount',
                     title='Monthly Spending',
                     color='amount', color_continuous_scale='Blues',
                     labels={'amount': 'Amount ($)', 'month': 'Month'})
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Bottom row: payment + day-of-week
    col1, col2 = st.columns(2)
    
    with col1:
        pay = filtered.groupby('payment_method')['amount'].sum()
        fig = px.pie(values=pay.values, names=pay.index,
                     title='Payment Method Distribution',
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                     'Friday', 'Saturday', 'Sunday']
        dow = filtered.groupby('day_of_week')['amount'].sum().reindex(day_order)
        fig = px.bar(x=dow.index, y=dow.values,
                     title='Spending by Day of Week',
                     color=dow.values, color_continuous_scale='OrRd',
                     labels={'x': 'Day', 'y': 'Amount ($)'})
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# PAGE 2: TRANSACTIONS
# ============================================
elif page == "💸 Transactions":
    st.markdown('<h1 class="main-title">💸 Transaction History</h1>',
                unsafe_allow_html=True)
    
    # Search
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search transactions", "")
    with col2:
        sort_by = st.selectbox("Sort by", ['date', 'amount', 'category'])
    
    display = filtered.copy()
    if search:
        display = display[
            display['description'].str.contains(search, case=False) |
            display['category'].str.contains(search, case=False)
        ]
    
    display = display.sort_values(sort_by, ascending=False)
    
    st.write(f"**{len(display)}** transactions | **Total: ${display['amount'].sum():,.2f}**")
    
    st.dataframe(
        display[['transaction_id', 'date', 'category', 'description',
                 'amount', 'payment_method']],
        use_container_width=True, hide_index=True, height=500
    )
    
    # Download
    csv = display.to_csv(index=False)
    st.download_button("📥 Download CSV", csv, "transactions.csv", "text/csv")

# ============================================
# PAGE 3: TRENDS
# ============================================
elif page == "📈 Trends & Insights":
    st.markdown('<h1 class="main-title">📈 Trends & Insights</h1>',
                unsafe_allow_html=True)
    
    # Daily timeline
    st.subheader("📅 Daily Spending Timeline")
    daily = filtered.groupby('date')['amount'].sum().reset_index()
    daily['rolling_7d'] = daily['amount'].rolling(7, min_periods=1).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily['date'], y=daily['amount'],
                             mode='markers+lines', name='Daily',
                             line=dict(color='#3498db', width=1),
                             marker=dict(size=4, opacity=0.6)))
    fig.add_trace(go.Scatter(x=daily['date'], y=daily['rolling_7d'],
                             mode='lines', name='7-day Avg',
                             line=dict(color='red', width=2.5)))
    fig.update_layout(title='Daily Spending', xaxis_title='Date',
                       yaxis_title='Amount ($)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Category trend
    st.subheader("📊 Category Trends")
    top_cats = filtered.groupby('category')['amount'].sum().nlargest(6).index
    cat_trend = filtered[filtered['category'].isin(top_cats)].pivot_table(
        values='amount', index='month', columns='category',
        aggfunc='sum', fill_value=0
    )
    fig = px.line(cat_trend, x=cat_trend.index, y=cat_trend.columns,
                  markers=True, title='Top Categories Over Time')
    fig.update_layout(xaxis_title='Month', yaxis_title='Amount ($)',
                       legend_title='Category')
    st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap
    st.subheader("🔥 Spending Heatmap (Category × Day)")
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                 'Friday', 'Saturday', 'Sunday']
    pivot = filtered.pivot_table(values='amount', index='category',
                                   columns='day_of_week', aggfunc='sum',
                                   fill_value=0).reindex(columns=day_order)
    fig = px.imshow(pivot, text_auto='.0f', aspect='auto',
                     color_continuous_scale='YlOrRd',
                     title='Total Spending by Category and Day')
    st.plotly_chart(fig, use_container_width=True)
    
    # Box plot
    st.subheader("📦 Transaction Distribution by Category")
    fig = px.box(filtered, x='category', y='amount', color='category',
                  title='Transaction Amount Distribution', log_y=True)
    fig.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# PAGE 4: FORECAST
# ============================================
elif page == "🔮 Forecast":
    st.markdown('<h1 class="main-title">🔮 Expense Forecast</h1>',
                unsafe_allow_html=True)
    
    from sklearn.linear_model import LinearRegression
    
    monthly = df.groupby('month')['amount'].sum().reset_index()
    monthly['idx'] = range(len(monthly))
    
    if len(monthly) < 3:
        st.warning("Need at least 3 months of data to forecast.")
        st.stop()
    
    X = monthly[['idx']].values
    y = monthly['amount'].values
    
    model = LinearRegression().fit(X, y)
    
    # Forecast
    n_forecast = st.slider("Months to forecast", 1, 6, 3)
    future_idx = np.array([[len(monthly) + i] for i in range(n_forecast)])
    future_pred = model.predict(future_idx)
    
    last_month = pd.to_datetime(monthly['month'].iloc[-1])
    future_months = [(last_month + pd.DateOffset(months=i+1)).strftime('%Y-%m')
                      for i in range(n_forecast)]
    
    # Display
    col1, col2, col3 = st.columns(3)
    col1.metric("Next Month", f"${future_pred[0]:,.0f}")
    col2.metric(f"{n_forecast}-Month Total", f"${future_pred.sum():,.0f}")
    col3.metric("Monthly Average", f"${future_pred.mean():,.0f}")
    
    # Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['amount'],
                             mode='lines+markers', name='Actual',
                             line=dict(color='#3498db', width=2.5)))
    fig.add_trace(go.Scatter(x=future_months, y=future_pred,
                             mode='lines+markers', name='Forecast',
                             line=dict(color='red', width=2.5, dash='dash'),
                             marker=dict(size=10, symbol='square')))
    # Confidence band
    fig.add_trace(go.Scatter(
        x=future_months + future_months[::-1],
        y=list(future_pred * 1.15) + list(future_pred * 0.85)[::-1],
        fill='toself', fillcolor='rgba(255,0,0,0.15)',
        line=dict(color='rgba(255,0,0,0)'),
        name='±15% Range'
    ))
    fig.update_layout(title='Spending Forecast',
                       xaxis_title='Month', yaxis_title='Amount ($)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Category forecast table
    st.subheader("📋 Category-Level Forecasts")
    forecast_table = []
    for cat in df['category'].unique():
        cat_data = df[df['category'] == cat].groupby('month')['amount'].sum().reset_index()
        cat_data['idx'] = range(len(cat_data))
        if len(cat_data) >= 3 and cat_data['amount'].sum() > 0:
            m = LinearRegression().fit(cat_data[['idx']], cat_data['amount'])
            pred = m.predict(future_idx)
            forecast_table.append({
                'Category': cat,
                **{f'Month {i+1}': max(0, p) for i, p in enumerate(pred)},
                'Total': max(0, pred.sum())
            })
    
    forecast_df = pd.DataFrame(forecast_table).sort_values('Total', ascending=False)
    st.dataframe(forecast_df.round(2), use_container_width=True, hide_index=True)

# ============================================
# PAGE 5: BUDGET MANAGER
# ============================================
elif page == "🎯 Budget Manager":
    st.markdown('<h1 class="main-title">🎯 Budget Manager</h1>',
                unsafe_allow_html=True)
    
    st.subheader("Set Your Monthly Budgets")
    
    default_budgets = {
        'Food & Dining': 400, 'Transportation': 200, 'Shopping': 500,
        'Groceries': 500, 'Bills & Utilities': 400, 'Entertainment': 250,
        'Healthcare': 300, 'Education': 300, 'Rent': 900,
        'Travel': 400, 'Personal Care': 150, 'Miscellaneous': 150,
    }
    
    categories = sorted(df['category'].unique())
    
    # Budget inputs
    cols = st.columns(3)
    budgets = {}
    for i, cat in enumerate(categories):
        with cols[i % 3]:
            budgets[cat] = st.number_input(
                f"{cat}", min_value=0, value=default_budgets.get(cat, 200),
                step=50, key=f"budget_{cat}"
            )
    
    total_budget = sum(budgets.values())
    st.info(f"💵 **Total Monthly Budget:** ${total_budget:,}")
    
    # Current month spending
    current_month = df['month'].max()
    month_df = df[df['month'] == current_month]
    spent = month_df.groupby('category')['amount'].sum()
    
    # Budget analysis
    st.markdown("---")
    st.subheader(f"📊 Budget Status for {current_month}")
    
    budget_data = []
    for cat in categories:
        b = budgets[cat]
        s = spent.get(cat, 0)
        pct = (s / b * 100) if b > 0 else 0
        budget_data.append({
            'Category': cat,
            'Budget': b,
            'Spent': round(s, 2),
            'Remaining': round(b - s, 2),
            'Used %': round(pct, 1),
            'Status': ('🚨 Over' if pct >= 100 else
                        '⚠️ Warning' if pct >= 80 else
                        '✅ OK')
        })
    
    budget_df = pd.DataFrame(budget_data)
    st.dataframe(budget_df, use_container_width=True, hide_index=True)
    
    # Progress bars
    st.subheader("📊 Budget Progress")
    for _, row in budget_df.iterrows():
        pct = min(row['Used %'], 100)
        color = '🔴' if row['Used %'] >= 100 else '🟡' if row['Used %'] >= 80 else '🟢'
        st.write(f"{color} **{row['Category']}** — ${row['Spent']:.0f} / ${row['Budget']:.0f}")
        st.progress(pct / 100)

# ============================================
# PAGE 6: ADD EXPENSE
# ============================================
elif page == "➕ Add Expense":
    st.markdown('<h1 class="main-title">➕ Add New Expense</h1>',
                unsafe_allow_html=True)
    
    with st.form("add_expense"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.now())
            category = st.selectbox("Category", sorted(df['category'].unique()))
            amount = st.number_input("Amount ($)", min_value=0.01,
                                       value=10.0, step=0.5)
        with col2:
            payment = st.selectbox("Payment Method",
                                     sorted(df['payment_method'].unique()))
            description = st.text_input("Description", "New expense")
            notes = st.text_area("Notes", "")
        
        submitted = st.form_submit_button("💾 Add Expense", type="primary")
        
        if submitted:
            new_txn = {
                'transaction_id': f"TXN{100000 + len(df)}",
                'date': pd.Timestamp(date),
                'category': category,
                'description': description,
                'amount': amount,
                'payment_method': payment,
                'notes': notes,
                'month': pd.Timestamp(date).to_period('M').strftime('%Y-%m'),
                'year': date.year,
                'day_of_week': date.strftime('%A'),
                'day_type': 'Weekend' if date.weekday() >= 5 else 'Weekday',
                'quarter': (date.month - 1) // 3 + 1
            }
            
            # Append to CSV
            new_df = pd.DataFrame([new_txn])
            all_df = pd.concat([df, new_df], ignore_index=True)
            all_df.to_csv('expenses.csv', index=False)
            st.cache_data.clear()
            st.success(f"✅ Added: {description} - ${amount:.2f}")
            st.balloons()