from langchain.agents import Tool, create_react_agent, AgentExecutor
from financial_services.wallet_api import get_usr_wallet_data
from financial_services.transcation_api import get_all_trans_details, get_all_bills_detail
from financial_services.loan_api import get_loan_details
from financial_services.insurance_api import get_insurance_policy_info


def make_tool(fn, name, description, access_token, user_id):
    return Tool.from_function(
        func=lambda input: fn(input, access_token=access_token, user_id=user_id),
        name=name,
        description=description
    )

# make_tool(
#             func=get_all_bills_detail,
#             name="get_all_bills_detail",
#             description="Get current bill amount due, payment due dates, and past billing history. Use ONLY when user specifically asks about: 'current bill', 'bill amount', 'due date', 'how much to pay', 'bill history', 'monthly bills'. DO NOT use for balance or transaction queries."
#         ),

def register_tools(access_token, user_id):
    return [
        make_tool(
            get_usr_wallet_data, 
            "get_usr_wallet_data", 
            "Get user's wallet account summary including current balance, available credit limit, outstanding amount, unbilled charges, last bill amount, and next billing date. Use ONLY when user asks about current balance, credit limit, credit amount ,outstanding amount, or wallet summary. DO NOT use for transaction history or bill details.",
            access_token,
            user_id
        ),
        
        make_tool(
            get_all_trans_details,
            "get_all_trans_details",
            "Get complete transaction history showing all money credited, debited, transferred across wallet, insurance, and loan accounts with dates and amounts. Use when user asks about: 'how much credited/debited', 'transaction history', 'money movements', 'payment records', 'all transactions'. This is the PRIMARY tool for transaction-related queries.",
            access_token,
            user_id
        ),
        
        make_tool(
            get_all_bills_detail,
            "get_all_bills_detail",
            "Get current bill amount due, payment due dates, and past billing history. Use ONLY when user specifically asks about: 'current bill', 'bill amount', 'due date', 'how much to pay', 'bill history', 'monthly bills'. DO NOT use for balance or transaction queries.",
            access_token,
            user_id
        ),
        
        make_tool(
            get_loan_details,
            "get_loan_details",
            "Get all loan information including active loans, EMI amounts, loan status, payment schedules, and loan history. Use ONLY when user asks about: 'loan details', 'EMI amount', 'loan status', 'loan balance', 'loan payment', 'personal loans'. DO NOT use for other financial queries.",
            access_token,
            user_id
        ),
        
        make_tool(
            get_insurance_policy_info,
            "get_insurance_policy_info",
            "Get all insurance policies (active/expired), policy types, premium amounts, coverage details, renewal dates, and claim status. Use ONLY when user asks about: 'insurance policy', 'premium amount', 'policy details', 'insurance coverage', 'policy renewal', 'health/life insurance'. DO NOT use for other queries.",
            access_token,
            user_id
        ),
    ]

# CRITICAL: Tool Selection Rules for Agent
"""
EXACT MATCHING RULES:

1. User asks "how much amount is credited my account?"  USE get_all_trans_details
2. User asks "what's my balance?"  USE get_usr_wallet_data  
3. User asks "what's my current bill?"  USE get_all_bills_detail
4. User asks "what loans do I have?"  USE get_loan_details
5. User asks "what insurance do I have?"  USE get_insurance_policy_info

NEVER use multiple tools unless user specifically asks for comprehensive information.
Each tool serves ONE specific purpose - do not overlap.
"""