import os

# MongoDB Configuration
# Using the working MongoDB Atlas connection string
MONGODB_URI = 'mongodb+srv://krishnadabhi:krishnadabhi159@cluster0.kb8oner.mongodb.net/fintrack_db?retryWrites=true&w=majority&appName=Cluster0'
MONGODB_DB_NAME = 'fintrack_db'

# App Configuration
APP_TITLE = "FinTrack - Personal Finance Dashboard"
APP_ICON = "💰"

# Default budget categories
DEFAULT_BUDGET = {
    'Food': 5000, 'Transportation': 3000, 'Entertainment': 2000,
    'Shopping': 4000, 'Utilities': 2500, 'Medical': 1500,
    'Education': 2000, 'Miscellaneous': 1000
}

# Default savings goals
DEFAULT_SAVINGS_GOALS = [
    {'name': 'Emergency Fund', 'target': 50000, 'current': 15000, 'deadline': '2024-12-31'},
    {'name': 'Vacation', 'target': 25000, 'current': 8000, 'deadline': '2024-08-15'}
]

# Expense categories
EXPENSE_CATEGORIES = [
    'Food', 'Transportation', 'Entertainment', 'Shopping', 'Utilities',
    'Medical', 'Education', 'Rent', 'Mobile Recharge', 'Health',
    'Clothes', 'Electricity', 'Miscellaneous'
]

# Income sources
INCOME_SOURCES = [
    'Salary', 'Freelance', 'Rental Income', 'Investment Returns', 
    'Business', 'Gifts', 'Other'
] 