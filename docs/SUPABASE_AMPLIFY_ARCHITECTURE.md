# Financial Management System - Supabase & AWS Amplify Architecture

## Overview
Updated architecture leveraging Supabase for backend services and AWS Amplify for frontend hosting and deployment.

## Infrastructure Stack

### Backend - Supabase
- **Database**: PostgreSQL (managed by Supabase)
- **Authentication**: Supabase Auth (replaces custom JWT implementation)
- **Real-time**: Supabase Realtime for live updates
- **Storage**: Supabase Storage for file attachments
- **Edge Functions**: For serverless API endpoints
- **Row Level Security (RLS)**: For data access control

### Frontend - AWS Amplify
- **Hosting**: React application with CI/CD
- **Custom Domain**: Via Route 53
- **Environment Variables**: Secure configuration
- **Build Settings**: Automated builds from Git

### Additional AWS Services
- **Lambda Functions**: For complex workflows and Plaid integration
- **EventBridge**: For scheduled tasks
- **SQS**: For queue management
- **Secrets Manager**: For API keys (Plaid, etc.)

## Supabase Schema Design

### Database Tables (with RLS enabled)

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;

-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Entities (LLC and Personal)
CREATE TABLE public.entities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('personal', 'business', 'llc', 'corporation')),
    ein TEXT,
    business_name TEXT,
    business_address JSONB,
    formation_date DATE,
    state_of_formation TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Accounts
CREATE TABLE public.accounts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id UUID REFERENCES public.entities(id) NOT NULL,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    institution_name TEXT,
    account_number_masked TEXT,
    current_balance DECIMAL(12,2) DEFAULT 0,
    available_balance DECIMAL(12,2) DEFAULT 0,
    plaid_account_id TEXT UNIQUE,
    plaid_access_token TEXT, -- Encrypted
    is_active BOOLEAN DEFAULT true,
    last_synced TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions
CREATE TABLE public.transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id UUID REFERENCES public.entities(id) NOT NULL,
    account_id UUID REFERENCES public.accounts(id) NOT NULL,
    transaction_type TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    transaction_date TIMESTAMPTZ NOT NULL,
    description TEXT NOT NULL,
    category TEXT,
    is_inter_entity BOOLEAN DEFAULT false,
    inter_entity_type TEXT,
    related_transaction_id UUID REFERENCES public.transactions(id),
    plaid_transaction_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflows
CREATE TABLE public.workflows (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',
    configuration JSONB NOT NULL,
    trigger_type TEXT,
    trigger_config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Row Level Security Policies

```sql
-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

-- Users can only see their own entities
CREATE POLICY "Users can view own entities" ON public.entities
    FOR ALL USING (auth.uid() = user_id);

-- Users can only see accounts belonging to their entities
CREATE POLICY "Users can view own accounts" ON public.accounts
    FOR ALL USING (
        entity_id IN (
            SELECT id FROM public.entities WHERE user_id = auth.uid()
        )
    );

-- Similar policies for transactions, workflows, etc.
```

## API Architecture

### Supabase Edge Functions
Located in `supabase/functions/`:

1. **plaid-link**: Handle Plaid Link token exchange
2. **plaid-sync**: Sync transactions from Plaid
3. **workflow-execute**: Execute workflow logic
4. **inter-entity-transfer**: Handle transfers between entities
5. **bill-pay**: Process bill payments

### AWS Lambda Functions
For complex operations requiring more resources:

1. **workflow-scheduler**: Cron-based workflow execution
2. **bank-sync-processor**: Heavy transaction processing
3. **report-generator**: Financial report generation
4. **data-export**: Export data for taxes

## Frontend Architecture (React + TypeScript)

### Folder Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── accounts/
│   │   ├── transactions/
│   │   ├── workflows/
│   │   │   ├── WorkflowBuilder.tsx
│   │   │   ├── NodeTypes/
│   │   │   └── WorkflowCanvas.tsx
│   │   └── shared/
│   ├── hooks/
│   │   ├── useSupabase.ts
│   │   ├── useRealtime.ts
│   │   └── usePlaid.ts
│   ├── lib/
│   │   ├── supabase.ts
│   │   └── plaid.ts
│   ├── pages/
│   ├── styles/
│   └── types/
├── amplify.yml
└── package.json
```

### Key Libraries
- **@supabase/supabase-js**: Supabase client
- **@supabase/auth-helpers-react**: Auth helpers
- **react-flow**: For workflow builder
- **react-plaid-link**: Plaid integration
- **@tanstack/react-query**: Data fetching
- **zustand**: State management

## Deployment Configuration

### AWS Amplify Build Settings (amplify.yml)
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: build
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
  customHeaders:
    - pattern: '**/*'
      headers:
        - key: 'X-Frame-Options'
          value: 'DENY'
        - key: 'X-Content-Type-Options'
          value: 'nosniff'
```

### Environment Variables
- `REACT_APP_SUPABASE_URL`
- `REACT_APP_SUPABASE_ANON_KEY`
- `REACT_APP_PLAID_PUBLIC_KEY`
- `REACT_APP_PLAID_ENV`

## Security Considerations

### Supabase Security
1. **RLS Policies**: Strict row-level security
2. **API Keys**: Anon key for client, service key for server
3. **Secrets**: Store in environment variables
4. **Encryption**: Enable transparent column encryption for sensitive data

### AWS Security
1. **IAM Roles**: Least privilege access
2. **Secrets Manager**: For API keys
3. **VPC**: For Lambda functions if needed
4. **CloudWatch**: For monitoring and alerts

## Migration from Current Architecture

### Steps to Migrate:
1. **Set up Supabase Project**
   - Create project
   - Run migration scripts
   - Set up RLS policies

2. **Update Backend Code**
   - Replace SQLAlchemy with Supabase client
   - Convert auth to Supabase Auth
   - Move complex logic to Edge Functions

3. **Create Frontend**
   - Initialize React app
   - Integrate Supabase client
   - Build UI components

4. **Set up AWS Amplify**
   - Connect GitHub repo
   - Configure build settings
   - Set environment variables

5. **Deploy Lambda Functions**
   - Package functions
   - Deploy with SAM or CDK
   - Configure EventBridge rules

## Cost Optimization

### Supabase (Free tier includes):
- 500MB database
- 2GB bandwidth
- 50,000 monthly active users
- 1GB file storage

### AWS Amplify:
- Build minutes: 1000/month free
- Hosting: $0.15/GB served
- Lambda: 1M requests free/month

### Estimated Monthly Cost (Personal Use):
- Supabase: $0 (free tier)
- AWS Amplify: ~$5-10
- AWS Lambda: $0 (free tier)
- Total: ~$5-10/month

## Monitoring & Maintenance

### Supabase Dashboard
- Database metrics
- API usage
- Auth analytics
- Real-time connections

### AWS CloudWatch
- Lambda execution metrics
- Amplify build logs
- Error tracking
- Cost monitoring

### Application Monitoring
- Sentry for error tracking
- Google Analytics for usage
- Custom dashboards for financial metrics