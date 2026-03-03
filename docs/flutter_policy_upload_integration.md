# Flutter Integration Guide: Policy Upload API

## Overview

This guide explains how to integrate the `/api/policy/upload` endpoint in your Flutter application for uploading insurance policy documents (PDF or images).

---

## API Endpoint

```
POST /api/policy/upload
Content-Type: multipart/form-data
```

---

## Upload Options

| Method | Field | Description |
|--------|-------|-------------|
| PDF Upload | `policyDocument` | Single PDF file (max 10MB) |
| Image Upload | `policyImages` | Multiple image files (max 10 images, 20MB total) |

**Supported Image Formats:** JPG, JPEG, PNG, WEBP, GIF, BMP

---

## Required Dependencies

Add these to your `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.1.0
  http_parser: ^4.0.2
  image_picker: ^1.0.4
  file_picker: ^6.1.1
  mime: ^1.0.4
```

---

## Data Models

### Request Model

```dart
class PolicyUploadRequest {
  final String policyFor;      // "self" or "family"
  final String name;           // Full name (2-100 chars)
  final String gender;         // "male", "female", "other"
  final String dateOfBirth;    // "YYYY-MM-DD" format
  final String relationship;   // "self", "spouse", "son", "daughter", etc.
  final String uploadedAt;     // ISO 8601 timestamp
  final String userId;
  final String? sessionId;

  PolicyUploadRequest({
    required this.policyFor,
    required this.name,
    required this.gender,
    required this.dateOfBirth,
    required this.relationship,
    required this.uploadedAt,
    required this.userId,
    this.sessionId,
  });

  Map<String, String> toFormFields() {
    return {
      'policyFor': policyFor,
      'name': name,
      'gender': gender,
      'dateOfBirth': dateOfBirth,
      'relationship': relationship,
      'uploadedAt': uploadedAt,
      'userId': userId,
      if (sessionId != null) 'session_id': sessionId!,
    };
  }
}
```

### Response Model

```dart
class PolicyUploadResponse {
  final bool success;
  final String? analysisId;
  final String? policyId;
  final PolicyAnalysis? analysis;
  final String? errorCode;
  final String? message;

  PolicyUploadResponse({
    required this.success,
    this.analysisId,
    this.policyId,
    this.analysis,
    this.errorCode,
    this.message,
  });

  factory PolicyUploadResponse.fromJson(Map<String, dynamic> json) {
    return PolicyUploadResponse(
      success: json['success'] ?? false,
      analysisId: json['analysisId'],
      policyId: json['policyId'],
      analysis: json['analysis'] != null
          ? PolicyAnalysis.fromJson(json['analysis'])
          : null,
      errorCode: json['error_code'],
      message: json['message'],
    );
  }
}

class PolicyAnalysis {
  final String? policyType;
  final String? insuranceProvider;
  final String? policyNumber;
  final int? sumInsured;
  final int? protectionScore;
  final String? protectionScoreLabel;
  final List<String>? coverageGaps;
  final List<String>? recommendations;

  PolicyAnalysis({
    this.policyType,
    this.insuranceProvider,
    this.policyNumber,
    this.sumInsured,
    this.protectionScore,
    this.protectionScoreLabel,
    this.coverageGaps,
    this.recommendations,
  });

  factory PolicyAnalysis.fromJson(Map<String, dynamic> json) {
    return PolicyAnalysis(
      policyType: json['policyType'],
      insuranceProvider: json['insuranceProvider'],
      policyNumber: json['policyNumber'],
      sumInsured: json['sumInsured'],
      protectionScore: json['protectionScore'],
      protectionScoreLabel: json['protectionScoreLabel'],
      coverageGaps: json['coverageGaps'] != null
          ? List<String>.from(json['coverageGaps'])
          : null,
      recommendations: json['recommendations'] != null
          ? List<String>.from(json['recommendations'])
          : null,
    );
  }
}
```

---

## Policy Upload Service

```dart
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:mime/mime.dart';
import 'dart:convert';

class PolicyUploadService {
  final String baseUrl;
  final String? authToken;

  PolicyUploadService({
    required this.baseUrl,
    this.authToken,
  });

  /// Upload PDF document
  Future<PolicyUploadResponse> uploadPdfPolicy({
    required File pdfFile,
    required PolicyUploadRequest request,
  }) async {
    final uri = Uri.parse('$baseUrl/api/policy/upload');

    final multipartRequest = http.MultipartRequest('POST', uri);

    // Add headers
    if (authToken != null) {
      multipartRequest.headers['Authorization'] = 'Bearer $authToken';
    }

    // Add form fields
    multipartRequest.fields.addAll(request.toFormFields());

    // Add PDF file
    multipartRequest.files.add(
      await http.MultipartFile.fromPath(
        'policyDocument',
        pdfFile.path,
        contentType: MediaType('application', 'pdf'),
      ),
    );

    return _sendRequest(multipartRequest);
  }

  /// Upload multiple images
  Future<PolicyUploadResponse> uploadImagePolicy({
    required List<File> imageFiles,
    required PolicyUploadRequest request,
  }) async {
    final uri = Uri.parse('$baseUrl/api/policy/upload');

    final multipartRequest = http.MultipartRequest('POST', uri);

    // Add headers
    if (authToken != null) {
      multipartRequest.headers['Authorization'] = 'Bearer $authToken';
    }

    // Add form fields
    multipartRequest.fields.addAll(request.toFormFields());

    // Add image files
    for (final imageFile in imageFiles) {
      final mimeType = lookupMimeType(imageFile.path) ?? 'image/jpeg';
      final mimeTypeParts = mimeType.split('/');

      multipartRequest.files.add(
        await http.MultipartFile.fromPath(
          'policyImages',  // Same field name for all images
          imageFile.path,
          contentType: MediaType(mimeTypeParts[0], mimeTypeParts[1]),
        ),
      );
    }

    return _sendRequest(multipartRequest);
  }

  /// Upload from bytes (useful for web or memory images)
  Future<PolicyUploadResponse> uploadImagePolicyFromBytes({
    required List<ImageData> images,
    required PolicyUploadRequest request,
  }) async {
    final uri = Uri.parse('$baseUrl/api/policy/upload');

    final multipartRequest = http.MultipartRequest('POST', uri);

    // Add headers
    if (authToken != null) {
      multipartRequest.headers['Authorization'] = 'Bearer $authToken';
    }

    // Add form fields
    multipartRequest.fields.addAll(request.toFormFields());

    // Add image files from bytes
    for (final image in images) {
      multipartRequest.files.add(
        http.MultipartFile.fromBytes(
          'policyImages',
          image.bytes,
          filename: image.filename,
          contentType: MediaType('image', image.extension),
        ),
      );
    }

    return _sendRequest(multipartRequest);
  }

  Future<PolicyUploadResponse> _sendRequest(
    http.MultipartRequest request,
  ) async {
    try {
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final jsonData = json.decode(response.body);
        return PolicyUploadResponse.fromJson(jsonData);
      } else {
        final errorData = json.decode(response.body);
        return PolicyUploadResponse(
          success: false,
          errorCode: errorData['error_code'] ?? 'UNKNOWN_ERROR',
          message: errorData['message'] ?? 'Upload failed',
        );
      }
    } catch (e) {
      return PolicyUploadResponse(
        success: false,
        errorCode: 'NETWORK_ERROR',
        message: e.toString(),
      );
    }
  }
}

class ImageData {
  final List<int> bytes;
  final String filename;
  final String extension;

  ImageData({
    required this.bytes,
    required this.filename,
    required this.extension,
  });
}
```

---

## Usage Examples

### Example 1: Upload PDF

```dart
import 'package:file_picker/file_picker.dart';

class PolicyUploadScreen extends StatefulWidget {
  @override
  _PolicyUploadScreenState createState() => _PolicyUploadScreenState();
}

class _PolicyUploadScreenState extends State<PolicyUploadScreen> {
  final PolicyUploadService _uploadService = PolicyUploadService(
    baseUrl: 'https://your-api-domain.com',
    authToken: 'your-auth-token',
  );

  bool _isLoading = false;

  Future<void> _uploadPdf() async {
    // Pick PDF file
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );

    if (result == null || result.files.isEmpty) return;

    final file = File(result.files.single.path!);

    setState(() => _isLoading = true);

    try {
      final request = PolicyUploadRequest(
        policyFor: 'self',
        name: 'John Doe',
        gender: 'male',
        dateOfBirth: '1990-05-15',
        relationship: 'self',
        uploadedAt: DateTime.now().toIso8601String(),
        userId: '12345',
      );

      final response = await _uploadService.uploadPdfPolicy(
        pdfFile: file,
        request: request,
      );

      if (response.success) {
        _showSuccess(response);
      } else {
        _showError(response.message ?? 'Upload failed');
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showSuccess(PolicyUploadResponse response) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Upload Successful'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Policy Type: ${response.analysis?.policyType}'),
            Text('Protection Score: ${response.analysis?.protectionScore}'),
            Text('Sum Insured: ${response.analysis?.sumInsured}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Upload Policy')),
      body: Center(
        child: _isLoading
            ? CircularProgressIndicator()
            : ElevatedButton.icon(
                onPressed: _uploadPdf,
                icon: Icon(Icons.upload_file),
                label: Text('Upload PDF'),
              ),
      ),
    );
  }
}
```

### Example 2: Upload Multiple Images

```dart
import 'package:image_picker/image_picker.dart';

Future<void> _uploadImages() async {
  final ImagePicker picker = ImagePicker();

  // Pick multiple images
  final List<XFile> images = await picker.pickMultiImage(
    maxWidth: 1920,
    maxHeight: 1920,
    imageQuality: 85,
  );

  if (images.isEmpty) return;

  // Validate image count
  if (images.length > 10) {
    _showError('Maximum 10 images allowed');
    return;
  }

  setState(() => _isLoading = true);

  try {
    final imageFiles = images.map((xFile) => File(xFile.path)).toList();

    final request = PolicyUploadRequest(
      policyFor: 'self',
      name: 'John Doe',
      gender: 'male',
      dateOfBirth: '1990-05-15',
      relationship: 'self',
      uploadedAt: DateTime.now().toIso8601String(),
      userId: '12345',
    );

    final response = await _uploadService.uploadImagePolicy(
      imageFiles: imageFiles,
      request: request,
    );

    if (response.success) {
      _showSuccess(response);
    } else {
      _showError(response.message ?? 'Upload failed');
    }
  } finally {
    setState(() => _isLoading = false);
  }
}
```

### Example 3: Camera Capture

```dart
Future<void> _captureAndUpload() async {
  final ImagePicker picker = ImagePicker();
  final List<File> capturedImages = [];

  // Capture multiple images
  bool continueCapturing = true;

  while (continueCapturing && capturedImages.length < 10) {
    final XFile? image = await picker.pickImage(
      source: ImageSource.camera,
      maxWidth: 1920,
      maxHeight: 1920,
      imageQuality: 85,
    );

    if (image != null) {
      capturedImages.add(File(image.path));

      // Ask if user wants to capture more
      continueCapturing = await _showCaptureMoreDialog(capturedImages.length);
    } else {
      continueCapturing = false;
    }
  }

  if (capturedImages.isEmpty) return;

  // Upload captured images
  final request = PolicyUploadRequest(
    policyFor: 'self',
    name: 'John Doe',
    gender: 'male',
    dateOfBirth: '1990-05-15',
    relationship: 'self',
    uploadedAt: DateTime.now().toIso8601String(),
    userId: '12345',
  );

  final response = await _uploadService.uploadImagePolicy(
    imageFiles: capturedImages,
    request: request,
  );

  // Handle response...
}

Future<bool> _showCaptureMoreDialog(int currentCount) async {
  return await showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('Image Captured'),
      content: Text('$currentCount image(s) captured. Capture more?'),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: Text('Done'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, true),
          child: Text('Capture More'),
        ),
      ],
    ),
  ) ?? false;
}
```

---

## Complete Widget Example

```dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';

class PolicyUploadWidget extends StatefulWidget {
  final String userId;
  final String userName;
  final String userGender;
  final String userDob;
  final Function(PolicyUploadResponse) onSuccess;
  final Function(String) onError;

  const PolicyUploadWidget({
    Key? key,
    required this.userId,
    required this.userName,
    required this.userGender,
    required this.userDob,
    required this.onSuccess,
    required this.onError,
  }) : super(key: key);

  @override
  _PolicyUploadWidgetState createState() => _PolicyUploadWidgetState();
}

class _PolicyUploadWidgetState extends State<PolicyUploadWidget> {
  final PolicyUploadService _uploadService = PolicyUploadService(
    baseUrl: 'https://your-api-domain.com',
  );

  bool _isLoading = false;
  List<File> _selectedImages = [];
  File? _selectedPdf;
  String _policyFor = 'self';
  String _relationship = 'self';

  final List<String> _relationships = [
    'self', 'spouse', 'son', 'daughter',
    'father', 'mother', 'brother', 'sister', 'other'
  ];

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Upload Insurance Policy',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            SizedBox(height: 16),

            // Policy For Selection
            _buildPolicyForSelector(),
            SizedBox(height: 12),

            // Relationship Dropdown
            _buildRelationshipDropdown(),
            SizedBox(height: 16),

            // Upload Options
            Row(
              children: [
                Expanded(
                  child: _buildUploadButton(
                    icon: Icons.picture_as_pdf,
                    label: 'Upload PDF',
                    onTap: _pickPdf,
                  ),
                ),
                SizedBox(width: 12),
                Expanded(
                  child: _buildUploadButton(
                    icon: Icons.image,
                    label: 'Upload Images',
                    onTap: _pickImages,
                  ),
                ),
                SizedBox(width: 12),
                Expanded(
                  child: _buildUploadButton(
                    icon: Icons.camera_alt,
                    label: 'Take Photo',
                    onTap: _captureImage,
                  ),
                ),
              ],
            ),
            SizedBox(height: 16),

            // Selected Files Preview
            if (_selectedPdf != null) _buildPdfPreview(),
            if (_selectedImages.isNotEmpty) _buildImagesPreview(),

            SizedBox(height: 16),

            // Upload Button
            ElevatedButton(
              onPressed: _canUpload() ? _upload : null,
              style: ElevatedButton.styleFrom(
                padding: EdgeInsets.symmetric(vertical: 16),
                backgroundColor: Colors.teal,
              ),
              child: _isLoading
                  ? SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation(Colors.white),
                      ),
                    )
                  : Text('Analyze Policy', style: TextStyle(fontSize: 16)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPolicyForSelector() {
    return Row(
      children: [
        Text('Policy For: '),
        SizedBox(width: 16),
        ChoiceChip(
          label: Text('Self'),
          selected: _policyFor == 'self',
          onSelected: (selected) {
            if (selected) setState(() => _policyFor = 'self');
          },
        ),
        SizedBox(width: 8),
        ChoiceChip(
          label: Text('Family'),
          selected: _policyFor == 'family',
          onSelected: (selected) {
            if (selected) setState(() => _policyFor = 'family');
          },
        ),
      ],
    );
  }

  Widget _buildRelationshipDropdown() {
    return DropdownButtonFormField<String>(
      value: _relationship,
      decoration: InputDecoration(
        labelText: 'Relationship',
        border: OutlineInputBorder(),
      ),
      items: _relationships.map((rel) {
        return DropdownMenuItem(
          value: rel,
          child: Text(rel[0].toUpperCase() + rel.substring(1)),
        );
      }).toList(),
      onChanged: (value) {
        if (value != null) setState(() => _relationship = value);
      },
    );
  }

  Widget _buildUploadButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: _isLoading ? null : onTap,
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade300),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Icon(icon, size: 32, color: Colors.teal),
            SizedBox(height: 8),
            Text(label, style: TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildPdfPreview() {
    return ListTile(
      leading: Icon(Icons.picture_as_pdf, color: Colors.red),
      title: Text(_selectedPdf!.path.split('/').last),
      trailing: IconButton(
        icon: Icon(Icons.close),
        onPressed: () => setState(() => _selectedPdf = null),
      ),
    );
  }

  Widget _buildImagesPreview() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('${_selectedImages.length} image(s) selected'),
        SizedBox(height: 8),
        SizedBox(
          height: 80,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            itemCount: _selectedImages.length,
            itemBuilder: (context, index) {
              return Stack(
                children: [
                  Container(
                    width: 80,
                    height: 80,
                    margin: EdgeInsets.only(right: 8),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8),
                      image: DecorationImage(
                        image: FileImage(_selectedImages[index]),
                        fit: BoxFit.cover,
                      ),
                    ),
                  ),
                  Positioned(
                    top: 0,
                    right: 8,
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          _selectedImages.removeAt(index);
                        });
                      },
                      child: Container(
                        padding: EdgeInsets.all(2),
                        decoration: BoxDecoration(
                          color: Colors.red,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(Icons.close, size: 16, color: Colors.white),
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }

  bool _canUpload() {
    return !_isLoading && (_selectedPdf != null || _selectedImages.isNotEmpty);
  }

  Future<void> _pickPdf() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );

    if (result != null && result.files.isNotEmpty) {
      setState(() {
        _selectedPdf = File(result.files.single.path!);
        _selectedImages.clear();  // Clear images if PDF selected
      });
    }
  }

  Future<void> _pickImages() async {
    final ImagePicker picker = ImagePicker();
    final List<XFile> images = await picker.pickMultiImage(
      maxWidth: 1920,
      maxHeight: 1920,
      imageQuality: 85,
    );

    if (images.isNotEmpty) {
      final totalImages = _selectedImages.length + images.length;
      if (totalImages > 10) {
        widget.onError('Maximum 10 images allowed');
        return;
      }

      setState(() {
        _selectedImages.addAll(images.map((xFile) => File(xFile.path)));
        _selectedPdf = null;  // Clear PDF if images selected
      });
    }
  }

  Future<void> _captureImage() async {
    if (_selectedImages.length >= 10) {
      widget.onError('Maximum 10 images allowed');
      return;
    }

    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(
      source: ImageSource.camera,
      maxWidth: 1920,
      maxHeight: 1920,
      imageQuality: 85,
    );

    if (image != null) {
      setState(() {
        _selectedImages.add(File(image.path));
        _selectedPdf = null;
      });
    }
  }

  Future<void> _upload() async {
    setState(() => _isLoading = true);

    try {
      final request = PolicyUploadRequest(
        policyFor: _policyFor,
        name: widget.userName,
        gender: widget.userGender,
        dateOfBirth: widget.userDob,
        relationship: _relationship,
        uploadedAt: DateTime.now().toIso8601String(),
        userId: widget.userId,
      );

      PolicyUploadResponse response;

      if (_selectedPdf != null) {
        response = await _uploadService.uploadPdfPolicy(
          pdfFile: _selectedPdf!,
          request: request,
        );
      } else {
        response = await _uploadService.uploadImagePolicy(
          imageFiles: _selectedImages,
          request: request,
        );
      }

      if (response.success) {
        widget.onSuccess(response);
        _clearSelection();
      } else {
        widget.onError(response.message ?? 'Upload failed');
      }
    } catch (e) {
      widget.onError(e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _clearSelection() {
    setState(() {
      _selectedPdf = null;
      _selectedImages.clear();
    });
  }
}
```

---

## Error Codes Reference

| Error Code | Description |
|------------|-------------|
| `VAL_2001` | Validation error (invalid field value) |
| `VAL_2002` | File size limit exceeded |
| `POL_8003` | Invalid file format |
| `POL_8005` | Duplicate policy detected |
| `POL_8010` | Not a valid insurance document |
| `POL_8011` | Unsupported insurance type |
| `AUTH_1001` | Invalid or expired session |

---

## Best Practices

1. **Image Quality**: Use `imageQuality: 85` to balance quality and file size
2. **Image Resolution**: Limit to 1920x1920 for optimal processing
3. **Error Handling**: Always handle network errors gracefully
4. **Loading States**: Show progress indicators during upload
5. **Validation**: Validate file count and size before upload
6. **Permissions**: Request camera and storage permissions properly

---

## Platform-Specific Setup

### Android (`android/app/src/main/AndroidManifest.xml`)

```xml
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
```

### iOS (`ios/Runner/Info.plist`)

```xml
<key>NSCameraUsageDescription</key>
<string>We need camera access to capture policy documents</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>We need photo library access to select policy documents</string>
</dict>
```

---

## Support

For API-related issues, contact the backend team or check the API documentation.
