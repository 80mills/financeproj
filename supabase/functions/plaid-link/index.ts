// Supabase Edge Function for Plaid Link Integration
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { Configuration, PlaidApi, PlaidEnvironments } from 'https://esm.sh/plaid@12.0.0'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        global: {
          headers: { Authorization: req.headers.get('Authorization')! },
        },
      }
    )

    const { data: { user } } = await supabaseClient.auth.getUser()
    if (!user) throw new Error('Not authenticated')

    const configuration = new Configuration({
      basePath: PlaidEnvironments[Deno.env.get('PLAID_ENV') || 'sandbox'],
      baseOptions: {
        headers: {
          'PLAID-CLIENT-ID': Deno.env.get('PLAID_CLIENT_ID'),
          'PLAID-SECRET': Deno.env.get('PLAID_SECRET'),
        },
      },
    })

    const plaidClient = new PlaidApi(configuration)
    const { action } = await req.json()

    switch (action) {
      case 'create_link_token': {
        const { entity_id } = await req.json()
        
        // Verify user owns the entity
        const { data: entity } = await supabaseClient
          .from('entities')
          .select('id')
          .eq('id', entity_id)
          .eq('user_id', user.id)
          .single()
          
        if (!entity) throw new Error('Entity not found')

        const request = {
          user: {
            client_user_id: user.id,
          },
          client_name: 'Financial Management System',
          products: ['transactions', 'accounts', 'liabilities'],
          country_codes: ['US'],
          language: 'en',
          webhook: `${Deno.env.get('SUPABASE_URL')}/functions/v1/plaid-webhook`,
          redirect_uri: `${Deno.env.get('APP_URL')}/plaid-redirect`,
        }

        const response = await plaidClient.linkTokenCreate(request)
        
        return new Response(
          JSON.stringify({ link_token: response.data.link_token }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      case 'exchange_public_token': {
        const { public_token, entity_id, account_name } = await req.json()
        
        // Exchange public token for access token
        const tokenResponse = await plaidClient.itemPublicTokenExchange({
          public_token,
        })
        
        const access_token = tokenResponse.data.access_token
        const item_id = tokenResponse.data.item_id
        
        // Get account details
        const accountsResponse = await plaidClient.accountsGet({
          access_token,
        })
        
        // Store accounts in database
        const accounts = accountsResponse.data.accounts.map(account => ({
          entity_id,
          name: account_name || account.name,
          account_type: mapPlaidAccountType(account.type),
          institution_name: accountsResponse.data.item.institution_id,
          account_number_masked: account.mask,
          current_balance: account.balances.current,
          available_balance: account.balances.available,
          plaid_account_id: account.account_id,
          plaid_item_id: item_id,
          plaid_access_token: access_token, // Should be encrypted in production
          is_manual: false,
        }))
        
        const { data: insertedAccounts, error } = await supabaseClient
          .from('accounts')
          .insert(accounts)
          .select()
          
        if (error) throw error
        
        // Sync initial transactions
        await syncTransactions(supabaseClient, plaidClient, access_token, entity_id, insertedAccounts)
        
        return new Response(
          JSON.stringify({ accounts: insertedAccounts }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      default:
        throw new Error('Invalid action')
    }
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})

function mapPlaidAccountType(plaidType: string): string {
  const mapping: Record<string, string> = {
    'depository': 'checking',
    'credit': 'credit_card',
    'loan': 'loan',
    'investment': 'investment',
  }
  return mapping[plaidType] || 'checking'
}

async function syncTransactions(
  supabaseClient: any,
  plaidClient: any,
  access_token: string,
  entity_id: string,
  accounts: any[]
) {
  const startDate = new Date()
  startDate.setDate(startDate.getDate() - 90) // Get 90 days of history
  
  const request = {
    access_token,
    start_date: startDate.toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
  }
  
  const response = await plaidClient.transactionsGet(request)
  const transactions = response.data.transactions
  
  // Map Plaid transactions to our schema
  const mappedTransactions = transactions.map(transaction => {
    const account = accounts.find(a => a.plaid_account_id === transaction.account_id)
    return {
      entity_id,
      account_id: account?.id,
      transaction_type: transaction.amount > 0 ? 'debit' : 'credit',
      amount: Math.abs(transaction.amount),
      transaction_date: transaction.date,
      posted_date: transaction.authorized_date,
      description: transaction.name,
      merchant_name: transaction.merchant_name,
      category: transaction.category?.[0],
      subcategory: transaction.category?.[1],
      plaid_transaction_id: transaction.transaction_id,
      is_pending: transaction.pending,
      import_source: 'plaid',
      imported_at: new Date().toISOString(),
    }
  })
  
  // Insert transactions
  await supabaseClient
    .from('transactions')
    .upsert(mappedTransactions, { onConflict: 'plaid_transaction_id' })
}