# Banner API - Flutter Integration Guide

This document explains how to integrate the Banner API in your Flutter mobile app.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/banners` | GET | Get all active banners for user |
| `/banners/track-view` | POST | Track banner impression |
| `/banners/track-click` | POST | Track banner click |
| `/banners/mark-seen` | POST | Mark banner as seen (for showOnlyOnce) |

---

## 1. Get Banners API

### Endpoint
```
GET /banners?userId={userId}&limit={limit}
```

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `userId` | int | No | null | User ID for personalized targeting |
| `limit` | int | No | 10 | Max banners to return |

### Example Request
```
GET https://eazr.ai.eazr.in/banners?userId=343&limit=10
```

### Example Response
```json
{
  "success": true,
  "data": {
    "banners": [
      {
        "bannerId": "697319b3243ff284bf5811c6",
        "title": "Premium Financing - Coming Soon!",
        "subtitle": "Pay your insurance premiums in easy EMIs",
        "description": "Can't afford to pay your full premium at once? Soon you'll be able to split your insurance premiums into affordable monthly installments with 0% interest for the first 3 months!",
        "imageUrl": "https://raceabove-dev.s3.ap-south-1.amazonaws.com/eaza_images/banner_20260123064818_bef11574.webp",
        "backgroundImageUrl": null,
        "backgroundColor": "#7C3AED",
        "textColor": "#FFFFFF",
        "bannerType": "coming_soon",
        "position": null,
        "ctaType": "none",
        "ctaText": null,
        "ctaValue": null,
        "targetAudience": "all_users",
        "priority": 95,
        "isActive": true,
        "showOnlyOnce": false,
        "startDate": null,
        "endDate": null,
        "tags": [],
        "createdAt": "2026-01-23T06:48:19Z",
        "updatedAt": "2026-01-23T06:48:19Z",
        "createdBy": "anonymous"
      }
    ],
    "count": 1
  }
}
```

---

## 2. Track Banner View API (Impression)

Call this API when a banner is displayed on the screen.

### Endpoint
```
POST /banners/track-view
```

### Request Body
```json
{
  "userId": 343,
  "bannerId": "697319b3243ff284bf5811c6"
}
```

### Example Response
```json
{
  "success": true,
  "message": "View tracked successfully"
}
```

---

## 3. Track Banner Click API

Call this API when user taps/clicks on a banner.

### Endpoint
```
POST /banners/track-click
```

### Request Body
```json
{
  "userId": 343,
  "bannerId": "697319b3243ff284bf5811c6"
}
```

### Example Response
```json
{
  "success": true,
  "message": "Click tracked successfully"
}
```

---

## 4. Mark Banner as Seen API

Call this API when user dismisses/closes a banner that has `showOnlyOnce: true`.
This ensures the banner won't appear again for this user.

### Endpoint
```
POST /banners/mark-seen
```

### Request Body
```json
{
  "userId": 343,
  "bannerId": "697319b3243ff284bf5811c6"
}
```

### Example Response
```json
{
  "success": true,
  "message": "Banner marked as seen"
}
```

---

## Flutter Implementation

### Step 1: Create Banner Model

```dart
// lib/models/banner_model.dart

class BannerModel {
  final String bannerId;
  final String title;
  final String? subtitle;
  final String? description;
  final String? imageUrl;
  final String? backgroundImageUrl;
  final String? backgroundColor;
  final String? textColor;
  final String bannerType;
  final String? position;
  final String ctaType;
  final String? ctaText;
  final String? ctaValue;
  final String targetAudience;
  final int priority;
  final bool isActive;
  final bool showOnlyOnce;
  final String? startDate;
  final String? endDate;

  BannerModel({
    required this.bannerId,
    required this.title,
    this.subtitle,
    this.description,
    this.imageUrl,
    this.backgroundImageUrl,
    this.backgroundColor,
    this.textColor,
    required this.bannerType,
    this.position,
    required this.ctaType,
    this.ctaText,
    this.ctaValue,
    required this.targetAudience,
    required this.priority,
    required this.isActive,
    required this.showOnlyOnce,
    this.startDate,
    this.endDate,
  });

  factory BannerModel.fromJson(Map<String, dynamic> json) {
    return BannerModel(
      bannerId: json['bannerId'] ?? '',
      title: json['title'] ?? '',
      subtitle: json['subtitle'],
      description: json['description'],
      imageUrl: json['imageUrl'],
      backgroundImageUrl: json['backgroundImageUrl'],
      backgroundColor: json['backgroundColor'],
      textColor: json['textColor'],
      bannerType: json['bannerType'] ?? 'promotional',
      position: json['position'],
      ctaType: json['ctaType'] ?? 'none',
      ctaText: json['ctaText'],
      ctaValue: json['ctaValue'],
      targetAudience: json['targetAudience'] ?? 'all_users',
      priority: json['priority'] ?? 0,
      isActive: json['isActive'] ?? true,
      showOnlyOnce: json['showOnlyOnce'] ?? false,
      startDate: json['startDate'],
      endDate: json['endDate'],
    );
  }

  // Helper to get background color as Color
  Color? get bgColor {
    if (backgroundColor == null) return null;
    try {
      String hex = backgroundColor!.replaceAll('#', '');
      if (hex.length == 6) hex = 'FF$hex';
      return Color(int.parse(hex, radix: 16));
    } catch (e) {
      return null;
    }
  }

  // Helper to get text color as Color
  Color? get txtColor {
    if (textColor == null) return null;
    try {
      String hex = textColor!.replaceAll('#', '');
      if (hex.length == 6) hex = 'FF$hex';
      return Color(int.parse(hex, radix: 16));
    } catch (e) {
      return null;
    }
  }
}
```

### Step 2: Create Banner Service

```dart
// lib/services/banner_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/banner_model.dart';

class BannerService {
  static const String baseUrl = 'https://eazr.ai.eazr.in';

  /// Get all active banners for a user
  static Future<List<BannerModel>> getBanners({
    required int userId,
    int limit = 10,
  }) async {
    try {
      final url = '$baseUrl/banners?userId=$userId&limit=$limit';

      final response = await http.get(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        if (data['success'] == true && data['data'] != null) {
          final bannersList = data['data']['banners'] as List;
          return bannersList
              .map((json) => BannerModel.fromJson(json))
              .toList();
        }
      }

      return [];
    } catch (e) {
      print('Error fetching banners: $e');
      return [];
    }
  }

  /// Track banner view/impression
  static Future<bool> trackView({
    required int userId,
    required String bannerId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/banners/track-view'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'userId': userId,
          'bannerId': bannerId,
        }),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error tracking banner view: $e');
      return false;
    }
  }

  /// Track banner click
  static Future<bool> trackClick({
    required int userId,
    required String bannerId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/banners/track-click'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'userId': userId,
          'bannerId': bannerId,
        }),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error tracking banner click: $e');
      return false;
    }
  }

  /// Mark banner as seen (for showOnlyOnce banners)
  static Future<bool> markSeen({
    required int userId,
    required String bannerId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/banners/mark-seen'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'userId': userId,
          'bannerId': bannerId,
        }),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error marking banner as seen: $e');
      return false;
    }
  }
}
```

### Step 3: Create Banner Widget

```dart
// lib/widgets/banner_card.dart

import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/banner_model.dart';
import '../services/banner_service.dart';

class BannerCard extends StatefulWidget {
  final BannerModel banner;
  final int userId;
  final VoidCallback? onDismiss;

  const BannerCard({
    Key? key,
    required this.banner,
    required this.userId,
    this.onDismiss,
  }) : super(key: key);

  @override
  State<BannerCard> createState() => _BannerCardState();
}

class _BannerCardState extends State<BannerCard> {
  bool _hasTrackedView = false;

  @override
  void initState() {
    super.initState();
    _trackView();
  }

  void _trackView() {
    if (!_hasTrackedView) {
      BannerService.trackView(
        userId: widget.userId,
        bannerId: widget.banner.bannerId,
      );
      _hasTrackedView = true;
    }
  }

  void _handleTap() {
    // Track click
    BannerService.trackClick(
      userId: widget.userId,
      bannerId: widget.banner.bannerId,
    );

    // Handle CTA based on type
    switch (widget.banner.ctaType) {
      case 'link':
        // Open external URL
        if (widget.banner.ctaValue != null) {
          // Use url_launcher to open link
          // launchUrl(Uri.parse(widget.banner.ctaValue!));
        }
        break;
      case 'screen':
        // Navigate to app screen
        if (widget.banner.ctaValue != null) {
          // Navigator.pushNamed(context, widget.banner.ctaValue!);
        }
        break;
      case 'action':
        // Trigger custom action
        break;
      default:
        // No action
        break;
    }
  }

  void _handleDismiss() {
    // Mark as seen if showOnlyOnce
    if (widget.banner.showOnlyOnce) {
      BannerService.markSeen(
        userId: widget.userId,
        bannerId: widget.banner.bannerId,
      );
    }

    widget.onDismiss?.call();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _handleTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: widget.banner.bgColor ?? Colors.indigo,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Stack(
          children: [
            // Background Image (if any)
            if (widget.banner.backgroundImageUrl != null)
              Positioned.fill(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: CachedNetworkImage(
                    imageUrl: widget.banner.backgroundImageUrl!,
                    fit: BoxFit.cover,
                  ),
                ),
              ),

            // Content
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  // Banner Image (if any)
                  if (widget.banner.imageUrl != null) ...[
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: CachedNetworkImage(
                        imageUrl: widget.banner.imageUrl!,
                        width: 80,
                        height: 80,
                        fit: BoxFit.cover,
                        placeholder: (context, url) => Container(
                          width: 80,
                          height: 80,
                          color: Colors.white24,
                        ),
                        errorWidget: (context, url, error) => Container(
                          width: 80,
                          height: 80,
                          color: Colors.white24,
                          child: const Icon(Icons.image, color: Colors.white54),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                  ],

                  // Text Content
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // Banner Type Badge
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white24,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            widget.banner.bannerType.toUpperCase().replaceAll('_', ' '),
                            style: TextStyle(
                              color: widget.banner.txtColor ?? Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),

                        // Title
                        Text(
                          widget.banner.title,
                          style: TextStyle(
                            color: widget.banner.txtColor ?? Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),

                        // Subtitle
                        if (widget.banner.subtitle != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            widget.banner.subtitle!,
                            style: TextStyle(
                              color: (widget.banner.txtColor ?? Colors.white)
                                  .withOpacity(0.9),
                              fontSize: 14,
                            ),
                          ),
                        ],

                        // Description
                        if (widget.banner.description != null) ...[
                          const SizedBox(height: 8),
                          Text(
                            widget.banner.description!,
                            style: TextStyle(
                              color: (widget.banner.txtColor ?? Colors.white)
                                  .withOpacity(0.8),
                              fontSize: 12,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],

                        // CTA Button
                        if (widget.banner.ctaType != 'none' &&
                            widget.banner.ctaText != null) ...[
                          const SizedBox(height: 12),
                          ElevatedButton(
                            onPressed: _handleTap,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.white,
                              foregroundColor: widget.banner.bgColor ?? Colors.indigo,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 8,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(20),
                              ),
                            ),
                            child: Text(widget.banner.ctaText!),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Close Button (for dismissible banners)
            if (widget.banner.showOnlyOnce)
              Positioned(
                top: 8,
                right: 8,
                child: GestureDetector(
                  onTap: _handleDismiss,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: Colors.black26,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.close,
                      color: widget.banner.txtColor ?? Colors.white,
                      size: 16,
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

### Step 4: Create Banner List Widget

```dart
// lib/widgets/banner_list.dart

import 'package:flutter/material.dart';
import '../models/banner_model.dart';
import '../services/banner_service.dart';
import 'banner_card.dart';

class BannerList extends StatefulWidget {
  final int userId;
  final int limit;
  final Axis scrollDirection;
  final double height;

  const BannerList({
    Key? key,
    required this.userId,
    this.limit = 10,
    this.scrollDirection = Axis.horizontal,
    this.height = 180,
  }) : super(key: key);

  @override
  State<BannerList> createState() => _BannerListState();
}

class _BannerListState extends State<BannerList> {
  List<BannerModel> _banners = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadBanners();
  }

  Future<void> _loadBanners() async {
    setState(() => _isLoading = true);

    final banners = await BannerService.getBanners(
      userId: widget.userId,
      limit: widget.limit,
    );

    setState(() {
      _banners = banners;
      _isLoading = false;
    });
  }

  void _removeBanner(String bannerId) {
    setState(() {
      _banners.removeWhere((b) => b.bannerId == bannerId);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return SizedBox(
        height: widget.height,
        child: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_banners.isEmpty) {
      return const SizedBox.shrink();
    }

    if (widget.scrollDirection == Axis.horizontal) {
      return SizedBox(
        height: widget.height,
        child: PageView.builder(
          itemCount: _banners.length,
          controller: PageController(viewportFraction: 0.9),
          itemBuilder: (context, index) {
            return BannerCard(
              banner: _banners[index],
              userId: widget.userId,
              onDismiss: () => _removeBanner(_banners[index].bannerId),
            );
          },
        ),
      );
    }

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _banners.length,
      itemBuilder: (context, index) {
        return BannerCard(
          banner: _banners[index],
          userId: widget.userId,
          onDismiss: () => _removeBanner(_banners[index].bannerId),
        );
      },
    );
  }
}
```

### Step 5: Usage in Your Screens

```dart
// In your home screen or any screen

import 'package:flutter/material.dart';
import '../widgets/banner_list.dart';

class HomeScreen extends StatelessWidget {
  final int userId = 343; // Get from your auth provider

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SingleChildScrollView(
        child: Column(
          children: [
            // ... other widgets

            // Horizontal scrolling banners
            BannerList(
              userId: userId,
              limit: 5,
              scrollDirection: Axis.horizontal,
              height: 200,
            ),

            // ... more widgets

            // Vertical list of banners
            BannerList(
              userId: userId,
              limit: 3,
              scrollDirection: Axis.vertical,
              height: 0, // Not used for vertical
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## Banner Types Reference

| Type | Description | Use Case |
|------|-------------|----------|
| `promotional` | Promotional offers | Discounts, special offers |
| `informational` | General information | Tips, news, updates |
| `coming_soon` | Upcoming features | Feature announcements |
| `announcement` | Important announcements | Policy changes, updates |
| `alert` | Urgent alerts | Critical notifications |

---

## Target Audience Reference

| Audience | Description |
|----------|-------------|
| `all_users` | Show to everyone |
| `new_users` | Users with no policies |
| `returning_users` | Users with at least 1 policy |
| `premium_users` | Users with 3+ policies |

---

## Dependencies

Add these to your `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.1.0
  cached_network_image: ^3.3.0
  url_launcher: ^6.2.0  # Optional, for external links
```

---

## Notes

1. **Track View**: Call when banner is displayed (automatically handled in BannerCard)
2. **Track Click**: Call when user taps the banner (automatically handled in BannerCard)
3. **Mark Seen**: Call when user dismisses a `showOnlyOnce` banner (automatically handled)
4. **Caching**: Consider caching banners locally to reduce API calls
5. **Error Handling**: Add proper error handling for production
