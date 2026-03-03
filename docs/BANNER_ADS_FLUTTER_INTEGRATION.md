# Banner/Ads System - Flutter Integration Guide

Complete guide for integrating the Banner/Ads system into your Flutter application.

## Table of Contents
1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [Flutter Models](#flutter-models)
4. [Banner Service](#banner-service)
5. [UI Components](#ui-components)
6. [Admin Panel Integration](#admin-panel-integration)
7. [Best Practices](#best-practices)

---

## Overview

The Banner/Ads system allows displaying promotional content, coming soon features, announcements, and alerts in the Flutter app. Features include:

- **Multiple Banner Types**: Promotional, Informational, Coming Soon, Announcement, Alert
- **Position-based Display**: Home top/bottom, Dashboard, Policy List, Profile, Full Screen
- **Smart Targeting**: All users, New users, Returning users, Premium users
- **One-time Display**: Show banners only once per user
- **Scheduling**: Set start and end dates for campaigns
- **Analytics**: Track impressions, clicks, and CTR

---

## API Endpoints

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/banners` | Get active banners for user |
| GET | `/banners/{id}` | Get single banner details |
| POST | `/banners/track-view` | Track banner impression |
| POST | `/banners/track-click` | Track banner click |
| POST | `/banners/mark-seen` | Mark banner as seen (for showOnlyOnce) |

### Admin Endpoints (Requires Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/banners` | List all banners |
| GET | `/admin/banners/{id}` | Get banner details with analytics |
| POST | `/admin/banners` | Create new banner |
| PUT | `/admin/banners/{id}` | Update banner |
| DELETE | `/admin/banners/{id}` | Delete banner |
| POST | `/admin/banners/upload-image` | Upload banner image |
| GET | `/admin/banners/{id}/analytics` | Get banner analytics |
| POST | `/admin/banners/bulk-update` | Bulk update banners |
| GET | `/admin/banners/analytics/summary` | Get overall analytics |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/banners/positions` | Get available positions |
| GET | `/banners/types` | Get available banner types |
| GET | `/banners/audiences` | Get target audiences |

---

## Flutter Models

### banner_model.dart

```dart
// lib/models/banner_model.dart

import 'package:json_annotation/json_annotation.dart';

part 'banner_model.g.dart';

/// Banner types available in the system
enum BannerType {
  @JsonValue('promotional')
  promotional,
  @JsonValue('informational')
  informational,
  @JsonValue('coming_soon')
  comingSoon,
  @JsonValue('announcement')
  announcement,
  @JsonValue('alert')
  alert,
}

/// Banner display positions in the app
enum BannerPosition {
  @JsonValue('home_top')
  homeTop,
  @JsonValue('home_bottom')
  homeBottom,
  @JsonValue('dashboard')
  dashboard,
  @JsonValue('policy_list')
  policyList,
  @JsonValue('profile')
  profile,
  @JsonValue('full_screen')
  fullScreen,
}

/// Call-to-action types
enum CTAType {
  @JsonValue('none')
  none,
  @JsonValue('link')
  link,
  @JsonValue('screen')
  screen,
  @JsonValue('action')
  action,
}

/// Target audience for banners
enum TargetAudience {
  @JsonValue('all_users')
  allUsers,
  @JsonValue('new_users')
  newUsers,
  @JsonValue('returning_users')
  returningUsers,
  @JsonValue('premium_users')
  premiumUsers,
}

@JsonSerializable()
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
  final String position;
  final String ctaType;
  final String? ctaText;
  final String? ctaValue;
  final String targetAudience;
  final int priority;
  final bool isActive;
  final bool showOnlyOnce;
  final String? startDate;
  final String? endDate;
  final List<String>? tags;
  final int? impressions;
  final int? clicks;
  final double? ctr;
  final String? createdAt;
  final String? updatedAt;

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
    required this.position,
    required this.ctaType,
    this.ctaText,
    this.ctaValue,
    required this.targetAudience,
    required this.priority,
    required this.isActive,
    required this.showOnlyOnce,
    this.startDate,
    this.endDate,
    this.tags,
    this.impressions,
    this.clicks,
    this.ctr,
    this.createdAt,
    this.updatedAt,
  });

  factory BannerModel.fromJson(Map<String, dynamic> json) =>
      _$BannerModelFromJson(json);

  Map<String, dynamic> toJson() => _$BannerModelToJson(this);

  /// Get banner type as enum
  BannerType get bannerTypeEnum {
    switch (bannerType) {
      case 'promotional':
        return BannerType.promotional;
      case 'informational':
        return BannerType.informational;
      case 'coming_soon':
        return BannerType.comingSoon;
      case 'announcement':
        return BannerType.announcement;
      case 'alert':
        return BannerType.alert;
      default:
        return BannerType.informational;
    }
  }

  /// Get position as enum
  BannerPosition get positionEnum {
    switch (position) {
      case 'home_top':
        return BannerPosition.homeTop;
      case 'home_bottom':
        return BannerPosition.homeBottom;
      case 'dashboard':
        return BannerPosition.dashboard;
      case 'policy_list':
        return BannerPosition.policyList;
      case 'profile':
        return BannerPosition.profile;
      case 'full_screen':
        return BannerPosition.fullScreen;
      default:
        return BannerPosition.homeTop;
    }
  }

  /// Get background color as Color
  Color? get bgColor {
    if (backgroundColor == null) return null;
    try {
      return Color(int.parse(backgroundColor!.replaceFirst('#', '0xFF')));
    } catch (_) {
      return null;
    }
  }

  /// Get text color as Color
  Color? get txtColor {
    if (textColor == null) return null;
    try {
      return Color(int.parse(textColor!.replaceFirst('#', '0xFF')));
    } catch (_) {
      return null;
    }
  }

  /// Check if banner has CTA
  bool get hasCTA => ctaType != 'none' && ctaText != null;

  /// Check if this is a coming soon banner
  bool get isComingSoon => bannerType == 'coming_soon';
}

/// Response model for banner list
@JsonSerializable()
class BannerListResponse {
  final bool success;
  final BannerListData? data;

  BannerListResponse({required this.success, this.data});

  factory BannerListResponse.fromJson(Map<String, dynamic> json) =>
      _$BannerListResponseFromJson(json);
}

@JsonSerializable()
class BannerListData {
  final List<BannerModel> banners;
  final int count;

  BannerListData({required this.banners, required this.count});

  factory BannerListData.fromJson(Map<String, dynamic> json) =>
      _$BannerListDataFromJson(json);
}
```

### banner_model.g.dart (Generated)

```dart
// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'banner_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BannerModel _$BannerModelFromJson(Map<String, dynamic> json) => BannerModel(
      bannerId: json['bannerId'] as String,
      title: json['title'] as String,
      subtitle: json['subtitle'] as String?,
      description: json['description'] as String?,
      imageUrl: json['imageUrl'] as String?,
      backgroundImageUrl: json['backgroundImageUrl'] as String?,
      backgroundColor: json['backgroundColor'] as String?,
      textColor: json['textColor'] as String?,
      bannerType: json['bannerType'] as String,
      position: json['position'] as String,
      ctaType: json['ctaType'] as String,
      ctaText: json['ctaText'] as String?,
      ctaValue: json['ctaValue'] as String?,
      targetAudience: json['targetAudience'] as String,
      priority: json['priority'] as int,
      isActive: json['isActive'] as bool,
      showOnlyOnce: json['showOnlyOnce'] as bool,
      startDate: json['startDate'] as String?,
      endDate: json['endDate'] as String?,
      tags: (json['tags'] as List<dynamic>?)?.map((e) => e as String).toList(),
      impressions: json['impressions'] as int?,
      clicks: json['clicks'] as int?,
      ctr: (json['ctr'] as num?)?.toDouble(),
      createdAt: json['createdAt'] as String?,
      updatedAt: json['updatedAt'] as String?,
    );

Map<String, dynamic> _$BannerModelToJson(BannerModel instance) =>
    <String, dynamic>{
      'bannerId': instance.bannerId,
      'title': instance.title,
      'subtitle': instance.subtitle,
      'description': instance.description,
      'imageUrl': instance.imageUrl,
      'backgroundImageUrl': instance.backgroundImageUrl,
      'backgroundColor': instance.backgroundColor,
      'textColor': instance.textColor,
      'bannerType': instance.bannerType,
      'position': instance.position,
      'ctaType': instance.ctaType,
      'ctaText': instance.ctaText,
      'ctaValue': instance.ctaValue,
      'targetAudience': instance.targetAudience,
      'priority': instance.priority,
      'isActive': instance.isActive,
      'showOnlyOnce': instance.showOnlyOnce,
      'startDate': instance.startDate,
      'endDate': instance.endDate,
      'tags': instance.tags,
      'impressions': instance.impressions,
      'clicks': instance.clicks,
      'ctr': instance.ctr,
      'createdAt': instance.createdAt,
      'updatedAt': instance.updatedAt,
    };

BannerListResponse _$BannerListResponseFromJson(Map<String, dynamic> json) =>
    BannerListResponse(
      success: json['success'] as bool,
      data: json['data'] == null
          ? null
          : BannerListData.fromJson(json['data'] as Map<String, dynamic>),
    );

BannerListData _$BannerListDataFromJson(Map<String, dynamic> json) =>
    BannerListData(
      banners: (json['banners'] as List<dynamic>)
          .map((e) => BannerModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      count: json['count'] as int,
    );
```

---

## Banner Service

### banner_service.dart

```dart
// lib/services/banner_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/banner_model.dart';
import '../config/api_config.dart';

class BannerService {
  static final BannerService _instance = BannerService._internal();
  factory BannerService() => _instance;
  BannerService._internal();

  final String _baseUrl = ApiConfig.baseUrl;

  /// Get active banners for user
  ///
  /// [userId] - Optional user ID for personalized targeting
  /// [position] - Optional position filter (home_top, dashboard, etc.)
  /// [limit] - Max banners to return (default 10)
  Future<List<BannerModel>> getBanners({
    int? userId,
    String? position,
    int limit = 10,
  }) async {
    try {
      final queryParams = <String, String>{
        'limit': limit.toString(),
      };

      if (userId != null) {
        queryParams['userId'] = userId.toString();
      }
      if (position != null) {
        queryParams['position'] = position;
      }

      final uri = Uri.parse('$_baseUrl/banners').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true && data['data'] != null) {
          final bannerList = data['data']['banners'] as List;
          return bannerList
              .map((b) => BannerModel.fromJson(b))
              .toList();
        }
      }
      return [];
    } catch (e) {
      print('Error fetching banners: $e');
      return [];
    }
  }

  /// Get banners for a specific position
  Future<List<BannerModel>> getBannersForPosition(
    String position, {
    int? userId,
  }) async {
    return getBanners(userId: userId, position: position);
  }

  /// Track banner view/impression
  Future<bool> trackView({
    required String bannerId,
    int? userId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/banners/track-view'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'bannerId': bannerId,
          if (userId != null) 'userId': userId,
        }),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error tracking banner view: $e');
      return false;
    }
  }

  /// Track banner click
  Future<bool> trackClick({
    required String bannerId,
    int? userId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/banners/track-click'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'bannerId': bannerId,
          if (userId != null) 'userId': userId,
        }),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Error tracking banner click: $e');
      return false;
    }
  }

  /// Mark banner as seen (for showOnlyOnce banners)
  Future<bool> markBannerSeen({
    required String bannerId,
    required int userId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/banners/mark-seen'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'bannerId': bannerId,
          'userId': userId,
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

### banner_provider.dart (State Management)

```dart
// lib/providers/banner_provider.dart

import 'package:flutter/foundation.dart';
import '../models/banner_model.dart';
import '../services/banner_service.dart';

class BannerProvider with ChangeNotifier {
  final BannerService _bannerService = BannerService();

  List<BannerModel> _banners = [];
  Map<String, List<BannerModel>> _bannersByPosition = {};
  bool _isLoading = false;
  String? _error;

  // Getters
  List<BannerModel> get banners => _banners;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Get banners for a specific position
  List<BannerModel> getBannersForPosition(String position) {
    return _bannersByPosition[position] ?? [];
  }

  /// Get home top banners
  List<BannerModel> get homeTopBanners =>
      getBannersForPosition('home_top');

  /// Get dashboard banners
  List<BannerModel> get dashboardBanners =>
      getBannersForPosition('dashboard');

  /// Fetch all banners
  Future<void> fetchBanners({int? userId}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _banners = await _bannerService.getBanners(userId: userId);

      // Group by position
      _bannersByPosition = {};
      for (var banner in _banners) {
        final position = banner.position;
        _bannersByPosition[position] ??= [];
        _bannersByPosition[position]!.add(banner);
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch banners for specific position
  Future<void> fetchBannersForPosition(
    String position, {
    int? userId,
  }) async {
    try {
      final banners = await _bannerService.getBannersForPosition(
        position,
        userId: userId,
      );
      _bannersByPosition[position] = banners;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  /// Track view for a banner
  Future<void> trackView(String bannerId, {int? userId}) async {
    await _bannerService.trackView(bannerId: bannerId, userId: userId);
  }

  /// Track click for a banner
  Future<void> trackClick(String bannerId, {int? userId}) async {
    await _bannerService.trackClick(bannerId: bannerId, userId: userId);
  }

  /// Mark banner as seen
  Future<void> markSeen(String bannerId, int userId) async {
    await _bannerService.markBannerSeen(
      bannerId: bannerId,
      userId: userId,
    );

    // Remove from local list
    _banners.removeWhere((b) => b.bannerId == bannerId);
    for (var list in _bannersByPosition.values) {
      list.removeWhere((b) => b.bannerId == bannerId);
    }
    notifyListeners();
  }
}
```

---

## UI Components

### banner_card_widget.dart

```dart
// lib/widgets/banner_card_widget.dart

import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/banner_model.dart';

class BannerCardWidget extends StatelessWidget {
  final BannerModel banner;
  final VoidCallback? onView;
  final VoidCallback? onClick;
  final VoidCallback? onDismiss;

  const BannerCardWidget({
    Key? key,
    required this.banner,
    this.onView,
    this.onClick,
    this.onDismiss,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Trigger view tracking
    WidgetsBinding.instance.addPostFrameCallback((_) {
      onView?.call();
    });

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: banner.bgColor ?? _getDefaultColor(),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Stack(
          children: [
            // Background image if present
            if (banner.backgroundImageUrl != null)
              Positioned.fill(
                child: CachedNetworkImage(
                  imageUrl: banner.backgroundImageUrl!,
                  fit: BoxFit.cover,
                ),
              ),

            // Content
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Type badge (for Coming Soon)
                  if (banner.isComingSoon)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.rocket_launch,
                            size: 14,
                            color: banner.txtColor ?? Colors.white,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            'COMING SOON',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: banner.txtColor ?? Colors.white,
                              letterSpacing: 1,
                            ),
                          ),
                        ],
                      ),
                    ),

                  if (banner.isComingSoon) const SizedBox(height: 12),

                  // Main image
                  if (banner.imageUrl != null) ...[
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: CachedNetworkImage(
                        imageUrl: banner.imageUrl!,
                        height: 120,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        placeholder: (context, url) => Container(
                          height: 120,
                          color: Colors.white.withOpacity(0.1),
                          child: const Center(
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          ),
                        ),
                        errorWidget: (context, url, error) => Container(
                          height: 120,
                          color: Colors.white.withOpacity(0.1),
                          child: const Icon(Icons.image, color: Colors.white54),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Title
                  Text(
                    banner.title,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: banner.txtColor ?? Colors.white,
                    ),
                  ),

                  // Subtitle
                  if (banner.subtitle != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      banner.subtitle!,
                      style: TextStyle(
                        fontSize: 14,
                        color: (banner.txtColor ?? Colors.white).withOpacity(0.8),
                      ),
                    ),
                  ],

                  // Description
                  if (banner.description != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      banner.description!,
                      style: TextStyle(
                        fontSize: 13,
                        color: (banner.txtColor ?? Colors.white).withOpacity(0.7),
                        height: 1.4,
                      ),
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],

                  // CTA Button
                  if (banner.hasCTA) ...[
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => _handleCTA(context),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: banner.bgColor ?? Colors.blue,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 24,
                          vertical: 12,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      child: Text(
                        banner.ctaText!,
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ],
              ),
            ),

            // Dismiss button (for showOnlyOnce banners)
            if (banner.showOnlyOnce && onDismiss != null)
              Positioned(
                top: 8,
                right: 8,
                child: IconButton(
                  onPressed: onDismiss,
                  icon: Icon(
                    Icons.close,
                    color: (banner.txtColor ?? Colors.white).withOpacity(0.7),
                  ),
                  style: IconButton.styleFrom(
                    backgroundColor: Colors.black.withOpacity(0.2),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Color _getDefaultColor() {
    switch (banner.bannerTypeEnum) {
      case BannerType.promotional:
        return const Color(0xFF4F46E5); // Indigo
      case BannerType.informational:
        return const Color(0xFF0284C7); // Blue
      case BannerType.comingSoon:
        return const Color(0xFF7C3AED); // Purple
      case BannerType.announcement:
        return const Color(0xFF059669); // Green
      case BannerType.alert:
        return const Color(0xFFDC2626); // Red
    }
  }

  void _handleCTA(BuildContext context) {
    onClick?.call();

    switch (banner.ctaType) {
      case 'link':
        if (banner.ctaValue != null) {
          launchUrl(Uri.parse(banner.ctaValue!));
        }
        break;
      case 'screen':
        if (banner.ctaValue != null) {
          Navigator.pushNamed(context, banner.ctaValue!);
        }
        break;
      case 'action':
        // Handle custom actions
        _handleAction(context, banner.ctaValue);
        break;
      default:
        break;
    }
  }

  void _handleAction(BuildContext context, String? action) {
    // Implement custom action handling
    switch (action) {
      case 'notify_me':
        // Show notification dialog
        break;
      case 'share':
        // Share banner
        break;
      default:
        break;
    }
  }
}
```

### banner_carousel_widget.dart

```dart
// lib/widgets/banner_carousel_widget.dart

import 'package:flutter/material.dart';
import 'package:carousel_slider/carousel_slider.dart';
import 'package:provider/provider.dart';
import '../models/banner_model.dart';
import '../providers/banner_provider.dart';
import 'banner_card_widget.dart';

class BannerCarouselWidget extends StatefulWidget {
  final String position;
  final int? userId;
  final double height;
  final bool autoPlay;
  final Duration autoPlayInterval;

  const BannerCarouselWidget({
    Key? key,
    required this.position,
    this.userId,
    this.height = 200,
    this.autoPlay = true,
    this.autoPlayInterval = const Duration(seconds: 5),
  }) : super(key: key);

  @override
  State<BannerCarouselWidget> createState() => _BannerCarouselWidgetState();
}

class _BannerCarouselWidgetState extends State<BannerCarouselWidget> {
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<BannerProvider>().fetchBannersForPosition(
        widget.position,
        userId: widget.userId,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<BannerProvider>(
      builder: (context, provider, child) {
        final banners = provider.getBannersForPosition(widget.position);

        if (banners.isEmpty) {
          return const SizedBox.shrink();
        }

        return Column(
          children: [
            CarouselSlider.builder(
              itemCount: banners.length,
              itemBuilder: (context, index, realIndex) {
                final banner = banners[index];
                return BannerCardWidget(
                  banner: banner,
                  onView: () => provider.trackView(
                    banner.bannerId,
                    userId: widget.userId,
                  ),
                  onClick: () => provider.trackClick(
                    banner.bannerId,
                    userId: widget.userId,
                  ),
                  onDismiss: banner.showOnlyOnce && widget.userId != null
                      ? () => provider.markSeen(
                            banner.bannerId,
                            widget.userId!,
                          )
                      : null,
                );
              },
              options: CarouselOptions(
                height: widget.height,
                viewportFraction: 0.9,
                enlargeCenterPage: true,
                autoPlay: widget.autoPlay && banners.length > 1,
                autoPlayInterval: widget.autoPlayInterval,
                onPageChanged: (index, reason) {
                  setState(() {
                    _currentIndex = index;
                  });
                },
              ),
            ),

            // Page indicators
            if (banners.length > 1) ...[
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  banners.length,
                  (index) => AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: _currentIndex == index ? 24 : 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: _currentIndex == index
                          ? Theme.of(context).primaryColor
                          : Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ),
              ),
            ],
          ],
        );
      },
    );
  }
}
```

### full_screen_banner_dialog.dart

```dart
// lib/widgets/full_screen_banner_dialog.dart

import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/banner_model.dart';

class FullScreenBannerDialog extends StatelessWidget {
  final BannerModel banner;
  final VoidCallback? onDismiss;
  final VoidCallback? onClick;

  const FullScreenBannerDialog({
    Key? key,
    required this.banner,
    this.onDismiss,
    this.onClick,
  }) : super(key: key);

  static Future<void> show(
    BuildContext context, {
    required BannerModel banner,
    VoidCallback? onDismiss,
    VoidCallback? onClick,
  }) {
    return showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => FullScreenBannerDialog(
        banner: banner,
        onDismiss: onDismiss,
        onClick: onClick,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.all(20),
      backgroundColor: Colors.transparent,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 400),
        decoration: BoxDecoration(
          color: banner.bgColor ?? const Color(0xFF4F46E5),
          borderRadius: BorderRadius.circular(24),
        ),
        child: Stack(
          children: [
            // Background image
            if (banner.backgroundImageUrl != null)
              Positioned.fill(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(24),
                  child: CachedNetworkImage(
                    imageUrl: banner.backgroundImageUrl!,
                    fit: BoxFit.cover,
                  ),
                ),
              ),

            // Content
            Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Close button
                  Align(
                    alignment: Alignment.topRight,
                    child: IconButton(
                      onPressed: () {
                        Navigator.of(context).pop();
                        onDismiss?.call();
                      },
                      icon: Icon(
                        Icons.close,
                        color: banner.txtColor ?? Colors.white,
                      ),
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.white.withOpacity(0.2),
                      ),
                    ),
                  ),

                  // Coming Soon Badge
                  if (banner.isComingSoon) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.rocket_launch,
                            color: banner.txtColor ?? Colors.white,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'COMING SOON',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: banner.txtColor ?? Colors.white,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],

                  // Image
                  if (banner.imageUrl != null) ...[
                    ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: CachedNetworkImage(
                        imageUrl: banner.imageUrl!,
                        height: 180,
                        width: double.infinity,
                        fit: BoxFit.cover,
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],

                  // Title
                  Text(
                    banner.title,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: banner.txtColor ?? Colors.white,
                    ),
                    textAlign: TextAlign.center,
                  ),

                  // Subtitle
                  if (banner.subtitle != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      banner.subtitle!,
                      style: TextStyle(
                        fontSize: 16,
                        color: (banner.txtColor ?? Colors.white).withOpacity(0.8),
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],

                  // Description
                  if (banner.description != null) ...[
                    const SizedBox(height: 16),
                    Text(
                      banner.description!,
                      style: TextStyle(
                        fontSize: 14,
                        color: (banner.txtColor ?? Colors.white).withOpacity(0.7),
                        height: 1.5,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],

                  const SizedBox(height: 24),

                  // CTA Button
                  if (banner.hasCTA)
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {
                          onClick?.call();
                          _handleCTA(context);
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: banner.bgColor ?? Colors.blue,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: Text(
                          banner.ctaText!,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _handleCTA(BuildContext context) {
    Navigator.of(context).pop();

    if (banner.ctaType == 'link' && banner.ctaValue != null) {
      launchUrl(Uri.parse(banner.ctaValue!));
    } else if (banner.ctaType == 'screen' && banner.ctaValue != null) {
      Navigator.pushNamed(context, banner.ctaValue!);
    }
  }
}
```

---

## Usage Examples

### Home Screen Integration

```dart
// lib/screens/home_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/banner_provider.dart';
import '../widgets/banner_carousel_widget.dart';

class HomeScreen extends StatefulWidget {
  final int userId;

  const HomeScreen({Key? key, required this.userId}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    // Check for full-screen banners
    _checkFullScreenBanners();
  }

  Future<void> _checkFullScreenBanners() async {
    await Future.delayed(const Duration(milliseconds: 500));
    if (!mounted) return;

    final provider = context.read<BannerProvider>();
    await provider.fetchBannersForPosition('full_screen', userId: widget.userId);

    final fullScreenBanners = provider.getBannersForPosition('full_screen');
    if (fullScreenBanners.isNotEmpty) {
      final banner = fullScreenBanners.first;

      FullScreenBannerDialog.show(
        context,
        banner: banner,
        onDismiss: () {
          if (banner.showOnlyOnce) {
            provider.markSeen(banner.bannerId, widget.userId);
          }
        },
        onClick: () {
          provider.trackClick(banner.bannerId, userId: widget.userId);
        },
      );

      provider.trackView(banner.bannerId, userId: widget.userId);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              // Top banner carousel
              BannerCarouselWidget(
                position: 'home_top',
                userId: widget.userId,
                height: 200,
              ),

              // Your other home content...
              const Padding(
                padding: EdgeInsets.all(16),
                child: Text(
                  'Welcome to Eazr',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),

              // More content...

              // Bottom banner
              BannerCarouselWidget(
                position: 'home_bottom',
                userId: widget.userId,
                height: 150,
                autoPlay: false,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### Dashboard Integration

```dart
// In your dashboard screen
BannerCarouselWidget(
  position: 'dashboard',
  userId: currentUserId,
  height: 180,
),
```

---

## Admin Panel Integration

### Admin Banner Management

```dart
// lib/admin/services/admin_banner_service.dart

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../../models/banner_model.dart';
import '../../config/api_config.dart';

class AdminBannerService {
  final String _baseUrl = ApiConfig.baseUrl;
  final String _adminToken;

  AdminBannerService(this._adminToken);

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $_adminToken',
  };

  /// List all banners
  Future<List<BannerModel>> listBanners({
    int skip = 0,
    int limit = 20,
    bool? isActive,
    String? bannerType,
    String? position,
  }) async {
    final params = <String, String>{
      'skip': skip.toString(),
      'limit': limit.toString(),
    };
    if (isActive != null) params['isActive'] = isActive.toString();
    if (bannerType != null) params['bannerType'] = bannerType;
    if (position != null) params['position'] = position;

    final uri = Uri.parse('$_baseUrl/admin/banners').replace(
      queryParameters: params,
    );

    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data['success'] == true) {
        final bannerList = data['data']['banners'] as List;
        return bannerList.map((b) => BannerModel.fromJson(b)).toList();
      }
    }
    throw Exception('Failed to list banners');
  }

  /// Create new banner
  Future<BannerModel> createBanner({
    required String title,
    String? subtitle,
    String? description,
    String? imageUrl,
    String? backgroundColor,
    String? textColor,
    required String bannerType,
    required String position,
    String ctaType = 'none',
    String? ctaText,
    String? ctaValue,
    String targetAudience = 'all_users',
    int priority = 0,
    bool isActive = true,
    bool showOnlyOnce = false,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    final body = {
      'title': title,
      if (subtitle != null) 'subtitle': subtitle,
      if (description != null) 'description': description,
      if (imageUrl != null) 'imageUrl': imageUrl,
      if (backgroundColor != null) 'backgroundColor': backgroundColor,
      if (textColor != null) 'textColor': textColor,
      'bannerType': bannerType,
      'position': position,
      'ctaType': ctaType,
      if (ctaText != null) 'ctaText': ctaText,
      if (ctaValue != null) 'ctaValue': ctaValue,
      'targetAudience': targetAudience,
      'priority': priority,
      'isActive': isActive,
      'showOnlyOnce': showOnlyOnce,
      if (startDate != null) 'startDate': startDate.toIso8601String(),
      if (endDate != null) 'endDate': endDate.toIso8601String(),
    };

    final response = await http.post(
      Uri.parse('$_baseUrl/admin/banners'),
      headers: _headers,
      body: json.encode(body),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data['success'] == true) {
        return BannerModel.fromJson(data['data']['banner']);
      }
    }
    throw Exception('Failed to create banner');
  }

  /// Update banner
  Future<BannerModel> updateBanner(
    String bannerId,
    Map<String, dynamic> updates,
  ) async {
    final response = await http.put(
      Uri.parse('$_baseUrl/admin/banners/$bannerId'),
      headers: _headers,
      body: json.encode(updates),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data['success'] == true) {
        return BannerModel.fromJson(data['data']['banner']);
      }
    }
    throw Exception('Failed to update banner');
  }

  /// Delete banner
  Future<void> deleteBanner(String bannerId, {bool permanent = false}) async {
    final uri = Uri.parse('$_baseUrl/admin/banners/$bannerId').replace(
      queryParameters: {'permanent': permanent.toString()},
    );

    final response = await http.delete(uri, headers: _headers);

    if (response.statusCode != 200) {
      throw Exception('Failed to delete banner');
    }
  }

  /// Upload banner image
  Future<String> uploadImage(File imageFile) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/admin/banners/upload-image'),
    );

    request.headers.addAll({
      'Authorization': 'Bearer $_adminToken',
    });

    final mimeType = _getMimeType(imageFile.path);
    request.files.add(
      await http.MultipartFile.fromPath(
        'file',
        imageFile.path,
        contentType: MediaType.parse(mimeType),
      ),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data['success'] == true) {
        return data['data']['imageUrl'];
      }
    }
    throw Exception('Failed to upload image');
  }

  String _getMimeType(String path) {
    final ext = path.split('.').last.toLowerCase();
    switch (ext) {
      case 'jpg':
      case 'jpeg':
        return 'image/jpeg';
      case 'png':
        return 'image/png';
      case 'webp':
        return 'image/webp';
      case 'gif':
        return 'image/gif';
      default:
        return 'application/octet-stream';
    }
  }

  /// Get banner analytics
  Future<Map<String, dynamic>> getAnalytics(
    String bannerId, {
    int days = 30,
  }) async {
    final uri = Uri.parse('$_baseUrl/admin/banners/$bannerId/analytics').replace(
      queryParameters: {'days': days.toString()},
    );

    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data['success'] == true) {
        return data['data'];
      }
    }
    throw Exception('Failed to get analytics');
  }

  /// Get analytics summary
  Future<Map<String, dynamic>> getAnalyticsSummary({int days = 30}) async {
    final uri = Uri.parse('$_baseUrl/admin/banners/analytics/summary').replace(
      queryParameters: {'days': days.toString()},
    );

    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      if (data['success'] == true) {
        return data['data'];
      }
    }
    throw Exception('Failed to get analytics summary');
  }
}
```

---

## Best Practices

### 1. Loading Banners Efficiently

```dart
// Load banners on app startup
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Pre-fetch banners
  final bannerProvider = BannerProvider();
  await bannerProvider.fetchBanners(userId: await getUserId());

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: bannerProvider),
        // ... other providers
      ],
      child: const MyApp(),
    ),
  );
}
```

### 2. Caching Images

Use `cached_network_image` package for efficient image caching:

```yaml
# pubspec.yaml
dependencies:
  cached_network_image: ^3.3.0
```

### 3. Error Handling

```dart
try {
  await bannerProvider.fetchBanners(userId: userId);
} catch (e) {
  // Show cached banners or fallback UI
  // Don't crash the app for banner failures
}
```

### 4. Analytics Integration

```dart
// Track views when banner becomes visible
VisibilityDetector(
  key: Key('banner_${banner.bannerId}'),
  onVisibilityChanged: (info) {
    if (info.visibleFraction > 0.5 && !_viewTracked) {
      _viewTracked = true;
      bannerProvider.trackView(banner.bannerId, userId: userId);
    }
  },
  child: BannerCardWidget(banner: banner),
)
```

### 5. Full-screen Banner Timing

```dart
// Show full-screen banner after app loads
// Don't show immediately - wait for main content
Future.delayed(const Duration(seconds: 2), () {
  _showFullScreenBannerIfNeeded();
});
```

---

## API Response Examples

### GET /banners

```json
{
  "success": true,
  "data": {
    "banners": [
      {
        "bannerId": "678abc123def456789012345",
        "title": "AI Policy Assistant - Coming Soon!",
        "subtitle": "Your personal insurance advisor",
        "description": "Get instant answers about your policies...",
        "imageUrl": null,
        "backgroundColor": "#4F46E5",
        "textColor": "#FFFFFF",
        "bannerType": "coming_soon",
        "position": "home_top",
        "ctaType": "none",
        "ctaText": null,
        "ctaValue": null,
        "targetAudience": "all_users",
        "priority": 100,
        "isActive": true,
        "showOnlyOnce": false,
        "startDate": null,
        "endDate": null,
        "createdAt": "2024-01-23T10:30:00Z"
      }
    ],
    "count": 1
  }
}
```

### POST /admin/banners (Create)

**Request:**
```json
{
  "title": "Special Health Insurance Offer",
  "subtitle": "20% Off Premium",
  "description": "Get comprehensive health coverage at discounted rates.",
  "imageUrl": "https://s3.amazonaws.com/bucket/banner.jpg",
  "backgroundColor": "#059669",
  "textColor": "#FFFFFF",
  "bannerType": "promotional",
  "position": "home_top",
  "ctaType": "link",
  "ctaText": "Learn More",
  "ctaValue": "https://eazr.in/offers",
  "targetAudience": "returning_users",
  "priority": 90,
  "isActive": true,
  "showOnlyOnce": false,
  "startDate": "2024-01-01T00:00:00Z",
  "endDate": "2024-03-31T23:59:59Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Banner created successfully",
  "data": {
    "banner": {
      "bannerId": "678def456abc789012345678",
      "title": "Special Health Insurance Offer",
      ...
    }
  }
}
```

---

## File Locations

| File | Location |
|------|----------|
| Banner Model | `lib/models/banner_model.dart` |
| Banner Service | `lib/services/banner_service.dart` |
| Banner Provider | `lib/providers/banner_provider.dart` |
| Banner Card Widget | `lib/widgets/banner_card_widget.dart` |
| Banner Carousel Widget | `lib/widgets/banner_carousel_widget.dart` |
| Full Screen Banner | `lib/widgets/full_screen_banner_dialog.dart` |
| Admin Banner Service | `lib/admin/services/admin_banner_service.dart` |

---

## Dependencies

Add to `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.1.0
  provider: ^6.1.1
  cached_network_image: ^3.3.0
  carousel_slider: ^4.2.1
  url_launcher: ^6.2.1
  json_annotation: ^4.8.1
  visibility_detector: ^0.4.0+2

dev_dependencies:
  json_serializable: ^6.7.1
  build_runner: ^2.4.7
```

---

## Summary

The Banner/Ads system provides a complete solution for displaying promotional content in your Flutter app with:

1. **User-facing features**: Carousel banners, full-screen popups, smart targeting
2. **Admin management**: Full CRUD, image upload, analytics
3. **Analytics**: Impressions, clicks, CTR tracking
4. **Scheduling**: Start/end dates for campaigns
5. **Targeting**: Different content for different user segments

For questions or issues, contact the development team.
