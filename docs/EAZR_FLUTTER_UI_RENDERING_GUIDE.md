# EAZR WebSocket — Flutter UI Rendering Guide

Complete guide for rendering every WebSocket response type as Flutter widgets. This covers **how to build the UI** for each `response_type` and `flow_step` — with exact JSON data structures and Flutter widget code.

> **Prerequisite:** Read `EAZR_WEBSOCKET_FLUTTER_INTEGRATION.md` for the WebSocket protocol (connection, auth, sending messages, ping/pong, etc.). This guide focuses **only on UI rendering**.

---

## Table of Contents

1. [Message Routing — How to Decide Which Widget to Show](#1-message-routing)
2. [Chat Message (Simple Text + Suggestions)](#2-chat-message-simple-text)
3. [Streaming Text (Token-by-Token Typing)](#3-streaming-text)
4. [Thinking Indicator (Rotating Words)](#4-thinking-indicator)
5. [Suggestion Chips](#5-suggestion-chips)
6. [Quick Action Buttons](#6-quick-action-buttons)
7. [Selection Menu (Cards with Icons)](#7-selection-menu)
8. [Policy Query — ask_self_or_family](#8-policy-query-ask-self-or-family)
9. [Policy Query — show_family_members](#9-policy-query-show-family-members)
10. [Policy Query — show_self_policies / show_member_policies](#10-policy-query-show-policies)
11. [Policy Query — show_policy_details (Full Card)](#11-policy-query-show-policy-details)
12. [Policy Query — show_policy_benefits](#12-policy-query-show-policy-benefits)
13. [Policy Query — show_policy_gaps](#13-policy-query-show-policy-gaps)
14. [Policy Query — show_policy_recommendations](#14-policy-query-show-policy-recommendations)
15. [Policy Query — no_policies (Empty State)](#15-policy-query-no-policies)
16. [Question Form (Multi-Step Q&A)](#16-question-form)
17. [Review & Edit Application](#17-review-edit-application)
18. [Application Completed (Success + Payment)](#18-application-completed)
19. [Application Cancelled](#19-application-cancelled)
20. [Insurance Analysis (Add Policy Prompt)](#20-insurance-analysis)
21. [Education / Claim Guidance / Off-Topic / Live Info](#21-text-response-types)
22. [Protection Score](#22-protection-score)
23. [Error Response](#23-error-response)
24. [Notification Card](#24-notification-card)
25. [Complete Chat Screen Widget](#25-complete-chat-screen)

---

## 1. Message Routing — How to Decide Which Widget to Show {#1-message-routing}

Every `chat_message` from the server has `response_type` and inside `data` there may be a `flow_step`. Use this routing logic:

```dart
Widget buildResponseWidget(Map<String, dynamic> serverMessage) {
  final responseType = serverMessage['response_type'] as String;
  final data = serverMessage['data'] as Map<String, dynamic>;
  final flowStep = data['flow_step'] as String?;

  // 1. Policy query — route by flow_step
  if (responseType == 'policy_query') {
    switch (flowStep) {
      case 'ask_self_or_family':
        return PolicySelfFamilySelector(data: data);
      case 'show_family_members':
        return FamilyMemberSelector(data: data);
      case 'show_self_policies':
      case 'show_member_policies':
        return PolicyCardList(data: data);
      case 'show_policy_details':
        return PolicyDetailsCard(data: data);
      case 'show_policy_benefits':
        return PolicyBenefitsList(data: data);
      case 'show_policy_gaps':
        return PolicyGapsList(data: data);
      case 'show_policy_recommendations':
        return PolicyRecommendationsList(data: data);
      case 'no_policies':
        return NoPoliciesEmptyState(data: data);
      default:
        return TextMessageBubble(data: data);
    }
  }

  // 2. Other response types
  switch (responseType) {
    case 'chat_message':
      return TextMessageBubble(data: data);
    case 'selection_menu':
      return SelectionMenu(data: data);
    case 'question':
      return QuestionForm(data: data);
    case 'review_and_edit_application':
      return ReviewApplicationForm(data: data);
    case 'application_completed':
      return ApplicationCompletedCard(data: data);
    case 'application_cancelled':
      return ApplicationCancelledCard(data: data);
    case 'insurance_analysis':
      return InsuranceAnalysisPrompt(data: data);
    case 'policy_details':
      return MarketplacePolicyDetails(data: data);
    case 'education':
    case 'claim_guidance':
    case 'off_topic':
    case 'live_information':
    case 'information':
    case 'protection_score':
      return TextMessageBubble(data: data);
    case 'eligibility_details':
      return EligibilityDetailsCard(data: data);
    case 'error':
      return ErrorMessageBubble(data: data);
    default:
      return TextMessageBubble(data: data);
  }
}
```

---

## 2. Chat Message (Simple Text + Suggestions) {#2-chat-message-simple-text}

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "chat_message",
  "data": {
    "response": "Hello! How can I assist you with your insurance needs today?",
    "message": "Hello! How can I assist you with your insurance needs today?",
    "action": "casual_conversation",
    "suggestions": ["Show my policies", "What is my coverage?", "Help me with insurance"],
    "quick_actions": [],
    "language": "en"
  }
}
```

### Flutter Widget

```dart
class TextMessageBubble extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(String)? onSuggestionTap;
  final Function(Map<String, dynamic>)? onQuickAction;

  const TextMessageBubble({
    required this.data,
    this.onSuggestionTap,
    this.onQuickAction,
  });

  @override
  Widget build(BuildContext context) {
    final text = data['response'] ?? data['message'] ?? '';
    final suggestions = List<String>.from(data['suggestions'] ?? []);
    final quickActions = List<Map<String, dynamic>>.from(
      (data['quick_actions'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Text bubble
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16).copyWith(
              bottomLeft: const Radius.circular(4),
            ),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(
            text,
            style: const TextStyle(fontSize: 14, height: 1.5, color: Color(0xFF333333)),
          ),
        ),

        // Quick action buttons
        if (quickActions.isNotEmpty) ...[
          const SizedBox(height: 12),
          QuickActionButtons(actions: quickActions, onTap: onQuickAction),
        ],

        // Suggestion chips
        if (suggestions.isNotEmpty) ...[
          const SizedBox(height: 8),
          SuggestionChips(suggestions: suggestions, onTap: onSuggestionTap),
        ],
      ],
    );
  }
}
```

### User Message Bubble

```dart
class UserMessageBubble extends StatelessWidget {
  final String text;
  final String time;

  const UserMessageBubble({required this.text, required this.time});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerRight,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.7,
            ),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF007BFF),
              borderRadius: BorderRadius.circular(16).copyWith(
                bottomRight: const Radius.circular(4),
              ),
            ),
            child: Text(
              text,
              style: const TextStyle(fontSize: 14, height: 1.5, color: Colors.white),
            ),
          ),
          const SizedBox(height: 4),
          Text(time, style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
        ],
      ),
    );
  }
}
```

---

## 3. Streaming Text (Token-by-Token Typing) {#3-streaming-text}

Used for `greeting`, `small_talk`, `unknown` intents only. Tokens arrive one-by-one via `chat_stream` messages.

### Server JSON Sequence

```
1. {"type": "chat_stream", "token": "Hello", "token_index": 1, "is_final": false}
2. {"type": "chat_stream", "token": "!", "token_index": 2, "is_final": false}
3. {"type": "chat_stream", "token": " How", "token_index": 3, "is_final": false}
...
N. {"type": "chat_stream_end", "full_response": "Hello! How can I help?", "data": {...}}
```

### Flutter Widget

```dart
class StreamingMessageBubble extends StatelessWidget {
  final String currentText;
  final bool isStreaming;

  const StreamingMessageBubble({
    required this.currentText,
    required this.isStreaming,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16).copyWith(
          bottomLeft: const Radius.circular(4),
        ),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Flexible(
            child: Text(
              currentText,
              style: const TextStyle(fontSize: 14, height: 1.5, color: Color(0xFF333333)),
            ),
          ),
          if (isStreaming) ...[
            const SizedBox(width: 2),
            _BlinkingCursor(),
          ],
        ],
      ),
    );
  }
}

class _BlinkingCursor extends StatefulWidget {
  @override
  State<_BlinkingCursor> createState() => _BlinkingCursorState();
}

class _BlinkingCursorState extends State<_BlinkingCursor>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _controller,
      child: Container(
        width: 2,
        height: 16,
        color: const Color(0xFF333333),
      ),
    );
  }
}
```

### State Management for Streaming

```dart
// In your chat state management
String _streamBuffer = '';
bool _isStreaming = false;

void handleStreamToken(Map<String, dynamic> data) {
  final token = data['token'] as String? ?? '';
  setState(() {
    if (!_isStreaming) {
      _isStreaming = true;
      _streamBuffer = '';
    }
    _streamBuffer += token;
  });
}

void handleStreamEnd(Map<String, dynamic> data) {
  setState(() {
    _isStreaming = false;
    final fullResponse = data['full_response'] as String? ?? _streamBuffer;
    // Add as final message to chat list
    _messages.add(ChatBubble(
      isUser: false,
      text: fullResponse,
      data: data['data'] ?? {},
      responseType: 'chat_message',
    ));
    _streamBuffer = '';
  });
}
```

---

## 4. Thinking Indicator (Rotating Words) {#4-thinking-indicator}

Server sends rotating words every 1 second: `Thinking...` -> `Analyzing...` -> `Processing...` etc.

### Server JSON

```json
// Started (repeats every 1 second with different word):
{"type": "thinking", "status": "started", "message": "Analyzing...", "chat_session_id": "..."}

// Stopped (response is ready):
{"type": "thinking", "status": "stopped", "message": "", "chat_session_id": "..."}
```

### Word List (15 words, rotated by server)

```
Thinking, Analyzing, Processing, Searching, Computing,
Reviewing, Checking, Evaluating, Preparing, Gathering,
Scanning, Compiling, Assessing, Fetching, Resolving
```

### Flutter Widget

```dart
class ThinkingIndicator extends StatelessWidget {
  final String word;

  const ThinkingIndicator({required this.word});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFFF8F9FA),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: const Color(0xFF007BFF),
            ),
          ),
          const SizedBox(width: 8),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 300),
            transitionBuilder: (child, animation) => FadeTransition(
              opacity: animation,
              child: SlideTransition(
                position: Tween<Offset>(
                  begin: const Offset(0, 0.3),
                  end: Offset.zero,
                ).animate(animation),
                child: child,
              ),
            ),
            child: Text(
              word,
              key: ValueKey(word),
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey.shade600,
                fontStyle: FontStyle.italic,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
```

### State Management

```dart
bool _isThinking = false;
String _thinkingWord = 'Thinking...';

void handleThinking(Map<String, dynamic> data) {
  final status = data['status'] as String;
  setState(() {
    if (status == 'started') {
      _isThinking = true;
      _thinkingWord = data['message'] as String? ?? 'Thinking...';
    } else {
      _isThinking = false;
      _thinkingWord = '';
    }
  });
}
```

---

## 5. Suggestion Chips {#5-suggestion-chips}

Horizontal scrollable chip buttons shown below responses.

### Data (inside `data.suggestions`)

```json
["Show my policies", "What is my coverage?", "Help me with insurance"]
```

### Flutter Widget

```dart
class SuggestionChips extends StatelessWidget {
  final List<String> suggestions;
  final Function(String)? onTap;

  const SuggestionChips({required this.suggestions, this.onTap});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: suggestions.map((text) {
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: GestureDetector(
              onTap: () => onTap?.call(text),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0xFFF0F0F0),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  text,
                  style: const TextStyle(fontSize: 12, color: Color(0xFF333333)),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
```

### Sending a Suggestion Tap

```dart
// When user taps a suggestion chip:
void onSuggestionTap(String text) {
  wsService.sendMessage(text); // sends: {type: "chat", query: text}
}
```

---

## 6. Quick Action Buttons {#6-quick-action-buttons}

Action buttons shown below responses. Can be `redirect` (navigate in app) or WebSocket action.

### Data (inside `data.quick_actions`)

```json
[
  {"title": "View All Benefits", "action": "view_benefits", "policy_id": "ANL_282_abc"},
  {"title": "Coverage Gaps", "action": "view_gaps", "policy_id": "ANL_282_abc"},
  {"title": "Back to Policies", "action": "policy_query_self"},
  {"title": "Add Policy", "action": "add_policy", "redirect": true, "redirect_page": "add_policy"}
]
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Button label |
| `action` | string | Action to send via WebSocket |
| `policy_id` | string? | Policy ID to include in action |
| `redirect` | bool? | If `true` → navigate in Flutter app, do NOT send WebSocket message |
| `redirect_page` | string? | Flutter page/route to navigate to |

### Flutter Widget

```dart
class QuickActionButtons extends StatelessWidget {
  final List<Map<String, dynamic>> actions;
  final Function(Map<String, dynamic>)? onTap;

  const QuickActionButtons({required this.actions, this.onTap});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: actions.map((action) {
        final isRedirect = action['redirect'] == true;
        return GestureDetector(
          onTap: () => onTap?.call(action),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: isRedirect ? const Color(0xFF007BFF) : const Color(0xFFF0F0F0),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              action['title'] ?? '',
              style: TextStyle(
                fontSize: 13,
                color: isRedirect ? Colors.white : const Color(0xFF333333),
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
```

### Handling Quick Action Taps

```dart
void onQuickActionTap(Map<String, dynamic> action) {
  final isRedirect = action['redirect'] == true;

  if (isRedirect) {
    // Navigate to a Flutter page — do NOT send WebSocket message
    final page = action['redirect_page'] as String?;
    switch (page) {
      case 'add_policy':
        Navigator.pushNamed(context, '/add-policy');
        break;
      case 'my_policies':
        Navigator.pushNamed(context, '/my-policies');
        break;
      default:
        Navigator.pushNamed(context, '/$page');
    }
  } else {
    // Send WebSocket action
    final actionName = action['action'] as String;
    final policyId = action['policy_id'] as String?;
    final query = action['query'] ?? action['title'] ?? actionName.replaceAll('_', ' ');

    wsService.sendAction(actionName, query: query, policyId: policyId);
  }
}
```

---

## 7. Selection Menu (Cards with Icons) {#7-selection-menu}

Used for insurance type selection, financial assistance type selection, service selection.

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "selection_menu",
  "data": {
    "response": "What type of insurance are you looking for?",
    "type": "insurance_type_selection",
    "options": [
      {
        "title": "Health Insurance",
        "subtitle": "Medical coverage for you and family",
        "action": "select_insurance",
        "insurance_type": "health",
        "icon": "health"
      },
      {
        "title": "Life Insurance",
        "subtitle": "Financial protection for loved ones",
        "action": "select_insurance",
        "insurance_type": "life",
        "icon": "life"
      },
      {
        "title": "Motor Insurance",
        "subtitle": "Car and bike coverage",
        "action": "select_insurance",
        "insurance_type": "motor",
        "icon": "motor"
      }
    ]
  }
}
```

### Flutter Widget

```dart
class SelectionMenu extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(Map<String, dynamic>)? onSelect;

  const SelectionMenu({required this.data, this.onSelect});

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? '';
    final options = List<Map<String, dynamic>>.from(
      (data['options'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Text message
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(response, style: const TextStyle(fontSize: 14, height: 1.5)),
        ),
        const SizedBox(height: 12),

        // Selection cards
        ...options.map((option) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: GestureDetector(
              onTap: () => onSelect?.call(option),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Row(
                  children: [
                    // Icon
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: _getIconBgColor(option['icon']),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Center(
                        child: Text(
                          _getIconEmoji(option['icon']),
                          style: const TextStyle(fontSize: 18),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Text
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            option['title'] ?? '',
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 14,
                              color: Color(0xFF333333),
                            ),
                          ),
                          if (option['subtitle'] != null)
                            Text(
                              option['subtitle'],
                              style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                            ),
                        ],
                      ),
                    ),
                    Icon(Icons.chevron_right, color: Colors.grey.shade400),
                  ],
                ),
              ),
            ),
          );
        }),
      ],
    );
  }

  String _getIconEmoji(String? icon) {
    switch (icon?.toLowerCase()) {
      case 'health': return '❤️';
      case 'life': return '💜';
      case 'motor': return '🚗';
      case 'home': return '🏠';
      case 'travel': return '✈️';
      default: return '📋';
    }
  }

  Color _getIconBgColor(String? icon) {
    switch (icon?.toLowerCase()) {
      case 'health': return const Color(0xFFFFEBEE);
      case 'life': return const Color(0xFFF3E5F5);
      case 'motor': return const Color(0xFFE3F2FD);
      default: return const Color(0xFFF5F5F5);
    }
  }
}
```

### Sending Selection

```dart
void onSelectionTap(Map<String, dynamic> option) {
  wsService.sendAction(
    option['action'],
    query: option['title'],
    insuranceType: option['insurance_type'],
    assistanceType: option['assistance_type'],
  );
}
```

---

## 8. Policy Query — ask_self_or_family {#8-policy-query-ask-self-or-family}

Shown when user has both self and family policies. Two tappable cards: "My Policies" and "Family Policies".

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "response": "You have 3 self policies and 1 family policies.",
    "flow_step": "ask_self_or_family",
    "has_policies": true,
    "policy_count": 4,
    "self_count": 3,
    "family_count": 1,
    "policies": [],
    "family_members": [],
    "quick_actions": [
      {"title": "My Policies", "action": "policy_query_self"},
      {"title": "Family Policies", "action": "policy_query_family"}
    ]
  }
}
```

### Flutter Widget

```dart
class PolicySelfFamilySelector extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(String action)? onSelect;

  const PolicySelfFamilySelector({required this.data, this.onSelect});

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? '';
    final selfCount = data['self_count'] ?? 0;
    final familyCount = data['family_count'] ?? 0;
    final quickActions = List<Map<String, dynamic>>.from(
      (data['quick_actions'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Text message
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(response, style: const TextStyle(fontSize: 14, height: 1.5)),
        ),
        const SizedBox(height: 12),

        // Self policies card
        if (selfCount > 0)
          _buildSelectorCard(
            icon: '👤',
            iconBgColor: const Color(0xFFE3F2FD),
            title: 'My Policies',
            subtitle: '$selfCount policies',
            onTap: () => onSelect?.call('policy_query_self'),
          ),

        const SizedBox(height: 8),

        // Family policies card
        if (familyCount > 0)
          _buildSelectorCard(
            icon: '👨‍👩‍👧‍👦',
            iconBgColor: const Color(0xFFF3E5F5),
            title: 'Family Policies',
            subtitle: '$familyCount policies',
            onTap: () => onSelect?.call('policy_query_family'),
          ),

        // Quick action buttons (same as cards above, as pill buttons)
        if (quickActions.isNotEmpty) ...[
          const SizedBox(height: 12),
          QuickActionButtons(actions: quickActions),
        ],
      ],
    );
  }

  Widget _buildSelectorCard({
    required String icon,
    required Color iconBgColor,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: iconBgColor,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Center(child: Text(icon, style: const TextStyle(fontSize: 18))),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                Text(subtitle, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
```

### Sending Selection

```dart
// User taps "My Policies":
wsService.sendAction('policy_query_self');

// User taps "Family Policies":
wsService.sendAction('policy_query_family');
```

---

## 9. Policy Query — show_family_members {#9-policy-query-show-family-members}

Shows family member cards to select whose policies to view.

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "response": "You have 1 family policies. Select a family member to view their policies.",
    "flow_step": "show_family_members",
    "family_members": ["Other"],
    "policy_count": 1,
    "quick_actions": [
      {"title": "Other (1)", "action": "policy_query_family", "query": "Show policies for Other"},
      {"title": "Back", "action": "policy_query"}
    ]
  }
}
```

### Flutter Widget

```dart
class FamilyMemberSelector extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(String member)? onSelectMember;
  final Function(Map<String, dynamic>)? onQuickAction;

  const FamilyMemberSelector({
    required this.data,
    this.onSelectMember,
    this.onQuickAction,
  });

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? '';
    final members = List<String>.from(data['family_members'] ?? []);
    final quickActions = List<Map<String, dynamic>>.from(
      (data['quick_actions'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Text message
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(response, style: const TextStyle(fontSize: 14, height: 1.5)),
        ),
        const SizedBox(height: 12),

        // Family member cards
        ...members.map((member) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: GestureDetector(
              onTap: () => onSelectMember?.call(member),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: const Color(0xFFE3F2FD),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Center(
                        child: Text('👤', style: TextStyle(fontSize: 18)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(member, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                        Text('View policies', style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          );
        }),

        // Quick action buttons
        if (quickActions.isNotEmpty) ...[
          const SizedBox(height: 8),
          QuickActionButtons(actions: quickActions, onTap: onQuickAction),
        ],
      ],
    );
  }
}
```

### Sending Selection

```dart
// User taps a family member card:
void onSelectMember(String member) {
  wsService.sendAction(
    'policy_query_family',
    query: 'Show policies for $member',
  );
}
```

---

## 10. Policy Query — show_self_policies / show_member_policies {#10-policy-query-show-policies}

List of policy cards. Each card shows provider, type, coverage amount, and protection score.

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "response": "Here are the policies for other.",
    "flow_step": "show_member_policies",
    "selected_member": "Other",
    "policy_count": 1,
    "policies": [
      {
        "policyId": "ANL_282_ae9929261fea",
        "policy_id": "ANL_282_ae9929261fea",
        "provider": "Care Health Insurance Limited",
        "policyType": "accidental",
        "policy_type": "accidental",
        "coverage": 100000,
        "protectionScore": 75,
        "protection_score": 75
      }
    ],
    "quick_actions": [
      {"title": "Care Health Ins... (accidental)", "action": "show_policy_details", "policy_id": "ANL_282_ae9929261fea"},
      {"title": "View All Policies", "action": "policy_query"}
    ]
  }
}
```

### Flutter Widget

```dart
class PolicyCardList extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(String policyId)? onPolicyTap;
  final Function(Map<String, dynamic>)? onQuickAction;

  const PolicyCardList({required this.data, this.onPolicyTap, this.onQuickAction});

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? '';
    final policies = List<Map<String, dynamic>>.from(
      (data['policies'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );
    final quickActions = List<Map<String, dynamic>>.from(
      (data['quick_actions'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Text message
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(response, style: const TextStyle(fontSize: 14, height: 1.5)),
        ),
        const SizedBox(height: 12),

        // Policy cards
        ...policies.map((policy) {
          final policyId = policy['policyId'] ?? policy['policy_id'] ?? '';
          final provider = policy['provider'] ?? 'Unknown';
          final policyType = policy['policyType'] ?? policy['policy_type'] ?? 'Insurance';
          final coverage = policy['coverage'] ?? 0;
          final score = policy['protectionScore'] ?? policy['protection_score'] ?? 0;

          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: GestureDetector(
              onTap: () => onPolicyTap?.call(policyId),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Row(
                  children: [
                    // Policy icon
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        color: _getIconBgColor(policyType),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Center(
                        child: Text(_getIcon(policyType), style: const TextStyle(fontSize: 20)),
                      ),
                    ),
                    const SizedBox(width: 12),

                    // Provider + type
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            provider,
                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          Text(
                            policyType,
                            style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                          ),
                        ],
                      ),
                    ),

                    // Coverage + score
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          _formatCoverage(coverage),
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                            color: Color(0xFF28A745),
                          ),
                        ),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text('🛡️ ', style: TextStyle(fontSize: 12)),
                            Text(
                              '$score%',
                              style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          );
        }),

        // Quick action buttons
        if (quickActions.isNotEmpty) ...[
          const SizedBox(height: 8),
          QuickActionButtons(actions: quickActions, onTap: onQuickAction),
        ],
      ],
    );
  }

  String _formatCoverage(dynamic amount) {
    final num value = amount is num ? amount : 0;
    if (value >= 10000000) return '₹${(value / 10000000).toStringAsFixed(1)} Cr';
    if (value >= 100000) return '₹${(value / 100000).toStringAsFixed(1)} L';
    if (value >= 1000) return '₹${(value / 1000).toStringAsFixed(1)} K';
    return '₹$value';
  }

  String _getIcon(String type) {
    final t = type.toLowerCase();
    if (t.contains('health')) return '❤️';
    if (t.contains('life')) return '💜';
    if (t.contains('motor') || t.contains('car')) return '🚗';
    if (t.contains('home')) return '🏠';
    if (t.contains('travel')) return '✈️';
    return '📋';
  }

  Color _getIconBgColor(String type) {
    final t = type.toLowerCase();
    if (t.contains('health')) return const Color(0xFFFFEBEE);
    if (t.contains('life')) return const Color(0xFFF3E5F5);
    if (t.contains('motor')) return const Color(0xFFE3F2FD);
    return const Color(0xFFF5F5F5);
  }
}
```

### Sending Policy Details Request

```dart
void onPolicyTap(String policyId) {
  wsService.sendAction(
    'show_policy_details',
    query: 'Show details for policy $policyId',
    policyId: policyId,
  );
}
```

---

## 11. Policy Query — show_policy_details (Full Card) {#11-policy-query-show-policy-details}

Full policy details card with 2-column grid layout: Policy Number, Coverage Amount, Premium, Validity, Protection Score, Coverage Gaps, and Key Benefits preview.

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "response": "Care Health Insurance Limited - accidental",
    "flow_step": "show_policy_details",
    "policy_id": "ANL_282_ae9929261fea",
    "policy_data": {
      "provider": "Care Health Insurance Limited",
      "policyType": "accidental",
      "policyNumber": "26016147",
      "formattedCoverage": "₹100,000",
      "formattedPremium": "₹1",
      "formattedValidity": "2026-01-03 to 2027-01-02",
      "protectionScore": 75,
      "gapCount": 6,
      "highGapCount": 2,
      "keyBenefits": [
        "Personal Accident Cover-Sum Insured: Rs. 1,00,000",
        "Accidental Death: 100% of Sum Insured payout",
        "Permanent Partial Disability: Up to Sum Insured as per PPD table",
        "Permanent Total Disability: Up to Sum Insured as per PTD table",
        "Health Service-Doctors on Call: Unlimited GP consultations covered"
      ]
    },
    "quick_actions": [
      {"title": "View All Benefits", "action": "view_benefits", "policy_id": "ANL_282_ae9929261fea"},
      {"title": "Coverage Gaps", "action": "view_gaps", "policy_id": "ANL_282_ae9929261fea"},
      {"title": "Back to Policies", "action": "policy_query_self"}
    ]
  }
}
```

### Flutter Widget

```dart
class PolicyDetailsCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(Map<String, dynamic>)? onQuickAction;

  const PolicyDetailsCard({required this.data, this.onQuickAction});

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? '';
    final policyData = Map<String, dynamic>.from(data['policy_data'] ?? {});
    final quickActions = List<Map<String, dynamic>>.from(
      (data['quick_actions'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    final provider = policyData['provider'] ?? 'Unknown Provider';
    final policyType = policyData['policyType'] ?? 'Insurance';
    final policyNumber = policyData['policyNumber'] ?? 'N/A';
    final coverage = policyData['formattedCoverage'] ?? 'N/A';
    final premium = policyData['formattedPremium'] ?? 'N/A';
    final validity = policyData['formattedValidity'] ?? 'N/A';
    final score = policyData['protectionScore'] ?? 0;
    final gapCount = policyData['gapCount'] ?? 0;
    final highGapCount = policyData['highGapCount'] ?? 0;
    final keyBenefits = List<String>.from(policyData['keyBenefits'] ?? []);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Text message
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(response, style: const TextStyle(fontSize: 14, height: 1.5)),
        ),
        const SizedBox(height: 12),

        // Policy details card
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header with icon
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: const Color(0xFFF5F5F5),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Center(child: Text('📋', style: TextStyle(fontSize: 24))),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(provider, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                          Text(policyType, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              Divider(height: 1, color: Colors.grey.shade100),

              // Info grid (2 columns)
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    _buildInfoRow('POLICY NUMBER', policyNumber, 'COVERAGE AMOUNT', coverage),
                    const SizedBox(height: 12),
                    _buildInfoRow('PREMIUM', premium, 'VALIDITY', validity),
                    const SizedBox(height: 12),
                    _buildInfoRowWithWidgets(
                      'PROTECTION SCORE',
                      _buildScoreBadge(score),
                      'COVERAGE GAPS',
                      Text(
                        '$gapCount gaps ($highGapCount high priority)',
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                      ),
                    ),
                  ],
                ),
              ),

              // Key benefits preview
              if (keyBenefits.isNotEmpty) ...[
                Divider(height: 1, color: Colors.grey.shade100),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'KEY BENEFITS',
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.grey.shade600,
                          letterSpacing: 0.5,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 8),
                      // Show first 3 benefits
                      ...keyBenefits.take(3).map((benefit) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Text(
                            '✓ $benefit',
                            style: const TextStyle(fontSize: 12, color: Color(0xFF333333)),
                          ),
                        );
                      }),
                      // "+N more" link
                      if (keyBenefits.length > 3)
                        Text(
                          '+${keyBenefits.length - 3} more benefits',
                          style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                        ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),

        // Quick action buttons
        if (quickActions.isNotEmpty) ...[
          const SizedBox(height: 12),
          QuickActionButtons(actions: quickActions, onTap: onQuickAction),
        ],
      ],
    );
  }

  Widget _buildInfoRow(String label1, String value1, String label2, String value2) {
    return Row(
      children: [
        Expanded(child: _buildInfoItem(label1, Text(value1, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)))),
        const SizedBox(width: 12),
        Expanded(child: _buildInfoItem(label2, Text(value2, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)))),
      ],
    );
  }

  Widget _buildInfoRowWithWidgets(String label1, Widget value1, String label2, Widget value2) {
    return Row(
      children: [
        Expanded(child: _buildInfoItem(label1, value1)),
        const SizedBox(width: 12),
        Expanded(child: _buildInfoItem(label2, value2)),
      ],
    );
  }

  Widget _buildInfoItem(String label, Widget value) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF9F9F9),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(fontSize: 11, color: Colors.grey.shade600, letterSpacing: 0.5),
          ),
          const SizedBox(height: 2),
          value,
        ],
      ),
    );
  }

  Widget _buildScoreBadge(int score) {
    Color bgColor, textColor;
    if (score >= 70) {
      bgColor = const Color(0xFFE8F5E9);
      textColor = const Color(0xFF2E7D32);
    } else if (score >= 40) {
      bgColor = const Color(0xFFFFF3E0);
      textColor = const Color(0xFFEF6C00);
    } else {
      bgColor = const Color(0xFFFFEBEE);
      textColor = const Color(0xFFC62828);
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        '🛡️ $score%',
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: textColor),
      ),
    );
  }
}
```

### Quick Action Buttons for Policy Details

```dart
// User taps "View All Benefits":
wsService.sendAction('view_benefits', policyId: 'ANL_282_ae9929261fea');

// User taps "Coverage Gaps":
wsService.sendAction('view_gaps', policyId: 'ANL_282_ae9929261fea');

// User taps "Back to Policies":
wsService.sendAction('policy_query_self');
```

---

## 12. Policy Query — show_policy_benefits {#12-policy-query-show-policy-benefits}

Green-themed benefits list with checkmark icons.

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "response": "Benefits for Care Health Insurance Limited - accidental",
    "flow_step": "show_policy_benefits",
    "benefits_data": {
      "benefitsCount": 6,
      "benefits": [
        "Personal Accident Cover-Sum Insured: Rs. 1,00,000",
        "Accidental Death: 100% of Sum Insured payout",
        "Permanent Partial Disability: Up to Sum Insured as per PPD table",
        "Permanent Total Disability: Up to Sum Insured as per PTD table",
        "Health Service-Doctors on Call: Unlimited GP consultations covered",
        "Claims payout: Personal Accident - Reimbursement, Health Service - Cashless within network"
      ],
      "noBenefitsMessage": "No benefits information available."
    },
    "quick_actions": [
      {"title": "Coverage Gaps", "action": "view_gaps", "policy_id": "ANL_282_ae9929261fea"},
      {"title": "Policy Details", "action": "show_policy_details", "policy_id": "ANL_282_ae9929261fea"},
      {"title": "Back to Policies", "action": "policy_query_self"}
    ]
  }
}
```

### Flutter Widget

```dart
class PolicyBenefitsList extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(Map<String, dynamic>)? onQuickAction;

  const PolicyBenefitsList({required this.data, this.onQuickAction});

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? '';
    final benefitsData = Map<String, dynamic>.from(data['benefits_data'] ?? {});
    final benefits = List<String>.from(benefitsData['benefits'] ?? []);
    final benefitsCount = benefitsData['benefitsCount'] ?? benefits.length;
    final noMsg = benefitsData['noBenefitsMessage'] ?? 'No benefits information available.';
    final quickActions = List<Map<String, dynamic>>.from(
      (data['quick_actions'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Text message
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(response, style: const TextStyle(fontSize: 14, height: 1.5)),
        ),
        const SizedBox(height: 12),

        // Benefits card
        Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFC8E6C9)),
          ),
          child: Column(
            children: [
              // Green header
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: const BoxDecoration(
                  color: Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(12),
                    topRight: Radius.circular(12),
                  ),
                ),
                child: Row(
                  children: [
                    const Text('✨', style: TextStyle(fontSize: 20)),
                    const SizedBox(width: 8),
                    const Text(
                      'Policy Benefits',
                      style: TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF2E7D32)),
                    ),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF2E7D32),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '$benefitsCount benefits',
                        style: const TextStyle(fontSize: 11, color: Colors.white),
                      ),
                    ),
                  ],
                ),
              ),

              // Benefits items
              if (benefits.isNotEmpty)
                ...benefits.asMap().entries.map((entry) {
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: entry.key < benefits.length - 1
                          ? Border(bottom: BorderSide(color: Colors.grey.shade100))
                          : null,
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('✓', style: TextStyle(color: Color(0xFF4CAF50), fontWeight: FontWeight.bold)),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            entry.value,
                            style: const TextStyle(fontSize: 13, color: Color(0xFF333333), height: 1.4),
                          ),
                        ),
                      ],
                    ),
                  );
                })
              else
                Container(
                  padding: const EdgeInsets.all(20),
                  alignment: Alignment.center,
                  child: Text(noMsg, style: TextStyle(color: Colors.grey.shade600, fontStyle: FontStyle.italic)),
                ),
            ],
          ),
        ),

        // Quick actions
        if (quickActions.isNotEmpty) ...[
          const SizedBox(height: 12),
          QuickActionButtons(actions: quickActions, onTap: onQuickAction),
        ],
      ],
    );
  }
}
```

---

## 13. Policy Query — show_policy_gaps {#13-policy-query-show-policy-gaps}

Coverage gaps grouped by priority: High (red), Medium (orange), Low (blue). Each gap has title, description, and recommendation.

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "response": "Coverage Gaps for Care Health Insurance Limited - accidental",
    "flow_step": "show_policy_gaps",
    "gaps_data": {
      "totalGaps": 6,
      "highGaps": [
        {
          "gap": "Coverage Gap",
          "title": "Coverage Gap",
          "description": "Sum insured of Rs. 1,00,000 is extremely low for a 35-year-old...",
          "recommendation": "Purchase a separate personal accident policy with minimum Rs. 50 lakhs sum insured..."
        }
      ],
      "mediumGaps": [
        {
          "gap": "Coverage Gap",
          "title": "Coverage Gap",
          "description": "Policy lacks temporary total disability benefit...",
          "recommendation": "Add temporary total disability rider providing 1-2% of sum insured per week..."
        }
      ],
      "lowGaps": []
    },
    "quick_actions": [
      {"title": "View Benefits", "action": "view_benefits", "policy_id": "ANL_282_ae9929261fea"},
      {"title": "Get Recommendations", "action": "view_recommendations", "policy_id": "ANL_282_ae9929261fea"},
      {"title": "Back to Policies", "action": "policy_query_self"}
    ]
  }
}
```

### Flutter Widget

```dart
class PolicyGapsList extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(Map<String, dynamic>)? onQuickAction;

  const PolicyGapsList({required this.data, this.onQuickAction});

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? '';
    final gapsData = Map<String, dynamic>.from(data['gaps_data'] ?? {});
    final totalGaps = gapsData['totalGaps'] ?? 0;
    final highGaps = List<Map<String, dynamic>>.from(
      (gapsData['highGaps'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );
    final mediumGaps = List<Map<String, dynamic>>.from(
      (gapsData['mediumGaps'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );
    final lowGaps = List<Map<String, dynamic>>.from(
      (gapsData['lowGaps'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );
    final quickActions = List<Map<String, dynamic>>.from(
      (data['quick_actions'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    final hasNoGaps = totalGaps == 0 && highGaps.isEmpty && mediumGaps.isEmpty && lowGaps.isEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Text message
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(response, style: const TextStyle(fontSize: 14, height: 1.5)),
        ),
        const SizedBox(height: 12),

        // No gaps — excellent coverage
        if (hasNoGaps)
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFFE8F5E9),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Column(
              children: [
                Text('🛡️', style: TextStyle(fontSize: 32)),
                SizedBox(height: 8),
                Text('Excellent Coverage!', style: TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF2E7D32))),
                Text('No significant coverage gaps found.', style: TextStyle(color: Color(0xFF2E7D32))),
              ],
            ),
          )
        else ...[
          // High priority gaps (red)
          if (highGaps.isNotEmpty)
            _buildGapsSection(
              title: 'High Priority',
              icon: '⚠️',
              gaps: highGaps,
              headerBgColor: const Color(0xFFFFEBEE),
              headerTextColor: const Color(0xFFC62828),
              headerBorderColor: const Color(0xFFFFCDD2),
              count: highGaps.length,
            ),

          // Medium priority gaps (orange)
          if (mediumGaps.isNotEmpty) ...[
            const SizedBox(height: 12),
            _buildGapsSection(
              title: 'Medium Priority',
              icon: '⚡',
              gaps: mediumGaps,
              headerBgColor: const Color(0xFFFFF3E0),
              headerTextColor: const Color(0xFFEF6C00),
              headerBorderColor: const Color(0xFFFFE0B2),
              count: mediumGaps.length,
            ),
          ],

          // Low priority gaps (blue)
          if (lowGaps.isNotEmpty) ...[
            const SizedBox(height: 12),
            _buildGapsSection(
              title: 'Low Priority',
              icon: 'ℹ️',
              gaps: lowGaps,
              headerBgColor: const Color(0xFFE3F2FD),
              headerTextColor: const Color(0xFF1565C0),
              headerBorderColor: const Color(0xFFBBDEFB),
              count: lowGaps.length,
            ),
          ],
        ],

        // Quick actions
        if (quickActions.isNotEmpty) ...[
          const SizedBox(height: 12),
          QuickActionButtons(actions: quickActions, onTap: onQuickAction),
        ],
      ],
    );
  }

  Widget _buildGapsSection({
    required String title,
    required String icon,
    required List<Map<String, dynamic>> gaps,
    required Color headerBgColor,
    required Color headerTextColor,
    required Color headerBorderColor,
    required int count,
  }) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        children: [
          // Section header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: headerBgColor,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(8),
                topRight: Radius.circular(8),
              ),
              border: Border.all(color: headerBorderColor),
            ),
            child: Row(
              children: [
                Text(icon, style: const TextStyle(fontSize: 14)),
                const SizedBox(width: 8),
                Text(title, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: headerTextColor)),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: headerTextColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text('$count', style: TextStyle(fontSize: 11, color: headerTextColor)),
                ),
              ],
            ),
          ),

          // Gap items
          ...gaps.asMap().entries.map((entry) {
            final gap = entry.value;
            return Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                border: entry.key < gaps.length - 1
                    ? Border(bottom: BorderSide(color: Colors.grey.shade100))
                    : null,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    gap['gap'] ?? gap['title'] ?? 'Coverage Gap',
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    gap['description'] ?? '',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600, height: 1.4),
                  ),
                  if (gap['recommendation'] != null && gap['recommendation'].toString().isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.only(left: 12),
                      decoration: const BoxDecoration(
                        border: Border(left: BorderSide(color: Color(0xFF1976D2), width: 2)),
                      ),
                      child: Text(
                        gap['recommendation'],
                        style: const TextStyle(fontSize: 12, color: Color(0xFF1976D2), height: 1.4),
                      ),
                    ),
                  ],
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
```

---

## 14. Policy Query — show_policy_recommendations {#14-policy-query-show-policy-recommendations}

Recommendations with score badge and priority icons.

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "response": "Recommendations for Care Health Insurance Limited - accidental",
    "flow_step": "show_policy_recommendations",
    "recommendations_data": {
      "protectionScore": 75,
      "recommendationsCount": 2,
      "hasRecommendations": true,
      "recommendations": [
        {
          "text": "Consider adding coverage for...",
          "priority": "high",
          "category": "COVERAGE GAP"
        }
      ],
      "noRecommendationsMessage": "Your policy looks comprehensive!"
    },
    "quick_actions": [
      {"title": "View Benefits", "action": "view_benefits", "policy_id": "ANL_282_ae9929261fea"},
      {"title": "Back to Policies", "action": "policy_query_self"}
    ]
  }
}
```

### Flutter Widget

```dart
class PolicyRecommendationsList extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(Map<String, dynamic>)? onQuickAction;

  const PolicyRecommendationsList({required this.data, this.onQuickAction});

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? '';
    final recData = Map<String, dynamic>.from(data['recommendations_data'] ?? {});
    final score = recData['protectionScore'] ?? 0;
    final hasRecs = recData['hasRecommendations'] ?? false;
    final recs = List<Map<String, dynamic>>.from(
      (recData['recommendations'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );
    final recCount = recData['recommendationsCount'] ?? recs.length;
    final noMsg = recData['noRecommendationsMessage'] ?? 'Your policy looks comprehensive!';
    final quickActions = List<Map<String, dynamic>>.from(
      (data['quick_actions'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    final scoreColor = score >= 70
        ? const Color(0xFF2E7D32)
        : (score >= 40 ? const Color(0xFFEF6C00) : const Color(0xFFC62828));
    final scoreBgColor = score >= 70
        ? const Color(0xFFE8F5E9)
        : (score >= 40 ? const Color(0xFFFFF3E0) : const Color(0xFFFFEBEE));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Text message
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(response, style: const TextStyle(fontSize: 14, height: 1.5)),
        ),
        const SizedBox(height: 12),

        // Recommendations card
        Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFFFCC80)),
          ),
          child: Column(
            children: [
              // Orange gradient header
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: const BoxDecoration(
                  gradient: LinearGradient(colors: [Color(0xFFFFF3E0), Color(0xFFFFE0B2)]),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(12),
                    topRight: Radius.circular(12),
                  ),
                ),
                child: Row(
                  children: [
                    const Text('💡', style: TextStyle(fontSize: 20)),
                    const SizedBox(width: 8),
                    const Text(
                      'Recommendations',
                      style: TextStyle(fontWeight: FontWeight.w600, color: Color(0xFFE65100)),
                    ),
                    const SizedBox(width: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: scoreBgColor,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Text(
                        'Score: $score/100',
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: scoreColor),
                      ),
                    ),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE65100),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text('$recCount items', style: const TextStyle(fontSize: 11, color: Colors.white)),
                    ),
                  ],
                ),
              ),

              // Recommendation items
              if (hasRecs && recs.isNotEmpty)
                ...recs.asMap().entries.map((entry) {
                  final rec = entry.value;
                  final priority = rec['priority'] ?? 'medium';
                  final icon = priority == 'high' ? '⚠️' : (priority == 'medium' ? '💡' : 'ℹ️');
                  final category = (rec['category'] ?? 'general').toString().replaceAll('_', ' ');

                  return Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: entry.key < recs.length - 1
                          ? Border(bottom: BorderSide(color: Colors.grey.shade100))
                          : null,
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(icon, style: const TextStyle(fontSize: 16)),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                rec['text'] ?? '',
                                style: const TextStyle(fontSize: 13, height: 1.4),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                category.toUpperCase(),
                                style: TextStyle(fontSize: 10, color: Colors.grey.shade600, letterSpacing: 0.5),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                })
              else
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F5E9),
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(12),
                      bottomRight: Radius.circular(12),
                    ),
                  ),
                  child: Column(
                    children: [
                      const Text('✅', style: TextStyle(fontSize: 32)),
                      const SizedBox(height: 8),
                      const Text('Great Coverage!', style: TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF2E7D32))),
                      Text(noMsg, style: const TextStyle(color: Color(0xFF2E7D32))),
                    ],
                  ),
                ),
            ],
          ),
        ),

        // Quick actions
        if (quickActions.isNotEmpty) ...[
          const SizedBox(height: 12),
          QuickActionButtons(actions: quickActions, onTap: onQuickAction),
        ],
      ],
    );
  }
}
```

---

## 15. Policy Query — no_policies (Empty State) {#15-policy-query-no-policies}

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "policy_query",
  "data": {
    "response": "You haven't uploaded any insurance policies yet. Would you like to add your first policy?",
    "flow_step": "no_policies",
    "has_policies": false,
    "policy_count": 0,
    "quick_actions": [
      {"title": "Add Policy", "action": "add_policy", "redirect": true, "redirect_page": "add_policy"},
      {"title": "Buy Insurance", "action": "select_insurance_type"}
    ]
  }
}
```

### Flutter Widget

```dart
class NoPoliciesEmptyState extends StatelessWidget {
  final Map<String, dynamic> data;
  final Function(Map<String, dynamic>)? onQuickAction;

  const NoPoliciesEmptyState({required this.data, this.onQuickAction});

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? '';
    final quickActions = List<Map<String, dynamic>>.from(
      (data['quick_actions'] ?? []).map((e) => Map<String, dynamic>.from(e)),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Column(
            children: [
              const Text('📋', style: TextStyle(fontSize: 48)),
              const SizedBox(height: 12),
              Text(
                response,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 14, height: 1.5),
              ),
            ],
          ),
        ),
        if (quickActions.isNotEmpty) ...[
          const SizedBox(height: 12),
          QuickActionButtons(actions: quickActions, onTap: onQuickAction),
        ],
      ],
    );
  }
}
```

---

## 16. Question Form (Multi-Step Q&A) {#16-question-form}

Used during insurance application (26 questions), wallet setup, etc.

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "question",
  "data": {
    "response": "What is your full name?",
    "message": "What is your full name?",
    "type": "question",
    "question_number": 1,
    "total_questions": 26,
    "field_key": "fullName",
    "field_type": "text",
    "placeholder": "Enter your full name",
    "options": null,
    "required": true,
    "progress": 3.8,
    "session_continuation": true
  }
}
```

### Field Types

| field_type | UI Widget |
|-----------|-----------|
| `text` | TextField |
| `number` | TextField with numeric keyboard |
| `date` | DatePicker |
| `dropdown` | DropdownButton with `options` array |
| `email` | TextField with email keyboard |
| `phone` | TextField with phone keyboard |

### Flutter Widget

```dart
class QuestionForm extends StatefulWidget {
  final Map<String, dynamic> data;
  final Function(String answer)? onAnswer;

  const QuestionForm({required this.data, this.onAnswer});

  @override
  State<QuestionForm> createState() => _QuestionFormState();
}

class _QuestionFormState extends State<QuestionForm> {
  final _controller = TextEditingController();
  String? _selectedOption;

  @override
  Widget build(BuildContext context) {
    final question = widget.data['response'] ?? widget.data['message'] ?? '';
    final questionNum = widget.data['question_number'] ?? 0;
    final totalQuestions = widget.data['total_questions'] ?? 0;
    final fieldType = widget.data['field_type'] ?? 'text';
    final placeholder = widget.data['placeholder'] ?? '';
    final options = widget.data['options'] != null
        ? List<String>.from(widget.data['options'])
        : <String>[];
    final progress = widget.data['progress'] ?? 0.0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Progress bar
        if (totalQuestions > 0) ...[
          Row(
            children: [
              Expanded(
                child: LinearProgressIndicator(
                  value: questionNum / totalQuestions,
                  backgroundColor: Colors.grey.shade200,
                  color: const Color(0xFF007BFF),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                '$questionNum/$totalQuestions',
                style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
              ),
            ],
          ),
          const SizedBox(height: 12),
        ],

        // Question text
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Text(question, style: const TextStyle(fontSize: 14, height: 1.5)),
        ),
        const SizedBox(height: 12),

        // Input field based on type
        if (fieldType == 'dropdown' && options.isNotEmpty)
          ..._buildDropdown(options)
        else if (fieldType == 'date')
          _buildDatePicker(context)
        else
          _buildTextField(fieldType, placeholder),
      ],
    );
  }

  List<Widget> _buildDropdown(List<String> options) {
    return [
      Wrap(
        spacing: 8,
        runSpacing: 8,
        children: options.map((option) {
          final isSelected = _selectedOption == option;
          return GestureDetector(
            onTap: () {
              setState(() => _selectedOption = option);
              widget.onAnswer?.call(option);
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: isSelected ? const Color(0xFF007BFF) : const Color(0xFFF0F0F0),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                option,
                style: TextStyle(
                  color: isSelected ? Colors.white : const Color(0xFF333333),
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    ];
  }

  Widget _buildDatePicker(BuildContext context) {
    return GestureDetector(
      onTap: () async {
        final date = await showDatePicker(
          context: context,
          initialDate: DateTime(1990),
          firstDate: DateTime(1940),
          lastDate: DateTime.now(),
        );
        if (date != null) {
          final formatted = '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
          widget.onAnswer?.call(formatted);
        }
      },
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade300),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(Icons.calendar_today, color: Colors.grey.shade600),
            const SizedBox(width: 8),
            Text('Select date', style: TextStyle(color: Colors.grey.shade600)),
          ],
        ),
      ),
    );
  }

  Widget _buildTextField(String fieldType, String placeholder) {
    return TextField(
      controller: _controller,
      keyboardType: fieldType == 'number' || fieldType == 'phone'
          ? TextInputType.number
          : fieldType == 'email'
              ? TextInputType.emailAddress
              : TextInputType.text,
      decoration: InputDecoration(
        hintText: placeholder,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      ),
      onSubmitted: (value) {
        if (value.isNotEmpty) {
          widget.onAnswer?.call(value);
          _controller.clear();
        }
      },
    );
  }
}
```

### Sending an Answer

```dart
// User answers are sent as plain text messages — the active session handler routes them
void onAnswer(String answer) {
  wsService.sendMessage(answer); // sends: {type: "chat", query: answer}
}
```

---

## 17. Review & Edit Application {#17-review-edit-application}

Editable form showing all 26 answers for review before submission.

### Key Fields in `data`

| Field | Type | Description |
|-------|------|-------------|
| `editable_fields` | array | List of all questions with current answers |
| `editable_fields[].question_number` | int | Question number |
| `editable_fields[].question` | string | Question text |
| `editable_fields[].current_answer` | string | Current answer value |
| `editable_fields[].field_type` | string | text/dropdown/date/number |
| `editable_fields[].field_key` | string | API field key |
| `editable_fields[].options` | array? | Dropdown options |
| `next_action` | object | `{action: "confirm_submit_application", policy_id: "..."}` |
| `back_action` | object | `{action: "cancel_application", policy_id: "..."}` |

### Sending Submit with Edits

```dart
// Collect only edited fields
final editedAnswers = <Map<String, dynamic>>[];
for (final field in editableFields) {
  if (field['is_edited'] == true) {
    editedAnswers.add({
      'question_number': field['question_number'],
      'answer': field['current_answer'],
      'field_key': field['field_key'],
      'question': field['question'],
      'question_type': field['field_type'],
    });
  }
}

// Submit
wsService._send({
  'type': 'chat',
  'chat_session_id': wsService.chatSessionId,
  'query': jsonEncode(editedAnswers),
  'action': 'confirm_submit_application',
  'policy_id': policyId,
});
```

### Sending Cancel

```dart
wsService.sendAction('cancel_application', policyId: policyId);
```

---

## 18. Application Completed (Success + Payment) {#18-application-completed}

### Key Fields in `data`

| Field | Type | Description |
|-------|------|-------------|
| `application_id` | string | Application ID |
| `reference_number` | string | Proposal reference number |
| `order_id` | string | Payment order ID |
| `order_amount` | number | Payment amount |
| `payment_session_id` | string | Cashfree payment session ID |
| `proposalNum` | string | Insurance proposal number |
| `show_payment_option` | bool | If true, show payment button |
| `next_steps` | string[] | What happens next |
| `quick_actions` | array | Action buttons |

### Payment Integration

```dart
if (data['show_payment_option'] == true) {
  final paymentSessionId = data['payment_session_id'];
  final orderId = data['order_id'];
  final amount = data['order_amount'];

  // Use Cashfree Flutter SDK
  // CFPaymentGatewayService().doPayment(...)
}
```

---

## 19. Application Cancelled {#19-application-cancelled}

Simple text message with quick actions to start a new application.

### Key Fields in `data`

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | "Your application has been cancelled successfully." |
| `policy_id` | string | The cancelled policy ID |
| `quick_actions` | array | Start New, Check Balance, Get Help |

---

## 20. Insurance Analysis (Add Policy Prompt) {#20-insurance-analysis}

Shown when user says "analyze my policy". Has redirect buttons.

### Important: `redirect: true` Buttons

When `redirect` is `true`, do **NOT** send a WebSocket message. Instead, navigate in the Flutter app:

```dart
// "Add Policy" button → navigate to add policy page
Navigator.pushNamed(context, '/add-policy');

// "View My Policies" button → navigate to my policies page
Navigator.pushNamed(context, '/my-policies');
```

---

## 21. Text Response Types {#21-text-response-types}

These response types all render as simple text + suggestions:

| response_type | Typical Content |
|--------------|----------------|
| `education` | Insurance/finance educational content |
| `claim_guidance` | Step-by-step claim filing instructions |
| `off_topic` | Redirect to insurance topics |
| `live_information` | Stock market, live financial data |
| `information` | RAG-retrieved document information |

All use the same `TextMessageBubble` widget from Section 2. The `suggestions` array provides relevant follow-up chips.

---

## 22. Protection Score {#22-protection-score}

Text-based response about user's protection score. Rendered as `TextMessageBubble`.

---

## 23. Error Response {#23-error-response}

### Server JSON

```json
{
  "type": "chat_message",
  "response_type": "error",
  "data": {
    "response": "I apologize, but something went wrong. Please try again.",
    "error": "Failed to process action: show_policy_details",
    "action": "error"
  }
}
```

### Flutter Widget

```dart
class ErrorMessageBubble extends StatelessWidget {
  final Map<String, dynamic> data;

  const ErrorMessageBubble({required this.data});

  @override
  Widget build(BuildContext context) {
    final response = data['response'] ?? 'Something went wrong.';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFEBEE),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFFCDD2)),
      ),
      child: Text(
        response,
        style: const TextStyle(fontSize: 14, color: Color(0xFFC62828), height: 1.5),
      ),
    );
  }
}
```

---

## 24. Notification Card {#24-notification-card}

### Server JSON

```json
{
  "type": "notification",
  "notification_id": "notif_abc123",
  "notification_type": "policy_renewal",
  "title": "Policy Renewal Reminder",
  "body": "Your health insurance policy expires in 30 days",
  "priority": "high"
}
```

### Flutter Widget

```dart
class NotificationCard extends StatelessWidget {
  final Map<String, dynamic> data;

  const NotificationCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final title = data['title'] ?? 'Notification';
    final body = data['body'] ?? '';

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF3E0),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFF9800)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('🔔', style: TextStyle(fontSize: 16)),
              const SizedBox(width: 8),
              Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 4),
          Text(body, style: const TextStyle(fontSize: 13)),
        ],
      ),
    );
  }
}
```

---

## 25. Complete Chat Screen Widget {#25-complete-chat-screen}

Putting it all together — a full chat screen with all response types.

### Chat Message Model

```dart
class ChatBubbleData {
  final bool isUser;
  final String text;
  final String responseType;
  final Map<String, dynamic> data;
  final DateTime timestamp;

  ChatBubbleData({
    required this.isUser,
    required this.text,
    this.responseType = 'chat_message',
    this.data = const {},
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}
```

### Chat Screen State

```dart
class ChatScreen extends StatefulWidget {
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final EazrWebSocketService _ws = EazrWebSocketService();
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatBubbleData> _messages = [];

  bool _isThinking = false;
  String _thinkingWord = '';
  bool _isStreaming = false;
  String _streamBuffer = '';

  @override
  void initState() {
    super.initState();
    _setupCallbacks();
    _ws.connect('YOUR_JWT_TOKEN', deviceId: 'flutter_${DateTime.now().millisecondsSinceEpoch}');
  }

  void _setupCallbacks() {
    _ws.onThinkingChanged = (word, isThinking) {
      setState(() {
        _isThinking = isThinking;
        _thinkingWord = word;
      });
    };

    _ws.onChatMessage = (data) {
      setState(() {
        _messages.add(ChatBubbleData(
          isUser: false,
          text: data['data']?['response'] ?? '',
          responseType: data['response_type'] ?? 'chat_message',
          data: Map<String, dynamic>.from(data['data'] ?? {}),
        ));
      });
      _scrollToBottom();
    };

    _ws.onStreamToken = (currentText) {
      setState(() {
        _isStreaming = true;
        _streamBuffer = currentText;
      });
      _scrollToBottom();
    };

    _ws.onStreamEnd = (data) {
      setState(() {
        _isStreaming = false;
        _messages.add(ChatBubbleData(
          isUser: false,
          text: data['full_response'] ?? _streamBuffer,
          responseType: 'chat_message',
          data: Map<String, dynamic>.from(data['data'] ?? {}),
        ));
        _streamBuffer = '';
      });
      _scrollToBottom();
    };
  }

  void _sendMessage(String text) {
    if (text.isEmpty) return;
    setState(() {
      _messages.add(ChatBubbleData(isUser: true, text: text));
    });
    _ws.sendMessage(text);
    _inputController.clear();
    _scrollToBottom();
  }

  void _sendAction(Map<String, dynamic> action) {
    final isRedirect = action['redirect'] == true;
    if (isRedirect) {
      final page = action['redirect_page'] as String? ?? '';
      Navigator.pushNamed(context, '/$page');
      return;
    }

    final actionName = action['action'] as String? ?? '';
    final query = action['query'] ?? action['title'] ?? actionName.replaceAll('_', ' ');
    final policyId = action['policy_id'] ?? action['policyId'];

    setState(() {
      _messages.add(ChatBubbleData(isUser: true, text: query));
    });

    _ws.sendAction(actionName, query: query, policyId: policyId);
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('EAZR Chat')),
      body: Column(
        children: [
          // Messages list
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length + (_isStreaming ? 1 : 0) + (_isThinking ? 1 : 0),
              itemBuilder: (context, index) {
                // Existing messages
                if (index < _messages.length) {
                  final msg = _messages[index];
                  if (msg.isUser) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: UserMessageBubble(
                        text: msg.text,
                        time: _formatTime(msg.timestamp),
                      ),
                    );
                  }
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: buildResponseWidget({
                      'response_type': msg.responseType,
                      'data': msg.data,
                    }),
                  );
                }

                // Streaming message
                if (_isStreaming && index == _messages.length) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: StreamingMessageBubble(
                      currentText: _streamBuffer,
                      isStreaming: true,
                    ),
                  );
                }

                // Thinking indicator
                if (_isThinking) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: ThinkingIndicator(word: _thinkingWord),
                  );
                }

                return const SizedBox.shrink();
              },
            ),
          ),

          // Bottom suggestion chips (from latest message)
          if (_messages.isNotEmpty && !_messages.last.isUser) ...[
            _buildBottomSuggestions(),
          ],

          // Input area
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildBottomSuggestions() {
    final lastData = _messages.last.data;
    final suggestions = List<String>.from(lastData['suggestions'] ?? []);
    if (suggestions.isEmpty) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: SuggestionChips(
        suggestions: suggestions,
        onTap: (text) => _sendMessage(text),
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey.shade200)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _inputController,
              decoration: InputDecoration(
                hintText: 'Type a message...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
              onSubmitted: _sendMessage,
            ),
          ),
          const SizedBox(width: 12),
          FloatingActionButton.small(
            onPressed: () => _sendMessage(_inputController.text),
            child: const Icon(Icons.send),
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime dt) {
    return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  // Use the routing function from Section 1
  Widget buildResponseWidget(Map<String, dynamic> serverMessage) {
    final responseType = serverMessage['response_type'] as String;
    final data = serverMessage['data'] as Map<String, dynamic>;
    final flowStep = data['flow_step'] as String?;

    if (responseType == 'policy_query') {
      switch (flowStep) {
        case 'ask_self_or_family':
          return PolicySelfFamilySelector(
            data: data,
            onSelect: (action) => _ws.sendAction(action),
          );
        case 'show_family_members':
          return FamilyMemberSelector(
            data: data,
            onSelectMember: (member) => _ws.sendAction('policy_query_family', query: 'Show policies for $member'),
            onQuickAction: _sendAction,
          );
        case 'show_self_policies':
        case 'show_member_policies':
          return PolicyCardList(
            data: data,
            onPolicyTap: (id) => _ws.sendAction('show_policy_details', query: 'Show details for policy $id', policyId: id),
            onQuickAction: _sendAction,
          );
        case 'show_policy_details':
          return PolicyDetailsCard(data: data, onQuickAction: _sendAction);
        case 'show_policy_benefits':
          return PolicyBenefitsList(data: data, onQuickAction: _sendAction);
        case 'show_policy_gaps':
          return PolicyGapsList(data: data, onQuickAction: _sendAction);
        case 'show_policy_recommendations':
          return PolicyRecommendationsList(data: data, onQuickAction: _sendAction);
        case 'no_policies':
          return NoPoliciesEmptyState(data: data, onQuickAction: _sendAction);
        default:
          return TextMessageBubble(data: data, onSuggestionTap: _sendMessage, onQuickAction: _sendAction);
      }
    }

    switch (responseType) {
      case 'selection_menu':
        return SelectionMenu(data: data, onSelect: (opt) => _sendAction(opt));
      case 'question':
        return QuestionForm(data: data, onAnswer: (ans) => _ws.sendMessage(ans));
      case 'error':
        return ErrorMessageBubble(data: data);
      default:
        return TextMessageBubble(data: data, onSuggestionTap: _sendMessage, onQuickAction: _sendAction);
    }
  }

  @override
  void dispose() {
    _ws.disconnect();
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
```

---

## Policy Query Flow — Complete Navigation Map

```
User says "show my policies"
    |
    v
[ask_self_or_family] — "My Policies" / "Family Policies" buttons
    |                         |
    v                         v
[show_self_policies]    [show_family_members]
    |                         |
    |  Tap policy card        |  Tap member card
    v                         v
[show_policy_details]   [show_member_policies]
    |                         |  Tap policy card
    |                         v
    |                   [show_policy_details]
    |
    +-- "View All Benefits" --> [show_policy_benefits]
    |       |-- "Coverage Gaps" --> [show_policy_gaps]
    |       |-- "Policy Details" --> [show_policy_details]
    |       '-- "Back to Policies" --> [show_self_policies]
    |
    +-- "Coverage Gaps" ------> [show_policy_gaps]
    |       |-- "View Benefits" --> [show_policy_benefits]
    |       |-- "Get Recommendations" --> [show_policy_recommendations]
    |       '-- "Back to Policies" --> [show_self_policies]
    |
    '-- "Back to Policies" --> [show_self_policies]
```

### Quick Reference — What Action to Send at Each Step

| User Action | WebSocket Message |
|------------|-------------------|
| Tap "My Policies" | `sendAction('policy_query_self')` |
| Tap "Family Policies" | `sendAction('policy_query_family')` |
| Tap family member "Other" | `sendAction('policy_query_family', query: 'Show policies for Other')` |
| Tap a policy card | `sendAction('show_policy_details', policyId: 'ANL_282_xxx')` |
| Tap "View All Benefits" | `sendAction('view_benefits', policyId: 'ANL_282_xxx')` |
| Tap "Coverage Gaps" | `sendAction('view_gaps', policyId: 'ANL_282_xxx')` |
| Tap "Get Recommendations" | `sendAction('view_recommendations', policyId: 'ANL_282_xxx')` |
| Tap "Back to Policies" | `sendAction('policy_query_self')` |
| Tap "Policy Details" | `sendAction('show_policy_details', policyId: 'ANL_282_xxx')` |
| Tap "View All Policies" | `sendAction('policy_query')` |
