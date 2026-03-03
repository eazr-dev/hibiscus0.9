# EAZR WebSocket Chat - Response Reference

> **Endpoint:** `ws://localhost:8000/ws/chat?token=JWT_TOKEN&device_id=DEVICE_ID`

---

## Table of Contents

1. [Connection & Auth Responses](#1-connection--auth-responses)
2. [Chat Message Responses](#2-chat-message-responses)
3. [Streaming Responses](#3-streaming-responses)
4. [Thinking Indicators](#4-thinking-indicators)
5. [Response Types by Intent](#5-response-types-by-intent)
6. [Notification Responses](#6-notification-responses)
7. [Heartbeat / Presence / Typing](#7-heartbeat--presence--typing)
8. [Error Responses](#8-error-responses)

---

## 1. Connection & Auth Responses

### 1.1 Connection Acknowledgment

Sent immediately after WebSocket connection is established (before auth).

```json
{
  "type": "connection_ack",
  "connection_id": "temp_conn_1739447067_abc123",
  "requires_auth": true,
  "server_time": "2026-02-13T16:04:27.000000",
  "message": "Please send authenticate message with your access token"
}
```

### 1.2 Auth Success

Sent after successful JWT authentication.

```json
{
  "type": "auth_success",
  "connection_id": "conn_1739447067_abc12345",
  "user_id": 343,
  "chat_session_id": "chat_343_1770989767_1355c7c4",
  "user_session_id": "user_1770998664_343_7751",
  "user_name": "Hrushikesh",
  "timestamp": "2026-02-13T16:04:27.000000"
}
```

### 1.3 Auth Failure

```json
{
  "type": "auth_failure",
  "error": "Token expired",
  "error_code": "TOKEN_EXPIRED",
  "timestamp": "2026-02-13T16:04:27.000000"
}
```

**Error codes:** `AUTH_FAILED`, `TOKEN_EXPIRED`, `TOKEN_INVALID`, `AUTH_SERVICE_UNAVAILABLE`, `USER_ID_MISMATCH`

---

## 2. Chat Message Responses

All non-streaming chat responses use `type: "chat_message"`.

### Common Structure

```json
{
  "type": "chat_message",
  "chat_session_id": "chat_343_1770989767_1355c7c4",
  "response_type": "<see table below>",
  "data": {
    "type": "<mirrors response_type>",
    "response": "Main text response",
    "message": "Alternative text field",
    "title": "Optional header",
    "action": "Intent or action identifier",
    "suggestions": ["Follow-up suggestion 1", "Follow-up suggestion 2"],
    "options": ["Option A", "Option B"],
    "quick_actions": [
      {
        "title": "Button Label",
        "action": "action_name",
        "policyId": "optional_policy_id",
        "query": "optional_query_text",
        "redirect": false,
        "redirect_page": "optional_page_name"
      }
    ],
    "show_service_options": false,
    "language": "en",
    "chat_session_id": "chat_343_...",
    "user_session_id": "user_..."
  },
  "metadata": {
    "intent": "detected_intent",
    "timestamp": "2026-02-13T16:04:27.378123"
  },
  "timestamp": "2026-02-13T16:04:27.378135"
}
```

### response_type Values Summary

| response_type | When Used |
|--------------|-----------|
| `chat_message` | greeting, small_talk, unknown, default |
| `question` | Insurance/wallet/loan Q&A flow steps |
| `selection_menu` | financial_assistance, insurance_plan menus |
| `policy_query` | Policy listing, details, benefits, gaps |
| `policy_details` | Marketplace insurance product details |
| `education` | financial_education responses |
| `coverage_advisory` | Coverage recommendation responses |
| `claim_guidance` | Claim guidance / claim_support |
| `protection_score` | User's protection score |
| `live_information` | Live event / market data |
| `off_topic` | Off-topic redirect |
| `insurance_analysis` | Policy upload/analysis entry point |
| `review_and_edit_application` | Application review before submit |
| `application_completed` | Application submitted successfully |
| `application_cancelled` | Application cancelled |
| `error` | Error condition |

---

## 5. Response Types by Intent

### 5.1 `greeting` / `small_talk` / `unknown`

**response_type:** `chat_message`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "Hello"
}
```

**Response (streamed):** Tokens arrive as `chat_stream`, then final:
```json
{
  "type": "chat_stream_end",
  "chat_session_id": "chat_343_...",
  "full_response": "Hey there! I'm eazr, your friendly insurance and finance buddy...",
  "response_type": "chat_message",
  "data": {
    "response": "Hey there! I'm eazr...",
    "action": "casual_conversation",
    "language": "en",
    "suggestions": ["Show my policies", "What is my coverage?", "Help me with insurance"],
    "show_service_options": false
  },
  "total_tokens": 42,
  "timestamp": "2026-02-13T16:04:28.000000"
}
```

### 5.2 `financial_assistance`

**response_type:** `selection_menu`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "I need money"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "chat_session_id": "chat_343_...",
  "response_type": "selection_menu",
  "data": {
    "type": "selection_menu",
    "response": "I can help you explore financial assistance options...",
    "title": "Financial Assistance",
    "action": "financial_assistance",
    "options": [
      "Personal Loan",
      "Business Loan",
      "Medical Loan",
      "Education Loan",
      "Gold Loan"
    ],
    "suggestions": [],
    "quick_actions": [],
    "show_service_options": false,
    "language": "en"
  },
  "metadata": { "intent": "financial_assistance" }
}
```

### 5.3 `insurance_plan`

**response_type:** `selection_menu`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "I want insurance"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "chat_session_id": "chat_343_...",
  "response_type": "selection_menu",
  "data": {
    "type": "selection_menu",
    "response": "Choose from our available insurance policies:",
    "title": "Insurance Plans",
    "action": "select_insurance_type",
    "options": [
      "Health Insurance",
      "Life Insurance",
      "Auto Insurance",
      "Home Insurance"
    ],
    "quick_actions": [],
    "show_service_options": false,
    "language": "en"
  },
  "metadata": { "intent": "insurance_plan" }
}
```

### 5.4 `insurance_analysis`

**response_type:** `insurance_analysis`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "Analyze my policy"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "chat_session_id": "chat_343_...",
  "response_type": "insurance_analysis",
  "data": {
    "type": "insurance_analysis",
    "response": "I can analyze your insurance policy! Upload your policy document...",
    "action": "insurance_analysis",
    "quick_actions": [
      {
        "title": "Add Policy",
        "action": "add_policy",
        "redirect": true,
        "redirect_page": "policy_locker"
      }
    ],
    "suggestions": ["Show my policies", "What is my coverage?"],
    "show_service_options": false,
    "language": "en"
  },
  "metadata": { "intent": "insurance_analysis" }
}
```

### 5.5 `policy_query` (Full Flow)

**response_type:** `policy_query`

The `policy_query` intent supports a multi-step flow controlled by the `flow_step` field.

#### Step 1: Initial Query ("Show my policies")

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "Show my policies"
}
```

**Response — Ask Self or Family:**
```json
{
  "type": "chat_message",
  "chat_session_id": "chat_343_...",
  "response_type": "policy_query",
  "data": {
    "type": "policy_query",
    "response": "You've got 3 policies! Want to see your own or a family member's?",
    "action": "policy_query",
    "flow_step": "ask_self_or_family",
    "has_policies": true,
    "policy_count": 3,
    "self_count": 2,
    "family_count": 1,
    "policies": [],
    "family_members": ["friend"],
    "selected_member": null,
    "portfolio_overview": {},
    "quick_actions": [
      { "title": "My Policies", "action": "policy_query", "query": "show my own policies" },
      { "title": "Family Policies", "action": "policy_query", "query": "show family policies" }
    ],
    "suggestions": ["Show my own policies", "Show family policies"],
    "show_service_options": false,
    "language": "en"
  }
}
```

#### Step 2: Self Policies List

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "show my own policies"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "type": "policy_query",
    "response": "Here are your policies - tap any one for the full details!",
    "action": "policy_query",
    "flow_step": "show_self_policies",
    "has_policies": true,
    "policy_count": 2,
    "policies": [
      {
        "analysisId": "ANL_343_abc123",
        "provider": "ICICI Lombard",
        "policyType": "health",
        "policyNumber": "POL12345",
        "coverage": 500000,
        "formattedCoverage": "₹5,00,000",
        "premium": 12000,
        "formattedPremium": "₹12,000",
        "protectionScore": 65,
        "startDate": "2025-01-01",
        "endDate": "2026-01-01"
      }
    ],
    "quick_actions": [
      { "title": "ICICI Lombard (health)", "action": "policy_query", "query": "Show details for policy ANL_343_abc123" },
      { "title": "View All Policies", "action": "policy_query", "query": "show my policies" }
    ],
    "suggestions": ["What is my coverage?", "Where am I not covered?"]
  }
}
```

#### Step 3: Family Members List

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "policy query family"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "type": "policy_query",
    "response": "You've got 1 family policy. Pick a family member to see their coverage.",
    "action": "policy_query",
    "flow_step": "show_family_members",
    "family_members": ["friend"],
    "family_count": 1,
    "quick_actions": [
      { "title": "Friend (1)", "action": "policy_query", "query": "Show policies for friend" },
      { "title": "Back", "action": "policy_query", "query": "show my policies" }
    ]
  }
}
```

#### Step 4: Member's Policies

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "Show policies for friend"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "type": "policy_query",
    "response": "Here are friend's policies - tap any one for the full details!",
    "action": "policy_query",
    "flow_step": "show_member_policies",
    "selected_member": "friend",
    "policies": [
      {
        "analysisId": "ANL_343_0c2cbf318944",
        "provider": "United India Insurance Company Limited",
        "policyType": "health",
        "coverage": 2000000,
        "formattedCoverage": "₹20.0 L",
        "protectionScore": 40
      }
    ],
    "quick_actions": [
      { "title": "United India In... (health)", "action": "policy_query", "query": "Show details for policy ANL_343_0c2cbf318944" },
      { "title": "View All Policies", "action": "policy_query", "query": "show my policies" }
    ]
  }
}
```

#### Step 5: Single Policy Details

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "Show details for policy ANL_343_0c2cbf318944"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "chat_session_id": "chat_343_1770989767_1355c7c4",
  "response_type": "policy_query",
  "data": {
    "type": "policy_query",
    "response": "United India Insurance Company Limited - health",
    "response_markdown": "United India Insurance Company Limited - health",
    "action": "policy_query",
    "flow_step": "show_policy_details",
    "has_policies": true,
    "policy_id": "ANL_343_0c2cbf318944",
    "policy_data": {
      "provider": "United India Insurance Company Limited",
      "policyType": "health",
      "policyNumber": "SCR900347020",
      "coverage": 2000000,
      "formattedCoverage": "₹2,000,000",
      "premium": 26441,
      "formattedPremium": "₹26,441",
      "startDate": "2022-04-01",
      "endDate": "2023-03-31",
      "formattedValidity": "2022-04-01 to 2023-03-31",
      "protectionScore": 40,
      "keyBenefits": [
        "Sum Insured: Rs. 2,000,000 coverage for medical expenses",
        "TPA Support: Health Insurance TPA of India Ltd. with toll-free numbers 1800 102 3600 / 1800 180 3600",
        "Tax Benefit: Premium eligible for deduction under section 80-D of Income Tax Act",
        "Family Coverage: Covers spouse and son under single policy",
        "Senior Citizen Coverage: Includes 75-year-old spouse with specific premium allocation"
      ],
      "exclusions": [
        "Pre-existing conditions: Standard waiting periods likely apply",
        "Non-medical expenses: Administrative and documentation costs not covered",
        "Experimental treatments: Unproven medical procedures excluded"
      ],
      "gapCount": 5,
      "highGapCount": 3,
      "analysisId": "ANL_343_0c2cbf318944"
    },
    "benefits_data": null,
    "gaps_data": null,
    "recommendations_data": null,
    "quick_actions": [
      { "title": "View All Benefits", "action": "view_benefits", "policyId": "ANL_343_0c2cbf318944" },
      { "title": "Coverage Gaps", "action": "view_gaps", "policyId": "ANL_343_0c2cbf318944" },
      { "title": "Back to Policies", "action": "policy_query", "query": "show my policies" }
    ],
    "suggestions": [
      "Where am I not covered?",
      "What would you recommend?",
      "What's my protection score?"
    ],
    "show_service_options": false,
    "language": "en"
  },
  "metadata": {
    "intent": "policy_query",
    "timestamp": "2026-02-13T16:04:27.378123"
  }
}
```

#### Step 6: View Benefits

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "View benefits",
  "action": "view_benefits",
  "policy_id": "ANL_343_0c2cbf318944"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "type": "policy_query",
    "response": "Here are the key benefits of your policy:",
    "action": "policy_query",
    "flow_step": "show_policy_benefits",
    "policy_id": "ANL_343_0c2cbf318944",
    "benefits_data": {
      "keyBenefits": ["..."],
      "additionalBenefits": ["..."]
    },
    "quick_actions": [
      { "title": "Coverage Gaps", "action": "view_gaps", "policyId": "ANL_343_0c2cbf318944" },
      { "title": "Recommendations", "action": "view_recommendations", "policyId": "ANL_343_0c2cbf318944" },
      { "title": "Back to Details", "action": "policy_query", "query": "Show details for policy ANL_343_0c2cbf318944" }
    ]
  }
}
```

#### Step 7: View Coverage Gaps

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "Coverage gaps",
  "action": "view_gaps",
  "policy_id": "ANL_343_0c2cbf318944"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "type": "policy_query",
    "response": "Your policy has 5 coverage gaps (3 high priority):",
    "action": "policy_query",
    "flow_step": "show_policy_gaps",
    "policy_id": "ANL_343_0c2cbf318944",
    "gaps_data": [
      {
        "gap": "No Critical Illness Cover",
        "severity": "high",
        "description": "Policy does not cover critical illnesses separately"
      }
    ],
    "quick_actions": [
      { "title": "View Benefits", "action": "view_benefits", "policyId": "ANL_343_0c2cbf318944" },
      { "title": "Recommendations", "action": "view_recommendations", "policyId": "ANL_343_0c2cbf318944" },
      { "title": "Back to Details", "action": "policy_query", "query": "Show details for policy ANL_343_0c2cbf318944" }
    ]
  }
}
```

#### No Policies

```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "type": "policy_query",
    "response": "You don't have any policies yet. Upload your first policy to get started!",
    "action": "policy_query",
    "flow_step": "no_policies",
    "has_policies": false,
    "policy_count": 0,
    "quick_actions": [
      { "title": "Add Policy", "action": "add_policy", "redirect": true, "redirect_page": "policy_locker" }
    ]
  }
}
```

#### flow_step Values

| flow_step | Description |
|-----------|-------------|
| `no_policies` | User has no policies |
| `ask_self_or_family` | Ask whether to show self or family policies |
| `show_self_policies` | List of user's own policies |
| `show_family_members` | List of family members with policies |
| `show_member_policies` | List of a specific member's policies |
| `show_policy_details` | Full details of one policy |
| `show_policy_benefits` | Benefits breakdown |
| `show_policy_gaps` | Coverage gaps analysis |
| `show_policy_recommendations` | AI recommendations |
| `specific_question_answer` | Answer about a specific policy |
| `general_response` | General policy-related answer |
| `no_self_policies` | No self policies found |
| `no_family_policies` | No family policies found |
| `no_member_policies` | Specific member has no policies |
| `policy_not_found` | Requested policy ID not found |
| `error` | Error during policy fetch |

---

### 5.6 `financial_education`

**response_type:** `education`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "What is insurance?"
}
```

**Response (streamed via LLM):**
```json
{
  "type": "chat_stream_end",
  "chat_session_id": "chat_343_...",
  "full_response": "Insurance is a financial safety net that protects you against unexpected losses...",
  "response_type": "education",
  "data": {
    "response": "Insurance is a financial safety net...",
    "action": "financial_education",
    "language": "en",
    "suggestions": ["Tell me about health insurance", "What is term insurance?", "How does premium work?"],
    "show_service_options": false
  },
  "total_tokens": 85
}
```

### 5.7 `protection_score`

**response_type:** `protection_score`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "What's my protection score?"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "protection_score",
  "data": {
    "type": "protection_score",
    "response": "Your protection score is 40%. Here's what that means...",
    "score": 40,
    "message": "Your coverage needs improvement",
    "analysis": "Based on your uploaded policies, you have moderate health coverage but lack...",
    "language": "en",
    "suggestions": ["How can I improve my score?", "Show my coverage gaps", "Show my policies"],
    "show_service_options": false
  }
}
```

### 5.8 `claim_guidance`

**response_type:** `claim_guidance`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "How do I file a health insurance claim?"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "claim_guidance",
  "data": {
    "type": "claim_guidance",
    "response": "Here's how to file a health insurance claim step by step...",
    "action": "claim_guidance",
    "language": "en",
    "suggestions": ["What documents do I need?", "How long does it take?", "Show my policies"],
    "show_service_options": false,
    "user_session_id": "user_..."
  }
}
```

### 5.9 `off_topic`

**response_type:** `off_topic`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "Who is Narendra Modi?"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "off_topic",
  "data": {
    "type": "off_topic",
    "response": "That's an interesting question, but I'm best at helping with insurance and finance! How about I help you with...",
    "action": "off_topic",
    "language": "en",
    "suggestions": [
      "Show my policies",
      "Help me with insurance",
      "What is my protection score?"
    ],
    "show_service_options": false
  }
}
```

### 5.10 `live_event`

**response_type:** `live_information`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "What's happening in the stock market today?"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "live_information",
  "data": {
    "type": "live_information",
    "response": "Here's the latest market update...",
    "event_data": {},
    "action": "live_event",
    "language": "en",
    "suggestions": ["Show my policies", "Help me with insurance"],
    "show_service_options": false
  }
}
```

### 5.11 `wallet_setup`

**response_type:** `question`

**Request:**
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "Set up my wallet"
}
```

**Response:**
```json
{
  "type": "chat_message",
  "response_type": "question",
  "data": {
    "type": "question",
    "response": "Let's set up your financial wallet! First, what is your monthly income?",
    "title": "Wallet Setup",
    "action": "wallet_setup",
    "options": ["Under 25,000", "25,000 - 50,000", "50,000 - 1,00,000", "Above 1,00,000"],
    "suggestions": [],
    "show_service_options": false,
    "user_session_id": "user_...",
    "chat_session_id": "chat_343_..."
  }
}
```

---

## 3. Streaming Responses

When `stream: true` (default), LLM responses are sent token-by-token.

### 3.1 Stream Token

```json
{
  "type": "chat_stream",
  "chat_session_id": "chat_343_...",
  "token": "Hey",
  "token_index": 0,
  "is_final": false,
  "timestamp": "2026-02-13T16:04:27.500000"
}
```

```json
{
  "type": "chat_stream",
  "chat_session_id": "chat_343_...",
  "token": " there",
  "token_index": 1,
  "is_final": false,
  "timestamp": "2026-02-13T16:04:27.520000"
}
```

### 3.2 Stream End

Final message with complete response and metadata.

```json
{
  "type": "chat_stream_end",
  "chat_session_id": "chat_343_...",
  "full_response": "Hey there! I'm eazr, your insurance and finance buddy...",
  "response_type": "chat_message",
  "data": {
    "response": "Hey there! I'm eazr...",
    "action": "casual_conversation",
    "language": "en",
    "suggestions": ["Show my policies", "What is my coverage?"],
    "show_service_options": false
  },
  "total_tokens": 42,
  "timestamp": "2026-02-13T16:04:28.000000"
}
```

### Intents That Use Streaming

| Intent | Streamed? |
|--------|-----------|
| `greeting` | Yes |
| `small_talk` | Yes |
| `unknown` | Yes |
| `financial_education` | Yes |
| All others | No (direct `chat_message`) |

To disable streaming, send `"stream": false`:
```json
{
  "type": "chat",
  "chat_session_id": "chat_343_...",
  "query": "Hello",
  "stream": false
}
```

---

## 4. Thinking Indicators

Sent while processing the user's message. Rotates through status words.

### Thinking Started

```json
{
  "type": "thinking",
  "chat_session_id": "chat_343_...",
  "status": "started",
  "message": "Thinking...",
  "timestamp": "2026-02-13T16:04:27.000000"
}
```

### Thinking Rotating

```json
{
  "type": "thinking",
  "chat_session_id": "chat_343_...",
  "status": "started",
  "message": "Analyzing...",
  "timestamp": "2026-02-13T16:04:28.000000"
}
```

### Thinking Stopped

```json
{
  "type": "thinking",
  "chat_session_id": "chat_343_...",
  "status": "stopped",
  "message": "",
  "timestamp": "2026-02-13T16:04:29.000000"
}
```

**Rotating words:** Thinking, Analyzing, Processing, Searching, Computing, Reviewing, Checking, Evaluating, Preparing, Gathering, Scanning, Compiling, Assessing, Fetching, Resolving

---

## 6. Notification Responses

### 6.1 Real-time Notification

```json
{
  "type": "notification",
  "notification_id": "notif_abc123",
  "notification_type": "policy_renewal",
  "title": "Policy Renewal Reminder",
  "body": "Your health insurance policy expires in 30 days",
  "data": {},
  "image_url": null,
  "action_url": null,
  "priority": "high"
}
```

**notification_type values:** `policy_renewal`, `claim_update`, `payment_due`, `system`
**priority values:** `low`, `normal`, `high`

### 6.2 Unread Count

```json
{
  "type": "unread_count",
  "unread_count": 5
}
```

### 6.3 Notification List

**Request:**
```json
{
  "type": "get_notifications"
}
```

**Response:**
```json
{
  "type": "notification_list",
  "notifications": [
    {
      "notification_id": "notif_abc123",
      "notification_type": "policy_renewal",
      "title": "Policy Renewal Reminder",
      "body": "Your health insurance policy expires in 30 days",
      "data": {},
      "image_url": null,
      "action_url": null,
      "priority": "high",
      "sent_at": "2026-02-13T10:00:00",
      "read": false,
      "read_at": null
    }
  ],
  "total": 10,
  "unread_count": 5,
  "has_more": true
}
```

### 6.4 DND Status

```json
{
  "type": "dnd_status",
  "enabled": true,
  "until": "2026-02-13T22:00:00"
}
```

### 6.5 Notification Settings

```json
{
  "type": "notification_settings",
  "settings": {
    "policy_renewal": true,
    "promotional": false,
    "claim_update": true,
    "payment_due": true
  }
}
```

### 6.6 Topic Subscribed / Unsubscribed

```json
{
  "type": "topic_subscribed",
  "topic": "health_insurance_updates",
  "success": true,
  "message": "Subscribed to health_insurance_updates"
}
```

---

## 7. Heartbeat / Presence / Typing

### 7.1 Ping / Pong

**Client sends:**
```json
{ "type": "ping" }
```

**Server responds:**
```json
{
  "type": "pong",
  "server_time": "2026-02-13T16:04:27.000000"
}
```

### 7.2 Typing Indicator

**Client sends:**
```json
{
  "type": "typing_start",
  "chat_session_id": "chat_343_..."
}
```

**Server broadcasts to other devices:**
```json
{
  "type": "typing_indicator",
  "chat_session_id": "chat_343_...",
  "user_id": 343,
  "is_typing": true,
  "device_id": "device_abc",
  "user_name": "Hrushikesh"
}
```

### 7.3 Presence Update

**Client sends:**
```json
{
  "type": "presence_update",
  "status": "away"
}
```

**Server broadcasts:**
```json
{
  "type": "presence_status",
  "user_id": 343,
  "status": "away",
  "last_seen": "2026-02-13T16:04:27.000000",
  "user_name": "Hrushikesh"
}
```

**Status values:** `online`, `offline`, `away`, `busy`

---

## 8. Error Responses

### 8.1 Chat Error (inside chat flow)

```json
{
  "type": "chat_message",
  "chat_session_id": "chat_343_...",
  "response_type": "error",
  "data": {
    "type": "error",
    "response": "Oops, something hiccupped on my end! Try that again?",
    "error": "Failed to process query",
    "action": "error",
    "show_service_options": false
  }
}
```

### 8.2 System Error (protocol level)

```json
{
  "type": "error",
  "error": "Authentication required",
  "error_code": "NOT_AUTHENTICATED",
  "details": null,
  "recoverable": true
}
```

### Error Codes

| error_code | Description | Recoverable |
|-----------|-------------|-------------|
| `AUTH_FAILED` | Authentication failed | Yes (re-auth) |
| `TOKEN_EXPIRED` | JWT token expired | Yes (refresh token) |
| `TOKEN_INVALID` | Invalid JWT token | Yes (re-auth) |
| `INVALID_JSON` | Malformed JSON message | Yes |
| `INVALID_MESSAGE` | Message validation failed | Yes |
| `INVALID_MESSAGE_TYPE` | Unknown message type | Yes |
| `NOT_AUTHENTICATED` | Auth required first | Yes (send auth) |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Yes (wait) |
| `CHAT_SESSION_NOT_FOUND` | Invalid chat session | Yes |
| `USER_NOT_FOUND` | User not found | No |
| `INTERNAL_ERROR` | Server error | Yes (retry) |
| `CONNECTION_TIMEOUT` | Idle too long | Yes (reconnect) |

---

## Client Request Reference

### All Client Message Types

| type | Required Fields | Optional Fields |
|------|----------------|-----------------|
| `authenticate` | `access_token` | `user_id`, `chat_session_id`, `device_id`, `user_session_id` |
| `chat` | `chat_session_id`, `query` | `action`, `policy_id`, `assistance_type`, `insurance_type`, `service_type`, `model`, `stream` |
| `typing_start` | `chat_session_id` | |
| `typing_stop` | `chat_session_id` | |
| `presence_update` | `status` | |
| `ping` | | |
| `join_chat` | `chat_session_id` | |
| `leave_chat` | `chat_session_id` | |
| `mark_notification_read` | `notification_id` | |
| `mark_all_read` | | |
| `get_notifications` | | |
| `set_dnd` | `enabled` | `until` |
| `update_notification_settings` | `settings` | |
| `subscribe_topic` | `topic` | |
| `unsubscribe_topic` | `topic` | |

### `model` Field Values

| model | Description |
|-------|-------------|
| `policy_analysis` | Default - general insurance analysis |
| `coverage_advisory` | Coverage recommendation focus |
| `claim_support` | Claim guidance focus |

---

## Intent Detection → Response Type Map

```
User Query                         → Intent              → response_type
=====================================================================================
"Hello" / "Hi"                     → greeting             → chat_message (streamed)
"How are you?"                     → small_talk           → chat_message (streamed)
"I need money"                     → financial_assistance → selection_menu
"I want insurance"                 → insurance_plan       → selection_menu
"Analyze my policy"                → insurance_analysis   → insurance_analysis
"Show my policies"                 → policy_query         → policy_query
"What is my coverage?"             → policy_query         → policy_query
"What is insurance?"               → financial_education  → education (streamed)
"How to file a claim?"             → claim_guidance       → claim_guidance
"What's my protection score?"      → protection_score     → protection_score
"Stock market today"               → live_event           → live_information
"Who is Narendra Modi?"            → off_topic            → off_topic
"Set up my wallet"                 → wallet_setup         → question
"Random unknown query"             → unknown              → chat_message (streamed)
```
