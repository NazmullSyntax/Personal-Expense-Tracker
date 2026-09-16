# expense_tracker.py
# ============================================================
# PERSONAL EXPENSE TRACKER - ALL-IN-ONE
# ============================================================
# Run:
#   python expense_tracker.py              → generates data + analysis
#   streamlit run expense_tracker.py       → launches dashboard
# ============================================================

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ---------- Global paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'expenses.csv')
OUT_DIR = os.path.join(BASE_DIR, 'output')
CHART_DIR = os.path.join(OUT_DIR, 'charts')
os.makedirs(CHART_DIR, exist_ok=True)


# ============================================================
# 1. DATA GENERATOR
# ============================================================
def generate_expense_data(n_transactions=1500, months=12, seed=42):
    """Generate realistic personal expense data."""
    np.random.seed(seed)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)

    categories = {
        'Food & Dining':     {'mean': 25,  'std': 15,  'freq': 0.25},
        'Transportation':    {'mean': 15,  'std': 10,  'freq': 0.15},
        'Shopping':          {'mean': 60,  'std': 40,  'freq': 0.12},
        'Groceries':         {'mean': 80,  'std': 30,  'freq': 0.12},
        'Bills & Utilities': {'mean': 120, 'std': 50,  'freq': 0.06},
        'Entertainment':     {'mean': 35,  'std': 20,  'freq': 0.10},
        'Healthcare':        {'mean': 90,  'std': 60,  'freq': 0.04},
        'Education':         {'mean': 150, 'std': 80,  'freq': 0.03},
        'Rent':              {'mean': 800, 'std': 5,   'freq': 0.01},
        'Travel':            {'mean': 300, 'std': 200, 'freq': 0.02},
        'Personal Care':     {'mean': 40,  'std': 20,  'freq': 0.05},
        'Miscellaneous':     {'mean': 30,  'std': 25,  'freq': 0.05},
    }

    payment_methods = ['Cash', 'Credit Card', 'Debit Card', 'UPI', 'Net Banking']
    methods_prob = [0.15, 0.30, 0.25, 0.20, 0.10]

    cat_names = list(categories.keys())
    cat_probs = np.array([categories[c]['freq'] for c in cat_names])
    cat_probs = cat_probs / cat_probs.sum()

    descriptions = {
        'Food & Dining': ['Restaurant', 'Coffee shop', 'Fast food', 'Lunch', 'Dinner'],
        'Transportation': ['Uber', 'Taxi', 'Bus fare', 'Fuel', 'Metro'],
        'Shopping': ['Clothing', 'Electronics', 'Shoes', 'Accessories', 'Home decor'],
        'Groceries': ['Supermarket', 'Vegetables', 'Fruits', 'Dairy', 'Meat'],
        'Bills & Utilities': ['Electricity', 'Water', 'Internet', 'Phone', 'Gas'],
        'Entertainment': ['Movie', 'Concert', 'Streaming', 'Games', 'Books'],
        'Healthcare': ['Doctor visit', 'Pharmacy', 'Lab test', 'Dentist'],
        'Education': ['Online course', 'Books', 'Tuition', 'Workshop'],
        'Rent': ['Monthly rent'],
        'Travel': ['Flight', 'Hotel', 'Train ticket', 'Vacation'],
        'Personal Care': ['Salon', 'Gym', 'Spa', 'Cosmetics'],
        'Miscellaneous': ['Gift', 'Donation', 'Repairs', 'Other'],
    }

    records = []
    for i in range(n_transactions):
        days_offset = np.random.randint(0, months * 30)
        date = start_date + timedelta(days=int(days_offset))
        is_weekend = date.weekday() >= 5

        category = np.random.choice(cat_names, p=cat_probs)
        info = categories[category]
        amount = abs(np.random.normal(info['mean'], info['std']))
        amount = max(2, round(float(amount), 2))

        if is_weekend and category in ['Food & Dining', 'Entertainment']:
            amount *= 1.3
        if (date.day >= 28 or date.day <= 3) and category in ['Shopping', 'Entertainment']:
            amount *= 1.2

        payment = np.random.choice(payment_methods, p=methods_prob)
        description = np.random.choice(descriptions[category])

        records.append({
            'transaction_id': f"TXN{100000 + i}",
            'date': date.strftime('%Y-%m-%d'),
            'category': category,
            'description': description,
            'amount': round(amount, 2),
            'payment_method': payment,
            'notes': ''
        })

    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df['month'] = df['date'].dt.to_period('M').astype(str)
    df['year'] = df['date'].dt.year
    df['day_of_week'] = df['date'].dt.day_name()
    df['day_type'] = df['date'].dt.weekday.apply(
        lambda x: 'Weekend' if x >= 5 else 'Weekday')
    df['quarter'] = df['date'].dt.quarter
    return df


def load_or_create_data():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, parse_dates=['date'])
        # Recompute derived cols if missing
        if 'month' not in df.columns:
            df['month'] = df['date'].dt.to_period('M').astype(str)
        if 'day_of_week' not in df.columns:
            df['day_of_week'] = df['date'].dt.day_name()
        if 'day_type' not in df.columns:
            df['day_type'] = df['date'].dt.weekday.apply(
                lambda x: 'Weekend' if x >= 5 else 'Weekday')
        return df
    df = generate_expense_data()
    df.to_csv(CSV_PATH, index=False)
    return df


# ============================================================
# 2. ANALYZER (Matplotlib charts + console summary)
# ============================================================
def run_analysis(df):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns

    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (13, 6)

    print("=" * 70)
    print("PERSONAL EXPENSE TRACKER - ANALYSIS")
    print("=" * 70)
    print(f"\n✅ Loaded {len(df)} transactions")
    print(f"📅 Period: {df['date'].min().date()} → {df['date'].max().date()}")

    total_spent = df['amount'].sum()
    avg_txn = df['amount'].mean()
    max_txn = df['amount'].max()
    n_days = (df['date'].max() - df['date'].min()).days + 1
    n_months = df['month'].nunique()

    print("\n💰 OVERALL SUMMARY")
    print("-" * 70)
    print(f"Total Spent:            ${total_spent:>12,.2f}")
    print(f"Average per Transaction:${avg_txn:>11,.2f}")
    print(f"Average Daily Spend:    ${total_spent/n_days:>12,.2f}")
    print(f"Average Monthly Spend:  ${total_spent/n_months:>12,.2f}")
    print(f"Largest Transaction:    ${max_txn:>12,.2f}")

    # Category breakdown
    cat_summary = df.groupby('category').agg(
        Total=('amount', 'sum'),
        Count=('amount', 'count'),
        Average=('amount', 'mean'),
        Max=('amount', 'max')
    ).round(2).sort_values('Total', ascending=False)
    cat_summary['Percentage'] = (cat_summary['Total'] / total_spent * 100).round(1)

    print("\n📊 CATEGORY BREAKDOWN")
    print("-" * 70)
    for cat, row in cat_summary.iterrows():
        bar = '█' * int(row['Percentage'] / 2)
        print(f"{cat:<20} ${row['Total']:>10,.2f} ({row['Percentage']:>5.1f}%) {bar}")

    # Monthly trend
    monthly = df.groupby('month').agg(
        Total=('amount', 'sum'),
        Count=('amount', 'count'),
        Avg=('amount', 'mean')
    ).round(2)
    print("\n📈 MONTHLY TREND")
    print("-" * 70)
    for month, row in monthly.iterrows():
        bar = '█' * int(row['Total'] / 200)
        print(f"{month}  ${row['Total']:>9,.2f}  ({int(row['Count']):>3} txns)  {bar}")

    # Payment method
    payment = df.groupby('payment_method').agg(
        Total=('amount', 'sum'),
        Count=('amount', 'count'),
        Avg=('amount', 'mean')
    ).round(2).sort_values('Total', ascending=False)
    payment['%'] = (payment['Total'] / total_spent * 100).round(1)
    print("\n💳 PAYMENT METHOD")
    print("-" * 70)
    print(payment.to_string())

    # Day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                 'Friday', 'Saturday', 'Sunday']
    dow = df.groupby('day_of_week')['amount'].agg(
        ['sum', 'mean', 'count']).reindex(day_order)
    print("\n📅 DAY-OF-WEEK")
    print("-" * 70)
    for day, row in dow.iterrows():
        bar = '█' * int(row['sum'] / 500)
        print(f"{day:<10} ${row['sum']:>9,.2f}  {bar}")

    # Top 10
    print("\n🏆 TOP 10 TRANSACTIONS")
    print("-" * 70)
    top10 = df.nlargest(10, 'amount')[
        ['date', 'category', 'description', 'amount', 'payment_method']].copy()
    top10['date'] = top10['date'].dt.strftime('%Y-%m-%d')
    print(top10.to_string(index=False))

    # ---------- Charts ----------
    # Chart 1: Category pie + bar
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    colors = plt.cm.Set3(np.linspace(0, 1, len(cat_summary)))
    axes[0].pie(cat_summary['Total'], labels=cat_summary.index,
                autopct='%1.1f%%', colors=colors, startangle=90,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
    axes[0].set_title('Spending Distribution by Category', fontweight='bold')
    axes[1].barh(cat_summary.index[::-1], cat_summary['Total'][::-1],
                 color=colors[::-1], edgecolor='black', alpha=0.85)
    axes[1].set_xlabel('Total Spent ($)')
    axes[1].set_title('Total Spending by Category', fontweight='bold')
    for i, v in enumerate(cat_summary['Total'][::-1]):
        axes[1].text(v + 20, i, f'${v:,.0f}', va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, '01_category.png'), dpi=100, bbox_inches='tight')
    plt.close()

    # Chart 2: Monthly trend
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    axes[0].plot(monthly.index, monthly['Total'], marker='o',
                 linewidth=2.5, color='#3498db', markersize=8)
    axes[0].fill_between(monthly.index, monthly['Total'],
                          alpha=0.25, color='#3498db')
    axes[0].axhline(monthly['Total'].mean(), color='red', linestyle='--',
                    label=f"Avg: ${monthly['Total'].mean():,.0f}")
    axes[0].set_title('Monthly Spending Trend', fontweight='bold')
    axes[0].set_ylabel('Amount ($)')
    axes[0].legend()
    axes[0].tick_params(axis='x', rotation=45)
    axes[1].bar(monthly.index, monthly['Count'], color='coral',
                alpha=0.8, edgecolor='black')
    axes[1].set_title('Transactions per Month', fontweight='bold')
    axes[1].tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, '02_monthly.png'), dpi=100, bbox_inches='tight')
    plt.close()

    # Chart 3: Daily timeline
    fig, ax = plt.subplots(figsize=(14, 6))
    daily = df.groupby('date')['amount'].sum()
    ax.plot(daily.index, daily.values, linewidth=1, color='steelblue', alpha=0.7)
    rolling = daily.rolling(7, min_periods=1).mean()
    ax.plot(rolling.index, rolling.values, linewidth=2.5,
            color='red', label='7-day rolling avg')
    ax.set_title('Daily Spending Timeline', fontweight='bold')
    ax.set_ylabel('Amount ($)')
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, '03_timeline.png'), dpi=100, bbox_inches='tight')
    plt.close()

    # Chart 4: Category trends
    fig, ax = plt.subplots(figsize=(14, 7))
    top_cats = cat_summary.head(6).index.tolist()
    cat_monthly = df[df['category'].isin(top_cats)].pivot_table(
        values='amount', index='month', columns='category',
        aggfunc='sum', fill_value=0)
    for cat in top_cats:
        ax.plot(cat_monthly.index, cat_monthly[cat], marker='o',
                linewidth=2, label=cat)
    ax.set_title('Top 6 Categories - Monthly Trend', fontweight='bold')
    ax.set_ylabel('Amount ($)')
    ax.legend(loc='upper left', fontsize=9)
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, '04_category_trends.png'), dpi=100, bbox_inches='tight')
    plt.close()

    # Chart 5: Heatmap
    fig, ax = plt.subplots(figsize=(12, 7))
    pivot = df.pivot_table(values='amount', index='category',
                            columns='day_of_week', aggfunc='sum',
                            fill_value=0).reindex(columns=day_order)
    sns.heatmap(pivot, annot=True, fmt='.0f', cmap='YlOrRd',
                linewidths=1, ax=ax, cbar_kws={'label': 'Total ($)'})
    ax.set_title('Spending Heatmap: Category × Day', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, '05_heatmap.png'), dpi=100, bbox_inches='tight')
    plt.close()

    # Chart 6: Boxplot
    fig, ax = plt.subplots(figsize=(14, 6))
    order = cat_summary.sort_values('Total', ascending=False).index
    sns.boxplot(data=df, x='category', y='amount', order=order,
                palette='Set2', ax=ax)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_title('Transaction Amount Distribution by Category', fontweight='bold')
    ax.set_yscale('log')
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, '06_boxplot.png'), dpi=100, bbox_inches='tight')
    plt.close()

    # Save CSVs
    cat_summary.to_csv(os.path.join(OUT_DIR, 'category_summary.csv'))
    monthly.to_csv(os.path.join(OUT_DIR, 'monthly_report.csv'))
    payment.to_csv(os.path.join(OUT_DIR, 'payment_summary.csv'))

    print(f"\n✅ Charts saved in: {CHART_DIR}")
    print(f"✅ CSVs saved in:   {OUT_DIR}")


# ============================================================
# 3. BUDGET ALERTS
# ============================================================
DEFAULT_BUDGETS = {
    'Food & Dining': 400, 'Transportation': 200, 'Shopping': 500,
    'Groceries': 500, 'Bills & Utilities': 400, 'Entertainment': 250,
    'Healthcare': 300, 'Education': 300, 'Rent': 900,
    'Travel': 400, 'Personal Care': 150, 'Miscellaneous': 150,
}


def check_budgets(df, budgets=None):
    budgets = budgets or DEFAULT_BUDGETS
    current_month = df['month'].max()
    month_df = df[df['month'] == current_month]
    spent = month_df.groupby('category')['amount'].sum()

    rows = []
    for cat, b in budgets.items():
        s = float(spent.get(cat, 0))
        pct = (s / b * 100) if b > 0 else 0
        if pct >= 100:
            status = '🚨 OVER'
        elif pct >= 80:
            status = '⚠️  Warning'
        else:
            status = '✅ OK'
        rows.append({
            'Category': cat, 'Budget': b, 'Spent': round(s, 2),
            'Remaining': round(b - s, 2), 'Used_%': round(pct, 1),
            'Status': status
        })
    return pd.DataFrame(rows), current_month


def print_budget_report(df):
    print("\n" + "=" * 80)
    print("💰 BUDGET ALERT SYSTEM")
    print("=" * 80)
    report, month = check_budgets(df)
    total_budget = report['Budget'].sum()
    total_spent = report['Spent'].sum()
    print(f"\n📅 Month: {month}")
    print(f"💵 Total Budget: ${total_budget:,}")
    print(f"💸 Total Spent:  ${total_spent:,.2f}")
    print(f"📊 Usage: {total_spent/total_budget*100:.1f}%\n")
    print(f"{'Category':<20}{'Budget':>10}{'Spent':>10}{'Remain':>10}{'Used':>8}  Status")
    print("-" * 80)
    for _, r in report.iterrows():
        print(f"{r['Category']:<20}${r['Budget']:>8,.0f}"
              f"${r['Spent']:>9,.2f}${r['Remaining']:>9,.2f}"
              f"{r['Used_%']:>7.1f}%  {r['Status']}")
    over = report[report['Used_%'] >= 100]
    warn = report[(report['Used_%'] >= 80) & (report['Used_%'] < 100)]
    if len(over):
        print(f"\n🚨 OVER BUDGET ({len(over)}):")
        for _, r in over.iterrows():
            print(f"   • {r['Category']}: ${-r['Remaining']:,.2f} over")
    if len(warn):
        print(f"\n⚠️  NEAR LIMIT ({len(warn)}):")
        for _, r in warn.iterrows():
            print(f"   • {r['Category']}: {r['Used_%']:.0f}% used")
    if not len(over) and not len(warn):
        print("\n✅ All categories within safe limits!")
    report.to_csv(os.path.join(OUT_DIR, f'budget_{month}.csv'), index=False)
    return report


# ============================================================
# 4. FORECAST
# ============================================================
def run_forecast(df):
    from sklearn.linear_model import LinearRegression

    print("\n" + "=" * 70)
    print("EXPENSE FORECAST")
    print("=" * 70)

    monthly = df.groupby('month')['amount'].sum().reset_index()
    monthly['idx'] = range(len(monthly))

    if len(monthly) < 3:
        print("Not enough months to forecast.")
        return

    X = monthly[['idx']].values
    y = monthly['amount'].values

    model = LinearRegression().fit(X, y)
    future_idx = np.array([[len(monthly)], [len(monthly)+1], [len(monthly)+2]])
    future_pred = model.predict(future_idx)

    last_month = pd.to_datetime(monthly['month'].iloc[-1])
    future_months = [(last_month + pd.DateOffset(months=i)).strftime('%Y-%m')
                      for i in range(1, 4)]

    print(f"\n📈 Trend slope: ${model.coef_[0]:,.2f}/month")
    print("\n🔮 Next 3 Months Forecast:")
    for m, p in zip(future_months, future_pred):
        print(f"   {m}: ${p:,.2f}")

    # Category forecast
    cat_rows = []
    for cat in df['category'].unique():
        cd = df[df['category'] == cat].groupby('month')['amount'].sum().reset_index()
        cd['idx'] = range(len(cd))
        if len(cd) >= 3 and cd['amount'].sum() > 0:
            m = LinearRegression().fit(cd[['idx']], cd['amount'])
            pred = np.clip(m.predict(future_idx), 0, None)
            cat_rows.append({'Category': cat,
                              **{future_months[i]: round(pred[i], 2)
                                 for i in range(3)},
                              'Total': round(pred.sum(), 2)})

    fdf = pd.DataFrame(cat_rows).sort_values('Total', ascending=False)
    print("\n📊 Category Forecasts:")
    print(fdf.to_string(index=False))
    fdf.to_csv(os.path.join(OUT_DIR, 'forecast.csv'), index=False)

    # Forecast chart
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(monthly['month'], monthly['amount'], marker='o',
            linewidth=2.5, color='#3498db', label='Actual')
    ax.plot(future_months, future_pred, marker='s', linestyle='--',
            linewidth=2.5, color='red', markersize=10, label='Forecast')
    ax.fill_between(future_months, future_pred * 0.85, future_pred * 1.15,
                     color='red', alpha=0.15, label='±15%')
    ax.set_title('Monthly Spending Forecast', fontweight='bold')
    ax.set_ylabel('Amount ($)')
    ax.tick_params(axis='x', rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, '07_forecast.png'),
                dpi=100, bbox_inches='tight')
    plt.close()
    print(f"\n✅ Forecast chart saved: {CHART_DIR}/07_forecast.png")


# ============================================================
# 5. STREAMLIT DASHBOARD
# ============================================================
def run_streamlit():
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    from sklearn.linear_model import LinearRegression

    st.set_page_config(page_title="Expense Tracker",
                        page_icon="💰", layout="wide")

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
        </style>
    """, unsafe_allow_html=True)

    @st.cache_data
    def _load():
        return load_or_create_data()

    df = _load()

    # ----- Sidebar -----
    st.sidebar.image("https://img.icons8.com/color/96/000000/money-bag.png",
                      width=80)
    st.sidebar.title("💰 Expense Tracker")
    page = st.sidebar.radio("Navigate", [
        "📊 Dashboard", "💸 Transactions", "📈 Trends",
        "🔮 Forecast", "🎯 Budget", "➕ Add Expense"
    ])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Filters")
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    dr = st.sidebar.date_input("Date Range", [min_date, max_date],
                                min_value=min_date, max_value=max_date)
    all_cats = sorted(df['category'].unique())
    sel_cats = st.sidebar.multiselect("Categories", all_cats, default=all_cats)
    all_pay = sorted(df['payment_method'].unique())
    sel_pay = st.sidebar.multiselect("Payment", all_pay, default=all_pay)

    if len(dr) == 2:
        filtered = df[(df['date'].dt.date >= dr[0]) &
                      (df['date'].dt.date <= dr[1]) &
                      (df['category'].isin(sel_cats)) &
                      (df['payment_method'].isin(sel_pay))]
    else:
        filtered = df[(df['category'].isin(sel_cats)) &
                      (df['payment_method'].isin(sel_pay))]

    # ============ PAGE: DASHBOARD ============
    if page == "📊 Dashboard":
        st.markdown('<h1 class="main-title">💰 Expense Dashboard</h1>',
                     unsafe_allow_html=True)

        if len(filtered) == 0:
            st.warning("No data for the selected filters.")
            st.stop()

        total = filtered['amount'].sum()
        avg_txn = filtered['amount'].mean()
        n_txn = len(filtered)
        days = (filtered['date'].max() - filtered['date'].min()).days + 1
        n_months = filtered['month'].nunique()

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("💵 Total Spent", f"${total:,.0f}")
        c2.metric("📊 Transactions", f"{n_txn:,}")
        c3.metric("💳 Avg Txn", f"${avg_txn:.2f}")
        c4.metric("📅 Daily Avg", f"${total/days:,.2f}")
        c5.metric("📆 Monthly Avg", f"${total/n_months:,.0f}")

        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        with col1:
            cats = filtered.groupby('category')['amount'].sum().sort_values(ascending=False)
            fig = px.pie(values=cats.values, names=cats.index,
                          title='Spending by Category', hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            mo = filtered.groupby('month')['amount'].sum().reset_index()
            fig = px.bar(mo, x='month', y='amount', title='Monthly Spending',
                          color='amount', color_continuous_scale='Blues')
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            pay = filtered.groupby('payment_method')['amount'].sum()
            fig = px.pie(values=pay.values, names=pay.index,
                          title='Payment Method Split',
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                         'Friday', 'Saturday', 'Sunday']
            dow = filtered.groupby('day_of_week')['amount'].sum().reindex(day_order)
            fig = px.bar(x=dow.index, y=dow.values, title='Spending by Day',
                          color=dow.values, color_continuous_scale='OrRd')
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    # ============ PAGE: TRANSACTIONS ============
    elif page == "💸 Transactions":
        st.markdown('<h1 class="main-title">💸 Transactions</h1>',
                     unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            search = st.text_input("🔍 Search", "")
        with c2:
            sort_by = st.selectbox("Sort by", ['date', 'amount', 'category'])

        d = filtered.copy()
        if search:
            d = d[d['description'].str.contains(search, case=False) |
                  d['category'].str.contains(search, case=False)]
        d = d.sort_values(sort_by, ascending=False)
        st.write(f"**{len(d)}** transactions | **Total: ${d['amount'].sum():,.2f}**")
        st.dataframe(d[['transaction_id', 'date', 'category', 'description',
                         'amount', 'payment_method']],
                      use_container_width=True, hide_index=True, height=500)
        st.download_button("📥 Download CSV", d.to_csv(index=False),
                            "transactions.csv", "text/csv")

    # ============ PAGE: TRENDS ============
    elif page == "📈 Trends":
        st.markdown('<h1 class="main-title">📈 Trends</h1>',
                     unsafe_allow_html=True)

        st.subheader("Daily Spending")
        daily = filtered.groupby('date')['amount'].sum().reset_index()
        daily['rolling_7d'] = daily['amount'].rolling(7, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['amount'],
                                  mode='markers+lines', name='Daily'))
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['rolling_7d'],
                                  mode='lines', name='7-day Avg',
                                  line=dict(color='red', width=2.5)))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Category Trends")
        top = filtered.groupby('category')['amount'].sum().nlargest(6).index
        ct = filtered[filtered['category'].isin(top)].pivot_table(
            values='amount', index='month', columns='category',
            aggfunc='sum', fill_value=0)
        fig = px.line(ct, x=ct.index, y=ct.columns, markers=True)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Heatmap: Category × Day")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                     'Friday', 'Saturday', 'Sunday']
        pivot = filtered.pivot_table(values='amount', index='category',
                                       columns='day_of_week',
                                       aggfunc='sum', fill_value=0
                                       ).reindex(columns=day_order)
        fig = px.imshow(pivot, text_auto='.0f', aspect='auto',
                          color_continuous_scale='YlOrRd')
        st.plotly_chart(fig, use_container_width=True)

    # ============ PAGE: FORECAST ============
    elif page == "🔮 Forecast":
        st.markdown('<h1 class="main-title">🔮 Forecast</h1>',
                     unsafe_allow_html=True)

        monthly = df.groupby('month')['amount'].sum().reset_index()
        monthly['idx'] = range(len(monthly))
        if len(monthly) < 3:
            st.warning("Need ≥3 months of data.")
            st.stop()

        X = monthly[['idx']].values
        y = monthly['amount'].values
        model = LinearRegression().fit(X, y)

        n = st.slider("Months to forecast", 1, 6, 3)
        fidx = np.array([[len(monthly)+i] for i in range(n)])
        pred = model.predict(fidx)
        last = pd.to_datetime(monthly['month'].iloc[-1])
        fm = [(last + pd.DateOffset(months=i+1)).strftime('%Y-%m')
              for i in range(n)]

        c1, c2, c3 = st.columns(3)
        c1.metric("Next Month", f"${pred[0]:,.0f}")
        c2.metric(f"{n}-Month Total", f"${pred.sum():,.0f}")
        c3.metric("Avg / Month", f"${pred.mean():,.0f}")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['amount'],
                                  mode='lines+markers', name='Actual'))
        fig.add_trace(go.Scatter(x=fm, y=pred, mode='lines+markers',
                                  name='Forecast',
                                  line=dict(color='red', dash='dash')))
        fig.add_trace(go.Scatter(
            x=fm + fm[::-1],
            y=list(pred*1.15) + list(pred*0.85)[::-1],
            fill='toself', fillcolor='rgba(255,0,0,0.15)',
            line=dict(color='rgba(255,0,0,0)'), name='±15%'))
        st.plotly_chart(fig, use_container_width=True)

        # Category forecast
        rows = []
        for cat in df['category'].unique():
            cd = df[df['category'] == cat].groupby('month')['amount'].sum().reset_index()
            cd['idx'] = range(len(cd))
            if len(cd) >= 3 and cd['amount'].sum() > 0:
                m = LinearRegression().fit(cd[['idx']], cd['amount'])
                p = np.clip(m.predict(fidx), 0, None)
                rows.append({'Category': cat,
                              **{f'Month {i+1}': round(p[i], 2) for i in range(n)},
                              'Total': round(p.sum(), 2)})
        st.subheader("Category Forecasts")
        st.dataframe(pd.DataFrame(rows).sort_values('Total', ascending=False)
                       .round(2), use_container_width=True, hide_index=True)

    # ============ PAGE: BUDGET ============
    elif page == "🎯 Budget":
        st.markdown('<h1 class="main-title">🎯 Budget Manager</h1>',
                     unsafe_allow_html=True)
        categories = sorted(df['category'].unique())
        cols = st.columns(3)
        budgets = {}
        for i, cat in enumerate(categories):
            with cols[i % 3]:
                budgets[cat] = st.number_input(
                    cat, min_value=0, value=DEFAULT_BUDGETS.get(cat, 200),
                    step=50, key=f"b_{cat}")
        total_budget = sum(budgets.values())
        st.info(f"💵 **Total Monthly Budget:** ${total_budget:,}")

        report, month = check_budgets(df, budgets)
        st.subheader(f"Budget Status — {month}")
        st.dataframe(report, use_container_width=True, hide_index=True)

        for _, r in report.iterrows():
            pct = min(r['Used_%'], 100)
            color = '🔴' if r['Used_%'] >= 100 else '🟡' if r['Used_%'] >= 80 else '🟢'
            st.write(f"{color} **{r['Category']}** — ${r['Spent']:.0f} / ${r['Budget']:.0f}")
            st.progress(pct / 100)

    # ============ PAGE: ADD EXPENSE ============
    elif page == "➕ Add Expense":
        st.markdown('<h1 class="main-title">➕ Add Expense</h1>',
                     unsafe_allow_html=True)
        with st.form("add"):
            c1, c2 = st.columns(2)
            with c1:
                date = st.date_input("Date", datetime.now())
                category = st.selectbox("Category", sorted(df['category'].unique()))
                amount = st.number_input("Amount ($)", min_value=0.01,
                                          value=10.0, step=0.5)
            with c2:
                payment = st.selectbox("Payment Method",
                                        sorted(df['payment_method'].unique()))
                description = st.text_input("Description", "New expense")
                notes = st.text_area("Notes", "")
            if st.form_submit_button("💾 Add", type="primary"):
                new_row = {
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
                    'quarter': (date.month - 1) // 3 + 1,
                }
                all_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                all_df.to_csv(CSV_PATH, index=False)
                st.cache_data.clear()
                st.success(f"✅ Added: {description} — ${amount:.2f}")
                st.balloons()


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def main():
    # Detect Streamlit environment
    try:
        import streamlit
        is_streamlit = True
    except ImportError:
        is_streamlit = False

    # Streamlit runs file with special context; detect via runtime
    from streamlit import runtime
    if runtime.exists():
        run_streamlit()
    else:
        # CLI mode → data + analysis
        df = load_or_create_data()
        run_analysis(df)
        print_budget_report(df)
        try:
            run_forecast(df)
        except ImportError:
            print("\n⚠️  scikit-learn not installed → skipping forecast.")


if __name__ == "__main__":
    main()