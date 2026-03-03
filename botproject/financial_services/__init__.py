"""
Financial Services Module
==========================

This module contains all financial service components including:
- Insurance API integration and auditing
- Dynamic insurance analysis
- Report generation
- Loan API integration
- Wallet API integration
- Transaction API
"""

# Import commonly used components
try:
    from .insurance_api import fetch_insurance_data
except ImportError:
    pass

try:
    from .loan_api import fetch_loan_data
except ImportError:
    pass

try:
    from .wallet_api import fetch_wallet_data
except ImportError:
    pass

try:
    from .transcation_api import fetch_transaction_data
except ImportError:
    pass

try:
    from .protection_score_ans import calculate_protection_score
except ImportError:
    pass

__all__ = [
    'fetch_insurance_data',
    'fetch_loan_data',
    'fetch_wallet_data',
    'fetch_transaction_data',
    'calculate_protection_score',
]
