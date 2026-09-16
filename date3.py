# expense_tracker.py
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'expenses.csv')
CHART_DIR = os.path.join(BASE_DIR, 'output', 'charts')
os.makedirs(CHART_DIR, exist_ok=True)


# ============================================================
# 1. DATA GENERATION
# ============================================================
def generate_data(n=1000, months=12, seed=42):
    np.random.seed(seed)
    end = datetime.now()
    start = end - timedelta(days=months * 30)

    cats = ['Food & Dining', 'Transportation', 'Shopping', 'Groceries',
            'Bills & Utilities', 'Entertainment', 'Healthcare', 'Education',
            'Rent', 'Travel', 'Personal Care', 'Miscellaneous']
    means = [25, 15, 60, 80, 120, 35, 90, 150, 800, 300, 40, 30]
    stds = [15, 10, 40, 30, 50, 20, 60, 80, 5, 200, 20, 25]
    freq = np.array([0.25, 0.15, 0.12, 0.12, 0.06, 0.10, 0.04,
                     0.03, 0.01, 0.02, 0.05, 0.05])
    freq = freq / freq.sum()

    payments = ['Cash', 'Credit Card', 'Debit Card', 'UPI', 'Net Banking']
    pay_prob = [0.15, 0.30, 0.25, 0.20, 0.10]

    desc_map = {
        'Food & Dining': ['Restaurant', 'Coffee', 'Fast food', 'Lunch'],
        'Transportation': ['Uber', 'Taxi', 'Fuel', 'Metro'],
        'Shopping': ['Clothing', 'Electronics', 'Shoes'],
        'Groceries': ['Supermarket', 'Vegetables', 'Dairy'],
        'Bills & Utilities': ['Electricity', 'Internet', 'Phone'],
        'Entertainment': ['Movie', 'Streaming', 'Games'],
        'Healthcare': ['Doctor', 'Pharmacy', 'Lab test'],
        'Education': ['Course', 'Books', 'Tuition'],
        'Rent': ['Monthly rent'],
        'Travel': ['Flight', 'Hotel', 'Train'],
        'Personal Care': ['Salon', 'Gym', 'Spa'],
        'Miscellaneous': ['Gift', 'Donation', 'Other'],
    }

    rows = []
    for i in range(n):
        offset = np.random.randint(0, months * 30)
        date = start + timedelta(days=int(offset))
        weekend = date.weekday() >= 5

        ci = np.random.choice(len(cats), p=freq)
        cat = cats[ci]
        amt = max(2.0, round(abs(np.random.normal(means[ci], stds[ci])), 2))

        if weekend and cat in ['Food & Dining', 'Entertainment']:
            amt *= 1.3
        if (date.day >= 28 or date.day <= 3) and cat in ['Shopping', 'Entertainment']:
            amt *= 1.2

        rows.append({
            'transaction_id': f"TXN{100000 + i}",
            'date': date.strftime('%Y-%m-%d'),
            'category': cat,
            'description': np.random.choice(desc_map[cat]),
            'amount': round(amt, 2),
            'payment_method': np.random.choice(payments, p=pay_prob),
        })

    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df['month'] = df['date'].dt.to_period('M').astype(str)
    df['day_of_week'] = df['date'].dt.day_name()
    return df


def load_data():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH, parse_dates=['date'])
    df = generate_data()
    df.to_csv(CSV_PATH, index=False)
    return df


# ============================================================
# 2. CONSOLE REPORT
# ============================================================
def console_report(df):
    total = df['amount'].sum()
    print("=" * 70)
    print("PERSONAL EXPENSE TRACKER")
    print("=" * 70)
    print(f"Transactions: {len(df)}")
    print(f"Period:       {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"Total Spent:  ${total:,.2f}")
    print(f"Avg / Txn:    ${df['amount'].mean():,.2f}")
    print(f"Avg / Month:  ${total / df['month'].nunique():,.2f}")

    print("\n📊 CATEGORY BREAKDOWN")
    print("-" * 70)
    cats = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    for c, v in cats.items():
        pct = v / total * 100
        print(f"{c:<20} ${v:>10,.2f} ({pct:>5.1f}%) {'█' * int(pct / 2)}")

    print("\n📈 MONTHLY TREND")
    print("-" * 70)
    for m, v in df.groupby('month')['amount'].sum().items():
        print(f"{m}  ${v:>10,.2f}  {'█' * int(v / 200)}")


# ============================================================
# 3. ALL GRAPHS (Matplotlib → PNG)
# ============================================================
def create_graphs(df):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    sns.set_style("whitegrid")

    print("\n📊 Generating graphs...")

    # ---------- GRAPH 1: Category Bar + Pie ----------
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    cats = df.groupby('category')['amount'].sum().sort_values()

    colors = plt.cm.Set3(np.linspace(0, 1, len(cats)))
    ax[0].barh(cats.index, cats.values, color=colors, edgecolor='black')
    ax[0].set_xlabel('Total Spent ($)')
    ax[0].set_title('Spending by Category (Bar)', fontweight='bold', fontsize=13)
    for i, v in enumerate(cats.values):
        ax[0].text(v + 30, i, f'${v:,.0f}', va='center', fontsize=9)

    ax[1].pie(cats.values, labels=cats.index, autopct='%1.1f%%',
              colors=colors, startangle=90,
              wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
    ax[1].set_title('Spending by Category (Pie)', fontweight='bold', fontsize=13)

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/01_category.png', dpi=100, bbox_inches='tight')
    plt.close()

    # ---------- GRAPH 2: Monthly Line + Bar ----------
    monthly = df.groupby('month')['amount'].sum()
    fig, ax = plt.subplots(2, 1, figsize=(14, 10))

    ax[0].plot(monthly.index, monthly.values, marker='o', color='#3498db',
               linewidth=2.5, markersize=8)
    ax[0].fill_between(monthly.index, monthly.values, alpha=0.25, color='#3498db')
    ax[0].axhline(monthly.mean(), color='red', linestyle='--',
                   label=f'Avg: ${monthly.mean():,.0f}')
    ax[0].set_title('Monthly Spending Trend (Line)', fontweight='bold', fontsize=13)
    ax[0].set_ylabel('Amount ($)')
    ax[0].legend()
    ax[0].tick_params(axis='x', rotation=45)

    ax[1].bar(monthly.index, monthly.values, color='coral',
              edgecolor='black', alpha=0.85)
    ax[1].set_title('Monthly Spending (Bar)', fontweight='bold', fontsize=13)
    ax[1].set_ylabel('Amount ($)')
    ax[1].tick_params(axis='x', rotation=45)
    for i, v in enumerate(monthly.values):
        ax[1].text(i, v + 50, f'${v:,.0f}', ha='center', fontsize=8)

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/02_monthly.png', dpi=100, bbox_inches='tight')
    plt.close()

    # ---------- GRAPH 3: Daily Timeline (Line) ----------
    fig, ax = plt.subplots(figsize=(14, 6))
    daily = df.groupby('date')['amount'].sum()

    ax.plot(daily.index, daily.values, color='steelblue',
            alpha=0.4, linewidth=1, label='Daily')
    ax.plot(daily.index, daily.rolling(7, min_periods=1).mean(),
            color='red', linewidth=2.5, label='7-day Avg')
    ax.plot(daily.index, daily.rolling(30, min_periods=1).mean(),
            color='green', linewidth=2.5, linestyle='--', label='30-day Avg')

    ax.set_title('Daily Spending Timeline (Line Graph)',
                  fontweight='bold', fontsize=13)
    ax.set_ylabel('Amount ($)')
    ax.set_xlabel('Date')
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/03_timeline.png', dpi=100, bbox_inches='tight')
    plt.close()

    # ---------- GRAPH 4: Payment Method Bar + Pie ----------
    pay = df.groupby('payment_method')['amount'].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))

    ax[0].bar(pay.index, pay.values, color='mediumseagreen',
              edgecolor='black', alpha=0.85)
    ax[0].set_title('Spending by Payment Method (Bar)',
                     fontweight='bold', fontsize=13)
    ax[0].set_ylabel('Amount ($)')
    ax[0].tick_params(axis='x', rotation=30)
    for i, v in enumerate(pay.values):
        ax[0].text(i, v + 100, f'${v:,.0f}', ha='center', fontsize=9)

    ax[1].pie(pay.values, labels=pay.index, autopct='%1.1f%%',
              colors=plt.cm.Pastel1(np.linspace(0, 1, len(pay))),
              startangle=90,
              wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
    ax[1].set_title('Payment Method Distribution (Pie)',
                     fontweight='bold', fontsize=13)

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/04_payment.png', dpi=100, bbox_inches='tight')
    plt.close()

    # ---------- GRAPH 5: Day-of-Week Bar ----------
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday', 'Sunday']
    dow = df.groupby('day_of_week')['amount'].sum().reindex(days)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ['#e74c3c' if d in ['Saturday', 'Sunday'] else '#3498db'
              for d in dow.index]
    bars = ax.bar(dow.index, dow.values, color=colors,
                   edgecolor='black', alpha=0.85)
    ax.set_title('Spending by Day of Week (Bar Graph)',
                  fontweight='bold', fontsize=13)
    ax.set_ylabel('Amount ($)')
    for bar, v in zip(bars, dow.values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 30,
                f'${v:,.0f}', ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/05_dayofweek.png', dpi=100, bbox_inches='tight')
    plt.close()

    # ---------- GRAPH 6: Heatmap Category × Day ----------
    fig, ax = plt.subplots(figsize=(12, 7))
    pivot = df.pivot_table(values='amount', index='category',
                            columns='day_of_week', aggfunc='sum',
                            fill_value=0).reindex(columns=days)
    sns.heatmap(pivot, annot=True, fmt='.0f', cmap='YlOrRd',
                linewidths=1, ax=ax, cbar_kws={'label': 'Total ($)'})
    ax.set_title('Heatmap: Category × Day of Week',
                  fontweight='bold', fontsize=13)
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/06_heatmap.png', dpi=100, bbox_inches='tight')
    plt.close()

    # ---------- GRAPH 7: Boxplot by Category ----------
    fig, ax = plt.subplots(figsize=(14, 6))
    order = df.groupby('category')['amount'].sum().sort_values(ascending=False).index
    sns.boxplot(data=df, x='category', y='amount', order=order,
                palette='Set2', ax=ax)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_title('Transaction Amount Distribution (Boxplot)',
                  fontweight='bold', fontsize=13)
    ax.set_ylabel('Amount ($)')
    ax.set_yscale('log')
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/07_boxplot.png', dpi=100, bbox_inches='tight')
    plt.close()

    # ---------- GRAPH 8: Top Categories Trend (Multi-Line) ----------
    top_cats = df.groupby('category')['amount'].sum().nlargest(6).index
    cat_monthly = df[df['category'].isin(top_cats)].pivot_table(
        values='amount', index='month', columns='category',
        aggfunc='sum', fill_value=0)

    fig, ax = plt.subplots(figsize=(14, 7))
    for cat in top_cats:
        ax.plot(cat_monthly.index, cat_monthly[cat],
                marker='o', linewidth=2, label=cat)
    ax.set_title('Top 6 Categories - Monthly Trend (Multi-Line)',
                  fontweight='bold', fontsize=13)
    ax.set_ylabel('Amount ($)')
    ax.legend(loc='upper left', fontsize=9)
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/08_category_trends.png', dpi=100, bbox_inches='tight')
    plt.close()

    # ---------- GRAPH 9: Histogram of Transaction Amounts ----------
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(df['amount'], bins=50, color='steelblue',
            edgecolor='black', alpha=0.75)
    ax.axvline(df['amount'].mean(), color='red', linestyle='--',
               linewidth=2, label=f'Mean: ${df["amount"].mean():.2f}')
    ax.axvline(df['amount'].median(), color='green', linestyle='--',
               linewidth=2, label=f'Median: ${df["amount"].median():.2f}')
    ax.set_title('Distribution of Transaction Amounts (Histogram)',
                  fontweight='bold', fontsize=13)
    ax.set_xlabel('Amount ($)')
    ax.set_ylabel('Frequency')
    ax.set_xlim(0, 500)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/09_histogram.png', dpi=100, bbox_inches='tight')
    plt.close()

    # ---------- GRAPH 10: Scatter (Amount vs Day-of-Month) ----------
    fig, ax = plt.subplots(figsize=(12, 6))
    df_copy = df.copy()
    df_copy['day'] = df_copy['date'].dt.day
    scatter = ax.scatter(df_copy['day'], df_copy['amount'],
                          c=df_copy['amount'], cmap='viridis',
                          alpha=0.5, s=20)
    ax.set_title('Transaction Amount vs Day of Month (Scatter)',
                  fontweight='bold', fontsize=13)
    ax.set_xlabel('Day of Month')
    ax.set_ylabel('Amount ($)')
    ax.set_yscale('log')
    plt.colorbar(scatter, ax=ax, label='Amount ($)')
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/10_scatter.png', dpi=100, bbox_inches='tight')
    plt.close()

    print(f"✅ 10 graphs saved to: {CHART_DIR}")
    for f in sorted(os.listdir(CHART_DIR)):
        print(f"   • {f}")


# ============================================================
# 4. BUDGET CHECK
# ============================================================
BUDGETS = {
    'Food & Dining': 400, 'Transportation': 200, 'Shopping': 500,
    'Groceries': 500, 'Bills & Utilities': 400, 'Entertainment': 250,
    'Healthcare': 300, 'Education': 300, 'Rent': 900,
    'Travel': 400, 'Personal Care': 150, 'Miscellaneous': 150,
}


def check_budget(df):
    month = df['month'].max()
    spent = df[df['month'] == month].groupby('category')['amount'].sum()

    print("\n" + "=" * 70)
    print(f"💰 BUDGET REPORT — {month}")
    print("=" * 70)
    print(f"{'Category':<20}{'Budget':>9}{'Spent':>10}{'Used':>8}  Status")
    print("-" * 70)

    total_b, total_s = 0, 0
    for cat, b in BUDGETS.items():
        s = float(spent.get(cat, 0))
        pct = s / b * 100
        total_b += b
        total_s += s
        status = '🚨 OVER' if pct >= 100 else '⚠️  Warn' if pct >= 80 else '✅ OK'
        print(f"{cat:<20}${b:>8}{s:>10,.2f}{pct:>7.1f}%  {status}")

    print("-" * 70)
    print(f"{'TOTAL':<20}${total_b:>8}{total_s:>10,.2f}"
          f"{total_s / total_b * 100:>7.1f}%")


def create_budget_graph(df):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    month = df['month'].max()
    spent = df[df['month'] == month].groupby('category')['amount'].sum()

    cats = list(BUDGETS.keys())
    budgets = [BUDGETS[c] for c in cats]
    actuals = [float(spent.get(c, 0)) for c in cats]

    x = np.arange(len(cats))
    width = 0.4

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.bar(x - width / 2, budgets, width, label='Budget',
           color='#3498db', edgecolor='black', alpha=0.85)
    bars = ax.bar(x + width / 2, actuals, width, label='Actual',
                   color='#e74c3c', edgecolor='black', alpha=0.85)

    # Color over-budget bars
    for bar, actual, budget in zip(bars, actuals, budgets):
        if actual > budget:
            bar.set_color('#c0392b')

    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=45, ha='right')
    ax.set_ylabel('Amount ($)')
    ax.set_title(f'Budget vs Actual Spending — {month}',
                  fontweight='bold', fontsize=13)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/11_budget.png', dpi=100, bbox_inches='tight')
    plt.close()
    print(f"✅ Budget graph saved: {CHART_DIR}/11_budget.png")


# ============================================================
# 5. FORECAST
# ============================================================
def forecast(df):
    try:
        from sklearn.linear_model import LinearRegression
    except ImportError:
        print("\n⚠️  scikit-learn not installed — skipping forecast.")
        return

    monthly = df.groupby('month')['amount'].sum().reset_index()
    monthly['idx'] = range(len(monthly))

    if len(monthly) < 3:
        print("Need ≥3 months of data for forecast.")
        return

    model = LinearRegression().fit(monthly[['idx']], monthly['amount'])
    future = model.predict(np.array([[len(monthly)],
                                      [len(monthly) + 1],
                                      [len(monthly) + 2]]))
    last = pd.to_datetime(monthly['month'].iloc[-1])
    fmonths = [(last + pd.DateOffset(months=i)).strftime('%Y-%m')
               for i in range(1, 4)]

    print("\n" + "=" * 70)
    print("🔮 3-MONTH FORECAST")
    print("=" * 70)
    for m, p in zip(fmonths, future):
        print(f"  {m}:  ${p:,.2f}")
    print(f"\n  Total:  ${future.sum():,.2f}")

    # Forecast Graph
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(13, 6))

    # Historical
    ax.plot(monthly['month'], monthly['amount'], marker='o',
            color='#3498db', linewidth=2.5, markersize=8,
            label='Actual', zorder=3)

    # Forecast
    ax.plot(fmonths, future, marker='s', color='red',
            linewidth=2.5, linestyle='--', markersize=10,
            label='Forecast', zorder=3)

    # Confidence band
    ax.fill_between(fmonths, future * 0.85, future * 1.15,
                     color='red', alpha=0.15, label='±15% Range')

    # Connection line
    ax.plot([monthly['month'].iloc[-1], fmonths[0]],
            [monthly['amount'].iloc[-1], future[0]],
            color='red', linewidth=2, linestyle='--', alpha=0.7)

    ax.set_title('Monthly Spending Forecast (Line Graph)',
                  fontweight='bold', fontsize=13)
    ax.set_ylabel('Amount ($)')
    ax.set_xlabel('Month')
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/12_forecast.png', dpi=100, bbox_inches='tight')
    plt.close()
    print(f"✅ Forecast graph saved: {CHART_DIR}/12_forecast.png")


# ============================================================
# 6. STREAMLIT DASHBOARD
# ============================================================
def run_streamlit():
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    from sklearn.linear_model import LinearRegression

    st.set_page_config(page_title="Expense Tracker", page_icon="💰",
                        layout="wide")

    st.title("💰 Personal Expense Tracker")

    @st.cache_data
    def _load():
        return load_data()

    df = _load()

    # Sidebar
    st.sidebar.header("🎯 Filters")
    cats = sorted(df['category'].unique())
    sel_cats = st.sidebar.multiselect("Categories", cats, default=cats)
    pays = sorted(df['payment_method'].unique())
    sel_pays = st.sidebar.multiselect("Payment Methods", pays, default=pays)

    filtered = df[df['category'].isin(sel_cats) &
                  df['payment_method'].isin(sel_pays)]

    page = st.sidebar.radio("📄 Page", [
        "Dashboard", "Trends", "Heatmap", "Forecast", "Budget"
    ])

    # ============ DASHBOARD ============
    if page == "Dashboard":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Spent", f"${filtered['amount'].sum():,.0f}")
        c2.metric("Transactions", f"{len(filtered):,}")
        c3.metric("Avg / Txn", f"${filtered['amount'].mean():.2f}")
        c4.metric("Avg / Month",
                   f"${filtered['amount'].sum() / filtered['month'].nunique():,.0f}")

        st.markdown("---")

        # Graph 1: Category bar
        col1, col2 = st.columns(2)
        with col1:
            cat_sum = filtered.groupby('category')['amount'].sum() \
                              .sort_values(ascending=True).reset_index()
            fig = px.bar(cat_sum, x='amount', y='category',
                          orientation='h',
                          title='Spending by Category',
                          color='amount', color_continuous_scale='Blues')
            fig.update_layout(coloraxis_showscale=False,
                               xaxis_title='Amount ($)',
                               yaxis_title='')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.pie(cat_sum, values='amount', names='category',
                          title='Category Distribution', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        # Graph 2: Monthly
        col1, col2 = st.columns(2)
        with col1:
            monthly = filtered.groupby('month')['amount'].sum().reset_index()
            fig = px.line(monthly, x='month', y='amount',
                           title='Monthly Trend', markers=True)
            fig.update_layout(xaxis_title='Month', yaxis_title='Amount ($)')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(monthly, x='month', y='amount',
                          title='Monthly Spending',
                          color='amount', color_continuous_scale='OrRd')
            fig.update_layout(coloraxis_showscale=False,
                               xaxis_title='Month', yaxis_title='Amount ($)')
            st.plotly_chart(fig, use_container_width=True)

        # Graph 3: Payment
        col1, col2 = st.columns(2)
        with col1:
            pay = filtered.groupby('payment_method')['amount'].sum().reset_index()
            fig = px.bar(pay, x='payment_method', y='amount',
                          title='Payment Methods',
                          color='amount', color_continuous_scale='Greens')
            fig.update_layout(coloraxis_showscale=False,
                               xaxis_title='', yaxis_title='Amount ($)')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                    'Friday', 'Saturday', 'Sunday']
            dow = filtered.groupby('day_of_week')['amount'].sum() \
                          .reindex(days).reset_index()
            fig = px.bar(dow, x='day_of_week', y='amount',
                          title='Spending by Day of Week',
                          color='amount', color_continuous_scale='Reds')
            fig.update_layout(coloraxis_showscale=False,
                               xaxis_title='', yaxis_title='Amount ($)')
            st.plotly_chart(fig, use_container_width=True)

    # ============ TRENDS ============
    elif page == "Trends":
        st.subheader("📈 Daily Spending Timeline")
        daily = filtered.groupby('date')['amount'].sum().reset_index()
        daily['rolling_7d'] = daily['amount'].rolling(7, min_periods=1).mean()
        daily['rolling_30d'] = daily['amount'].rolling(30, min_periods=1).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['amount'],
                                  mode='lines', name='Daily',
                                  line=dict(color='lightblue', width=1)))
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['rolling_7d'],
                                  mode='lines', name='7-day avg',
                                  line=dict(color='red', width=3)))
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['rolling_30d'],
                                  mode='lines', name='30-day avg',
                                  line=dict(color='green', width=2, dash='dash')))
        fig.update_layout(xaxis_title='Date', yaxis_title='Amount ($)',
                           title='Daily Spending with Moving Averages')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Category Trends (Multi-Line)")
        top = filtered.groupby('category')['amount'].sum().nlargest(6).index
        ct = filtered[filtered['category'].isin(top)].pivot_table(
            values='amount', index='month', columns='category',
            aggfunc='sum', fill_value=0).reset_index()
        ct_melted = ct.melt(id_vars='month', var_name='category',
                              value_name='amount')
        fig = px.line(ct_melted, x='month', y='amount', color='category',
                       markers=True, title='Top Categories Over Time')
        fig.update_layout(xaxis_title='Month', yaxis_title='Amount ($)')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📦 Transaction Distribution (Boxplot)")
        fig = px.box(filtered, x='category', y='amount', color='category',
                      title='Amount Distribution by Category', log_y=True)
        fig.update_layout(showlegend=False, xaxis_tickangle=-45,
                           xaxis_title='', yaxis_title='Amount ($)')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Transaction Histogram")
        fig = px.histogram(filtered, x='amount', nbins=50,
                            title='Distribution of Transaction Amounts')
        fig.update_layout(xaxis_title='Amount ($)', yaxis_title='Count')
        st.plotly_chart(fig, use_container_width=True)

    # ============ HEATMAP ============
    elif page == "Heatmap":
        st.subheader("🔥 Spending Heatmap: Category × Day of Week")
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                'Friday', 'Saturday', 'Sunday']
        pivot = filtered.pivot_table(values='amount', index='category',
                                       columns='day_of_week',
                                       aggfunc='sum', fill_value=0
                                       ).reindex(columns=days)
        fig = px.imshow(pivot, text_auto='.0f', aspect='auto',
                          color_continuous_scale='YlOrRd',
                          title='Heatmap by Day')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🔥 Month × Category Heatmap")
        pivot2 = filtered.pivot_table(values='amount', index='category',
                                        columns='month', aggfunc='sum',
                                        fill_value=0)
        fig = px.imshow(pivot2, text_auto='.0f', aspect='auto',
                          color_continuous_scale='Blues',
                          title='Heatmap by Month')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🎯 Scatter: Amount vs Day of Month")
        df_copy = filtered.copy()
        df_copy['day'] = df_copy['date'].dt.day
        fig = px.scatter(df_copy, x='day', y='amount', color='category',
                          title='Transaction Amount vs Day of Month',
                          log_y=True)
        fig.update_layout(xaxis_title='Day of Month',
                           yaxis_title='Amount ($)')
        st.plotly_chart(fig, use_container_width=True)

    # ============ FORECAST ============
    elif page == "Forecast":
        st.subheader("🔮 Spending Forecast")

        monthly = df.groupby('month')['amount'].sum().reset_index()
        monthly['idx'] = range(len(monthly))

        if len(monthly) < 3:
            st.warning("Need ≥3 months of data.")
            st.stop()

        model = LinearRegression().fit(monthly[['idx']], monthly['amount'])

        n = st.slider("Months to forecast", 1, 6, 3)
        fidx = np.array([[len(monthly) + i] for i in range(n)])
        pred = model.predict(fidx)

        last = pd.to_datetime(monthly['month'].iloc[-1])
        fm = [(last + pd.DateOffset(months=i + 1)).strftime('%Y-%m')
              for i in range(n)]

        c1, c2, c3 = st.columns(3)
        c1.metric("Next Month", f"${pred[0]:,.0f}")
        c2.metric(f"Next {n} Months", f"${pred.sum():,.0f}")
        c3.metric("Monthly Avg", f"${pred.mean():,.0f}")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['amount'],
                                  mode='lines+markers', name='Actual',
                                  line=dict(color='#3498db', width=3),
                                  marker=dict(size=10)))
        fig.add_trace(go.Scatter(x=fm, y=pred, mode='lines+markers',
                                  name='Forecast',
                                  line=dict(color='red', dash='dash', width=3),
                                  marker=dict(size=12, symbol='square')))
        fig.add_trace(go.Scatter(
            x=fm + fm[::-1],
            y=list(pred * 1.15) + list(pred * 0.85)[::-1],
            fill='toself', fillcolor='rgba(255,0,0,0.15)',
            line=dict(color='rgba(255,0,0,0)'), name='±15% Range'))
        fig.update_layout(xaxis_title='Month', yaxis_title='Amount ($)',
                           title='Monthly Spending Forecast')
        st.plotly_chart(fig, use_container_width=True)

    # ============ BUDGET ============
    elif page == "Budget":
        st.subheader("🎯 Budget Tracker")

        month = df['month'].max()
        spent = df[df['month'] == month].groupby('category')['amount'].sum()

        rows = []
        for cat, b in BUDGETS.items():
            s = float(spent.get(cat, 0))
            pct = s / b * 100
            rows.append({
                'Category': cat, 'Budget': b, 'Spent': round(s, 2),
                'Remaining': round(b - s, 2), 'Used %': round(pct, 1),
                'Status': '🚨 Over' if pct >= 100 else
                          '⚠️  Warn' if pct >= 80 else '✅ OK'
            })

        report = pd.DataFrame(rows)
        total_b = report['Budget'].sum()
        total_s = report['Spent'].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Budget", f"${total_b:,}")
        c2.metric("Total Spent", f"${total_s:,.2f}")
        c3.metric("Usage", f"{total_s / total_b * 100:.1f}%")

        # Graph: Budget vs Actual
        fig = go.Figure()
        fig.add_trace(go.Bar(x=report['Category'], y=report['Budget'],
                              name='Budget', marker_color='#3498db'))
        fig.add_trace(go.Bar(x=report['Category'], y=report['Spent'],
                              name='Actual', marker_color='#e74c3c'))
        fig.update_layout(barmode='group', title='Budget vs Actual Spending',
                           xaxis_title='', yaxis_title='Amount ($)',
                           xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(report, use_container_width=True, hide_index=True)

        st.markdown("### Progress")
        for _, r in report.iterrows():
            pct = min(r['Used %'], 100)
            icon = '🔴' if r['Used %'] >= 100 else \
                   '🟡' if r['Used %'] >= 80 else '🟢'
            st.write(f"{icon} **{r['Category']}** — "
                     f"${r['Spent']:.0f} / ${r['Budget']:.0f} "
                     f"({r['Used %']:.0f}%)")
            st.progress(pct / 100)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    try:
        from streamlit import runtime
        in_streamlit = runtime.exists()
    except ImportError:
        in_streamlit = False

    if in_streamlit:
        run_streamlit()
    else:
        df = load_data()
        console_report(df)
        check_budget(df)
        forecast(df)
        create_graphs(df)
        create_budget_graph(df)
        print(f"\n✅ All done! Open {CHART_DIR} to view graphs.")