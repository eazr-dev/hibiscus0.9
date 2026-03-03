# CEO Note API - Flutter Integration Guide

Complete guide for integrating CEO Note feature in Flutter app.

---

## Overview

The CEO Note feature displays a welcome message from the CEO to users. It shows only once per user and can be managed from the admin panel.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ceo-note?userId={userId}` | Get CEO note for display |
| POST | `/ceo-note/mark-seen` | Mark note as seen by user |

### MongoDB Collections

| Collection | Purpose |
|------------|---------|
| `ceo_notes` | Stores CEO note content |
| `ceo_note_views` | Tracks which users have seen notes |

---

## API 1: GET CEO Note

### Endpoint
```
GET /ceo-note?userId={userId}
```

### Request

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| userId | int | Yes | The user's ID |

**Example Request:**
```
GET /ceo-note?userId=343
```

### Response

**When note should be shown (First time user):**
```json
{
  "success": true,
  "data": {
    "shouldShow": true,
    "note": {
      "noteId": "678abc123def456...",
      "title": "Welcome to Eazr!",
      "content": "### Hi there!\n\nWelcome message in **Markdown** format...",
      "contentFormat": "markdown",
      "ceoName": "Team Eazr",
      "ceoDesignation": "Founder & CEO",
      "ceoImageUrl": null,
      "version": 1
    }
  }
}
```

**When note should NOT be shown (Already seen):**
```json
{
  "success": true,
  "data": {
    "shouldShow": false,
    "reason": "User has already seen this note"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| shouldShow | boolean | Whether to display the note |
| note.noteId | string | Unique ID of the note (needed for mark-seen) |
| note.title | string | Note title |
| note.content | string | Note content in Markdown format |
| note.contentFormat | string | Always "markdown" |
| note.ceoName | string | CEO name to display |
| note.ceoDesignation | string | CEO designation |
| note.ceoImageUrl | string? | Optional CEO image URL |
| note.version | int | Note version number |

---

## API 2: POST Mark Note as Seen

### Endpoint
```
POST /ceo-note/mark-seen
```

### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "userId": 343,
  "noteId": "678abc123def456..."
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| userId | int | Yes | The user's ID |
| noteId | string | Yes | The note ID from GET response |

### Response

**Success:**
```json
{
  "success": true,
  "message": "CEO note marked as seen"
}
```

---

## Flutter Implementation

### Step 1: Add Dependencies

Add to `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0
  flutter_markdown: ^0.6.18
```

Run:
```bash
flutter pub get
```

---

### Step 2: Create Models

Create file: `lib/models/ceo_note_model.dart`

```dart
// CEO Note Response Model
class CeoNoteResponse {
  final bool success;
  final CeoNoteData data;

  CeoNoteResponse({
    required this.success,
    required this.data,
  });

  factory CeoNoteResponse.fromJson(Map<String, dynamic> json) {
    return CeoNoteResponse(
      success: json['success'] ?? false,
      data: CeoNoteData.fromJson(json['data'] ?? {}),
    );
  }
}

// CEO Note Data
class CeoNoteData {
  final bool shouldShow;
  final String? reason;
  final CeoNote? note;

  CeoNoteData({
    required this.shouldShow,
    this.reason,
    this.note,
  });

  factory CeoNoteData.fromJson(Map<String, dynamic> json) {
    return CeoNoteData(
      shouldShow: json['shouldShow'] ?? false,
      reason: json['reason'],
      note: json['note'] != null ? CeoNote.fromJson(json['note']) : null,
    );
  }
}

// CEO Note Content
class CeoNote {
  final String noteId;
  final String title;
  final String content;
  final String contentFormat;
  final String ceoName;
  final String ceoDesignation;
  final String? ceoImageUrl;
  final int version;

  CeoNote({
    required this.noteId,
    required this.title,
    required this.content,
    required this.contentFormat,
    required this.ceoName,
    required this.ceoDesignation,
    this.ceoImageUrl,
    required this.version,
  });

  factory CeoNote.fromJson(Map<String, dynamic> json) {
    return CeoNote(
      noteId: json['noteId'] ?? '',
      title: json['title'] ?? '',
      content: json['content'] ?? '',
      contentFormat: json['contentFormat'] ?? 'markdown',
      ceoName: json['ceoName'] ?? '',
      ceoDesignation: json['ceoDesignation'] ?? '',
      ceoImageUrl: json['ceoImageUrl'],
      version: json['version'] ?? 1,
    );
  }
}

// Mark Seen Response
class MarkSeenResponse {
  final bool success;
  final String message;

  MarkSeenResponse({
    required this.success,
    required this.message,
  });

  factory MarkSeenResponse.fromJson(Map<String, dynamic> json) {
    return MarkSeenResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
    );
  }
}
```

---

### Step 3: Create Service

Create file: `lib/services/ceo_note_service.dart`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/ceo_note_model.dart';

class CeoNoteService {
  final String baseUrl;

  CeoNoteService({required this.baseUrl});

  /// GET /ceo-note?userId={userId}
  /// Fetches CEO note for the user
  Future<CeoNoteResponse> getCeoNote(int userId) async {
    try {
      final uri = Uri.parse('$baseUrl/ceo-note?userId=$userId');

      final response = await http.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        return CeoNoteResponse.fromJson(json);
      } else {
        throw Exception('Failed to load CEO note: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching CEO note: $e');
    }
  }

  /// POST /ceo-note/mark-seen
  /// Marks the CEO note as seen by user
  Future<MarkSeenResponse> markNoteAsSeen({
    required int userId,
    required String noteId,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/ceo-note/mark-seen');

      final response = await http.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'userId': userId,
          'noteId': noteId,
        }),
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        return MarkSeenResponse.fromJson(json);
      } else {
        throw Exception('Failed to mark note as seen: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error marking note as seen: $e');
    }
  }
}
```

---

### Step 4: Create CEO Note Dialog Widget

Create file: `lib/widgets/ceo_note_dialog.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../models/ceo_note_model.dart';

class CeoNoteDialog extends StatelessWidget {
  final CeoNote note;
  final VoidCallback onDismiss;

  const CeoNoteDialog({
    Key? key,
    required this.note,
    required this.onDismiss,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(context).size.height * 0.8,
          maxWidth: 400,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header with title
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(16),
                ),
              ),
              child: Row(
                children: [
                  // CEO Image (if available)
                  if (note.ceoImageUrl != null)
                    CircleAvatar(
                      radius: 24,
                      backgroundImage: NetworkImage(note.ceoImageUrl!),
                    )
                  else
                    CircleAvatar(
                      radius: 24,
                      backgroundColor: Colors.white,
                      child: Icon(
                        Icons.person,
                        color: Theme.of(context).primaryColor,
                      ),
                    ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          note.title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          '${note.ceoName} - ${note.ceoDesignation}',
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Content (Markdown)
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: MarkdownBody(
                  data: note.content,
                  styleSheet: MarkdownStyleSheet(
                    h3: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                    p: const TextStyle(
                      fontSize: 14,
                      height: 1.5,
                    ),
                  ),
                ),
              ),
            ),

            // Action Button
            Padding(
              padding: const EdgeInsets.all(20),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: onDismiss,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: const Text(
                    'Got it!',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

### Step 5: Implement in Home Screen

Create/Update file: `lib/screens/home_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../services/ceo_note_service.dart';
import '../models/ceo_note_model.dart';
import '../widgets/ceo_note_dialog.dart';

class HomeScreen extends StatefulWidget {
  final int userId;

  const HomeScreen({Key? key, required this.userId}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final CeoNoteService _ceoNoteService = CeoNoteService(
    baseUrl: 'https://your-api-url.com', // Replace with your API URL
  );

  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _checkAndShowCeoNote();
  }

  /// Step 1: Check if CEO note should be shown
  Future<void> _checkAndShowCeoNote() async {
    try {
      // Call GET /ceo-note?userId={userId}
      final response = await _ceoNoteService.getCeoNote(widget.userId);

      setState(() {
        _isLoading = false;
      });

      // Step 2: If shouldShow is true, display the dialog
      if (response.data.shouldShow && response.data.note != null) {
        _showCeoNoteDialog(response.data.note!);
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      debugPrint('Error checking CEO note: $e');
    }
  }

  /// Step 2: Show the CEO Note Dialog
  void _showCeoNoteDialog(CeoNote note) {
    showDialog(
      context: context,
      barrierDismissible: false, // User must tap button to dismiss
      builder: (context) => CeoNoteDialog(
        note: note,
        onDismiss: () => _onNoteDismissed(note),
      ),
    );
  }

  /// Step 3: Mark note as seen when user dismisses
  Future<void> _onNoteDismissed(CeoNote note) async {
    // Close the dialog first
    Navigator.of(context).pop();

    try {
      // Call POST /ceo-note/mark-seen
      await _ceoNoteService.markNoteAsSeen(
        userId: widget.userId,
        noteId: note.noteId,
      );
      debugPrint('CEO note marked as seen successfully');
    } catch (e) {
      debugPrint('Error marking note as seen: $e');
      // Note: Even if this fails, the dialog is already closed
      // The note might show again on next app launch
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Home'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : const Center(
              child: Text('Your app content here'),
            ),
    );
  }
}
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        APP LAUNCH                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Call GET /ceo-note?userId=343                          │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────────┐
│  shouldShow: false      │     │  shouldShow: true               │
│  (Already seen)         │     │  (First time)                   │
└─────────────────────────┘     └─────────────────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────────┐
│  Do nothing             │     │  STEP 2: Show CEO Note Dialog   │
│  Continue to app        │     │  Display title, content,        │
└─────────────────────────┘     │  CEO name with Markdown         │
                                └─────────────────────────────────┘
                                              │
                                              ▼
                                ┌─────────────────────────────────┐
                                │  User clicks "Got it!" button   │
                                └─────────────────────────────────┘
                                              │
                                              ▼
                                ┌─────────────────────────────────┐
                                │  STEP 3: Call POST              │
                                │  /ceo-note/mark-seen            │
                                │  Body: {userId, noteId}         │
                                └─────────────────────────────────┘
                                              │
                                              ▼
                                ┌─────────────────────────────────┐
                                │  Close dialog                   │
                                │  Continue to app                │
                                └─────────────────────────────────┘
                                              │
                                              ▼
                                ┌─────────────────────────────────┐
                                │  NEXT APP LAUNCH                │
                                │  GET /ceo-note returns          │
                                │  shouldShow: false              │
                                │  (Note already seen)            │
                                └─────────────────────────────────┘
```

---

## Error Handling

```dart
/// Enhanced error handling example
Future<void> _checkAndShowCeoNote() async {
  try {
    final response = await _ceoNoteService.getCeoNote(widget.userId);

    if (response.success && response.data.shouldShow && response.data.note != null) {
      _showCeoNoteDialog(response.data.note!);
    }
  } on SocketException {
    // No internet connection
    debugPrint('No internet connection');
  } on HttpException {
    // HTTP error
    debugPrint('HTTP error occurred');
  } on FormatException {
    // Invalid JSON response
    debugPrint('Invalid response format');
  } catch (e) {
    // Generic error
    debugPrint('Error: $e');
  } finally {
    setState(() {
      _isLoading = false;
    });
  }
}
```

---

## Testing

### Test Case 1: First Time User
1. Call `GET /ceo-note?userId=343`
2. Expected: `shouldShow: true` with note content
3. Display dialog
4. User clicks "Got it!"
5. Call `POST /ceo-note/mark-seen` with `{userId: 343, noteId: "..."}`

### Test Case 2: Returning User
1. Call `GET /ceo-note?userId=343`
2. Expected: `shouldShow: false` with reason "User has already seen this note"
3. Do not display dialog

### Test Case 3: Reset Views (Admin)
1. Call `DELETE /admin/ceo-note/views` (admin endpoint)
2. All users will see the note again

---

## Summary

| Step | API Call | When |
|------|----------|------|
| 1 | `GET /ceo-note?userId={id}` | On app launch / home screen load |
| 2 | Show Dialog | If `shouldShow: true` |
| 3 | `POST /ceo-note/mark-seen` | When user dismisses dialog |

**Request Body for mark-seen:**
```json
{
  "userId": 343,
  "noteId": "note_id_from_get_response"
}
```
