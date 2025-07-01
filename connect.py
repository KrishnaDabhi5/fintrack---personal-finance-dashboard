import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import json
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
import warnings
import pymongo
from pymongo import MongoClient
import hashlib
from config import *
import os
warnings.filterwarnings('ignore')

# MongoDB connection
def init_mongodb():
    """Initialize MongoDB connection - returns None if not available"""
    try:
        # Try to connect to MongoDB using config with very short timeout
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
        # Test the connection
        client.admin.command('ping')
        db = client[MONGODB_DB_NAME]
        st.session_state.mongodb_available = True
        print("MongoDB connection successful")
        return db
    except Exception as e:
        st.session_state.mongodb_available = False
        # Don't print the error to avoid cluttering logs
        return None

# User authentication functions
def hash_email(email):
    return hashlib.sha256(email.encode()).hexdigest()

def authenticate_user():
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    
    if st.session_state.user_email is None:
        st.sidebar.subheader("🔐 Login")
        email = st.sidebar.text_input("Enter your email:", key="login_email")
        if st.sidebar.button("Login"):
            if email:
                st.session_state.user_email = email.lower().strip()
                st.session_state.user_id = hash_email(st.session_state.user_email)
                st.rerun()
            else:
                st.sidebar.error("Please enter a valid email")
        return False
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.user_email = None
        st.session_state.user_id = None
        for key in list(st.session_state.keys()):
            if key not in ['user_email', 'user_id']:
                del st.session_state[key]
        st.rerun()
    
    st.sidebar.success(f"Logged in as: {st.session_state.user_email}")
    return True

# Database operations
def load_user_data(db, user_id):
    """Load user data from MongoDB or session state"""
    try:
        if db is not None and st.session_state.get('mongodb_available', False):
            # Try to load from MongoDB
            user_data = db.users.find_one({"user_id": user_id})
            
            if user_data:
                # Load expenses
                expenses_data = user_data.get('expenses', [])
                st.session_state.expenses = pd.DataFrame(expenses_data) if expenses_data else pd.DataFrame(columns=['date', 'category', 'amount', 'description'])
                
                # Load income
                income_data = user_data.get('income', [])
                st.session_state.income = pd.DataFrame(income_data) if income_data else pd.DataFrame(columns=['date', 'source', 'amount', 'frequency'])
                
                # Load budget
                st.session_state.budget = user_data.get('budget', {
                    'Food': 5000, 'Transportation': 3000, 'Entertainment': 2000,
                    'Shopping': 4000, 'Utilities': 2500, 'Medical': 1500,
                    'Education': 2000, 'Miscellaneous': 1000
                })
                
                # Load savings goals
                st.session_state.savings_goals = user_data.get('savings_goals', [
                    {'name': 'Emergency Fund', 'target': 50000, 'current': 15000, 'deadline': '2024-12-31'},
                    {'name': 'Vacation', 'target': 25000, 'current': 8000, 'deadline': '2024-08-15'}
                ])
                
                # Load user profile
                st.session_state.user_profile = user_data.get('user_profile', {
                    'name': st.session_state.user_email.split('@')[0],
                    'email': st.session_state.user_email,
                    'member_since': datetime.now().strftime('%Y-%m-%d'),
                    'currency': '₹',
                    'language': 'English'
                })
                
                print("Loading user data for user_id:", user_id)
                print("Loaded user data:", user_data)
            else:
                # Initialize new user with default data
                initialize_new_user()
        else:
            # MongoDB not available, use session state
            if 'expenses' not in st.session_state:
                initialize_new_user()
            print("Using session state storage (MongoDB not available)")
            
    except Exception as e:
        print(f"Error loading user data: {e}")
        # Fallback to session state
        if 'expenses' not in st.session_state:
            initialize_new_user()
        print("Falling back to session state storage")

def save_user_data(db, user_id):
    """Save user data to MongoDB or session state"""
    try:
        # Convert DataFrames to list of dictionaries
        expenses_data = st.session_state.expenses.to_dict('records') if not st.session_state.expenses.empty else []
        income_data = st.session_state.income.to_dict('records') if not st.session_state.income.empty else []

        # Convert all date fields to string (ISO format)
        for expense in expenses_data:
            if isinstance(expense['date'], (datetime, )):
                expense['date'] = expense['date'].strftime('%Y-%m-%d')
            elif isinstance(expense['date'], (pd.Timestamp, )):
                expense['date'] = expense['date'].strftime('%Y-%m-%d')
            elif isinstance(expense['date'], (date, )):
                expense['date'] = expense['date'].isoformat()
        for income in income_data:
            if isinstance(income['date'], (datetime, )):
                income['date'] = income['date'].strftime('%Y-%m-%d')
            elif isinstance(income['date'], (pd.Timestamp, )):
                income['date'] = income['date'].strftime('%Y-%m-%d')
            elif isinstance(income['date'], (date, )):
                income['date'] = income['date'].isoformat()

        if db is not None and st.session_state.get('mongodb_available', False):
            # Save to MongoDB
            user_data = {
                "user_id": user_id,
                "email": st.session_state.user_email,
                "expenses": expenses_data,
                "income": income_data,
                "budget": st.session_state.budget,
                "savings_goals": st.session_state.savings_goals,
                "user_profile": st.session_state.user_profile,
                "last_updated": datetime.now()
            }

            # Upsert user data
            db.users.replace_one({"user_id": user_id}, user_data, upsert=True)
            print("Saving user data to MongoDB:", user_data)
            print("user_id for saving:", st.session_state.user_id)
            print("Expenses to save:", expenses_data)
            print("Income to save:", income_data)
        else:
            # MongoDB not available, data is already in session state
            print("Data saved to session state (MongoDB not available)")
        
        return True
    except Exception as e:
        print("Error saving user data:", e)
        # Data is already in session state, so we don't need to show an error
        return True

def initialize_new_user():
    """Initialize session state for new user"""
    st.session_state.expenses = pd.DataFrame(columns=['date', 'category', 'amount', 'description'])
    st.session_state.income = pd.DataFrame(columns=['date', 'source', 'amount', 'frequency'])
    st.session_state.budget = DEFAULT_BUDGET.copy()
    st.session_state.savings_goals = DEFAULT_SAVINGS_GOALS.copy()
    st.session_state.user_profile = {
        'name': st.session_state.user_email.split('@')[0] if st.session_state.user_email else 'User',
        'email': st.session_state.user_email,
        'member_since': datetime.now().strftime('%Y-%m-%d'),
        'currency': '₹',
        'language': 'English'
    }

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    .danger-card {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Constants are now imported from config.py

# Helper functions (modified to save to DB)
def add_expense(date, category, amount, description=""):
    new_expense = pd.DataFrame({
        'date': [date],
        'category': [category],
        'amount': [amount],
        'description': [description]
    })
    st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
    
    # Save to database (if available) - use existing connection
    if st.session_state.get('mongodb_available', False) and 'db_connection' in st.session_state:
        print("user_id before saving:", st.session_state.user_id)
        save_user_data(st.session_state.db_connection, st.session_state.user_id)

def add_income(date, source, amount, frequency="One-time"):
    new_income = pd.DataFrame({
        'date': [date],
        'source': [source],
        'amount': [amount],
        'frequency': [frequency]
    })
    st.session_state.income = pd.concat([st.session_state.income, new_income], ignore_index=True)
    
    # Save to database (if available) - use existing connection
    if st.session_state.get('mongodb_available', False) and 'db_connection' in st.session_state:
        print("user_id before saving:", st.session_state.user_id)
        save_user_data(st.session_state.db_connection, st.session_state.user_id)

def get_monthly_data(df, date_col='date'):
    if df.empty:
        return 0
    df[date_col] = pd.to_datetime(df[date_col])
    # Show all data, no date filtering
    return df['amount'].sum()

def generate_ai_insights():
    insights = []
    
    if not st.session_state.expenses.empty:
        expenses_df = st.session_state.expenses.copy()
        expenses_df['date'] = pd.to_datetime(expenses_df['date'])
        
        # Top spending category
        top_category = expenses_df.groupby('category')['amount'].sum().idxmax()
        top_amount = expenses_df.groupby('category')['amount'].sum().max()
        insights.append(f"💡 Your highest spending category is {top_category} with ₹{top_amount:,.2f}")
        
        # Weekly pattern analysis
        expenses_df['day_of_week'] = expenses_df['date'].dt.day_name()
        busiest_day = expenses_df.groupby('day_of_week')['amount'].sum().idxmax()
        insights.append(f"📅 You tend to spend the most on {busiest_day}s")
        
        # Budget recommendations
        monthly_expenses = get_monthly_data(st.session_state.expenses)
        monthly_income = get_monthly_data(st.session_state.income)
        
        if monthly_income > 0:
            savings_rate = ((monthly_income - monthly_expenses) / monthly_income) * 100
            if savings_rate < 20:
                insights.append("⚠️ Consider increasing your savings rate to at least 20% of income")
            else:
                insights.append(f"✅ Great job! Your savings rate is {savings_rate:.1f}%")
    
    return insights

# Main navigation
def main():
    # Initialize MongoDB
    db = init_mongodb()
    
    # Store database connection in session state for reuse
    if db is not None:
        st.session_state.db_connection = db
    
    # Show MongoDB status in sidebar
    if st.session_state.get('mongodb_available', False):
        st.sidebar.success("✅ MongoDB Connected")
    else:
        st.sidebar.warning("⚠️ MongoDB not available - using session storage")
        st.sidebar.info("Data will be stored in browser session only")
    
    # Authenticate user
    if not authenticate_user():
        st.info("Please login to access your financial dashboard.")
        return
    
    # Load user data
    if 'data_loaded' not in st.session_state:
        load_user_data(db, st.session_state.user_id)
        st.session_state.data_loaded = True
    
    st.markdown('<div class="main-header">💰 FinTrack - Personal Finance Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a section", 
                               ["Dashboard", "Add Transaction", "Budget", "Analytics", "Profile"])
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Add Transaction":
        add_transaction_page()
    elif page == "Budget":
        budget_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "Profile":
        profile_page()

# Dashboard page (remains the same)
def dashboard_page():
    st.header("📊 Financial Overview")
    
    # Calculate key metrics
    monthly_income = get_monthly_data(st.session_state.income)
    monthly_expenses = get_monthly_data(st.session_state.expenses)
    monthly_savings = monthly_income - monthly_expenses
    savings_rate = (monthly_savings / monthly_income * 100) if monthly_income > 0 else 0
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Monthly Income", f"₹{monthly_income:,.2f}")
    with col2:
        st.metric("Monthly Expenses", f"₹{monthly_expenses:,.2f}")
    with col3:
        st.metric("Monthly Savings", f"₹{monthly_savings:,.2f}")
    with col4:
        st.metric("Savings Rate", f"{savings_rate:.1f}%")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        if not st.session_state.expenses.empty:
            st.subheader("💳 Spending by Category")
            expenses_by_category = st.session_state.expenses.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(expenses_by_category, values='amount', names='category', 
                        title="Current Month Spending Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data available. Add some transactions to see the breakdown.")
    
    with col2:
        st.subheader("🎯 Savings Goals Progress")
        for goal in st.session_state.savings_goals:
            progress = min(goal['current'] / goal['target'], 1.0)
            st.write(f"**{goal['name']}**")
            st.progress(progress)
            st.write(f"₹{goal['current']:,} / ₹{goal['target']:,} ({progress*100:.1f}%)")
            st.write(f"Deadline: {goal['deadline']}")
            st.write("---")
    
    # AI Insights
    st.subheader("🤖 AI-Powered Insights")
    insights = generate_ai_insights()
    for insight in insights:
        st.info(insight)
    
    # Quick stats
    st.subheader("📈 Quick Stats")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not st.session_state.expenses.empty:
            largest_expense = st.session_state.expenses['amount'].max()
            st.metric("Largest Expense", f"₹{largest_expense:,.2f}")
    
    with col2:
        if not st.session_state.expenses.empty:
            most_frequent = st.session_state.expenses['category'].mode().iloc[0] if not st.session_state.expenses.empty else "N/A"
            st.metric("Most Frequent Category", most_frequent)
    
    with col3:
        # Days until next salary (assuming monthly salary on 1st)
        today = datetime.now()
        if today.day == 1:
            days_until_salary = 0
        else:
            next_month = today.replace(day=1) + timedelta(days=32)
            next_salary = next_month.replace(day=1)
            days_until_salary = (next_salary - today).days
        st.metric("Days Until Next Salary", days_until_salary)

# Add transaction page (modified to include delete buttons)
def add_transaction_page():
    st.header("💳 Add Transaction")
    
    tab1, tab2 = st.tabs(["Add Expense", "Add Income"])
    
    with tab1:
        st.subheader("➖ Add Expense")
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            with col1:
                expense_date = st.date_input("Date", datetime.now())
                expense_category = st.selectbox("Category", EXPENSE_CATEGORIES)
            with col2:
                expense_amount = st.number_input("Amount (₹)", min_value=0.01, step=0.01)
                expense_description = st.text_input("Description (Optional)")
            
            if st.form_submit_button("Add Expense"):
                add_expense(expense_date, expense_category, expense_amount, expense_description)
                st.success(f"Added expense: ₹{expense_amount} for {expense_category}")
                st.rerun()
    
    with tab2:
        st.subheader("➕ Add Income")
        with st.form("income_form"):
            col1, col2 = st.columns(2)
            with col1:
                income_date = st.date_input("Date", datetime.now(), key="income_date")
                income_source = st.selectbox("Source", INCOME_SOURCES)
            with col2:
                income_amount = st.number_input("Amount (₹)", min_value=0.01, step=0.01, key="income_amount")
                income_frequency = st.selectbox("Frequency", ["One-time", "Monthly", "Weekly", "Yearly"])
            
            if st.form_submit_button("Add Income"):
                add_income(income_date, income_source, income_amount, income_frequency)
                st.success(f"Added income: ₹{income_amount} from {income_source}")
                st.rerun()
    
    # Recent transactions
    st.subheader("📝 Recent Transactions")
    
    if not st.session_state.expenses.empty or not st.session_state.income.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Recent Expenses**")
            if not st.session_state.expenses.empty:
                recent_expenses = st.session_state.expenses.tail(5).copy()
                if 'date' in recent_expenses.columns:
                    recent_expenses['date'] = recent_expenses['date'].astype(str)
                for idx, row in recent_expenses.iterrows():
                    st.write(row)
                    if st.button(f"Delete Expense {idx}", key=f"del_exp_{idx}"):
                        st.session_state.expenses.drop(idx, inplace=True)
                        st.session_state.expenses.reset_index(drop=True, inplace=True)
                        if st.session_state.get('mongodb_available', False) and 'db_connection' in st.session_state:
                            save_user_data(st.session_state.db_connection, st.session_state.user_id)
                        st.success("Expense deleted!")
                        st.rerun()
            else:
                st.info("No expenses recorded yet.")
        
        with col2:
            st.write("**Recent Income**")
            if not st.session_state.income.empty:
                recent_income = st.session_state.income.tail(5).copy()
                if 'date' in recent_income.columns:
                    recent_income['date'] = recent_income['date'].astype(str)
                for idx, row in recent_income.iterrows():
                    st.write(row)
                    if st.button(f"Delete Income {idx}", key=f"del_inc_{idx}"):
                        st.session_state.income.drop(idx, inplace=True)
                        st.session_state.income.reset_index(drop=True, inplace=True)
                        if st.session_state.get('mongodb_available', False) and 'db_connection' in st.session_state:
                            save_user_data(st.session_state.db_connection, st.session_state.user_id)
                        st.success("Income deleted!")
                        st.rerun()
            else:
                st.info("No income recorded yet.")

# Budget page (modified to save to DB)
def budget_page():
    st.header("💰 Budget Management")
    
    # Current budget overview
    total_budget = sum(st.session_state.budget.values())
    monthly_expenses = get_monthly_data(st.session_state.expenses)
    remaining_budget = total_budget - monthly_expenses
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Budget", f"₹{total_budget:,.2f}")
    with col2:
        st.metric("Total Spent", f"₹{monthly_expenses:,.2f}")
    with col3:
        color = "normal" if remaining_budget >= 0 else "inverse"
        st.metric("Remaining", f"₹{remaining_budget:,.2f}", delta=None)
    
    # Budget by category
    st.subheader("📊 Budget vs Actual Spending")
    
    if not st.session_state.expenses.empty:
        expenses_by_category = st.session_state.expenses.groupby('category')['amount'].sum().to_dict()
    else:
        expenses_by_category = {}
    
    budget_data = []
    for category, budget_amount in st.session_state.budget.items():
        spent = expenses_by_category.get(category, 0)
        remaining = budget_amount - spent
        budget_data.append({
            'Category': category,
            'Budget': budget_amount,
            'Spent': spent,
            'Remaining': remaining,
            'Usage %': (spent / budget_amount * 100) if budget_amount > 0 else 0
        })
    
    budget_df = pd.DataFrame(budget_data)
    
    # Display budget progress bars
    for _, row in budget_df.iterrows():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{row['Category']}**")
            usage_pct = min(row['Usage %'] / 100, 1.0)
            st.progress(usage_pct)
            
            # Color coding based on usage
            if row['Usage %'] > 100:
                st.error(f"Over budget by ₹{abs(row['Remaining']):,.2f}")
            elif row['Usage %'] > 80:
                st.warning(f"₹{row['Remaining']:,.2f} remaining")
            else:
                st.success(f"₹{row['Remaining']:,.2f} remaining")
        
        with col2:
            st.metric("Budget", f"₹{row['Budget']:,.2f}")
        with col3:
            st.metric("Spent", f"₹{row['Spent']:,.2f}")
    
    # Edit budget section
    st.subheader("✏️ Edit Budget")
    with st.expander("Modify Budget Categories"):
        st.write("Adjust your budget for each category:")
        new_budget = {}
        
        col1, col2 = st.columns(2)
        categories = list(st.session_state.budget.keys())
        mid_point = len(categories) // 2
        
        with col1:
            for category in categories[:mid_point]:
                new_budget[category] = st.number_input(
                    f"{category}", 
                    value=st.session_state.budget[category],
                    min_value=0,
                    step=100,
                    key=f"budget_{category}"
                )
        
        with col2:
            for category in categories[mid_point:]:
                new_budget[category] = st.number_input(
                    f"{category}", 
                    value=st.session_state.budget[category],
                    min_value=0,
                    step=100,
                    key=f"budget_{category}"
                )
        
        if st.button("Update Budget"):
            st.session_state.budget = new_budget
            # Use stored database connection
            if st.session_state.get('mongodb_available', False) and 'db_connection' in st.session_state:
                save_user_data(st.session_state.db_connection, st.session_state.user_id)
            st.success("Budget updated successfully!")
            st.rerun()

# Analytics page (remains the same)
def analytics_page():
    st.header("📈 Financial Analytics")
    
    if st.session_state.expenses.empty and st.session_state.income.empty:
        st.info("No data available for analysis. Please add some transactions first.")
        return
    
    # Time period selector
    time_period = st.selectbox("Select Time Period", ["Last 30 Days", "Last 3 Months", "Last 6 Months", "All Time"])
    
    # Spending trends
    if not st.session_state.expenses.empty:
        expenses_df = st.session_state.expenses.copy()
        expenses_df['date'] = pd.to_datetime(expenses_df['date'])
        
        st.subheader("💸 Spending Trends")
        
        # Daily spending trend
        daily_spending = expenses_df.groupby('date')['amount'].sum().reset_index()
        fig = px.line(daily_spending, x='date', y='amount', title="Daily Spending Trend")
        st.plotly_chart(fig, use_container_width=True)
        
        # Category analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Top Spending Categories")
            category_spending = expenses_df.groupby('category')['amount'].sum().sort_values(ascending=False)
            fig = px.bar(x=category_spending.index, y=category_spending.values, 
                        title="Spending by Category",
                        labels={'x': 'Category', 'y': 'Amount (₹)'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📅 Weekly Spending Pattern")
            expenses_df['day_of_week'] = expenses_df['date'].dt.day_name()
            weekly_pattern = expenses_df.groupby('day_of_week')['amount'].sum()
            # Reorder days
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_pattern = weekly_pattern.reindex(day_order, fill_value=0)
            
            fig = px.bar(x=weekly_pattern.index, y=weekly_pattern.values,
                        title="Spending by Day of Week")
            st.plotly_chart(fig, use_container_width=True)
    
    # Income vs Expenses comparison
    if not st.session_state.income.empty and not st.session_state.expenses.empty:
        st.subheader("💰 Income vs Expenses")
        
        income_df = st.session_state.income.copy()
        income_df['date'] = pd.to_datetime(income_df['date'])
        
        # Monthly comparison
        expenses_monthly = expenses_df.groupby(expenses_df['date'].dt.to_period('M'))['amount'].sum()
        income_monthly = income_df.groupby(income_df['date'].dt.to_period('M'))['amount'].sum()
        
        comparison_df = pd.DataFrame({
            'Month': expenses_monthly.index.astype(str),
            'Expenses': expenses_monthly.values,
            'Income': income_monthly.reindex(expenses_monthly.index, fill_value=0).values
        })
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Income', x=comparison_df['Month'], y=comparison_df['Income']))
        fig.add_trace(go.Bar(name='Expenses', x=comparison_df['Month'], y=comparison_df['Expenses']))
        fig.update_layout(title="Monthly Income vs Expenses", barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    
    # Financial health metrics
    st.subheader("🏥 Financial Health Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_daily_spend = expenses_df['amount'].sum() / max(len(expenses_df['date'].unique()), 1) if not expenses_df.empty else 0
        st.metric("Average Daily Spend", f"₹{avg_daily_spend:.2f}")
    
    with col2:
        monthly_income = get_monthly_data(st.session_state.income)
        monthly_expenses = get_monthly_data(st.session_state.expenses)
        savings_rate = ((monthly_income - monthly_expenses) / monthly_income * 100) if monthly_income > 0 else 0
        st.metric("Current Savings Rate", f"{savings_rate:.1f}%")
    
    with col3:
        if not expenses_df.empty:
            largest_expense = expenses_df['amount'].max()
            st.metric("Largest Single Expense", f"₹{largest_expense:.2f}")

# Profile page (modified to save to DB)
def profile_page():
    st.header("👤 User Profile")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://via.placeholder.com/150", caption="Profile Picture")
        if st.button("Upload New Picture"):
            st.info("Photo upload feature would be implemented here")
    
    with col2:
        st.subheader("Profile Information")
        
        with st.form("profile_form"):
            name = st.text_input("Name", value=st.session_state.user_profile['name'])
            email = st.text_input("Email", value=st.session_state.user_profile['email'], disabled=True)
            member_since = st.text_input("Member Since", value=st.session_state.user_profile['member_since'], disabled=True)
            
            if st.form_submit_button("Update Profile"):
                st.session_state.user_profile['name'] = name
                # Use stored database connection
                if st.session_state.get('mongodb_available', False) and 'db_connection' in st.session_state:
                    save_user_data(st.session_state.db_connection, st.session_state.user_id)
                st.success("Profile updated successfully!")
    
    # Account statistics
    st.subheader("📊 Account Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_transactions = len(st.session_state.expenses) + len(st.session_state.income)
        st.metric("Total Transactions", total_transactions)
    
    with col2:
        total_expenses = st.session_state.expenses['amount'].sum() if not st.session_state.expenses.empty else 0
        st.metric("Total Expenses", f"₹{total_expenses:,.2f}")
    
    with col3:
        total_income = st.session_state.income['amount'].sum() if not st.session_state.income.empty else 0
        st.metric("Total Income", f"₹{total_income:,.2f}")
    
    with col4:
        net_worth = total_income - total_expenses
        st.metric("Net Position", f"₹{net_worth:,.2f}")

if __name__ == "__main__":
    main()