// Policy Analyzer Response Models
// Generated for EAZR Policy Analysis API
// Supports: Motor, Health, Life Insurance unified response structure

import 'package:json_annotation/json_annotation.dart';

part 'policy_analyzer_models.g.dart';

/// Main API Response wrapper
@JsonSerializable(explicitToJson: true)
class PolicyUploadResponse {
  final bool success;
  final String userId;
  final String policyId;
  final String policyNumber;
  final String message;
  final PolicyDetails policyDetails;
  final PolicyAnalyzer policyAnalyzer;
  final InsuranceProviderInfo? insuranceProviderInfo;
  final String processedAt;
  final InternalMetadata internal;

  PolicyUploadResponse({
    required this.success,
    required this.userId,
    required this.policyId,
    required this.policyNumber,
    required this.message,
    required this.policyDetails,
    required this.policyAnalyzer,
    this.insuranceProviderInfo,
    required this.processedAt,
    required this.internal,
  });

  factory PolicyUploadResponse.fromJson(Map<String, dynamic> json) =>
      _$PolicyUploadResponseFromJson(json);

  Map<String, dynamic> toJson() => _$PolicyUploadResponseToJson(this);
}

/// Policy Details Section
@JsonSerializable(explicitToJson: true)
class PolicyDetails {
  final String policyNumber;
  final String? uin;
  final String insuranceProvider;
  final String policyType;
  final String policyHolderName;
  final String insuredName;
  final double coverageAmount;
  final double sumAssured;
  final double premium;
  final String premiumFrequency;
  final String startDate;
  final String endDate;
  final String status; // active, expired, upcoming
  final String relationship;
  final String originalDocumentUrl;
  final List<PolicySection> sections;
  final Map<String, dynamic> categorySpecificData;
  final List<String> keyBenefitsSummary;
  final List<String> coverageGapsSummary;

  PolicyDetails({
    required this.policyNumber,
    this.uin,
    required this.insuranceProvider,
    required this.policyType,
    required this.policyHolderName,
    required this.insuredName,
    required this.coverageAmount,
    required this.sumAssured,
    required this.premium,
    required this.premiumFrequency,
    required this.startDate,
    required this.endDate,
    required this.status,
    required this.relationship,
    required this.originalDocumentUrl,
    required this.sections,
    required this.categorySpecificData,
    required this.keyBenefitsSummary,
    required this.coverageGapsSummary,
  });

  factory PolicyDetails.fromJson(Map<String, dynamic> json) =>
      _$PolicyDetailsFromJson(json);

  Map<String, dynamic> toJson() => _$PolicyDetailsToJson(this);
}

/// Policy Section (Unified structure for all policy types)
@JsonSerializable(explicitToJson: true)
class PolicySection {
  final String sectionId;
  final String sectionTitle;
  final String sectionType; // fields, list, value
  final int displayOrder;
  final List<PolicyField>? fields; // For sectionType: "fields"
  final List<PolicyItem>? items; // For sectionType: "list"
  final dynamic value; // For sectionType: "value"
  final String? valueType;

  PolicySection({
    required this.sectionId,
    required this.sectionTitle,
    required this.sectionType,
    required this.displayOrder,
    this.fields,
    this.items,
    this.value,
    this.valueType,
  });

  factory PolicySection.fromJson(Map<String, dynamic> json) =>
      _$PolicySectionFromJson(json);

  Map<String, dynamic> toJson() => _$PolicySectionToJson(this);
}

/// Policy Field (key-value pair)
@JsonSerializable()
class PolicyField {
  final String fieldId;
  final String label;
  final dynamic value;
  final String valueType; // string, number, boolean, date, currency, array, object
  final int displayOrder;

  PolicyField({
    required this.fieldId,
    required this.label,
    required this.value,
    required this.valueType,
    required this.displayOrder,
  });

  factory PolicyField.fromJson(Map<String, dynamic> json) =>
      _$PolicyFieldFromJson(json);

  Map<String, dynamic> toJson() => _$PolicyFieldToJson(this);
}

/// Policy Item (for list sections)
@JsonSerializable(explicitToJson: true)
class PolicyItem {
  final String itemId;
  final List<PolicyField>? fields;
  final String? value;

  PolicyItem({
    required this.itemId,
    this.fields,
    this.value,
  });

  factory PolicyItem.fromJson(Map<String, dynamic> json) =>
      _$PolicyItemFromJson(json);

  Map<String, dynamic> toJson() => _$PolicyItemToJson(this);
}

/// Policy Analyzer Section (Light Analysis)
/// UNIFIED structure for Motor, Health, Life insurance
@JsonSerializable(explicitToJson: true)
class PolicyAnalyzer {
  final String insurerName;
  final String planName;
  final String policyType;

  // Motor-specific fields
  final VehicleInfo? vehicleInfo;

  // UNIFIED FIELDS (present in all types)
  final CoverageVerdict coverageVerdict;
  final ProtectionVerdict? protectionVerdict; // Backward compatibility
  final int protectionScore;
  final String protectionScoreLabel;
  final ClaimRealityCheck claimRealityCheck;
  final NumbersThatMatter numbersThatMatter;
  final List<KeyConcern> keyConcerns;
  final List<CoverageGap> coverageGaps;
  final WhatYouShouldDo whatYouShouldDo;
  final List<String> policyStrengths;
  final QuickReference quickReference;

  // Motor-specific additional fields
  final ReplacementGap? replacementGap; // Motor only
  final AddOnsStatus? addOnsStatus; // Motor only
  final NCBInfo? ncb; // Motor only

  // Report metadata
  final String? reportUrl;
  final String? reportError;
  final String reportDate;
  final String analysisVersion;

  PolicyAnalyzer({
    required this.insurerName,
    required this.planName,
    required this.policyType,
    this.vehicleInfo,
    required this.coverageVerdict,
    this.protectionVerdict,
    required this.protectionScore,
    required this.protectionScoreLabel,
    required this.claimRealityCheck,
    required this.numbersThatMatter,
    required this.keyConcerns,
    required this.coverageGaps,
    required this.whatYouShouldDo,
    required this.policyStrengths,
    required this.quickReference,
    this.replacementGap,
    this.addOnsStatus,
    this.ncb,
    this.reportUrl,
    this.reportError,
    required this.reportDate,
    required this.analysisVersion,
  });

  factory PolicyAnalyzer.fromJson(Map<String, dynamic> json) =>
      _$PolicyAnalyzerFromJson(json);

  Map<String, dynamic> toJson() => _$PolicyAnalyzerToJson(this);

  // Helper methods
  bool get isMotorInsurance => policyType == 'motor';
  bool get isHealthInsurance =>
      policyType == 'health' || policyType == 'medical';
  bool get isLifeInsurance => policyType == 'life' || policyType == 'term';
  bool get hasReport => reportUrl != null && reportUrl!.isNotEmpty;
}

/// Vehicle Info (Motor Insurance only)
@JsonSerializable()
class VehicleInfo {
  final String make;
  final String model;
  final int year;

  VehicleInfo({
    required this.make,
    required this.model,
    required this.year,
  });

  factory VehicleInfo.fromJson(Map<String, dynamic> json) =>
      _$VehicleInfoFromJson(json);

  Map<String, dynamic> toJson() => _$VehicleInfoToJson(this);

  String get displayName => '$make $model ($year)';
}

/// Coverage Verdict (UNIFIED)
@JsonSerializable()
class CoverageVerdict {
  final String emoji; // shield, warning, alert
  final String label; // Well Protected, Adequate Coverage, Needs Attention
  final String oneLiner;

  CoverageVerdict({
    required this.emoji,
    required this.label,
    required this.oneLiner,
  });

  factory CoverageVerdict.fromJson(Map<String, dynamic> json) =>
      _$CoverageVerdictFromJson(json);

  Map<String, dynamic> toJson() => _$CoverageVerdictToJson(this);

  String get emojiIcon {
    switch (emoji) {
      case 'shield':
        return '🛡️';
      case 'warning':
        return '⚠️';
      case 'alert':
        return '🚨';
      case 'check':
        return '✅';
      case 'cross':
        return '❌';
      default:
        return '⚠️';
    }
  }
}

/// Protection Verdict (Backward compatibility - same as CoverageVerdict)
@JsonSerializable()
class ProtectionVerdict {
  final String emoji;
  final String label;
  final String oneLiner;

  ProtectionVerdict({
    required this.emoji,
    required this.label,
    required this.oneLiner,
  });

  factory ProtectionVerdict.fromJson(Map<String, dynamic> json) =>
      _$ProtectionVerdictFromJson(json);

  Map<String, dynamic> toJson() => _$ProtectionVerdictToJson(this);
}

/// Claim Reality Check (UNIFIED)
@JsonSerializable()
class ClaimRealityCheck {
  final double claimAmount;
  final double insurancePays;
  final double youPay;
  final String oneLiner;
  final String currency;

  // Motor-specific fields
  final bool? hasZeroDep;
  final int? depreciationPercentage;

  ClaimRealityCheck({
    required this.claimAmount,
    required this.insurancePays,
    required this.youPay,
    required this.oneLiner,
    required this.currency,
    this.hasZeroDep,
    this.depreciationPercentage,
  });

  factory ClaimRealityCheck.fromJson(Map<String, dynamic> json) =>
      _$ClaimRealityCheckFromJson(json);

  Map<String, dynamic> toJson() => _$ClaimRealityCheckToJson(this);

  double get youPayPercentage =>
      claimAmount > 0 ? (youPay / claimAmount) * 100 : 0;
}

/// Numbers That Matter (UNIFIED)
@JsonSerializable()
class NumbersThatMatter {
  final double yourCover;
  final double yourNeed;
  final double gap;
  final String gapOneLiner;

  // Motor-specific nested data
  final Map<String, dynamic>? motorSpecific;

  NumbersThatMatter({
    required this.yourCover,
    required this.yourNeed,
    required this.gap,
    required this.gapOneLiner,
    this.motorSpecific,
  });

  factory NumbersThatMatter.fromJson(Map<String, dynamic> json) =>
      _$NumbersThatMatterFromJson(json);

  Map<String, dynamic> toJson() => _$NumbersThatMatterToJson(this);

  bool get hasGap => gap > 0;
  double get coveragePercentage =>
      yourNeed > 0 ? (yourCover / yourNeed) * 100 : 100;
}

/// Replacement Gap (Motor Insurance only)
@JsonSerializable()
class ReplacementGap {
  final double idv;
  final double currentOnRoadPrice;
  final double gap;
  final bool hasLoan;
  final double outstandingLoan;
  final String loanWarning;

  ReplacementGap({
    required this.idv,
    required this.currentOnRoadPrice,
    required this.gap,
    required this.hasLoan,
    required this.outstandingLoan,
    required this.loanWarning,
  });

  factory ReplacementGap.fromJson(Map<String, dynamic> json) =>
      _$ReplacementGapFromJson(json);

  Map<String, dynamic> toJson() => _$ReplacementGapToJson(this);
}

/// Key Concern (UNIFIED)
@JsonSerializable()
class KeyConcern {
  final String title;
  final String brief;
  final String severity; // high, medium, low

  KeyConcern({
    required this.title,
    required this.brief,
    required this.severity,
  });

  factory KeyConcern.fromJson(Map<String, dynamic> json) =>
      _$KeyConcernFromJson(json);

  Map<String, dynamic> toJson() => _$KeyConcernToJson(this);

  String get severityIcon {
    switch (severity) {
      case 'high':
        return '🔴';
      case 'medium':
        return '🟡';
      case 'low':
        return '🟢';
      default:
        return '⚪';
    }
  }

  bool get isHighSeverity => severity == 'high';
}

/// Coverage Gap (UNIFIED)
@JsonSerializable()
class CoverageGap {
  final String area;
  final String status;
  final String statusType; // success, warning, danger, info
  final String details;

  CoverageGap({
    required this.area,
    required this.status,
    required this.statusType,
    required this.details,
  });

  factory CoverageGap.fromJson(Map<String, dynamic> json) =>
      _$CoverageGapFromJson(json);

  Map<String, dynamic> toJson() => _$CoverageGapToJson(this);

  String get statusIcon {
    switch (statusType) {
      case 'success':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'danger':
        return '❌';
      case 'info':
        return 'ℹ️';
      default:
        return '⚪';
    }
  }

  bool get isCritical => statusType == 'danger';
}

/// Add-Ons Status (Motor Insurance only)
@JsonSerializable(explicitToJson: true)
class AddOnsStatus {
  final AddOnDetail zeroDepreciation;
  final AddOnDetail engineProtection;
  final AddOnDetail ncbProtection;
  final AddOnDetail returnToInvoice;
  final AddOnDetail roadsideAssistance;

  AddOnsStatus({
    required this.zeroDepreciation,
    required this.engineProtection,
    required this.ncbProtection,
    required this.returnToInvoice,
    required this.roadsideAssistance,
  });

  factory AddOnsStatus.fromJson(Map<String, dynamic> json) =>
      _$AddOnsStatusFromJson(json);

  Map<String, dynamic> toJson() => _$AddOnsStatusToJson(this);

  List<AddOnDetail> get allAddOns => [
        zeroDepreciation,
        engineProtection,
        ncbProtection,
        returnToInvoice,
        roadsideAssistance,
      ];

  List<AddOnDetail> get activeAddOns =>
      allAddOns.where((addon) => addon.isActive).toList();

  List<AddOnDetail> get missingAddOns =>
      allAddOns.where((addon) => !addon.isActive).toList();
}

/// Add-On Detail
@JsonSerializable()
class AddOnDetail {
  final String status; // Active, Not Covered
  final String emoji; // ✅, ❌
  final String impact;

  AddOnDetail({
    required this.status,
    required this.emoji,
    required this.impact,
  });

  factory AddOnDetail.fromJson(Map<String, dynamic> json) =>
      _$AddOnDetailFromJson(json);

  Map<String, dynamic> toJson() => _$AddOnDetailToJson(this);

  bool get isActive => status == 'Active';
}

/// NCB Info (Motor Insurance only)
@JsonSerializable()
class NCBInfo {
  final int percentage;
  final double savings;
  final String claimConsequence;
  final String recommendation;

  NCBInfo({
    required this.percentage,
    required this.savings,
    required this.claimConsequence,
    required this.recommendation,
  });

  factory NCBInfo.fromJson(Map<String, dynamic> json) =>
      _$NCBInfoFromJson(json);

  Map<String, dynamic> toJson() => _$NCBInfoToJson(this);

  bool get hasNCB => percentage > 0;
}

/// What You Should Do (UNIFIED)
@JsonSerializable(explicitToJson: true)
class WhatYouShouldDo {
  final ActionItem? immediate;
  final ActionItem? shortTerm;
  final ActionItem? ongoing;
  final ActionItem? renewal; // Motor uses this instead of shortTerm

  WhatYouShouldDo({
    this.immediate,
    this.shortTerm,
    this.ongoing,
    this.renewal,
  });

  factory WhatYouShouldDo.fromJson(Map<String, dynamic> json) =>
      _$WhatYouShouldDoFromJson(json);

  Map<String, dynamic> toJson() => _$WhatYouShouldDoToJson(this);

  List<ActionItem> get allActions {
    final actions = <ActionItem>[];
    if (immediate != null) actions.add(immediate!);
    if (shortTerm != null) actions.add(shortTerm!);
    if (renewal != null) actions.add(renewal!);
    if (ongoing != null) actions.add(ongoing!);
    return actions;
  }

  bool get hasActions => allActions.isNotEmpty;
}

/// Action Item
@JsonSerializable()
class ActionItem {
  final String action;
  final String brief;

  ActionItem({
    required this.action,
    required this.brief,
  });

  factory ActionItem.fromJson(Map<String, dynamic> json) =>
      _$ActionItemFromJson(json);

  Map<String, dynamic> toJson() => _$ActionItemToJson(this);
}

/// Quick Reference (UNIFIED)
@JsonSerializable()
class QuickReference {
  final String? claimsHelpline;
  final String? policyExpiry;
  final int? ncbPercentage; // Motor

  // Health-specific
  final String? cashlessHospitals;
  final String? tpaName;
  final String? renewalDate;

  // Motor-specific
  final String? garageNetwork;
  final double? idv;

  // Life-specific
  final String? policyTerm;
  final String? premiumPayingTerm;
  final String? maturityDate;

  QuickReference({
    this.claimsHelpline,
    this.policyExpiry,
    this.ncbPercentage,
    this.cashlessHospitals,
    this.tpaName,
    this.renewalDate,
    this.garageNetwork,
    this.idv,
    this.policyTerm,
    this.premiumPayingTerm,
    this.maturityDate,
  });

  factory QuickReference.fromJson(Map<String, dynamic> json) =>
      _$QuickReferenceFromJson(json);

  Map<String, dynamic> toJson() => _$QuickReferenceToJson(this);
}

/// Insurance Provider Info
@JsonSerializable(explicitToJson: true)
class InsuranceProviderInfo {
  final String providerName;
  final String? fullName;
  final String? type;
  final String? founded;
  final String? headquarters;
  final String? about;
  final String? claimSettlementRatio;
  final String? claimSettlementYear;
  final CustomerSupport? customerSupport;
  final List<String>? specialties;
  final String? networkSize;

  InsuranceProviderInfo({
    required this.providerName,
    this.fullName,
    this.type,
    this.founded,
    this.headquarters,
    this.about,
    this.claimSettlementRatio,
    this.claimSettlementYear,
    this.customerSupport,
    this.specialties,
    this.networkSize,
  });

  factory InsuranceProviderInfo.fromJson(Map<String, dynamic> json) =>
      _$InsuranceProviderInfoFromJson(json);

  Map<String, dynamic> toJson() => _$InsuranceProviderInfoToJson(this);
}

/// Customer Support
@JsonSerializable()
class CustomerSupport {
  final String? phone;
  final String? email;
  final String? whatsapp;
  final String? website;
  final String? claimEmail;

  CustomerSupport({
    this.phone,
    this.email,
    this.whatsapp,
    this.website,
    this.claimEmail,
  });

  factory CustomerSupport.fromJson(Map<String, dynamic> json) =>
      _$CustomerSupportFromJson(json);

  Map<String, dynamic> toJson() => _$CustomerSupportToJson(this);
}

/// Internal Metadata
@JsonSerializable()
class InternalMetadata {
  final String uploadId;
  final String analysisId;
  final String? extractedUIN;

  InternalMetadata({
    required this.uploadId,
    required this.analysisId,
    this.extractedUIN,
  });

  factory InternalMetadata.fromJson(Map<String, dynamic> json) =>
      _$InternalMetadataFromJson(json);

  Map<String, dynamic> toJson() => _$InternalMetadataToJson(this);
}