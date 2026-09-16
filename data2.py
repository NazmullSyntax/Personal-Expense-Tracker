# expense_tracker.py
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'expenses.csv')


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
    freq = [0.25, 0.15, 0.12, 0.12, 0.06, 0.10, 0.04, 0.03, 0.01, 0.02, 0.05, 0.05]
    freq = np.array(freq) / sum(freq)

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
        amt = abs(np.random.normal(means[ci], stds[ci]))
        amt = max(2.0, round(float(amt), 2))

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
    df['day_type'] = df['date'].dt.weekday.apply(
        lambda x: 'Weekend' if x >= 5 else 'Weekday')
    return df


def load_data():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH, parse_dates=['date'])
    df = generate_data()
    df.to_csv(CSV_PATH, index=False)
    return df


# ============================================================
# 2. CONSOLE REPORT + CHARTS
# ============================================================
def analyze(df):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_style("whitegrid")

    os.makedirs('output/charts', exist_ok=True)

    total = df['amount'].sum()
    print("=" * 70)
    print("PERSONAL EXPENSE TRACKER")
    print("=" * 70)
    print(f"Transactions: {len(df)}")
    print(f"Period:       {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"Total Spent:  ${total:,.2f}")
    print(f"Avg / Txn:    ${df['amount'].mean():,.2f}")
    print(f"Avg / Month:  ${total / df['month'].nunique():,.2f}")

    # Category breakdown
    cats = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    print("\n📊 CATEGORY BREAKDOWN")
    print("-" * 70)
    for c, v in cats.items():
        pct = v / total * 100
        print(f"{c:<20} ${v:>10,.2f} ({pct:>5.1f}%) {'█' * int(pct / 2)}")

    # Monthly trend
    monthly = df.groupby('month')['amount'].sum()
    print("\n📈 MONTHLY TREND")
    print("-" * 70)
    for m, v in monthly.items():
        print(f"{m}  ${v:>10,.2f}  {'█' * int(v / 200)}")

    # Payment methods
    print("\n💳 PAYMENT METHODS")
    print("-" * 70)
    pay = df.groupby('payment_method')['amount'].sum().sort_values(ascending=False)
    for p, v in pay.items():
        print(f"{p:<15} ${v:>10,.2f} ({v/total*100:>5.1f}%)")

    # Top 5
    print("\n🏆 TOP 5 TRANSACTIONS")
    print("-" * 70)
    top = df.nlargest(5, 'amount')[['date', 'category', 'description', 'amount']]
    print(top.to_string(index=False))

    # ---------- Charts ----------
    # Chart 1: category + monthly
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    cats.plot(kind='barh', ax=ax[0], color='steelblue')
    ax[0].set_title('Spending by Category')
    ax[0].set_xlabel('Amount ($)')
    ax[0].invert_yaxis()

    monthly.plot(kind='bar', ax=ax[1], color='coral')
    ax[1].set_title('Monthly Spending')
    ax[1].set_ylabel('Amount ($)')
    ax[1].tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig('output/charts/01_overview.png', dpi=100, bbox_inches='tight')
    plt.close()

    # Chart 2: pie + payments
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    cats.plot(kind='pie', ax=ax[0], autopct='%1.1f%%',
              colors=plt.cm.Set3(np.linspace(0, 1, len(cats))))
    ax[0].set_ylabel('')
    ax[0].set_title('Category Distribution')

    pay.plot(kind='bar', ax=ax[1], color='mediumseagreen')
    ax[1].set_title('Spending by Payment Method')
    ax[1].set_ylabel('Amount ($)')
    ax[1].tick_params(axis='x', rotation=30)
    plt.tight_layout()
    plt.savefig('output/charts/02_pie_payment.png', dpi=100, bbox_inches='tight')
    plt.close()

    # Chart 3: daily timeline
    fig, ax = plt.subplots(figsize=(13, 5))
    daily = df.groupby('date')['amount'].sum()
    ax.plot(daily.index, daily.values, color='steelblue', alpha=0.6, linewidth=1)
    ax.plot(daily.index, daily.rolling(7, min_periods=1).mean(),
            color='red', linewidth=2, label='7-day avg')
    ax.set_title('Daily Spending Timeline')
    ax.set_ylabel('Amount ($)')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('output/charts/03_timeline.png', dpi=100, bbox_inches='tight')
    plt.close()

    # Chart 4: heatmap
    fig, ax = plt.subplots(figsize=(11, 6))
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday', 'Sunday']
    pivot = df.pivot_table(values='amount', index='category',
                            columns='day_of_week', aggfunc='sum',
                            fill_value=0).reindex(columns=days)
    sns.heatmap(pivot, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
    ax.set_title('Spending Heatmap: Category × Day')
    plt.tight_layout()
    plt.savefig('output/charts/04_heatmap.png', dpi=100, bbox_inches='tight')
    plt.close()

    print("\n✅ Charts saved to output/charts/")


# ============================================================
# 3. BUDGET CHECK
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
          f"{total_s/total_b*100:>7.1f}%")


# ============================================================
# 4. FORECAST
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
    months = [(last + pd.DateOffset(months=i)).strftime('%Y-%m')
              for i in range(1, 4)]

    print("\n" + "=" * 70)
    print("🔮 3-MONTH FORECAST")
    print("=" * 70)
    for m, p in zip(months, future):
        print(f"  {m}:  ${p:,.2f}")
    print(f"\n  Total:  ${future.sum():,.2f}")


# ============================================================
# 5. STREAMLIT DASHBOARD
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

    # Sidebar filters
    st.sidebar.header("🎯 Filters")
    cats = sorted(df['category'].unique())
    sel_cats = st.sidebar.multiselect("Categories", cats, default=cats)
    pays = sorted(df['payment_method'].unique())
    sel_pays = st.sidebar.multiselect("Payment Methods", pays, default=pays)

    filtered = df[df['category'].isin(sel_cats) &
                  df['payment_method'].isin(sel_pays)]

    page = st.sidebar.radio("📄 Page", [
        "Dashboard", "Transactions", "Trends", "Forecast", "Budget"
    ])

    # ============ DASHBOARD ============
    if page == "Dashboard":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Spent", f"${filtered['amount'].sum():,.0f}")
        c2.metric("Transactions", f"{len(filtered):,}")
        c3.metric("Avg / Txn", f"${filtered['amount'].mean():.2f}")
        c4.metric("Avg / Month", f"${filtered['amount'].sum() / filtered['month'].nunique():,.0f}")

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            cat_sum = filtered.groupby('category')['amount'].sum()
            fig = px.pie(values=cat_sum.values, names=cat_sum.index,
                          title='Spending by Category', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            monthly = filtered.groupby('month')['amount'].sum().reset_index()
            fig = px.bar(monthly, x='month', y='amount',
                          title='Monthly Spending', color='amount',
                          color_continuous_scale='Blues')
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            pay = filtered.groupby('payment_method')['amount'].sum()
            fig = px.pie(values=pay.values, names=pay.index,
                          title='Payment Methods')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                    'Friday', 'Saturday', 'Sunday']
            dow = filtered.groupby('day_of_week')['amount'].sum().reindex(days)
            fig = px.bar(x=dow.index, y=dow.values,
                          title='Spending by Day of Week',
                          color=dow.values, color_continuous_scale='OrRd')
            fig.update_layout(coloraxis_showscale=False,
                               xaxis_title='Day', yaxis_title='Amount ($)')
            st.plotly_chart(fig, use_container_width=True)

    # ============ TRANSACTIONS ============
    elif page == "Transactions":
        st.subheader("💸 Transaction History")

        search = st.text_input("🔍 Search by description or category", "")
        d = filtered.copy()
        if search:
            d = d[d['description'].str.contains(search, case=False, na=False) |
                  d['category'].str.contains(search, case=False, na=False)]

        d = d.sort_values('date', ascending=False)
        st.write(f"**{len(d)}** transactions — Total: **${d['amount'].sum():,.2f}**")

        st.dataframe(d[['transaction_id', 'date', 'category', 'description',
                         'amount', 'payment_method']],
                      use_container_width=True, hide_index=True, height=500)

        st.download_button("📥 Download CSV",
                            d.to_csv(index=False),
                            "transactions.csv", "text/csv")

    # ============ TRENDS ============
    elif page == "Trends":
        st.subheader("📈 Daily Spending Timeline")
        daily = filtered.groupby('date')['amount'].sum().reset_index()
        daily['rolling_7d'] = daily['amount'].rolling(7, min_periods=1).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['amount'],
                                  mode='markers+lines', name='Daily',
                                  marker=dict(size=4)))
        fig.add_trace(go.Scatter(x=daily['date'], y=daily['rolling_7d'],
                                  mode='lines', name='7-day avg',
                                  line=dict(color='red', width=3)))
        fig.update_layout(xaxis_title='Date', yaxis_title='Amount ($)')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🔥 Heatmap: Category × Day")
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                'Friday', 'Saturday', 'Sunday']
        pivot = filtered.pivot_table(values='amount', index='category',
                                       columns='day_of_week',
                                       aggfunc='sum', fill_value=0
                                       ).reindex(columns=days)
        fig = px.imshow(pivot, text_auto='.0f', aspect='auto',
                          color_continuous_scale='YlOrRd')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Category Trends Over Time")
        top = filtered.groupby('category')['amount'].sum().nlargest(6).index
        ct = filtered[filtered['category'].isin(top)].pivot_table(
            values='amount', index='month', columns='category',
            aggfunc='sum', fill_value=0)
        fig = px.line(ct, x=ct.index, y=ct.columns, markers=True)
        fig.update_layout(xaxis_title='Month', yaxis_title='Amount ($)')
        st.plotly_chart(fig, use_container_width=True)

    # ============ FORECAST ============
    elif page == "Forecast":
        st.subheader("🔮 Spending Forecast")

        monthly = df.groupby('month')['amount'].sum().reset_index()
        monthly['idx'] = range(len(monthly))

        if len(monthly) < 3:
            st.warning("Need at least 3 months of data.")
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
                                  line=dict(color='#3498db', width=3)))
        fig.add_trace(go.Scatter(x=fm, y=pred, mode='lines+markers',
                                  name='Forecast',
                                  line=dict(color='red', dash='dash', width=3)))
        fig.update_layout(xaxis_title='Month', yaxis_title='Amount ($)')
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
        analyze(df)
        check_budget(df)
        forecast(df)