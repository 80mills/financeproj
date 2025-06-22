-- Initial schema for Financial Management System

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
CREATE TYPE entity_type AS ENUM ('personal', 'business', 'llc', 'corporation');
CREATE TYPE account_type AS ENUM ('checking', 'savings', 'credit_card', 'loan', 'investment', 'cash');
CREATE TYPE transaction_type AS ENUM ('debit', 'credit', 'transfer');
CREATE TYPE workflow_status AS ENUM ('draft', 'active', 'paused', 'archived');
CREATE TYPE inter_entity_transfer_type AS ENUM (
    'equity_contribution',
    'owner_draw', 
    'distribution',
    'loan_to_entity',
    'loan_from_entity',
    'expense_reimbursement'
);

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
    entity_type entity_type NOT NULL,
    ein TEXT,
    business_name TEXT,
    business_address JSONB,
    formation_date DATE,
    state_of_formation TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX idx_entities_user_id ON public.entities(user_id);

-- Accounts
CREATE TABLE public.accounts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    account_type account_type NOT NULL,
    institution_name TEXT,
    account_number_masked TEXT,
    routing_number TEXT,
    current_balance DECIMAL(12,2) DEFAULT 0,
    available_balance DECIMAL(12,2) DEFAULT 0,
    credit_limit DECIMAL(12,2),
    minimum_payment DECIMAL(12,2),
    interest_rate DECIMAL(5,2),
    plaid_account_id TEXT UNIQUE,
    plaid_item_id TEXT,
    plaid_access_token TEXT, -- Will be encrypted
    is_active BOOLEAN DEFAULT true,
    is_manual BOOLEAN DEFAULT false,
    last_synced TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_accounts_entity_id ON public.accounts(entity_id);
CREATE INDEX idx_accounts_plaid_account_id ON public.accounts(plaid_account_id);

-- Transactions
CREATE TABLE public.transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE NOT NULL,
    account_id UUID REFERENCES public.accounts(id) ON DELETE CASCADE NOT NULL,
    transaction_type transaction_type NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    transaction_date TIMESTAMPTZ NOT NULL,
    posted_date TIMESTAMPTZ,
    description TEXT NOT NULL,
    merchant_name TEXT,
    category TEXT,
    subcategory TEXT,
    tags TEXT[] DEFAULT '{}',
    is_inter_entity BOOLEAN DEFAULT false,
    inter_entity_type inter_entity_transfer_type,
    related_transaction_id UUID REFERENCES public.transactions(id),
    related_entity_id UUID REFERENCES public.entities(id),
    workflow_execution_id UUID,
    plaid_transaction_id TEXT UNIQUE,
    bank_reference TEXT,
    check_number TEXT,
    is_pending BOOLEAN DEFAULT false,
    is_reconciled BOOLEAN DEFAULT false,
    is_recurring BOOLEAN DEFAULT false,
    notes TEXT,
    attachments JSONB DEFAULT '[]',
    imported_at TIMESTAMPTZ,
    import_source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_entity_id ON public.transactions(entity_id);
CREATE INDEX idx_transactions_account_id ON public.transactions(account_id);
CREATE INDEX idx_transactions_date ON public.transactions(transaction_date);
CREATE INDEX idx_transactions_entity_date ON public.transactions(entity_id, transaction_date);
CREATE INDEX idx_transactions_plaid_id ON public.transactions(plaid_transaction_id);

-- Workflows
CREATE TABLE public.workflows (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status workflow_status DEFAULT 'draft',
    configuration JSONB NOT NULL,
    trigger_type TEXT,
    trigger_config JSONB,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 300,
    version INTEGER DEFAULT 1,
    is_template BOOLEAN DEFAULT false,
    template_category TEXT,
    execution_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workflows_user_id ON public.workflows(user_id);
CREATE INDEX idx_workflows_status ON public.workflows(status);

-- Workflow executions
CREATE TABLE public.workflow_executions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id UUID REFERENCES public.workflows(id) ON DELETE CASCADE NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    error_message TEXT,
    triggered_by TEXT,
    trigger_details JSONB,
    input_data JSONB,
    output_data JSONB,
    node_executions JSONB DEFAULT '{}',
    total_duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workflow_executions_workflow_id ON public.workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON public.workflow_executions(status);

-- Budgets
CREATE TABLE public.budgets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    budget_type TEXT DEFAULT 'monthly',
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_budgets_entity_id ON public.budgets(entity_id);
CREATE INDEX idx_budgets_dates ON public.budgets(start_date, end_date);

-- Budget allocations
CREATE TABLE public.budget_allocations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    budget_id UUID REFERENCES public.budgets(id) ON DELETE CASCADE NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    allocated_amount DECIMAL(12,2) NOT NULL,
    spent_amount DECIMAL(12,2) DEFAULT 0,
    remaining_amount DECIMAL(12,2) GENERATED ALWAYS AS (allocated_amount - spent_amount) STORED,
    percentage DECIMAL(5,2),
    is_envelope BOOLEAN DEFAULT false,
    rollover_enabled BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_budget_allocations_budget_id ON public.budget_allocations(budget_id);

-- Bills
CREATE TABLE public.bills (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    account_id UUID REFERENCES public.accounts(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    payee TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    due_day INTEGER CHECK (due_day >= 1 AND due_day <= 31),
    frequency TEXT DEFAULT 'monthly',
    custom_frequency_days INTEGER,
    auto_pay_enabled BOOLEAN DEFAULT false,
    auto_pay_days_before INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    category TEXT,
    reminder_enabled BOOLEAN DEFAULT true,
    reminder_days_before INTEGER DEFAULT 3,
    account_number TEXT, -- Encrypted
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bills_account_id ON public.bills(account_id);

-- Bill payments
CREATE TABLE public.bill_payments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    bill_id UUID REFERENCES public.bills(id) ON DELETE CASCADE NOT NULL,
    amount_paid DECIMAL(12,2) NOT NULL,
    payment_date DATE NOT NULL,
    due_date DATE NOT NULL,
    transaction_id UUID REFERENCES public.transactions(id),
    status TEXT DEFAULT 'pending',
    payment_method TEXT,
    confirmation_number TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bill_payments_bill_id ON public.bill_payments(bill_id);
CREATE INDEX idx_bill_payments_status ON public.bill_payments(status);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budget_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bill_payments ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Users can only see and update their own profile
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Users can manage their own entities
CREATE POLICY "Users can manage own entities" ON public.entities
    FOR ALL USING (auth.uid() = user_id);

-- Users can manage accounts belonging to their entities
CREATE POLICY "Users can manage accounts in own entities" ON public.accounts
    FOR ALL USING (
        entity_id IN (
            SELECT id FROM public.entities WHERE user_id = auth.uid()
        )
    );

-- Users can manage transactions in their accounts
CREATE POLICY "Users can manage transactions in own accounts" ON public.transactions
    FOR ALL USING (
        entity_id IN (
            SELECT id FROM public.entities WHERE user_id = auth.uid()
        )
    );

-- Users can manage their own workflows
CREATE POLICY "Users can manage own workflows" ON public.workflows
    FOR ALL USING (auth.uid() = user_id);

-- Users can view workflow executions for their workflows
CREATE POLICY "Users can view own workflow executions" ON public.workflow_executions
    FOR SELECT USING (
        workflow_id IN (
            SELECT id FROM public.workflows WHERE user_id = auth.uid()
        )
    );

-- Users can manage budgets for their entities
CREATE POLICY "Users can manage budgets in own entities" ON public.budgets
    FOR ALL USING (
        entity_id IN (
            SELECT id FROM public.entities WHERE user_id = auth.uid()
        )
    );

-- Users can manage budget allocations for their budgets
CREATE POLICY "Users can manage budget allocations" ON public.budget_allocations
    FOR ALL USING (
        budget_id IN (
            SELECT b.id FROM public.budgets b
            JOIN public.entities e ON b.entity_id = e.id
            WHERE e.user_id = auth.uid()
        )
    );

-- Users can manage bills for their accounts
CREATE POLICY "Users can manage bills" ON public.bills
    FOR ALL USING (
        account_id IN (
            SELECT a.id FROM public.accounts a
            JOIN public.entities e ON a.entity_id = e.id
            WHERE e.user_id = auth.uid()
        )
    );

-- Users can manage bill payments
CREATE POLICY "Users can manage bill payments" ON public.bill_payments
    FOR ALL USING (
        bill_id IN (
            SELECT b.id FROM public.bills b
            JOIN public.accounts a ON b.account_id = a.id
            JOIN public.entities e ON a.entity_id = e.id
            WHERE e.user_id = auth.uid()
        )
    );

-- Functions for updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON public.entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON public.accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON public.transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON public.workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_executions_updated_at BEFORE UPDATE ON public.workflow_executions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_budgets_updated_at BEFORE UPDATE ON public.budgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_budget_allocations_updated_at BEFORE UPDATE ON public.budget_allocations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON public.bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bill_payments_updated_at BEFORE UPDATE ON public.bill_payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();