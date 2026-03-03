# Flutter Integration Guide - Policy Details API

This guide explains how to integrate the Policy Upload API response into your Flutter application for displaying health insurance policy details.

## Table of Contents

1. [API Response Overview](#api-response-overview)
2. [Dart Data Models](#dart-data-models)
3. [Parsing the Response](#parsing-the-response)
4. [Displaying Policy Sections](#displaying-policy-sections)
5. [Handling Different Value Types](#handling-different-value-types)
6. [Validation Results UI](#validation-results-ui)
7. [Complete Example Widget](#complete-example-widget)

---

## API Response Overview

The API returns a structured JSON response with the following main components:

```json
{
  "success": true,
  "userId": "282",
  "policyId": "ANL_282_3f747c6b0e3e",
  "policyNumber": "APHP20223052R2",
  "policyDetails": {
    "sections": [...],           // Formatted fields for UI
    "categorySpecificData": {...}, // Raw data model
    "dataValidation": {...},     // Validation warnings
    "redundantAddonAnalysis": {...} // Add-on analysis
  }
}
```

### Key Sections

| Section ID | Title | Description |
|------------|-------|-------------|
| `policyIdentification` | Policy Identification | Basic policy info (number, UIN, insurer, dates) |
| `insuredMembers` | Insured Members | List of covered members with details |
| `coverageDetails` | Coverage Details | Sum insured, cover type, limits, benefits |
| `waitingPeriods` | Waiting Periods | Initial, PED, specific disease waiting |
| `subLimits` | Sub-Limits | Disease-specific limits |
| `exclusions` | Exclusions | Policy exclusions |
| `premiumBreakdown` | Premium Breakdown | Base premium, GST, add-ons |
| `noClaimBonus` | No Claim Bonus | NCB details |
| `addOnPolicies` | Add-On Policies | Additional policies |
| `declaredPed` | Declared Pre-existing Diseases | PED status |
| `benefits` | Benefits & Features | All policy benefits |
| `accumulatedBenefits` | Accumulated Benefits | Inflation shield, etc. |
| `membersCovered` | Members Covered | Duplicate of insuredMembers |
| `policyHistory` | Policy History | Enrollment dates, portability |
| `networkInfo` | Network Hospital Information | Hospital network details |
| `claimInfo` | Claim Information | Claim process, documents |

---

## Dart Data Models

### 1. Base Response Model

```dart
class PolicyUploadResponse {
  final bool success;
  final String userId;
  final String policyId;
  final String policyNumber;
  final PolicyDetails policyDetails;

  PolicyUploadResponse({
    required this.success,
    required this.userId,
    required this.policyId,
    required this.policyNumber,
    required this.policyDetails,
  });

  factory PolicyUploadResponse.fromJson(Map<String, dynamic> json) {
    return PolicyUploadResponse(
      success: json['success'] ?? false,
      userId: json['userId']?.toString() ?? '',
      policyId: json['policyId']?.toString() ?? '',
      policyNumber: json['policyNumber']?.toString() ?? '',
      policyDetails: PolicyDetails.fromJson(json['policyDetails'] ?? {}),
    );
  }
}
```

### 2. Policy Details Model

```dart
class PolicyDetails {
  final String policyNumber;
  final String uin;
  final String insuranceProvider;
  final String policyType;
  final String policyHolderName;
  final double coverageAmount;
  final double premium;
  final String premiumFrequency;
  final String startDate;
  final String endDate;
  final String status;
  final String originalDocumentUrl;
  final List<PolicySection> sections;
  final Map<String, dynamic> categorySpecificData;
  final DataValidation? dataValidation;
  final RedundantAddonAnalysis? redundantAddonAnalysis;

  PolicyDetails({
    required this.policyNumber,
    required this.uin,
    required this.insuranceProvider,
    required this.policyType,
    required this.policyHolderName,
    required this.coverageAmount,
    required this.premium,
    required this.premiumFrequency,
    required this.startDate,
    required this.endDate,
    required this.status,
    required this.originalDocumentUrl,
    required this.sections,
    required this.categorySpecificData,
    this.dataValidation,
    this.redundantAddonAnalysis,
  });

  factory PolicyDetails.fromJson(Map<String, dynamic> json) {
    var sectionsList = json['sections'] as List? ?? [];
    var sections = sectionsList
        .map((section) => PolicySection.fromJson(section))
        .toList();

    return PolicyDetails(
      policyNumber: json['policyNumber']?.toString() ?? '',
      uin: json['uin']?.toString() ?? '',
      insuranceProvider: json['insuranceProvider']?.toString() ?? '',
      policyType: json['policyType']?.toString() ?? '',
      policyHolderName: json['policyHolderName']?.toString() ?? '',
      coverageAmount: (json['coverageAmount'] as num?)?.toDouble() ?? 0.0,
      premium: (json['premium'] as num?)?.toDouble() ?? 0.0,
      premiumFrequency: json['premiumFrequency']?.toString() ?? '',
      startDate: json['startDate']?.toString() ?? '',
      endDate: json['endDate']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      originalDocumentUrl: json['originalDocumentUrl']?.toString() ?? '',
      sections: sections,
      categorySpecificData: json['categorySpecificData'] as Map<String, dynamic>? ?? {},
      dataValidation: json['dataValidation'] != null
          ? DataValidation.fromJson(json['dataValidation'])
          : null,
      redundantAddonAnalysis: json['redundantAddonAnalysis'] != null
          ? RedundantAddonAnalysis.fromJson(json['redundantAddonAnalysis'])
          : null,
    );
  }
}
```

### 3. Section Model

```dart
class PolicySection {
  final String sectionId;
  final String sectionTitle;
  final String sectionType; // 'fields', 'list', 'value'
  final int displayOrder;
  final List<Field>? fields;
  final List<SectionItem>? items;
  final String? value; // For simple value sections

  PolicySection({
    required this.sectionId,
    required this.sectionTitle,
    required this.sectionType,
    required this.displayOrder,
    this.fields,
    this.items,
    this.value,
  });

  factory PolicySection.fromJson(Map<String, dynamic> json) {
    var fieldsList = json['fields'] as List?;
    var itemsList = json['items'] as List?;

    return PolicySection(
      sectionId: json['sectionId']?.toString() ?? '',
      sectionTitle: json['sectionTitle']?.toString() ?? '',
      sectionType: json['sectionType']?.toString() ?? 'fields',
      displayOrder: json['displayOrder'] as int? ?? 0,
      fields: fieldsList?.map((f) => Field.fromJson(f)).toList(),
      items: itemsList?.map((i) => SectionItem.fromJson(i)).toList(),
      value: json['value']?.toString(),
    );
  }
}
```

### 4. Field Model

```dart
class Field {
  final String fieldId;
  final String label;
  final dynamic value;
  final String valueType; // 'string', 'number', 'currency', 'date', 'boolean', 'array', 'email', 'phone'
  final int displayOrder;

  Field({
    required this.fieldId,
    required this.label,
    required this.value,
    required this.valueType,
    required this.displayOrder,
  });

  factory Field.fromJson(Map<String, dynamic> json) {
    return Field(
      fieldId: json['fieldId']?.toString() ?? '',
      label: json['label']?.toString() ?? '',
      value: json['value'],
      valueType: json['valueType']?.toString() ?? 'string',
      displayOrder: json['displayOrder'] as int? ?? 0,
    );
  }
}
```

### 5. Section Item Model (for list sections)

```dart
class SectionItem {
  final String itemId;
  final List<Field>? fields;
  final String? value;

  SectionItem({
    required this.itemId,
    this.fields,
    this.value,
  });

  factory SectionItem.fromJson(Map<String, dynamic> json) {
    var fieldsList = json['fields'] as List?;

    return SectionItem(
      itemId: json['itemId']?.toString() ?? '',
      fields: fieldsList?.map((f) => Field.fromJson(f)).toList(),
      value: json['value']?.toString(),
    );
  }
}
```

### 6. Validation Models

```dart
class DataValidation {
  final bool hasIssues;
  final bool hasWarnings;
  final bool hasErrors;
  final int totalIssues;
  final int warningCount;
  final int errorCount;
  final List<ValidationWarning> warnings;
  final List<ValidationError> errors;
  final List<String> recommendations;

  DataValidation({
    required this.hasIssues,
    required this.hasWarnings,
    required this.hasErrors,
    required this.totalIssues,
    required this.warningCount,
    required this.errorCount,
    required this.warnings,
    required this.errors,
    required this.recommendations,
  });

  factory DataValidation.fromJson(Map<String, dynamic> json) {
    var warningsList = json['warnings'] as List? ?? [];
    var errorsList = json['errors'] as List? ?? [];
    var recommendationsList = json['recommendations'] as List? ?? [];

    return DataValidation(
      hasIssues: json['hasIssues'] ?? false,
      hasWarnings: json['hasWarnings'] ?? false,
      hasErrors: json['hasErrors'] ?? false,
      totalIssues: json['totalIssues'] ?? 0,
      warningCount: json['warningCount'] ?? 0,
      errorCount: json['errorCount'] ?? 0,
      warnings: warningsList.map((w) => ValidationWarning.fromJson(w)).toList(),
      errors: errorsList.map((e) => ValidationError.fromJson(e)).toList(),
      recommendations: recommendationsList.map((r) => r.toString()).toList(),
    );
  }
}

class ValidationWarning {
  final String field;
  final String? currentValue;
  final String? expectedValue;
  final String issue;
  final String recommendation;
  final String severity; // 'low', 'medium', 'high'
  final String? issueType; // 'dataExtractionInconsistency'

  ValidationWarning({
    required this.field,
    this.currentValue,
    this.expectedValue,
    required this.issue,
    required this.recommendation,
    required this.severity,
    this.issueType,
  });

  factory ValidationWarning.fromJson(Map<String, dynamic> json) {
    return ValidationWarning(
      field: json['field']?.toString() ?? '',
      currentValue: json['currentValue']?.toString(),
      expectedValue: json['expectedValue']?.toString(),
      issue: json['issue']?.toString() ?? '',
      recommendation: json['recommendation']?.toString() ?? '',
      severity: json['severity']?.toString() ?? 'low',
      issueType: json['issueType']?.toString(),
    );
  }
}

class ValidationError {
  final String field;
  final dynamic value;
  final String issue;
  final String recommendation;
  final String severity;

  ValidationError({
    required this.field,
    required this.value,
    required this.issue,
    required this.recommendation,
    required this.severity,
  });

  factory ValidationError.fromJson(Map<String, dynamic> json) {
    return ValidationError(
      field: json['field']?.toString() ?? '',
      value: json['value'],
      issue: json['issue']?.toString() ?? '',
      recommendation: json['recommendation']?.toString() ?? '',
      severity: json['severity']?.toString() ?? 'high',
    );
  }
}

class RedundantAddonAnalysis {
  final bool hasRedundantAddons;
  final List<RedundantAddon> redundantAddons;
  final double totalWastedPremium;
  final String totalWastedFormatted;

  RedundantAddonAnalysis({
    required this.hasRedundantAddons,
    required this.redundantAddons,
    required this.totalWastedPremium,
    required this.totalWastedFormatted,
  });

  factory RedundantAddonAnalysis.fromJson(Map<String, dynamic> json) {
    var addonsList = json['redundantAddons'] as List? ?? [];

    return RedundantAddonAnalysis(
      hasRedundantAddons: json['hasRedundantAddons'] ?? false,
      redundantAddons: addonsList
          .map((a) => RedundantAddon.fromJson(a))
          .toList(),
      totalWastedPremium: (json['totalWastedPremium'] as num?)?.toDouble() ?? 0.0,
      totalWastedFormatted: json['totalWastedFormatted']?.toString() ?? '',
    );
  }
}

class RedundantAddon {
  final String addOnName;
  final double premium;
  final String premiumFormatted;
  final String reason;
  final String severity;

  RedundantAddon({
    required this.addOnName,
    required this.premium,
    required this.premiumFormatted,
    required this.reason,
    required this.severity,
  });

  factory RedundantAddon.fromJson(Map<String, dynamic> json) {
    return RedundantAddon(
      addOnName: json['addOnName']?.toString() ?? '',
      premium: (json['premium'] as num?)?.toDouble() ?? 0.0,
      premiumFormatted: json['premiumFormatted']?.toString() ?? '',
      reason: json['reason']?.toString() ?? '',
      severity: json['severity']?.toString() ?? 'medium',
    );
  }
}
```

---

## Parsing the Response

### Using `dart:convert`

```dart
import 'dart:convert';

Future<PolicyUploadResponse> fetchPolicyDetails(String policyId) async {
  final response = await http.get(
    Uri.parse('https://your-api.com/api/policy/$policyId'),
    headers: {'Authorization': 'Bearer $token'},
  );

  if (response.statusCode == 200) {
    final jsonData = json.decode(response.body);
    return PolicyUploadResponse.fromJson(jsonData);
  } else {
    throw Exception('Failed to load policy details');
  }
}
```

### Using Freezed Package (Recommended)

```yaml
# pubspec.yaml
dependencies:
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1
dev_dependencies:
  freezed: ^2.4.5
  json_serializable: ^6.7.1
build_runner: ^2.4.6
```

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'policy_models.freezed.dart';
part 'policy_models.g.dart';

@freezed
class PolicyUploadResponse with _$PolicyUploadResponse {
  const factory PolicyUploadResponse({
    required bool success,
    required String userId,
    required String policyId,
    required String policyNumber,
    required PolicyDetails policyDetails,
  }) = _PolicyUploadResponse;

  factory PolicyUploadResponse.fromJson(Map<String, dynamic> json) =>
      _$PolicyUploadResponseFromJson(json);
}
```

---

## Displaying Policy Sections

### Main Sections List Widget

```dart
class PolicyDetailsScreen extends StatelessWidget {
  final PolicyUploadResponse response;

  const PolicyDetailsScreen({Key? key, required this.response}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Policy Details'),
        actions: [
          if (response.policyDetails.dataValidation?.hasIssues ?? false)
            IconButton(
              icon: Icon(Icons.warning_amber_rounded),
              onPressed: () => _showValidationIssues(context),
            ),
        ],
      ),
      body: ListView.builder(
        itemCount: response.policyDetails.sections.length,
        itemBuilder: (context, index) {
          final section = response.policyDetails.sections[index];
          return _buildSection(section);
        },
      ),
    );
  }

  Widget _buildSection(PolicySection section) {
    switch (section.sectionType) {
      case 'fields':
        return FieldsSectionWidget(section: section);
      case 'list':
        return ListSectionWidget(section: section);
      case 'value':
        return ValueSectionWidget(section: section);
      default:
        return FieldsSectionWidget(section: section);
    }
  }

  void _showValidationIssues(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => ValidationBottomSheet(
        validation: response.policyDetails.dataValidation!,
        addonAnalysis: response.policyDetails.redundantAddonAnalysis,
      ),
    );
  }
}
```

### Fields Section Widget

```dart
class FieldsSectionWidget extends StatelessWidget {
  final PolicySection section;

  const FieldsSectionWidget({Key? key, required this.section}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(12),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Section Title
            Text(
              section.sectionTitle,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 16),
            // Fields
            ...section.fields!.map((field) => FieldWidget(field: field)),
          ],
        ),
      ),
    );
  }
}
```

---

## Handling Different Value Types

### Field Widget with Type-Based Rendering

```dart
class FieldWidget extends StatelessWidget {
  final Field field;

  const FieldWidget({Key? key, required this.field}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Label
          Expanded(
            flex: 2,
            child: Text(
              field.label,
              style: TextStyle(
                color: Colors.grey[700],
                fontSize: 14,
              ),
            ),
          ),
          SizedBox(width: 16),
          // Value (rendered based on type)
          Expanded(
            flex: 3,
            child: _buildValue(context),
          ),
        ],
      ),
    );
  }

  Widget _buildValue(BuildContext context) {
    switch (field.valueType) {
      case 'currency':
        return _buildCurrencyValue();
      case 'number':
        return _buildNumberValue();
      case 'date':
        return _buildDateValue();
      case 'boolean':
        return _buildBooleanValue();
      case 'array':
        return _buildArrayValue();
      case 'email':
        return _buildEmailValue();
      case 'phone':
        return _buildPhoneValue();
      default:
        return _buildStringValue();
    }
  }

  // String value
  Widget _buildStringValue() {
    return Text(
      field.value?.toString() ?? '-',
      style: TextStyle(
        fontWeight: FontWeight.w500,
        fontSize: 14,
      ),
    );
  }

  // Currency value
  Widget _buildCurrencyValue() {
    String displayValue = field.value?.toString() ?? '-';
    if (!displayValue.startsWith('₹') && !displayValue.startsWith('Rs')) {
      displayValue = '₹$displayValue';
    }
    return Text(
      displayValue,
      style: TextStyle(
        fontWeight: FontWeight.w600,
        fontSize: 14,
        color: Colors.green[700],
      ),
    );
  }

  // Number value
  Widget _buildNumberValue() {
    final value = field.value as num?;
    return Text(
      value != null ? value.toString() : '-',
      style: TextStyle(
        fontWeight: FontWeight.w600,
        fontSize: 14,
        color: Colors.blue[700],
      ),
    );
  }

  // Date value
  Widget _buildDateValue() {
    String dateStr = field.value?.toString() ?? '-';
    try {
      final date = DateTime.parse(dateStr);
      dateStr = DateFormat('dd MMM yyyy').format(date);
    } catch (e) {
      // Keep original if parsing fails
    }
    return Text(
      dateStr,
      style: TextStyle(
        fontWeight: FontWeight.w500,
        fontSize: 14,
        color: Colors.purple[700],
      ),
    );
  }

  // Boolean value
  Widget _buildBooleanValue() {
    final boolValue = field.value is bool ? field.value as bool : false;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: boolValue ? Colors.green[100] : Colors.red[100],
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        boolValue ? 'Yes' : 'No',
        style: TextStyle(
          color: boolValue ? Colors.green[800] : Colors.red[800],
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
      ),
    );
  }

  // Array value
  Widget _buildArrayValue() {
    final list = field.value as List?;
    if (list == null || list.isEmpty) {
      return Text('-', style: TextStyle(fontSize: 14));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: list.map((item) => Padding(
        padding: EdgeInsets.only(bottom: 4),
        child: Row(
          children: [
            Icon(Icons.circle, size: 4, color: Colors.grey[600]),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                item.toString(),
                style: TextStyle(fontSize: 13),
              ),
            ),
          ],
        ),
      )).toList(),
    );
  }

  // Email value (clickable)
  Widget _buildEmailValue() {
    return InkWell(
      onTap: () {
        // Launch email
        launch('mailto:${field.value}');
      },
      child: Row(
        children: [
          Icon(Icons.email, size: 16, color: Colors.blue[600]),
          SizedBox(width: 4),
          Text(
            field.value?.toString() ?? '-',
            style: TextStyle(
              color: Colors.blue[600],
              decoration: TextDecoration.underline,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  // Phone value (clickable)
  Widget _buildPhoneValue() {
    return InkWell(
      onTap: () {
        // Launch phone
        launch('tel:${field.value}');
      },
      child: Row(
        children: [
          Icon(Icons.phone, size: 16, color: Colors.green[600]),
          SizedBox(width: 4),
          Text(
            field.value?.toString() ?? '-',
            style: TextStyle(
              color: Colors.green[600],
              decoration: TextDecoration.underline,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}
```

---

## Validation Results UI

### Validation Bottom Sheet

```dart
class ValidationBottomSheet extends StatelessWidget {
  final DataValidation validation;
  final RedundantAddonAnalysis? addonAnalysis;

  const ValidationBottomSheet({
    Key? key,
    required this.validation,
    this.addonAnalysis,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      minChildSize: 0.3,
      maxChildSize: 0.9,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Handle
              Container(
                margin: EdgeInsets.symmetric(vertical: 12),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              // Header
              Padding(
                padding: EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, color: Colors.orange[700]),
                    SizedBox(width: 12),
                    Text(
                      'Data Validation Report',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              Divider(),
              // Content
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: EdgeInsets.all(16),
                  children: [
                    if (addonAnalysis?.hasRedundantAddons ?? false)
                      _buildRedundantAddonsSection(context),
                    if (validation.hasWarnings)
                      _buildWarningsSection(context),
                    if (validation.hasErrors)
                      _buildErrorsSection(context),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildRedundantAddonsSection(BuildContext context) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      color: Colors.red[50],
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.money_off, color: Colors.red[700]),
                SizedBox(width: 8),
                Text(
                  'Redundant Add-ons Detected',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Colors.red[900],
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            Text(
              'Total Wasted: ${addonAnalysis!.totalWastedFormatted}',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 14,
                color: Colors.red[700],
              ),
            ),
            SizedBox(height: 12),
            ...addonAnalysis!.redundantAddons.map((addon) => ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(addon.addOnName),
              subtitle: Text(addon.reason),
              trailing: Text(
                addon.premiumFormatted,
                style: TextStyle(
                  color: Colors.red[700],
                  fontWeight: FontWeight.w600,
                ),
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildWarningsSection(BuildContext context) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      color: Colors.orange[50],
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.warning_amber_rounded, color: Colors.orange[700]),
                SizedBox(width: 8),
                Text(
                  'Warnings (${validation.warningCount})',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Colors.orange[900],
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            ...validation.warnings.map((warning) => _buildWarningItem(warning)),
          ],
        ),
      ),
    );
  }

  Widget _buildWarningItem(ValidationWarning warning) {
    Color severityColor;
    switch (warning.severity) {
      case 'high':
        severityColor = Colors.red[700]!;
        break;
      case 'medium':
        severityColor = Colors.orange[700]!;
        break;
      default:
        severityColor = Colors.yellow[700]!;
    }

    return Padding(
      padding: EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  warning.field,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
              ),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: severityColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  warning.severity.toUpperCase(),
                  style: TextStyle(
                    color: severityColor,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 4),
          Text(
            warning.issue,
            style: TextStyle(fontSize: 13),
          ),
          if (warning.issueType == 'dataExtractionInconsistency')
            Padding(
              padding: EdgeInsets.only(top: 4),
              child: Row(
                children: [
                  Icon(Icons.info_outline, size: 12, color: Colors.blue[600]),
                  SizedBox(width: 4),
                  Text(
                    'AI extraction issue - verify from policy document',
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.blue[600],
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildErrorsSection(BuildContext context) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      color: Colors.red[50],
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.error, color: Colors.red[700]),
                SizedBox(width: 8),
                Text(
                  'Errors (${validation.errorCount})',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Colors.red[900],
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            ...validation.errors.map((error) => ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(error.field),
              subtitle: Text(error.issue),
              leading: Icon(Icons.error_outline, color: Colors.red[700]),
            )),
          ],
        ),
      ),
    );
  }
}
```

---

## Complete Example Widget

```dart
class PolicyDetailsView extends StatefulWidget {
  final String policyId;

  const PolicyDetailsView({Key? key, required this.policyId}) : super(key: key);

  @override
  State<PolicyDetailsView> createState() => _PolicyDetailsViewState();
}

class _PolicyDetailsViewState extends State<PolicyDetailsView> {
  Future<PolicyUploadResponse>? _futurePolicy;

  @override
  void initState() {
    super.initState();
    _futurePolicy = _loadPolicy();
  }

  Future<PolicyUploadResponse> _loadPolicy() async {
    // Replace with your API call
    final response = await http.get(
      Uri.parse('https://your-api.com/api/policy/${widget.policyId}'),
    );
    final jsonData = json.decode(response.body);
    return PolicyUploadResponse.fromJson(jsonData);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Policy Details'),
        actions: [
          IconButton(
            icon: Icon(Icons.share),
            onPressed: () {
              // Share policy details
            },
          ),
          IconButton(
            icon: Icon(Icons.download),
            onPressed: () {
              // Download policy PDF
            },
          ),
        ],
      ),
      body: FutureBuilder<PolicyUploadResponse>(
        future: _futurePolicy,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 48, color: Colors.red),
                  SizedBox(height: 16),
                  Text('Error loading policy'),
                  Text(snapshot.error.toString()),
                ],
              ),
            );
          } else if (!snapshot.hasData) {
            return Center(child: Text('No policy data found'));
          }

          final policy = snapshot.data!;

          return CustomScrollView(
            slivers: [
              // Policy Header
              SliverToBoxAdapter(
                child: PolicyHeaderWidget(policy: policy.policyDetails),
              ),

              // Validation Warning Banner
              if (policy.policyDetails.dataValidation?.hasIssues ?? false)
                SliverToBoxAdapter(
                  child: ValidationBanner(
                    validation: policy.policyDetails.dataValidation!,
                    onTap: () => _showValidationSheet(context, policy),
                  ),
                ),

              // Sections List
              SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    final section = policy.policyDetails.sections[index];
                    return _buildSection(section);
                  },
                  childCount: policy.policyDetails.sections.length,
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildSection(PolicySection section) {
    switch (section.sectionType) {
      case 'fields':
        return FieldsSectionWidget(section: section);
      case 'list':
        return ListSectionWidget(section: section);
      case 'value':
        return ValueSectionWidget(section: section);
      default:
        return FieldsSectionWidget(section: section);
    }
  }

  void _showValidationSheet(BuildContext context, PolicyUploadResponse policy) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => ValidationBottomSheet(
        validation: policy.policyDetails.dataValidation!,
        addonAnalysis: policy.policyDetails.redundantAddonAnalysis,
      ),
    );
  }
}

// Policy Header Widget
class PolicyHeaderWidget extends StatelessWidget {
  final PolicyDetails policy;

  const PolicyHeaderWidget({Key? key, required this.policy}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Colors.blue[600]!, Colors.blue[800]!],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                backgroundColor: Colors.white24,
                child: Icon(Icons.health_and_safety, color: Colors.white),
              ),
              SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      policy.insuranceProvider,
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                      ),
                    ),
                    Text(
                      policy.policyNumber,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.green,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  policy.status.toUpperCase(),
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  'Sum Insured',
                  '₹${(policy.coverageAmount / 100000).toStringAsFixed(0)}L',
                  Icons.shield,
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildStatCard(
                  'Premium',
                  '₹${policy.premium.toStringAsFixed(0)}',
                  Icons.payments,
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildStatCard(
                  'Type',
                  policy.policyType,
                  Icons.family_restroom,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white10,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Icon(icon, color: Colors.white70, size: 20),
          SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              color: Colors.white60,
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }
}

// Validation Banner Widget
class ValidationBanner extends StatelessWidget {
  final DataValidation validation;
  final VoidCallback onTap;

  const ValidationBanner({
    Key? key,
    required this.validation,
    required this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: EdgeInsets.all(16),
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.orange[50],
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.orange[300]!),
        ),
        child: Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.orange[700]),
            SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Data Issues Detected',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.orange[900],
                    ),
                  ),
                  Text(
                    '${validation.warningCount} warnings, ${validation.errorCount} errors',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.orange[700],
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: Colors.orange[700]),
          ],
        ),
      ),
    );
  }
}

// List Section Widget (for members, etc.)
class ListSectionWidget extends StatelessWidget {
  final PolicySection section;

  const ListSectionWidget({Key? key, required this.section}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(12),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              section.sectionTitle,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 16),
            ...section.items!.map((item) => _buildItem(context, item)),
          ],
        ),
      ),
    );
  }

  Widget _buildItem(BuildContext context, SectionItem item) {
    if (item.fields != null) {
      return Card(
        margin: EdgeInsets.only(bottom: 12),
        child: Padding(
          padding: EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: item.fields!.map((field) => FieldWidget(field: field)).toList(),
          ),
        ),
      );
    } else {
      return ListTile(
        title: Text(item.value ?? '-'),
      );
    }
  }
}

// Value Section Widget (for simple values)
class ValueSectionWidget extends StatelessWidget {
  final PolicySection section;

  const ValueSectionWidget({Key? key, required this.section}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(12),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              section.sectionTitle,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 8),
            Text(
              section.value ?? '-',
              style: TextStyle(fontSize: 16),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## Additional Utilities

### Formatting Utils

```dart
class PolicyFormatter {
  static String formatCurrency(dynamic value) {
    if (value == null) return '-';
    if (value is num) {
      return '₹${value.toStringAsFixed(2)}';
    }
    String str = value.toString();
    if (!str.startsWith('₹')) {
      str = '₹$str';
    }
    return str;
  }

  static String formatDate(dynamic value) {
    if (value == null) return '-';
    try {
      final date = DateTime.parse(value.toString());
      return DateFormat('dd MMM yyyy').format(date);
    } catch (e) {
      return value.toString();
    }
  }

  static String formatPercentage(dynamic value) {
    if (value == null) return '-';
    String str = value.toString();
    if (!str.endsWith('%')) {
      str = '$str%';
    }
    return str;
  }
}
```

### Color Utils for Severity

```dart
class SeverityColors {
  static Color getColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'high':
        return Colors.red[700]!;
      case 'medium':
        return Colors.orange[700]!;
      case 'low':
        return Colors.yellow[700]!;
      default:
        return Colors.grey[700]!;
    }
  }

  static Color getBackgroundColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'high':
        return Colors.red[50]!;
      case 'medium':
        return Colors.orange[50]!;
      case 'low':
        return Colors.yellow[50]!;
      default:
        return Colors.grey[100]!;
    }
  }
}
```

---

## Testing

### Mock Data for Testing

```dart
class MockPolicyData {
  static Map<String, dynamic> getMockResponse() {
    return {
      "success": true,
      "userId": "282",
      "policyId": "ANL_282_3f747c6b0e3e",
      "policyNumber": "APHP20223052R2",
      "policyDetails": {
        // ... paste actual API response here for testing
      },
    };
  }

  static PolicyUploadResponse getMockPolicy() {
    return PolicyUploadResponse.fromJson(getMockResponse());
  }
}
```

---

## Best Practices

1. **Error Handling**: Always handle null values and missing data gracefully
2. **Loading States**: Show proper loading indicators while fetching data
3. **Caching**: Implement caching for frequently accessed policies
4. **Pagination**: For large policy lists, implement pagination
5. **Search**: Add search functionality to filter policies
6. **Refresh**: Implement pull-to-refresh for updating policy data
7. **Offline Support**: Cache policies for offline viewing
8. **Analytics**: Track which sections are viewed most frequently

---

## Dependencies Required

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  intl: ^0.18.1
  url_launcher: ^6.1.14

  # Optional but recommended
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1

dev_dependencies:
  freezed: ^2.4.5
  json_serializable: ^6.7.1
  build_runner: ^2.4.6
```

---

## Troubleshooting

### Common Issues

1. **Date Parsing Errors**: Handle various date formats from the API
2. **Null Safety**: Always use null-aware operators (?., ??, ??=)
3. **Type Casting**: Properly cast dynamic values to expected types
4. **Missing Fields**: Provide default values for optional fields
5. **Large Responses**: Consider pagination or lazy loading for large datasets

---

## API Endpoint Reference

```
GET /api/policy/upload
POST /api/policy/upload

Headers:
  Content-Type: multipart/form-data
  Authorization: Bearer <token>

Request (POST):
  - file: Policy PDF
  - userId: User ID
  - policyType: Optional policy type hint

Response:
  - success: boolean
  - policyDetails: PolicyDetails object
  - sections: Formatted sections for UI
  - dataValidation: Validation results
  - redundantAddonAnalysis: Add-on analysis
```

---

## Support

For issues or questions:
- Check the API response structure
- Verify data models match API response
- Enable debug logging for API calls
- Test with mock data first

---

*Last Updated: February 2026*
*Version: 1.0.0*
