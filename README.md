# Financial Management System

A comprehensive financial management system for managing LLC and personal finances with automated workflows, bank integrations, and corporate veil preservation.

## 🚀 Features

### Core Functionality
- **Multi-Entity Management**: Separate tracking for personal and LLC finances
- **Bank Integration**: Connect to 11,000+ financial institutions via Plaid
- **Visual Workflow Builder**: Drag-and-drop interface for creating money flows
- **Corporate Veil Preservation**: Automatic documentation of inter-entity transfers
- **Zero-Based Budgeting**: Every dollar accounted for with envelope budgeting
- **Automated Bill Pay**: Schedule and automate recurring payments
- **Real-time Sync**: Live updates of account balances and transactions

### Technical Features
- **Secure Authentication**: Supabase Auth with MFA support
- **Row Level Security**: Data isolation at the database level
- **Serverless Architecture**: Edge functions for API endpoints
- **Real-time Updates**: WebSocket connections for live data
- **Mobile Responsive**: Works on all devices

## 🏗️ Architecture

### Backend
- **Database**: PostgreSQL (via Supabase)
- **Authentication**: Supabase Auth
- **API**: Supabase Edge Functions
- **File Storage**: Supabase Storage
- **Bank Integration**: Plaid API

### Frontend
- **Framework**: React with TypeScript
- **UI Library**: Material-UI
- **State Management**: Zustand
- **Workflow Builder**: React Flow
- **Hosting**: AWS Amplify

### Infrastructure
- **Primary Platform**: Supabase (BaaS)
- **Frontend Hosting**: AWS Amplify
- **Scheduled Tasks**: AWS Lambda + EventBridge
- **Secrets Management**: AWS Secrets Manager

## 📁 Project Structure

```
financeproj/
├── config/              # Configuration files
├── docs/               # Documentation
│   ├── ARCHITECTURE.md
│   ├── SUPABASE_AMPLIFY_ARCHITECTURE.md
│   └── SETUP_GUIDE.md
├── frontend/           # React application
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── pages/
│   └── package.json
├── supabase/          # Supabase configuration
│   ├── functions/     # Edge functions
│   └── migrations/    # Database migrations
├── lambda/            # AWS Lambda functions
└── README.md
```

## 🚦 Getting Started

### Prerequisites
- **macOS** (tested on macOS 12+)
- **Node.js 18+** and npm/yarn
- **Git** (usually pre-installed on macOS)
- **AWS Account**
- **Supabase Account**
- **Plaid Account** (for bank connections)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd financeproj
   ```

2. **Set up Supabase**
   - Create a new Supabase project
   - Run the database migration
   - Deploy edge functions using Supabase CLI

3. **Configure Frontend**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   # Edit .env.local with your credentials
   ```

4. **Deploy to AWS Amplify**
   ```bash
   amplify init
   amplify publish
   ```

See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed macOS-specific instructions.

## 💡 Use Cases

### Personal Finance
- Track income and expenses across multiple accounts
- Automate savings and investment transfers
- Manage bills and subscriptions
- Prepare for taxes with categorized transactions

### LLC Management
- Maintain clear separation between business and personal finances
- Document all inter-entity transfers
- Track business expenses and income
- Generate reports for accounting

### Workflow Examples
1. **Income Distribution**: Automatically split paycheck into taxes, savings, and expenses
2. **Bill Payment**: Schedule payments before due dates
3. **Investment Automation**: Transfer excess funds to investment accounts
4. **Tax Preparation**: Separate and categorize deductible expenses

## 🔒 Security

- **Authentication**: Secure login with MFA option
- **Encryption**: Sensitive data encrypted at rest
- **RLS Policies**: Database-level access control
- **API Security**: Rate limiting and CORS protection
- **Audit Trail**: Complete history of all transactions

## 💰 Cost Estimate

For personal use:
- **Supabase**: Free tier (500MB database, 2GB bandwidth)
- **AWS Amplify**: ~$5-10/month
- **Plaid**: Free development account (100 Items)
- **Total**: ~$5-10/month

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Supabase & Amplify Architecture](docs/SUPABASE_AMPLIFY_ARCHITECTURE.md)
- [Setup Guide](docs/SETUP_GUIDE.md) - **macOS-specific instructions**
- [Workflow Examples](docs/WORKFLOW_EXAMPLES.md)

## 🛠️ Development

### Local Development
```bash
# Backend (Supabase)
supabase start

# Frontend
cd frontend
npm start
```

### Testing
```bash
# Run tests
npm test

# E2E tests
npm run test:e2e
```

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome!

## 📄 License

This project is for personal use. Please create your own instance rather than using someone else's deployment.

## ⚠️ Disclaimer

This software is provided as-is for personal financial management. Always consult with financial and legal professionals for advice specific to your situation. The corporate veil preservation features are tools to help maintain proper documentation but do not constitute legal advice. 