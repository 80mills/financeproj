// Supabase Edge Function for Inter-Entity Transfers
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface TransferRequest {
  from_account_id: string
  to_account_id: string
  amount: number
  transfer_type: string
  description: string
  transaction_date?: string
  notes?: string
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

    const transferRequest: TransferRequest = await req.json()
    const {
      from_account_id,
      to_account_id,
      amount,
      transfer_type,
      description,
      transaction_date = new Date().toISOString(),
      notes
    } = transferRequest

    // Validate amount
    if (amount <= 0) {
      throw new Error('Transfer amount must be positive')
    }

    // Get both accounts with their entities
    const { data: fromAccount } = await supabaseClient
      .from('accounts')
      .select('*, entity:entities(*)')
      .eq('id', from_account_id)
      .single()

    const { data: toAccount } = await supabaseClient
      .from('accounts')
      .select('*, entity:entities(*)')
      .eq('id', to_account_id)
      .single()

    if (!fromAccount || !toAccount) {
      throw new Error('Invalid account IDs')
    }

    // Verify user owns both entities
    if (fromAccount.entity.user_id !== user.id || toAccount.entity.user_id !== user.id) {
      throw new Error('Unauthorized: You do not own these accounts')
    }

    // Check if this is an inter-entity transfer
    const isInterEntity = fromAccount.entity_id !== toAccount.entity_id

    // Validate transfer type for inter-entity transfers
    if (isInterEntity && !isValidInterEntityTransferType(transfer_type)) {
      throw new Error('Invalid inter-entity transfer type')
    }

    // Check sufficient balance
    if (fromAccount.available_balance < amount) {
      throw new Error('Insufficient funds')
    }

    // Begin transaction
    const transactionId1 = crypto.randomUUID()
    const transactionId2 = crypto.randomUUID()

    // Create withdrawal transaction
    const withdrawalTransaction = {
      id: transactionId1,
      entity_id: fromAccount.entity_id,
      account_id: from_account_id,
      transaction_type: 'debit',
      amount: amount,
      transaction_date: transaction_date,
      description: isInterEntity 
        ? `${transfer_type.replace(/_/g, ' ').toUpperCase()}: ${description}`
        : `Transfer to ${toAccount.name}: ${description}`,
      category: isInterEntity ? 'Inter-Entity Transfer' : 'Transfer',
      is_inter_entity: isInterEntity,
      inter_entity_type: isInterEntity ? transfer_type : null,
      related_transaction_id: transactionId2,
      related_entity_id: isInterEntity ? toAccount.entity_id : null,
      notes: notes,
      import_source: 'manual',
      imported_at: new Date().toISOString()
    }

    // Create deposit transaction
    const depositTransaction = {
      id: transactionId2,
      entity_id: toAccount.entity_id,
      account_id: to_account_id,
      transaction_type: 'credit',
      amount: amount,
      transaction_date: transaction_date,
      description: isInterEntity
        ? `${transfer_type.replace(/_/g, ' ').toUpperCase()}: ${description}`
        : `Transfer from ${fromAccount.name}: ${description}`,
      category: isInterEntity ? 'Inter-Entity Transfer' : 'Transfer',
      is_inter_entity: isInterEntity,
      inter_entity_type: isInterEntity ? transfer_type : null,
      related_transaction_id: transactionId1,
      related_entity_id: isInterEntity ? fromAccount.entity_id : null,
      notes: notes,
      import_source: 'manual',
      imported_at: new Date().toISOString()
    }

    // Insert both transactions
    const { error: txError } = await supabaseClient
      .from('transactions')
      .insert([withdrawalTransaction, depositTransaction])

    if (txError) throw txError

    // Update account balances
    const { error: updateError1 } = await supabaseClient
      .from('accounts')
      .update({
        current_balance: fromAccount.current_balance - amount,
        available_balance: fromAccount.available_balance - amount,
        last_synced: new Date().toISOString()
      })
      .eq('id', from_account_id)

    if (updateError1) throw updateError1

    const { error: updateError2 } = await supabaseClient
      .from('accounts')
      .update({
        current_balance: toAccount.current_balance + amount,
        available_balance: toAccount.available_balance + amount,
        last_synced: new Date().toISOString()
      })
      .eq('id', to_account_id)

    if (updateError2) throw updateError2

    // Create audit log entry for inter-entity transfers
    if (isInterEntity) {
      await createAuditLog(supabaseClient, {
        user_id: user.id,
        action: 'inter_entity_transfer',
        entity_from: fromAccount.entity.name,
        entity_to: toAccount.entity.name,
        transfer_type: transfer_type,
        amount: amount,
        transaction_ids: [transactionId1, transactionId2],
        metadata: {
          from_account: fromAccount.name,
          to_account: toAccount.name,
          description: description,
          notes: notes
        }
      })
    }

    return new Response(
      JSON.stringify({
        success: true,
        transactions: [withdrawalTransaction, depositTransaction],
        message: isInterEntity 
          ? `Inter-entity transfer completed. Type: ${transfer_type.replace(/_/g, ' ')}`
          : 'Transfer completed successfully'
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

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

function isValidInterEntityTransferType(type: string): boolean {
  const validTypes = [
    'equity_contribution',
    'owner_draw',
    'distribution',
    'loan_to_entity',
    'loan_from_entity',
    'expense_reimbursement'
  ]
  return validTypes.includes(type)
}

async function createAuditLog(supabaseClient: any, logData: any) {
  // In a production system, you'd have a separate audit_logs table
  // For now, we'll store in a generic logs table or use Supabase's built-in logging
  console.log('Audit Log:', logData)
  
  // You could also send this to a separate logging service
  // or store in a dedicated audit table with encryption
}