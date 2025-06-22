# Financial Management System - Setup Guide

This guide will walk you through setting up your personal financial management system using Supabase and AWS Amplify.

## Prerequisites

- Node.js 16+ and npm/yarn
- Git
- AWS Account
- Supabase Account
- Plaid Account (for bank connections)

## Step 1: Supabase Setup

### 1.1 Create Supabase Project

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Create a new project
3. Save your project URL and anon key

### 1.2 Configure Database

1. Go to SQL Editor in Supabase Dashboard
2. Run the migration script:
```sql
-- Copy and paste the contents of supabase/migrations/001_initial_schema.sql
```

### 1.3 Enable Authentication

1. Go to Authentication > Providers
2. Enable Email authentication
3. Configure email templates for better UX

### 1.4 Set up Storage Buckets

1. Go to Storage
2. Create a bucket called `attachments` for transaction attachments
3. Set up RLS policies:
```sql
-- Allow users to upload to their own folder
CREATE POLICY "Users can upload attachments" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'attachments' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Allow users to view their own attachments
CREATE POLICY "Users can view own attachments" ON storage.objects
FOR SELECT USING (bucket_id = 'attachments' AND auth.uid()::text = (storage.foldername(name))[1]);
```

### 1.5 Deploy Edge Functions

1. Install Supabase CLI:
```bash
npm install -g supabase
```

2. Link your project:
```bash
supabase link --project-ref your-project-ref
```

3. Set up environment variables:
```bash
supabase secrets set PLAID_CLIENT_ID=your_plaid_client_id
supabase secrets set PLAID_SECRET=your_plaid_secret
supabase secrets set PLAID_ENV=sandbox
```

4. Deploy functions:
```bash
supabase functions deploy plaid-link
supabase functions deploy inter-entity-transfer
```

## Step 2: Plaid Setup

### 2.1 Create Plaid Account

1. Sign up at [https://dashboard.plaid.com](https://dashboard.plaid.com)
2. Get your client ID and secret
3. For personal use, you can use Development mode (100 free Items)

### 2.2 Configure Plaid

1. Add redirect URI: `https://your-app-domain.com/plaid-redirect`
2. Configure webhook URL: `https://your-project-ref.supabase.co/functions/v1/plaid-webhook`

## Step 3: Frontend Setup

### 3.1 Initialize React App

```bash
npx create-react-app finance-app --template typescript
cd finance-app
```

### 3.2 Install Dependencies

```bash
npm install @supabase/supabase-js @supabase/auth-helpers-react
npm install reactflow @mui/material @emotion/react @emotion/styled
npm install react-plaid-link @tanstack/react-query zustand
npm install react-router-dom recharts date-fns
```

### 3.3 Configure Environment Variables

Create `.env.local`:
```env
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
REACT_APP_PLAID_PUBLIC_KEY=your_plaid_public_key
REACT_APP_PLAID_ENV=sandbox
```

### 3.4 Set up Supabase Client

Create `src/lib/supabase.ts`:
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL!
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

## Step 4: AWS Amplify Setup

### 4.1 Install Amplify CLI

```bash
npm install -g @aws-amplify/cli
amplify configure
```

### 4.2 Initialize Amplify

```bash
amplify init
```

Choose:
- Name: finance-app
- Environment: prod
- Default editor: Visual Studio Code
- App type: JavaScript
- Framework: React
- Source Directory: src
- Distribution Directory: build
- Build Command: npm run build
- Start Command: npm start

### 4.3 Add Hosting

```bash
amplify add hosting
```

Choose:
- Hosting with Amplify Console
- Continuous deployment (Git-based)

### 4.4 Create amplify.yml

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
```

### 4.5 Deploy

```bash
amplify publish
```

## Step 5: AWS Lambda Functions (Optional)

For complex workflows and scheduled tasks:

### 5.1 Create Lambda Functions

Create `lambda/workflow-scheduler/index.js`:
```javascript
const { createClient } = require('@supabase/supabase-js')

exports.handler = async (event) => {
    const supabase = createClient(
        process.env.SUPABASE_URL,
        process.env.SUPABASE_SERVICE_KEY
    )
    
    // Get active workflows
    const { data: workflows } = await supabase
        .from('workflows')
        .select('*')
        .eq('status', 'active')
        .eq('trigger_type', 'schedule')
    
    // Execute workflows
    for (const workflow of workflows) {
        // Trigger workflow execution
        await supabase.functions.invoke('workflow-execute', {
            body: { workflowId: workflow.id }
        })
    }
    
    return { statusCode: 200 }
}
```

### 5.2 Deploy with SAM

Create `template.yaml`:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 300
    MemorySize: 512
    Environment:
      Variables:
        SUPABASE_URL: !Ref SupabaseUrl
        SUPABASE_SERVICE_KEY: !Ref SupabaseServiceKey

Parameters:
  SupabaseUrl:
    Type: String
  SupabaseServiceKey:
    Type: String
    NoEcho: true

Resources:
  WorkflowScheduler:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambda/workflow-scheduler/
      Handler: index.handler
      Runtime: nodejs18.x
      Events:
        Schedule:
          Type: Schedule
          Properties:
            Schedule: rate(5 minutes)
```

Deploy:
```bash
sam deploy --guided
```

## Step 6: Initial Configuration

### 6.1 Create Your First Entity

1. Sign up/Login to your app
2. Go to Settings > Entities
3. Create your personal entity
4. Create your LLC entity

### 6.2 Connect Bank Accounts

1. Go to Accounts
2. Click "Connect Bank Account"
3. Follow Plaid Link flow
4. Select accounts to sync

### 6.3 Create Your First Workflow

1. Go to Workflows
2. Click "Create Workflow"
3. Design your money flow:
   - Add income source
   - Add splits for taxes, savings, expenses
   - Add conditions for different scenarios
   - Save and activate

## Security Best Practices

1. **Enable MFA**: Go to Supabase Auth settings and enable MFA
2. **Use Environment Variables**: Never commit secrets to Git
3. **Regular Backups**: Set up automated database backups in Supabase
4. **Monitor Usage**: Set up alerts for unusual activity
5. **Update Dependencies**: Regularly update all packages

## Troubleshooting

### Common Issues

1. **Plaid Connection Failed**
   - Check API keys are correct
   - Ensure you're using the right environment (sandbox/development)
   - Verify webhook URL is accessible

2. **Supabase RLS Errors**
   - Check user is authenticated
   - Verify RLS policies are correct
   - Use Supabase Dashboard to test queries

3. **Amplify Build Failures**
   - Check environment variables are set
   - Verify build command is correct
   - Check CloudWatch logs for details

### Support Resources

- Supabase Discord: [https://discord.supabase.com](https://discord.supabase.com)
- AWS Amplify Forums: [https://forum.amplify.aws](https://forum.amplify.aws)
- Plaid Support: [https://support.plaid.com](https://support.plaid.com)

## Next Steps

1. Set up automated bill payments
2. Configure tax estimation workflows
3. Create financial reports and dashboards
4. Set up data export for tax preparation
5. Implement investment tracking

## Cost Monitoring

Keep track of your usage:
- Supabase Dashboard > Usage
- AWS Cost Explorer
- Set up billing alerts

Expected costs for personal use:
- Supabase: Free tier should cover personal use
- AWS Amplify: ~$5-10/month
- Plaid: Free for development (100 Items)