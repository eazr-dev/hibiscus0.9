# EAZR WebSocket - Flutter Integration Guide

Complete reference for integrating the EAZR WebSocket chat system into Flutter.

---

## Table of Contents

1. [Connection Setup](#1-connection-setup)
2. [Authentication](#2-authentication)
3. [Client → Server Messages](#3-client--server-messages)
4. [Server → Client Messages](#4-server--client-messages)
5. [Chat Message Flow](#5-chat-message-flow)
6. [Streaming Responses](#6-streaming-responses)
7. [Thinking Indicator](#7-thinking-indicator)
8. [Response Types & Data Structures](#8-response-types--data-structures)
9. [Intent System](#9-intent-system)
10. [Action System](#10-action-system)
11. [Policy Query Flow](#11-policy-query-flow)
12. [Insurance Marketplace Flow](#12-insurance-marketplace-flow)
13. [Multi-Step Form Flows](#13-multi-step-form-flows)
14. [Typing Indicators](#14-typing-indicators)
15. [Presence System](#15-presence-system)
16. [Notification System](#16-notification-system)
17. [Heartbeat / Keep-Alive](#17-heartbeat--keep-alive)
18. [Error Handling](#18-error-handling)
19. [Rate Limiting](#19-rate-limiting)
20. [Multilingual Support](#20-multilingual-support)
21. [Flutter Dart Code Examples](#21-flutter-dart-code-examples)
22. [Complete Message Type Reference](#22-complete-message-type-reference)

---

## 1. Connection Setup

### Endpoint

```
ws://<host>:<port>/ws/chat
wss://<host>:<port>/ws/chat   (production)
```

### Query Parameters (Optional)

| Parameter    | Type   | Required | Description                                |
|-------------|--------|----------|--------------------------------------------|
| `token`     | string | No       | JWT token for immediate auth on connect    |
| `session_id`| string | No       | Existing chat session ID to rejoin         |
| `device_id` | string | No       | Device identifier for multi-device tracking|

### Connection Methods

**Method A: Token in Query Params (Recommended for Flutter)**

```
wss://your-domain/ws/chat?token=YOUR_JWT_TOKEN&device_id=flutter_device_abc123
```

Server authenticates immediately on connection. You receive `auth_success` directly.

**Method B: Authenticate via Message**

Connect without token, then send `authenticate` message after receiving `connection_ack`.

### Connection Flow

```
Client                          Server
  |                               |
  |--- WebSocket Connect -------->|
  |                               |
  |  (If token in query params)   |
  |<-- auth_success --------------|  (authenticated immediately)
  |                               |
  |  (If NO token in query)       |
  |<-- connection_ack ------------|  (requires_auth: true)
  |--- authenticate ------------->|
  |<-- auth_success --------------|
  |                               |
  |--- chat / typing / ping ----->|  (all messages require auth)
  |<-- chat_message / pong -------|
```

### Connection Timeout

- Unauthenticated connections timeout after **60 seconds**
- Authenticated connections receive server `ping` every **60 seconds** if idle
- Stale connections (no heartbeat for **120 seconds**) are cleaned up automatically

---

## 2. Authentication

### Request: `authenticate`

Send this after receiving `connection_ack` (only needed if token not in query params).

```json
{
  "type": "authenticate",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "device_id": "flutter_device_abc123",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4",
  "user_session_id": "user_1707800000_343_1234"
}
```

| Field             | Type   | Required | Description                          |
|-------------------|--------|----------|--------------------------------------|
| `type`            | string | Yes      | Must be `"authenticate"`             |
| `access_token`    | string | Yes      | JWT token (HS256, 1-week expiry)     |
| `device_id`       | string | No       | Unique device identifier             |
| `chat_session_id` | string | No       | Existing chat session to rejoin      |
| `user_session_id` | string | No       | Existing user session                |
| `user_id`         | int    | No       | Optional, verified against token     |

### Response: `auth_success`

```json
{
  "type": "auth_success",
  "user_id": 343,
  "user_session_id": "user_1707800000_343_1234",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4",
  "connection_id": "conn_1707800000_abcdef01",
  "user_name": "Hitesh",
  "is_new_session": false,
  "timestamp": "2024-02-13T10:00:00.000000"
}
```

| Field              | Type   | Description                                    |
|--------------------|--------|------------------------------------------------|
| `user_id`          | int    | Authenticated user's ID                        |
| `user_session_id`  | string | User session ID (15-day expiry)                |
| `chat_session_id`  | string | Chat session ID (24-hour expiry)               |
| `connection_id`    | string | Unique connection ID for this WebSocket        |
| `user_name`        | string | User's display name                            |
| `is_new_session`   | bool   | True if a new session was created              |

### Response: `auth_failure`

```json
{
  "type": "auth_failure",
  "error": "Token has expired",
  "error_code": "TOKEN_EXPIRED",
  "timestamp": "2024-02-13T10:00:00.000000"
}
```

Error codes: `AUTH_FAILED`, `TOKEN_EXPIRED`, `TOKEN_INVALID`, `USER_ID_MISMATCH`, `AUTH_SERVICE_UNAVAILABLE`

### Response: `connection_ack` (only if no token in query)

```json
{
  "type": "connection_ack",
  "connection_id": "temp_abcdef0123456789",
  "requires_auth": true,
  "server_time": "2024-02-13T10:00:00.000000",
  "message": "Please send authenticate message with your access token"
}
```

---

## 3. Client → Server Messages

All messages below require authentication. Send as JSON strings over WebSocket.

### 3.1 `chat` - Send Chat Message

```json
{
  "type": "chat",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4",
  "query": "I want to buy health insurance"
}
```

| Field              | Type   | Required | Description                                     |
|--------------------|--------|----------|-------------------------------------------------|
| `type`             | string | Yes      | Must be `"chat"`                                |
| `chat_session_id`  | string | Yes      | Current chat session ID                         |
| `query`            | string | Yes      | User's message text                             |
| `action`           | string | No       | Action identifier (for button clicks)           |
| `user_input`       | string | No       | Additional input (for form submissions)         |
| `assistance_type`  | string | No       | e.g., `"personal_loan"`, `"home_loan"`          |
| `insurance_type`   | string | No       | e.g., `"health"`, `"life"`, `"auto"`            |
| `service_type`     | string | No       | Service type identifier                         |
| `policy_id`        | string | No       | Policy ID for specific policy operations        |
| `model`            | string | No       | AI model: `"policy_analysis"` (default), `"coverage_advisory"`, `"claim_support"` |

### 3.2 `ping` - Client Heartbeat

```json
{
  "type": "ping"
}
```

### 3.3 `pong` - Response to Server Ping

```json
{
  "type": "pong"
}
```

### 3.4 `typing_start` / `typing_stop`

```json
{
  "type": "typing_start",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4"
}
```

```json
{
  "type": "typing_stop",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4"
}
```

### 3.5 `presence_update`

```json
{
  "type": "presence_update",
  "status": "online"
}
```

Status values: `"online"`, `"offline"`, `"away"`, `"busy"`

### 3.6 `join_chat` - Switch Chat Session

```json
{
  "type": "join_chat",
  "chat_session_id": "chat_343_1707800000_newchat"
}
```

Response: `{"type": "chat_joined", "chat_session_id": "...", "timestamp": "..."}`

### 3.7 `leave_chat`

```json
{
  "type": "leave_chat",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4"
}
```

Response: `{"type": "chat_left", "chat_session_id": "...", "timestamp": "..."}`

### 3.8 Notification Messages

```json
{"type": "mark_notification_read", "notification_id": "notif_abc123"}

{"type": "mark_all_read"}

{"type": "get_notifications", "limit": 20, "offset": 0, "unread_only": false}

{"type": "set_dnd", "enabled": true, "duration_minutes": 60}

{"type": "update_notification_settings", "settings": {"policy_renewal": true, "promotional": false}}

{"type": "subscribe_topic", "topic": "insurance_updates"}

{"type": "unsubscribe_topic", "topic": "insurance_updates"}
```

---

## 4. Server → Client Messages

### 4.1 `chat_message` - Complete Response

This is the **primary response type** for all chat interactions. Structure:

```json
{
  "type": "chat_message",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4",
  "response_type": "chat_message",
  "data": {
    "type": "chat_message",
    "response": "Hey! What's on your mind?",
    "message": null,
    "title": null,
    "action": "casual_conversation",
    "suggestions": ["Tell me about health insurance", "How do I get a loan?"],
    "options": [],
    "quick_actions": [],
    "show_service_options": false,
    "language": "en",
    "chat_session_id": "chat_343_1707800000_a1b2c3d4",
    "user_session_id": "user_1707800000_343_1234"
  },
  "metadata": {
    "intent": "greeting",
    "timestamp": "2024-02-13T10:00:00.000000"
  },
  "timestamp": "2024-02-13T10:00:00.000000"
}
```

#### Standard `data` Fields (present in ALL chat_message responses)

| Field                 | Type          | Description                                          |
|-----------------------|---------------|------------------------------------------------------|
| `type`                | string        | Same as outer `response_type`                        |
| `response`            | string        | Main text response to display                        |
| `message`             | string\|null  | Alternative message text                             |
| `title`               | string\|null  | Title for UI card/section                            |
| `action`              | string        | Action identifier for tracking                       |
| `suggestions`         | string[]      | Suggested follow-up messages (chips)                 |
| `options`             | object[]      | Selection options for menus                          |
| `quick_actions`       | object[]      | Action buttons                                       |
| `show_service_options`| bool          | Whether to show main service menu                    |
| `language`            | string        | Response language: `"en"` or `"hi"`                  |
| `chat_session_id`     | string        | Current chat session                                 |
| `user_session_id`     | string        | Current user session                                 |

### 4.2 `chat_stream` - Streaming Token

```json
{
  "type": "chat_stream",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4",
  "token": "Hey",
  "token_index": 1,
  "is_final": false,
  "timestamp": "2024-02-13T10:00:00.000000"
}
```

### 4.3 `chat_stream_end` - Stream Complete

```json
{
  "type": "chat_stream_end",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4",
  "full_response": "Hey! What do you want to know about insurance?",
  "response_type": "chat_message",
  "data": {
    "response": "Hey! What do you want to know about insurance?",
    "action": "casual_conversation",
    "language": "en",
    "suggestions": ["Tell me about health insurance", "I want to check my policies"],
    "show_service_options": false
  },
  "total_tokens": 12,
  "timestamp": "2024-02-13T10:00:00.000000"
}
```

### 4.4 `thinking` - Processing Indicator

```json
{
  "type": "thinking",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4",
  "status": "started",
  "message": "Thinking...",
  "timestamp": "2024-02-13T10:00:00.000000"
}
```

| `status`  | Description                                          |
|-----------|------------------------------------------------------|
| `started` | Show thinking indicator. `message` rotates every 1s: "Thinking...", "Analyzing...", "Processing...", "Searching...", "Computing...", "Reviewing...", "Checking...", "Evaluating...", "Preparing...", "Gathering...", "Scanning...", "Compiling...", "Assessing...", "Fetching...", "Resolving..." |
| `stopped` | Hide thinking indicator. `message` is empty string   |

### 4.5 `ping` - Server Heartbeat

```json
{
  "type": "ping",
  "server_time": "2024-02-13T10:00:00.000000"
}
```

**You MUST respond with `{"type": "pong"}` to keep the connection alive.**

### 4.6 `pong` - Response to Client Ping

```json
{
  "type": "pong",
  "server_time": "2024-02-13T10:00:00.000000"
}
```

### 4.7 `typing_indicator`

```json
{
  "type": "typing_indicator",
  "chat_session_id": "chat_343_1707800000_a1b2c3d4",
  "user_id": 343,
  "is_typing": true,
  "device_id": "flutter_device_abc",
  "user_name": "Hitesh"
}
```

### 4.8 `presence_status`

```json
{
  "type": "presence_status",
  "user_id": 343,
  "status": "online",
  "last_seen": "2024-02-13T10:00:00.000000",
  "user_name": "Hitesh"
}
```

### 4.9 `error`

```json
{
  "type": "error",
  "error": "Rate limit exceeded for chat. Please slow down.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "details": {"limit": 20, "remaining": 0, "reset_after": 60},
  "recoverable": true,
  "timestamp": "2024-02-13T10:00:00.000000"
}
```

### 4.10 `notification`

```json
{
  "type": "notification",
  "notification_id": "notif_abc123",
  "notification_type": "policy_renewal",
  "title": "Policy Renewal Reminder",
  "body": "Your health insurance policy expires in 30 days",
  "data": {"policy_id": "POL123"},
  "image_url": null,
  "action_url": null,
  "priority": "high"
}
```

### 4.11 `unread_count`

```json
{
  "type": "unread_count",
  "unread_count": 5
}
```

### 4.12 `notification_list`

```json
{
  "type": "notification_list",
  "notifications": [
    {
      "notification_id": "notif_abc123",
      "notification_type": "policy_renewal",
      "title": "Renewal Reminder",
      "body": "Your policy expires soon",
      "data": null,
      "image_url": null,
      "action_url": null,
      "priority": "normal",
      "sent_at": "2024-02-13T10:00:00.000000",
      "read": false,
      "read_at": null
    }
  ],
  "total": 15,
  "unread_count": 5,
  "has_more": true
}
```

### 4.13 `dnd_status`

```json
{
  "type": "dnd_status",
  "enabled": true,
  "until": "2024-02-13T11:00:00.000000"
}
```

---

## 5. Chat Message Flow

### Standard (Non-Streaming) Flow

```
Client                             Server
  |                                  |
  |--- chat (query: "hello") ------->|
  |                                  |
  |<-- thinking (status: started) ---|  (show loading)
  |<-- thinking (message rotates) ---|  (every 1 second)
  |<-- thinking (message rotates) ---|
  |                                  |
  |<-- thinking (status: stopped) ---|  (hide loading)
  |<-- chat_message ------------------|  (final response)
```

### Streaming Flow

For `greeting`, `small_talk`, `unknown`, and `task` intents, responses are streamed:

```
Client                               Server
  |                                    |
  |--- chat (query: "hello") --------->|
  |                                    |
  |<-- thinking (status: started) -----|  (show loading)
  |<-- thinking (message rotates) -----|
  |                                    |
  |<-- thinking (status: stopped) -----|  (hide loading)
  |<-- chat_stream (token: "Hey") -----|  (append token)
  |<-- chat_stream (token: "!") -------|  (append token)
  |<-- chat_stream (token: " What") ---|  (append token)
  |<-- chat_stream (token: "'s") ------|  (append token)
  |<-- chat_stream (token: " up") -----|  (append token)
  |<-- chat_stream (token: "?") -------|  (append token)
  |                                    |
  |<-- chat_stream_end ----------------|  (full_response + suggestions)
```

### Flutter Rendering Logic

```
on message received:
  switch (message.type):
    case "thinking":
      if status == "started" -> show thinking bubble with message text
      if status == "stopped" -> hide thinking bubble

    case "chat_stream":
      append token to current streaming message bubble

    case "chat_stream_end":
      finalize streaming message bubble
      render suggestions from data.suggestions

    case "chat_message":
      render based on response_type (see Section 8)
```

---

## 6. Streaming Responses

### When Streaming Happens

Streaming is used **only** for these intents: `greeting`, `small_talk`, `unknown`, `task`, and `default` (when no specific handler matches).

All other intents (like `policy_query`, `insurance_plan`, `financial_assistance`, etc.) return complete `chat_message` responses.

### Token Accumulation

```dart
String _streamingBuffer = '';

void onChatStream(Map<String, dynamic> msg) {
  _streamingBuffer += msg['token'];
  // Update UI with _streamingBuffer
}

void onChatStreamEnd(Map<String, dynamic> msg) {
  final fullResponse = msg['full_response'];
  final suggestions = msg['data']['suggestions'] as List;
  // Finalize message bubble with fullResponse
  // Render suggestion chips
  _streamingBuffer = '';
}
```

---

## 7. Thinking Indicator

The server sends rotating "thinking" words while processing. The first word arrives immediately; subsequent words rotate every 1 second.

### Thinking Words Sequence

```
Thinking... → Analyzing... → Processing... → Searching... → Computing... →
Reviewing... → Checking... → Evaluating... → Preparing... → Gathering... →
Scanning... → Compiling... → Assessing... → Fetching... → Resolving... → (repeats)
```

### Flutter Implementation

```dart
bool _isThinking = false;
String _thinkingMessage = '';

void handleThinking(Map<String, dynamic> msg) {
  if (msg['status'] == 'started') {
    _isThinking = true;
    _thinkingMessage = msg['message']; // e.g., "Thinking..."
  } else if (msg['status'] == 'stopped') {
    _isThinking = false;
    _thinkingMessage = '';
  }
}
```

---

## 8. Response Types & Data Structures

The `response_type` field in `chat_message` determines how to render the response.

### 8.1 `chat_message` - Plain Text Response

```json
{
  "response_type": "chat_message",
  "data": {
    "response": "Hey! What's on your mind?",
    "action": "casual_conversation",
    "suggestions": ["Tell me about health insurance", "I want to check my policies"],
    "show_service_options": false,
    "language": "en"
  }
}
```

**Render:** Text bubble + suggestion chips.

### 8.2 `selection_menu` - Selection Options

Used for: financial_assistance, insurance_plan, insurance_type_selection, etc.

```json
{
  "response_type": "selection_menu",
  "data": {
    "type": "insurance_type_selection",
    "response": "Great! What type of insurance are you looking for?",
    "message": "Select Insurance Type",
    "options": [
      {"title": "Health Insurance", "action": "select_insurance_type", "insurance_type": "health", "icon": "health"},
      {"title": "Life Insurance", "action": "select_insurance_type", "insurance_type": "life", "icon": "life"},
      {"title": "Auto Insurance", "action": "select_insurance_type", "insurance_type": "auto", "icon": "auto"}
    ],
    "show_service_options": false
  }
}
```

**Render:** Message + tappable option cards/buttons. On tap, send:

```json
{
  "type": "chat",
  "chat_session_id": "...",
  "query": "Health Insurance",
  "action": "select_insurance_type",
  "insurance_type": "health"
}
```

### 8.3 `question` - Form Question (Multi-Step Flow)

```json
{
  "response_type": "question",
  "data": {
    "type": "question",
    "response": "What's your full name?",
    "message": "What's your full name?",
    "question_number": 1,
    "total_questions": 6,
    "field_key": "fullName",
    "field_type": "text",
    "placeholder": "Enter your full name",
    "required": true,
    "options": null,
    "progress": 16.67,
    "service_type": "health_insurance",
    "show_service_options": false,
    "session_continuation": true
  }
}
```

**Render:** Question text + input field (type based on `field_type`) + progress bar.

User answers are sent as regular chat:
```json
{
  "type": "chat",
  "chat_session_id": "...",
  "query": "Hitesh Kumar"
}
```

The server auto-detects active Q&A sessions and routes answers to the correct handler.

#### Field Types

| `field_type` | Flutter Widget        | Notes                                    |
|--------------|-----------------------|------------------------------------------|
| `text`       | TextField             | Generic text input                       |
| `number`     | TextField (numeric)   | May have `min`/`max` validation          |
| `tel`        | TextField (phone)     | Phone number input                       |
| `email`      | TextField (email)     | Email validation                         |
| `date`       | DatePicker            | Date format DD/MM/YYYY                   |
| `dropdown`   | DropdownButton        | `options` array provided                 |

### 8.4 `policy_query` - Policy Information

```json
{
  "response_type": "policy_query",
  "data": {
    "response": "You've got 3 policies. Tap on any one to dig into the details!",
    "response_markdown": "## Your Policies\n...",
    "action": "policy_query",
    "flow_step": "show_self_policies",
    "has_policies": true,
    "policy_count": 3,
    "self_count": 2,
    "family_count": 1,
    "policies": [
      {
        "policy_id": "POL123",
        "policy_type": "health",
        "insurer": "Star Health",
        "holder_name": "Hitesh",
        "relationship": "self",
        "sum_insured": 500000,
        "premium": 12000,
        "expiry_date": "2025-03-15"
      }
    ],
    "family_members": ["self", "wife", "father"],
    "quick_actions": [
      {"title": "View Gaps", "action": "view_gaps", "policy_id": "POL123"},
      {"title": "View Benefits", "action": "view_benefits", "policy_id": "POL123"}
    ],
    "portfolio_overview": {},
    "suggestions": ["Where am I not covered?", "What would you recommend?"],
    "language": "en"
  }
}
```

**Render based on `flow_step`:** See [Section 11](#11-policy-query-flow).

### 8.5 `policy_details` - Marketplace Policy Details

```json
{
  "response_type": "policy_details",
  "data": {
    "response": "Here are the details for this insurance plan",
    "policy_id": "INS_456",
    "policy_name": "Star Health Comprehensive",
    "insurer": "Star Health",
    "premium": 8999,
    "sum_insured": 500000,
    "features": ["Cashless hospitalization", "Pre/post hospitalization"],
    "show_service_options": false
  }
}
```

### 8.6 `protection_score` - Score Analysis

```json
{
  "response_type": "protection_score",
  "data": {
    "response": "Your protection score is 72/100. Here's the breakdown...",
    "action": "protection_score_response",
    "suggestions": ["Where am I not covered?", "What should I improve?"],
    "language": "en"
  }
}
```

### 8.7 `education` - Financial Education

```json
{
  "response_type": "education",
  "data": {
    "response": "Great question! Term insurance is basically...",
    "action": "financial_education",
    "context_used": true,
    "topics_discussed": ["term insurance", "premium"],
    "suggestions": ["What about whole life insurance?", "How much coverage do I need?"]
  }
}
```

### 8.8 `claim_guidance` - Claims Help

```json
{
  "response_type": "claim_guidance",
  "data": {
    "response": "For claims, here's what you need to do...",
    "action": "claim_guidance",
    "suggestions": ["What papers do I need?", "How long will it take?", "Check my claim status"]
  }
}
```

### 8.9 `insurance_analysis` - Upload Prompt

```json
{
  "response_type": "insurance_analysis",
  "data": {
    "response": "Let's take a look at your policy! Just add your document...",
    "action": "insurance_analysis",
    "quick_actions": [
      {"title": "Add Policy", "action": "add_policy", "redirect": true, "redirect_page": "add_policy"},
      {"title": "View My Policies", "action": "view_policies", "redirect": true, "redirect_page": "my_policies"}
    ],
    "suggestions": ["What's a protection score?", "How do you analyze my policy?"]
  }
}
```

**Render:** Message + action buttons. `redirect: true` means navigate to a Flutter screen.

### 8.10 `off_topic` - Off-Topic Redirect

```json
{
  "response_type": "off_topic",
  "data": {
    "response": "Haha, that's a fun one but a bit outside my zone!",
    "action": "off_topic_redirect",
    "suggestions": ["Tell me about health insurance", "How do I get a loan?"]
  }
}
```

### 8.11 `live_information` - Live Event Data

```json
{
  "response_type": "live_information",
  "data": {
    "response": "Here's what's happening in the market...",
    "action": "live_event",
    "suggestions": ["Tell me about health insurance", "How do I get a loan?"]
  }
}
```

### 8.12 `coverage_advisory` - Coverage Recommendations

```json
{
  "response_type": "coverage_advisory",
  "data": {
    "response": "Based on your profile, here's what I'd recommend...",
    "title": "Coverage Recommendations",
    "action": "coverage_advisory_completed",
    "recommendations": [],
    "coverage_gaps": [],
    "quick_actions": [
      {"title": "Apply for Insurance", "action": "start_insurance_application"},
      {"title": "Compare Policies", "action": "compare_policies"}
    ],
    "suggestions": []
  }
}
```

### 8.13 `review_and_edit_application` - Editable Form

```json
{
  "response_type": "review_and_edit_application",
  "data": {
    "type": "review_and_edit_application",
    "response": "Review and edit your answers, then submit:",
    "title": "Review & Edit Application - Policy 456",
    "policy_id": "456",
    "application_id": "APP_456_343_1707800000",
    "editable_fields": [
      {
        "question_number": 1,
        "question": "What's your full name?",
        "current_answer": "Hitesh Kumar",
        "field_type": "text",
        "field_key": "fullName",
        "options": null,
        "placeholder": "",
        "required": true,
        "is_edited": false
      }
    ],
    "total_fields": 6,
    "completion_percentage": 100,
    "ready_for_submission": true,
    "edit_mode": true,
    "next_action": {
      "title": "Submit Application",
      "action": "confirm_submit_application",
      "policy_id": "456",
      "requires_edited_answers": true
    },
    "back_action": {
      "title": "Cancel Application",
      "action": "cancel_application",
      "policy_id": "456"
    }
  }
}
```

**Render:** Editable form fields. On submit, send:

```json
{
  "type": "chat",
  "chat_session_id": "...",
  "query": "[{\"question_number\": 1, \"answer\": \"Hitesh Kumar\", \"field_key\": \"fullName\", \"question\": \"What's your full name?\", \"question_type\": \"text\"}]",
  "action": "confirm_submit_application",
  "policy_id": "456"
}
```

### 8.14 `application_completed` - Submission Success

```json
{
  "response_type": "application_completed",
  "data": {
    "type": "application_completed",
    "response": "Your application has been submitted successfully!",
    "application_id": "APP_456_343_1707800000",
    "reference_number": "REF20240213100000",
    "policy_id": "456",
    "order_id": "order_abc",
    "order_amount": 8999.0,
    "payment_session_id": "pay_session_xyz",
    "proposalNum": "PROP123",
    "show_payment_option": true,
    "next_steps": [
      "You will receive confirmation via email/SMS",
      "Our team will review within 24-48 hours",
      "You can track status anytime"
    ],
    "quick_actions": [
      {"title": "Track Application", "action": "track_application"},
      {"title": "Apply for Another Policy", "action": "select_insurance_type"}
    ]
  }
}
```

**Render:** Success card. If `show_payment_option: true`, launch Cashfree payment SDK with `payment_session_id` and `order_id`.

### 8.15 `application_cancelled` - Cancellation Confirmed

```json
{
  "response_type": "application_cancelled",
  "data": {
    "response": "Your application has been cancelled successfully.",
    "policy_id": "456",
    "quick_actions": [
      {"title": "Start New Application", "action": "select_insurance_type"},
      {"title": "Check Balance", "action": "check_balance"}
    ]
  }
}
```

### 8.16 `task_result` - Task Completion

```json
{
  "response_type": "task_result",
  "data": {
    "response": "Sure thing, let me look into that for you!",
    "action": "task_completed",
    "quick_actions": [
      {"title": "Get Financial Help", "action": "select_financial_assistance_type"},
      {"title": "Get Insurance", "action": "select_insurance_type"}
    ],
    "suggestions": []
  }
}
```

### 8.17 `eligibility_details` - Loan/Service Eligibility

```json
{
  "response_type": "eligibility_details",
  "data": {
    "type": "eligibility_details",
    "response": "Based on your info, here's what you're eligible for...",
    "eligibility_data": {}
  }
}
```

### 8.18 `error` - Error Response

```json
{
  "response_type": "error",
  "data": {
    "type": "error",
    "response": "Oops, something hiccupped on my end! Try that again?",
    "error": "Failed to process chat message",
    "action": "error",
    "show_service_options": false
  }
}
```

---

## 9. Intent System

The server detects user intent from the query text. Here's how each intent is handled:

| Intent                  | Response Type        | Description                                  | Streaming? |
|-------------------------|----------------------|----------------------------------------------|------------|
| `greeting`              | `chat_message`       | Hello, hi, hey                               | Yes        |
| `small_talk`            | `chat_message`       | Casual conversation                          | Yes        |
| `unknown`               | `chat_message`       | Unrecognized intent                          | Yes        |
| `task`                  | `task_result`        | Task-like request                            | Yes        |
| `reference_to_previous` | `chat_message`       | "what I asked earlier"                       | No         |
| `protection_score`      | `protection_score`   | "my protection score"                        | No         |
| `financial_education`   | `education`          | "what is term insurance"                     | No         |
| `claim_guidance`        | `claim_guidance`     | "how to file a claim"                        | No         |
| `live_event`            | `live_information`   | "stock market today"                         | No         |
| `off_topic`             | `off_topic`          | Non-finance topics                           | No         |
| `financial_assistance`  | `selection_menu`     | "I need a loan"                              | No         |
| `insurance_plan`        | `selection_menu`     | "I want to buy insurance"                    | No         |
| `insurance_analysis`    | `insurance_analysis` | "analyze my policy"                          | No         |
| `policy_query`          | `policy_query`       | "show my policies"                           | No         |
| `wallet_setup`          | `question`           | "set up my wallet"                           | No         |
| `rag_query`             | `information`        | Document-based queries                       | No         |

### Pre-Check Priority (before AI detection)

The server applies these pattern-based pre-checks in order:

1. **Reference patterns** → `reference_to_previous`
2. **Family member patterns** → `policy_query`
3. **Buy insurance patterns** → `insurance_plan`
4. **Upload/analyze patterns** → `insurance_analysis`
5. **AI intent detection** → Any of the above intents

---

## 10. Action System

Actions are triggered by button/option clicks. Send with `action` field in chat message.

### Sending an Action

```json
{
  "type": "chat",
  "chat_session_id": "...",
  "query": "Health Insurance",
  "action": "select_insurance_type",
  "insurance_type": "health"
}
```

### Action Routing Priority

1. `show_policy_details` + `policy_id` → Marketplace product details
2. `accept_policy_and_start_application` + `policy_id` → Start application form
3. `review_application` + `policy_id` → Show editable application
4. `confirm_submit_application` + `policy_id` → Submit to API + payment
5. `cancel_application` + `policy_id` → Cancel and exit
6. Policy query actions → Uploaded policy queries
7. Everything else → `route_enhanced_chatbot`

### Common Actions Reference

| Action                              | Parameters Needed             | Returns                     |
|-------------------------------------|-------------------------------|-----------------------------|
| `select_financial_assistance_type`  | -                             | `selection_menu`            |
| `select_insurance_type`             | -                             | `selection_menu`            |
| `start_insurance_application`       | `insurance_type`              | `selection_menu`            |
| `show_policy_details`               | `policy_id`                   | `policy_details`            |
| `accept_policy_and_start_application`| `policy_id`                  | `question`                  |
| `review_application`                | `policy_id`                   | `review_and_edit_application`|
| `confirm_submit_application`        | `policy_id`, edited answers   | `application_completed`     |
| `cancel_application`                | `policy_id`                   | `application_cancelled`     |
| `policy_query`                      | -                             | `policy_query`              |
| `policy_query_self`                 | -                             | `policy_query`              |
| `policy_query_family`               | -                             | `policy_query`              |
| `select_family_member`              | `policy_id` (member name)     | `policy_query`              |
| `select_policy`                     | `policy_id`                   | `policy_query`              |
| `view_gaps`                         | `policy_id`                   | `policy_query`              |
| `view_benefits`                     | `policy_id`                   | `policy_query`              |
| `view_recommendations`              | `policy_id`                   | `policy_query`              |
| `start_wallet_setup`                | -                             | `question`                  |
| `check_balance`                     | -                             | `general_response`          |
| `view_transactions`                 | -                             | `general_response`          |
| `add_policy` (redirect)             | -                             | Navigate to add policy page |
| `view_policies` (redirect)          | -                             | Navigate to policies page   |

---

## 11. Policy Query Flow

The policy query system has a multi-step flow controlled by `flow_step` in the response data.

### Flow Steps

```
User: "show my policies"
  ↓
Server detects policy_query intent
  ↓
┌──────────────────────────┐
│ Has policies?            │
│ NO → flow_step:          │
│      "no_policies"       │
│ YES ↓                    │
│ Has both self & family?  │
│ YES → "ask_self_or_family│
│ Only self → "show_self_  │
│             policies"    │
│ Only family → "show_     │
│               family_    │
│               members"   │
└──────────────────────────┘
```

### Flow Step Rendering Guide

| `flow_step`                | UI Rendering                                            |
|----------------------------|---------------------------------------------------------|
| `no_policies`              | Empty state + "Upload Policy" button                    |
| `ask_self_or_family`       | Two buttons: "My Policies" / "Family Policies"          |
| `show_self_policies`       | List of policy cards (tappable)                         |
| `show_family_members`      | List of family member chips/cards (tappable)            |
| `show_member_policies`     | List of policy cards for selected member                |
| `show_policy_details`      | Detailed policy view (markdown)                         |
| `show_policy_benefits`     | Benefits list (markdown)                                |
| `show_policy_gaps`         | Coverage gaps list (markdown)                           |
| `show_policy_recommendations` | Recommendations (markdown)                           |
| `specific_question_answer` | Q&A about a specific policy (markdown)                  |
| `general_response`         | General policy-related response                         |
| `no_member_policies`       | Empty state for selected member                         |
| `no_self_policies`         | No self policies message + upload prompt                |
| `no_family_policies`       | No family policies message                              |
| `policy_not_found`         | Policy not found error                                  |
| `show_filtered_policies`   | Filtered policy results                                 |

### Policy Card Data Structure

Each item in `data.policies`:

```json
{
  "policy_id": "POL123",
  "policy_type": "health",
  "insurer": "Star Health",
  "holder_name": "Hitesh",
  "relationship": "self",
  "sum_insured": 500000,
  "premium": 12000,
  "expiry_date": "2025-03-15",
  "status": "active"
}
```

### Tapping a Policy Card

```json
{
  "type": "chat",
  "chat_session_id": "...",
  "query": "show details for policy POL123",
  "action": "select_policy",
  "policy_id": "POL123"
}
```

### Tapping a Family Member

```json
{
  "type": "chat",
  "chat_session_id": "...",
  "query": "show wife policies",
  "action": "select_family_member",
  "policy_id": "wife"
}
```

---

## 12. Insurance Marketplace Flow

Complete buy-insurance flow:

```
1. User: "I want insurance"
   → Server: selection_menu (insurance types: health, life, auto)

2. User taps "Health Insurance"
   → Send: action=select_insurance_type, insurance_type=health
   → Server: selection_menu (insurance plans from marketplace)

3. User taps a plan
   → Send: action=show_policy_details, policy_id=INS_456
   → Server: policy_details (plan details + "Apply" button)

4. User taps "Apply"
   → Send: action=accept_policy_and_start_application, policy_id=INS_456
   → Server: question (first question of application form)

5. User answers questions (6-13 questions)
   → Server auto-continues with next question

6. All questions answered
   → Server: review_and_edit_application (editable form)

7. User reviews and submits
   → Send: action=confirm_submit_application, policy_id=INS_456
   → Server calls external API + payment API
   → Server: application_completed (with payment_session_id)

8. Flutter launches Cashfree payment SDK
```

---

## 13. Multi-Step Form Flows

The server maintains active Q&A sessions. When a multi-step flow is active, **any text message** from the user is treated as an answer to the current question.

### Active Session Types

| Session Type            | Key Format                                      | Questions |
|-------------------------|------------------------------------------------|-----------|
| Policy Application      | `{chat_session}_policy_application_{policy_id}` | 6-13      |
| Insurance Application   | `{chat_session}_insurance_{insurance_type}`      | ~6        |
| Financial Assistance    | `{chat_session}_financial_{assistance_type}`     | ~13       |
| Wallet Setup            | `{chat_session}_wallet_setup`                   | ~21       |

### How It Works

1. An action triggers a multi-step flow (e.g., `start_wallet_setup`)
2. Server sends first `question` response
3. User sends their answer as a regular `chat` message (no action needed)
4. Server detects the active session and routes the answer automatically
5. Server sends next `question` or completes the flow

### Session Completion Response Types

- `question` → Next question in the flow
- `review_application` → All answers collected, show review form
- `application_completed` → Flow completed successfully
- `application_cancelled` → User cancelled

---

## 14. Typing Indicators

### Sending Typing Status

```json
// User starts typing
{"type": "typing_start", "chat_session_id": "..."}

// User stops typing
{"type": "typing_stop", "chat_session_id": "..."}
```

### Receiving Typing Status (Multi-Device)

When the same user types on another device:

```json
{
  "type": "typing_indicator",
  "chat_session_id": "...",
  "user_id": 343,
  "is_typing": true,
  "device_id": "web_browser",
  "user_name": "Hitesh"
}
```

---

## 15. Presence System

### Automatic Presence Management

- **Online**: Set automatically when WebSocket connects
- **Away**: Auto-set after **5 minutes** of inactivity (no messages)
- **Offline**: Set after all devices disconnect (30-second grace period)
- Activity resets away → online automatically

### Multi-Device Behavior

User is online if **any** device is connected. User goes offline only when **all** devices disconnect.

### Manual Presence Update

```json
{"type": "presence_update", "status": "busy"}
```

---

## 16. Notification System

### Initial State

After authentication, server automatically sends:
1. `unread_count` with current unread notification count
2. Any pending notifications

### Notification Types

`policy_renewal`, `claim_update`, `payment_due`, `system`, `promotional`

### DND (Do Not Disturb)

```json
// Enable DND for 1 hour
{"type": "set_dnd", "enabled": true, "duration_minutes": 60}

// Disable DND
{"type": "set_dnd", "enabled": false}
```

### Notification Settings

```json
{
  "type": "update_notification_settings",
  "settings": {
    "policy_renewal": true,
    "claim_update": true,
    "payment_due": true,
    "promotional": false
  }
}
```

---

## 17. Heartbeat / Keep-Alive

### Server → Client Ping

The server sends `ping` every **60 seconds** if no messages received. **You MUST respond with `pong`.**

```dart
void onServerPing(Map<String, dynamic> msg) {
  send({'type': 'pong'});
}
```

### Client → Server Ping (Optional)

You can also send periodic pings:

```dart
Timer.periodic(Duration(seconds: 30), (_) {
  send({'type': 'ping'});
});
```

Server responds with `pong` containing `server_time`.

### Connection Health

- If server receives no heartbeat for **120 seconds**, connection is terminated
- Client should implement reconnection with exponential backoff

---

## 18. Error Handling

### Error Codes

| Error Code              | Description                        | Recoverable | Action                    |
|-------------------------|------------------------------------|-------------|---------------------------|
| `AUTH_FAILED`           | Authentication failed              | No          | Re-authenticate           |
| `TOKEN_EXPIRED`         | JWT token expired                  | No          | Refresh token & reconnect |
| `TOKEN_INVALID`         | JWT token invalid                  | No          | Re-login                  |
| `INVALID_MESSAGE`       | Bad message format                 | Yes         | Fix message format        |
| `INVALID_MESSAGE_TYPE`  | Unknown message type               | Yes         | Check message type        |
| `RATE_LIMIT_EXCEEDED`   | Too many messages                  | Yes         | Wait and retry            |
| `CHAT_SESSION_NOT_FOUND`| Chat session doesn't exist         | Yes         | Create new session        |
| `USER_NOT_FOUND`        | User not found                     | No          | Re-authenticate           |
| `NOT_AUTHENTICATED`     | No auth yet                        | Yes         | Send authenticate message |
| `INTERNAL_ERROR`        | Server error                       | Yes         | Retry                     |
| `CONNECTION_TIMEOUT`    | Connection timed out               | Yes         | Reconnect                 |
| `INVALID_JSON`          | Invalid JSON received              | Yes         | Fix JSON                  |

### WebSocket Close Codes

| Code | Meaning            |
|------|--------------------|
| 1000 | Normal closure     |
| 1001 | Going away         |
| 1002 | Protocol error     |
| 1008 | Policy violation   |
| 1011 | Internal error     |
| 4001 | Auth failed        |
| 4002 | Token expired      |
| 4003 | Rate limited       |
| 4004 | Session not found  |
| 4005 | Invalid message    |

### Reconnection Strategy

```dart
int _reconnectAttempts = 0;
final _maxReconnectAttempts = 10;

Duration _getBackoffDuration() {
  final seconds = min(pow(2, _reconnectAttempts).toInt(), 60);
  return Duration(seconds: seconds);
}

void reconnect() {
  if (_reconnectAttempts >= _maxReconnectAttempts) return;

  Future.delayed(_getBackoffDuration(), () {
    _reconnectAttempts++;
    connect();
  });
}

void onConnected() {
  _reconnectAttempts = 0; // Reset on successful connection
}
```

---

## 19. Rate Limiting

### Limits

- **Connection rate**: Limited per IP address
- **Chat messages**: Limited per user per time window
- **Burst protection**: Additional limit on rapid consecutive messages
- Heartbeat messages (`ping`/`pong`) are excluded from rate limiting

### Rate Limit Response

```json
{
  "type": "error",
  "error": "Rate limit exceeded for chat. Please slow down.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 20,
    "remaining": 0,
    "reset_after": 60
  },
  "recoverable": true
}
```

### Burst Limit Response

```json
{
  "type": "error",
  "error": "Too many messages too quickly. Please wait a moment.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "retry_after": 1
  },
  "recoverable": true
}
```

---

## 20. Multilingual Support

### Supported Languages

- English (`"en"`) — default
- Hindi (`"hi"`) — Devanagari script and romanized Hindi

### Language Detection

The server automatically detects language from the user's query. The detected language affects:

- `data.response` text (response in detected language)
- `data.suggestions` text
- `data.language` field
- Policy flow messages

### Hindi (Devanagari) Example

```json
{
  "type": "chat",
  "chat_session_id": "...",
  "query": "मेरी पॉलिसी दिखाओ"
}
```

Response:

```json
{
  "data": {
    "response": "ये रहीं आपकी 3 पॉलिसी। किसी पर भी टैप करें!",
    "language": "hi",
    "suggestions": ["मैं कहां कवर नहीं हूं?", "तुम क्या सुझाव दोगे?"]
  }
}
```

---

## 21. Flutter Dart Code Examples

### Full WebSocket Manager

```dart
import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:web_socket_channel/web_socket_channel.dart';

class EazrWebSocket {
  WebSocketChannel? _channel;
  StreamController<Map<String, dynamic>> _messageController =
      StreamController.broadcast();

  String? _chatSessionId;
  String? _userSessionId;
  int? _userId;
  bool _isAuthenticated = false;
  Timer? _pingTimer;
  int _reconnectAttempts = 0;

  Stream<Map<String, dynamic>> get messages => _messageController.stream;

  // ---- Connection ----

  Future<void> connect(String baseUrl, String jwtToken, {String? deviceId}) async {
    final uri = Uri.parse('$baseUrl/ws/chat?token=$jwtToken'
        '${deviceId != null ? '&device_id=$deviceId' : ''}');

    _channel = WebSocketChannel.connect(uri);

    _channel!.stream.listen(
      (data) => _onMessage(jsonDecode(data)),
      onDone: _onDisconnected,
      onError: (e) => _onError(e),
    );
  }

  void _onMessage(Map<String, dynamic> msg) {
    final type = msg['type'];

    switch (type) {
      case 'auth_success':
        _isAuthenticated = true;
        _userId = msg['user_id'];
        _chatSessionId = msg['chat_session_id'];
        _userSessionId = msg['user_session_id'];
        _reconnectAttempts = 0;
        _startPingTimer();
        break;

      case 'auth_failure':
        _isAuthenticated = false;
        break;

      case 'ping':
        // MUST respond to server ping
        send({'type': 'pong'});
        return; // Don't forward to UI

      case 'pong':
        return; // Don't forward to UI
    }

    _messageController.add(msg);
  }

  // ---- Sending Messages ----

  void send(Map<String, dynamic> message) {
    _channel?.sink.add(jsonEncode(message));
  }

  void sendChat(String query, {String? action, String? insuranceType,
      String? policyId, String? assistanceType, String? model}) {
    send({
      'type': 'chat',
      'chat_session_id': _chatSessionId,
      'query': query,
      if (action != null) 'action': action,
      if (insuranceType != null) 'insurance_type': insuranceType,
      if (policyId != null) 'policy_id': policyId,
      if (assistanceType != null) 'assistance_type': assistanceType,
      if (model != null) 'model': model,
    });
  }

  void sendTypingStart() {
    send({'type': 'typing_start', 'chat_session_id': _chatSessionId});
  }

  void sendTypingStop() {
    send({'type': 'typing_stop', 'chat_session_id': _chatSessionId});
  }

  // ---- Heartbeat ----

  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(Duration(seconds: 30), (_) {
      send({'type': 'ping'});
    });
  }

  // ---- Reconnection ----

  void _onDisconnected() {
    _isAuthenticated = false;
    _pingTimer?.cancel();
    _reconnect();
  }

  void _onError(dynamic error) {
    _onDisconnected();
  }

  void _reconnect() {
    if (_reconnectAttempts >= 10) return;
    final delay = Duration(seconds: min(pow(2, _reconnectAttempts).toInt(), 60));
    _reconnectAttempts++;
    Future.delayed(delay, () {
      // Re-connect with saved credentials
    });
  }

  // ---- Cleanup ----

  void dispose() {
    _pingTimer?.cancel();
    _channel?.sink.close();
    _messageController.close();
  }
}
```

### Message Handler Widget

```dart
class ChatMessageHandler {
  String _streamingBuffer = '';
  bool _isThinking = false;
  String _thinkingMessage = '';

  void handleMessage(Map<String, dynamic> msg) {
    switch (msg['type']) {
      case 'thinking':
        _handleThinking(msg);
        break;
      case 'chat_stream':
        _handleStream(msg);
        break;
      case 'chat_stream_end':
        _handleStreamEnd(msg);
        break;
      case 'chat_message':
        _handleChatMessage(msg);
        break;
      case 'notification':
        _handleNotification(msg);
        break;
      case 'unread_count':
        _handleUnreadCount(msg);
        break;
      case 'typing_indicator':
        _handleTypingIndicator(msg);
        break;
      case 'presence_status':
        _handlePresence(msg);
        break;
      case 'error':
        _handleError(msg);
        break;
    }
  }

  void _handleThinking(Map<String, dynamic> msg) {
    _isThinking = msg['status'] == 'started';
    _thinkingMessage = msg['message'] ?? '';
    // Update UI: show/hide thinking bubble
  }

  void _handleStream(Map<String, dynamic> msg) {
    _isThinking = false;
    _streamingBuffer += msg['token'];
    // Update UI: append to streaming message bubble
  }

  void _handleStreamEnd(Map<String, dynamic> msg) {
    final fullResponse = msg['full_response'];
    final data = msg['data'];
    final suggestions = (data['suggestions'] as List?)?.cast<String>() ?? [];
    _streamingBuffer = '';
    // Finalize message bubble + show suggestions
  }

  void _handleChatMessage(Map<String, dynamic> msg) {
    _isThinking = false;
    final responseType = msg['response_type'];
    final data = msg['data'];

    switch (responseType) {
      case 'chat_message':
        _renderTextBubble(data);
        break;
      case 'selection_menu':
        _renderSelectionMenu(data);
        break;
      case 'question':
        _renderFormQuestion(data);
        break;
      case 'policy_query':
        _renderPolicyQuery(data);
        break;
      case 'policy_details':
        _renderPolicyDetails(data);
        break;
      case 'insurance_analysis':
        _renderInsuranceAnalysis(data);
        break;
      case 'review_and_edit_application':
        _renderEditableForm(data);
        break;
      case 'application_completed':
        _renderApplicationSuccess(data);
        break;
      case 'application_cancelled':
        _renderCancellation(data);
        break;
      case 'protection_score':
        _renderProtectionScore(data);
        break;
      case 'education':
        _renderEducation(data);
        break;
      case 'claim_guidance':
        _renderClaimGuidance(data);
        break;
      case 'coverage_advisory':
        _renderCoverageAdvisory(data);
        break;
      case 'off_topic':
        _renderTextBubble(data);
        break;
      case 'live_information':
        _renderTextBubble(data);
        break;
      case 'error':
        _renderError(data);
        break;
      default:
        _renderTextBubble(data);
    }
  }

  // Implement each _render method for your UI...
  void _renderTextBubble(Map<String, dynamic> data) {
    final response = data['response'] ?? '';
    final suggestions = (data['suggestions'] as List?)?.cast<String>() ?? [];
    final quickActions = data['quick_actions'] as List? ?? [];
    // Build: text bubble + suggestion chips + action buttons
  }

  void _renderSelectionMenu(Map<String, dynamic> data) {
    final response = data['response'] ?? '';
    final options = data['options'] as List? ?? [];
    // Build: message + option cards
    // Each option: {"title": "...", "action": "...", ...}
  }

  void _renderFormQuestion(Map<String, dynamic> data) {
    final question = data['response'] ?? data['message'] ?? '';
    final fieldType = data['field_type'] ?? 'text';
    final options = data['options'] as List?;
    final progress = data['progress'] as num? ?? 0;
    final questionNumber = data['question_number'];
    final totalQuestions = data['total_questions'];
    // Build: question + input field + progress bar
  }

  void _renderPolicyQuery(Map<String, dynamic> data) {
    final flowStep = data['flow_step'] ?? '';
    final policies = data['policies'] as List? ?? [];
    final familyMembers = data['family_members'] as List? ?? [];
    final quickActions = data['quick_actions'] as List? ?? [];
    // Build based on flow_step (see Section 11)
  }
}
```

### Action Button Handler

```dart
void onActionButtonTap(Map<String, dynamic> actionData, EazrWebSocket ws) {
  final action = actionData['action'] as String;
  final policyId = actionData['policy_id'] as String?;
  final redirect = actionData['redirect'] as bool? ?? false;
  final redirectPage = actionData['redirect_page'] as String?;

  // Handle redirect actions (navigate to Flutter screen)
  if (redirect && redirectPage != null) {
    switch (redirectPage) {
      case 'add_policy':
        Navigator.pushNamed(context, '/add-policy');
        return;
      case 'my_policies':
        Navigator.pushNamed(context, '/my-policies');
        return;
    }
  }

  // Send action to server
  ws.sendChat(
    actionData['title'] ?? action,
    action: action,
    policyId: policyId,
    insuranceType: actionData['insurance_type'],
    assistanceType: actionData['assistance_type'],
  );
}
```

### Suggestion Chip Handler

```dart
void onSuggestionTap(String suggestion, EazrWebSocket ws) {
  ws.sendChat(suggestion);
}
```

---

## 22. Complete Message Type Reference

### Client → Server

| Type                            | Purpose                              |
|---------------------------------|--------------------------------------|
| `authenticate`                  | Send JWT token for authentication    |
| `chat`                          | Send chat message or action          |
| `typing_start`                  | User started typing                  |
| `typing_stop`                   | User stopped typing                  |
| `presence_update`               | Update presence status               |
| `ping`                          | Client heartbeat                     |
| `pong`                          | Response to server ping              |
| `join_chat`                     | Switch to different chat session     |
| `leave_chat`                    | Leave current chat session           |
| `mark_notification_read`        | Mark single notification as read     |
| `mark_all_read`                 | Mark all notifications as read       |
| `get_notifications`             | Request notification list             |
| `set_dnd`                       | Enable/disable Do Not Disturb        |
| `update_notification_settings`  | Update notification preferences      |
| `subscribe_topic`               | Subscribe to notification topic      |
| `unsubscribe_topic`             | Unsubscribe from notification topic  |

### Server → Client

| Type                    | Purpose                                    |
|-------------------------|--------------------------------------------|
| `connection_ack`        | Connection accepted, auth required         |
| `auth_success`          | Authentication successful                  |
| `auth_failure`          | Authentication failed                      |
| `chat_message`          | Complete chat response                     |
| `chat_stream`           | Streaming token (for AI responses)         |
| `chat_stream_end`       | Stream complete with full data             |
| `thinking`              | Processing indicator (started/stopped)     |
| `typing_indicator`      | Other device/user typing status            |
| `presence_status`       | User presence change                       |
| `ping`                  | Server heartbeat (must respond with pong)  |
| `pong`                  | Response to client ping                    |
| `error`                 | Error message                              |
| `notification`          | Push notification                          |
| `unread_count`          | Unread notification count update           |
| `notification_list`     | List of notifications                      |
| `dnd_status`            | DND status response                        |
| `notification_settings` | Notification settings response             |
| `topic_subscribed`      | Topic subscription confirmed               |
| `topic_unsubscribed`    | Topic unsubscription confirmed             |
| `chat_joined`           | Chat session joined successfully           |
| `chat_left`             | Chat session left successfully             |

---

## Quick Reference: Response Type → Flutter Widget Mapping

| `response_type`               | Widget                                           |
|-------------------------------|--------------------------------------------------|
| `chat_message`                | Text bubble + suggestions                        |
| `selection_menu`              | Message + option cards/buttons                   |
| `question`                    | Question + input field + progress bar            |
| `policy_query`                | Policy cards / family member list (by flow_step) |
| `policy_details`              | Detailed policy card                             |
| `insurance_analysis`          | Message + redirect buttons                       |
| `review_and_edit_application` | Editable form + submit/cancel buttons            |
| `application_completed`       | Success card + payment (if applicable)           |
| `application_cancelled`       | Cancellation confirmation + action buttons       |
| `protection_score`            | Score display + suggestions                      |
| `education`                   | Education card + suggestions                     |
| `claim_guidance`              | Guidance text + suggestions                      |
| `coverage_advisory`           | Advisory card + recommendations                  |
| `off_topic`                   | Text bubble + redirect suggestions               |
| `live_information`            | Information card + suggestions                   |
| `task_result`                 | Result text + action buttons                     |
| `eligibility_details`         | Eligibility details card                         |
| `error`                       | Error message display                            |
