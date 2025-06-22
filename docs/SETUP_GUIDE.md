# Financial Management System - Setup Guide

This guide will walk you through setting up your personal financial management system using Supabase and AWS Amplify on macOS.

## Prerequisites

- **macOS** (tested on macOS 12+)
- **Node.js 18+** and npm/yarn
- **Git** (usually pre-installed on macOS)
- **AWS Account**
- **Supabase Account**
- **Plaid Account** (for bank connections)

## Step 1: Supabase Setup

### 1.1 Create Supabase Project

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Sign up/Login and create a new project
3. Choose a region close to you for better performance
4. Save your project URL and anon key from Settings > API

### 1.2 Configure Database

1. Go to SQL Editor in Supabase Dashboard
2. Create a new query and run the migration script:
```sql
-- Copy and paste the contents of supabase/migrations/001_initial_schema.sql
-- This creates all tables, indexes, and RLS policies
```

3. Verify the migration by checking Tables in the Database section

### 1.3 Enable Authentication

1. Go to Authentication > Providers
2. Enable Email authentication
3. Configure email templates for better UX
4. Set up redirect URLs for your domain

### 1.4 Set up Storage Buckets

1. Go to Storage in Supabase Dashboard
2. Create a bucket called `attachments` for transaction attachments
3. Set up RLS policies in SQL Editor:
```sql
-- Allow users to upload to their own folder
CREATE POLICY "Users can upload attachments" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'attachments' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Allow users to view their own attachments
CREATE POLICY "Users can view own attachments" ON storage.objects
FOR SELECT USING (bucket_id = 'attachments' AND auth.uid()::text = (storage.foldername(name))[1]);
```

### 1.5 Install and Configure Supabase CLI

1. Install Supabase CLI using Homebrew (recommended):
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Supabase CLI
brew install supabase/tap/supabase
```

2. Alternative installation methods:
```bash
# Using npm (if you prefer)
npm install -g supabase

# Using curl
curl -fsSL https://supabase.com/install.sh | sh
```

3. Verify installation:
```bash
supabase --version
```

### 1.6 Link and Deploy Edge Functions

1. Get your project reference from Supabase Dashboard > Settings > General
2. Link your project:
```bash
supabase link --project-ref your-project-ref
```

3. Set up environment variables:
```bash
# Set Plaid credentials
supabase secrets set PLAID_CLIENT_ID=your_plaid_client_id
supabase secrets set PLAID_SECRET=your_plaid_secret
supabase secrets set PLAID_ENV=sandbox

# Set your app URL
supabase secrets set APP_URL=https://your-app-domain.com
```

4. Deploy the edge functions:
```bash
# Deploy Plaid integration function
supabase functions deploy plaid-link

# Deploy inter-entity transfer function
supabase functions deploy inter-entity-transfer
```

5. Verify deployment in Supabase Dashboard > Edge Functions

## Step 2: Plaid Setup

### 2.1 Create Plaid Account

1. Sign up at [https://dashboard.plaid.com](https://dashboard.plaid.com)
2. Complete the onboarding process
3. Get your client ID and secret from the dashboard
4. For personal use, you can use Development mode (100 free Items)

### 2.2 Configure Plaid for Your App

1. In Plaid Dashboard, go to Team Settings > API Keys
2. Add redirect URI: `https://your-app-domain.com/plaid-redirect`
3. Configure webhook URL: `https://your-project-ref.supabase.co/functions/v1/plaid-webhook`
4. Note your public key for frontend integration

## Step 3: Frontend Setup

### 3.1 Initialize React App

```bash
# Create a new React app with TypeScript
npx create-react-app finance-app --template typescript
cd finance-app

# Or if you prefer using the existing structure:
cd frontend
npm install
```

### 3.2 Install Dependencies

```bash
# Core dependencies
npm install @supabase/supabase-js @supabase/auth-helpers-react

# UI and workflow dependencies
npm install reactflow @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material @mui/x-date-pickers

# Data management and routing
npm install @tanstack/react-query zustand react-router-dom

# Plaid integration and utilities
npm install react-plaid-link date-fns recharts

# Form handling
npm install react-hook-form
```

### 3.3 Configure Environment Variables

Create `.env.local` in your frontend directory:
```env
# Supabase Configuration
REACT_APP_SUPABASE_URL=your_supabase_project_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key

# Plaid Configuration
REACT_APP_PLAID_PUBLIC_KEY=your_plaid_public_key
REACT_APP_PLAID_ENV=sandbox

# App Configuration
REACT_APP_APP_URL=http://localhost:3000
```

### 3.4 Set up Supabase Client

Create `src/lib/supabase.ts`:
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL!
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Optional: Add real-time subscriptions
export const realtime = supabase.channel('custom-all-channel')
  .on('postgres_changes', { event: '*', schema: 'public' }, payload => {
    console.log('Change received!', payload)
  })
  .subscribe()
```

### 3.5 Test Local Development

```bash
# Start the development server
npm start

# The app should open at http://localhost:3000
```

## Step 4: AWS Amplify Setup

### 4.1 Install AWS CLI and Amplify CLI

1. Install AWS CLI:
```bash
# Using Homebrew
brew install awscli

# Or download from AWS website
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

2. Install Amplify CLI:
```bash
npm install -g @aws-amplify/cli
```

3. Configure AWS credentials:
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, region, and output format
```

4. Configure Amplify:
```bash
amplify configure
# Follow the prompts to set up your AWS profile
```

### 4.2 Initialize Amplify in Your Project

```bash
# Navigate to your frontend directory
cd frontend

# Initialize Amplify
amplify init
```

Choose the following options:
- **Enter a name for the project**: `finance-app`
- **Enter a name for the environment**: `prod`
- **Choose your default editor**: `Visual Studio Code` (or your preferred editor)
- **Choose the type of app that you're building**: `javascript`
- **What JavaScript framework are you using**: `react`
- **Source Directory Path**: `src`
- **Distribution Directory Path**: `build`
- **Build Command**: `npm run build`
- **Start Command**: `npm start`
- **Do you want to use an AWS profile**: `Yes` (select your configured profile)

### 4.3 Add Hosting

```bash
amplify add hosting
```

Choose:
- **Select the plugin module to execute**: `Hosting with Amplify Console`
- **Choose a type**: `Manual deployment`

### 4.4 Create amplify.yml

Create `amplify.yml` in your project root:
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
        - key: 'Referrer-Policy'
          value: 'strict-origin-when-cross-origin'
```

### 4.5 Deploy to Amplify

```bash
# Push your changes to Amplify
amplify push

# Publish to hosting
amplify publish
```

## Step 5: AWS Lambda Functions (Optional)

For complex workflows and scheduled tasks:

### 5.1 Install AWS SAM CLI

```bash
# Install using Homebrew
brew install aws-sam-cli

# Verify installation
sam --version
```

### 5.2 Create Lambda Functions

Create the directory structure:
```bash
mkdir -p lambda/workflow-scheduler
```

Create `lambda/workflow-scheduler/index.js`:
```javascript
const { createClient } = require('@supabase/supabase-js')

exports.handler = async (event) => {
    const supabase = createClient(
        process.env.SUPABASE_URL,
        process.env.SUPABASE_SERVICE_KEY
    )
    
    try {
        // Get active workflows
        const { data: workflows, error } = await supabase
            .from('workflows')
            .select('*')
            .eq('status', 'active')
            .eq('trigger_type', 'schedule')
        
        if (error) throw error
        
        // Execute workflows
        for (const workflow of workflows) {
            console.log(`Executing workflow: ${workflow.name}`)
            
            // Trigger workflow execution via Supabase Edge Function
            await supabase.functions.invoke('workflow-execute', {
                body: { workflowId: workflow.id }
            })
        }
        
        return { 
            statusCode: 200,
            body: JSON.stringify({ message: 'Workflows processed successfully' })
        }
    } catch (error) {
        console.error('Error processing workflows:', error)
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        }
    }
}
```

### 5.3 Deploy with SAM

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
    Description: Supabase project URL
  SupabaseServiceKey:
    Type: String
    NoEcho: true
    Description: Supabase service role key

Resources:
  WorkflowScheduler:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambda/workflow-scheduler/
      Handler: index.handler
      Runtime: nodejs18.x
      Description: Scheduled workflow execution function
      Events:
        Schedule:
          Type: Schedule
          Properties:
            Schedule: rate(5 minutes)
            Name: WorkflowScheduler
            Description: Execute scheduled workflows every 5 minutes
```

Deploy:
```bash
# Build the SAM application
sam build

# Deploy with guided setup
sam deploy --guided

# Follow the prompts to enter your Supabase URL and service key
```

## Step 6: Initial Configuration

### 6.1 Create Your First Entity

1. Sign up/Login to your app
2. Go to Settings > Entities
3. Create your personal entity with type "personal"
4. Create your LLC entity with type "llc"
5. Add business details (EIN, formation date, etc.)

### 6.2 Connect Bank Accounts

1. Go to Accounts in your app
2. Click "Connect Bank Account"
3. Follow Plaid Link flow
4. Select accounts to sync
5. Verify transactions are importing correctly

### 6.3 Create Your First Workflow

1. Go to Workflows
2. Click "Create Workflow"
3. Design your money flow:
   - Add income source node
   - Add split nodes for taxes, savings, expenses
   - Add condition nodes for different scenarios
   - Connect nodes with edges
   - Save and activate the workflow

## Security Best Practices

1. **Enable MFA**: Go to Supabase Auth settings and enable MFA
2. **Use Environment Variables**: Never commit secrets to Git
3. **Regular Backups**: Set up automated database backups in Supabase
4. **Monitor Usage**: Set up alerts for unusual activity
5. **Update Dependencies**: Regularly update all packages
6. **Use HTTPS**: Always use HTTPS in production
7. **Limit API Access**: Use least privilege principle for AWS IAM roles

## Troubleshooting

### Common Issues

1. **Supabase CLI Issues**
   ```bash
   # If you get permission errors
   sudo chown -R $(whoami) ~/.supabase
   
   # If functions fail to deploy
   supabase functions deploy plaid-link --debug
   ```

2. **Plaid Connection Failed**
   - Check API keys are correct
   - Ensure you're using the right environment (sandbox/development)
   - Verify webhook URL is accessible
   - Check browser console for errors

3. **Supabase RLS Errors**
   - Check user is authenticated
   - Verify RLS policies are correct
   - Use Supabase Dashboard to test queries
   - Check browser network tab for failed requests

4. **Amplify Build Failures**
   - Check environment variables are set in Amplify Console
   - Verify build command is correct
   - Check CloudWatch logs for details
   - Ensure all dependencies are in package.json

5. **Local Development Issues**
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Delete node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   
   # Check for port conflicts
   lsof -ti:3000 | xargs kill -9
   ```

### Support Resources

- **Supabase**: [Discord](https://discord.supabase.com) | [Documentation](https://supabase.com/docs)
- **AWS Amplify**: [Forums](https://forum.amplify.aws) | [Documentation](https://docs.amplify.aws)
- **Plaid**: [Support](https://support.plaid.com) | [Documentation](https://plaid.com/docs)
- **React**: [Documentation](https://react.dev) | [Community](https://react.dev/community)

## Next Steps

1. Set up automated bill payments
2. Configure tax estimation workflows
3. Create financial reports and dashboards
4. Set up data export for tax preparation
5. Implement investment tracking
6. Add mobile responsiveness
7. Set up monitoring and alerts

## Cost Monitoring

Keep track of your usage:
- **Supabase Dashboard** > Usage
- **AWS Cost Explorer**
- **Plaid Dashboard** > Usage

Expected costs for personal use:
- **Supabase**: Free tier should cover personal use
- **AWS Amplify**: ~$5-10/month
- **Plaid**: Free for development (100 Items)
- **Total**: ~$5-10/month

## Development Workflow

```bash
# Daily development workflow
cd frontend
npm start                    # Start local development
# Make changes to code
git add .
git commit -m "feat: add new feature"
git push origin main        # Triggers Amplify build

# Deploy edge functions
supabase functions deploy function-name

# Check logs
supabase functions logs function-name
```
