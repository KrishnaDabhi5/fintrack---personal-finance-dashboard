# FinTrack - Personal Finance Dashboard

A comprehensive personal finance tracking application built with Streamlit, featuring expense tracking, income management, budget planning, and financial analytics.

## Features

- 💰 **Expense & Income Tracking**: Add and categorize your financial transactions
- 📊 **Dashboard**: Visual overview of your financial health
- 💳 **Budget Management**: Set and track budgets by category
- 📈 **Analytics**: Detailed spending analysis and trends
- 🎯 **Savings Goals**: Track progress towards financial goals
- 🤖 **AI Insights**: Smart recommendations based on your spending patterns
- 👤 **User Profiles**: Personalized experience with user authentication

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd krishna
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run connect.py
```

## MongoDB Setup (Optional)

The app can work with or without MongoDB:

### With MongoDB (Recommended for production):
1. Install MongoDB on your system
2. Start MongoDB service
3. The app will automatically connect to `mongodb://localhost:27017/`

### Without MongoDB:
The app will automatically fall back to session state storage (data persists only during the browser session).

## Environment Variables

You can configure MongoDB connection using environment variables:

```bash
export MONGODB_URI="mongodb://your-mongodb-host:27017/"
export MONGODB_DB_NAME="your_database_name"
```

## Deployment

### Streamlit Cloud
1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Deploy with the following settings:
   - Main file path: `connect.py`
   - Python version: 3.9+

### Local Deployment
```bash
streamlit run connect.py --server.port 8501 --server.address 0.0.0.0
```

## Usage

1. **Login**: Enter your email to start using the app
2. **Add Transactions**: Use the "Add Transaction" page to record expenses and income
3. **Set Budget**: Configure your monthly budget in the "Budget" section
4. **Track Progress**: Monitor your spending and savings goals on the dashboard
5. **Analyze**: Use the "Analytics" page to understand your spending patterns

## Data Storage

- **With MongoDB**: Data is permanently stored in MongoDB database
- **Without MongoDB**: Data is stored in browser session state (temporary)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License. 