import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});
  final String message;
  final int? statusCode;
  @override
  String toString() => message;
}

class SessionStore {
  SessionStore(this._storage);
  static const _tokenKey = 'adpilot_access_token';
  static const _metaStateKey = 'adpilot_meta_oauth_state';
  final FlutterSecureStorage _storage;

  Future<String?> readToken() => _storage.read(key: _tokenKey);
  Future<void> writeToken(String token) =>
      _storage.write(key: _tokenKey, value: token);
  Future<void> clearToken() => _storage.delete(key: _tokenKey);
  Future<String?> readMetaState() => _storage.read(key: _metaStateKey);
  Future<void> writeMetaState(String value) =>
      _storage.write(key: _metaStateKey, value: value);
  Future<void> clearMetaState() => _storage.delete(key: _metaStateKey);
}

class ApiClient {
  ApiClient({required String baseUrl, required this._sessionStore})
    : _dio = Dio(
        BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 30),
          sendTimeout: const Duration(seconds: 30),
          headers: const {'Accept': 'application/json'},
        ),
      ) {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _sessionStore.readToken();
          if (token != null) options.headers['Authorization'] = 'Bearer $token';
          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401) {
            await _sessionStore.clearToken();
          }
          handler.next(error);
        },
      ),
    );
  }

  final Dio _dio;
  final SessionStore _sessionStore;

  Future<dynamic> get(String path, {Map<String, dynamic>? query}) async {
    try {
      return (await _dio.get<dynamic>(path, queryParameters: query)).data;
    } on DioException catch (error) {
      throw _toApiException(error);
    }
  }

  Future<dynamic> post(String path, {Object? data}) async {
    try {
      return (await _dio.post<dynamic>(path, data: data)).data;
    } on DioException catch (error) {
      throw _toApiException(error);
    }
  }

  Future<dynamic> put(String path, {Object? data}) async {
    try {
      return (await _dio.put<dynamic>(path, data: data)).data;
    } on DioException catch (error) {
      throw _toApiException(error);
    }
  }

  ApiException _toApiException(DioException error) {
    final data = error.response?.data;
    var message = 'Unable to reach AdPilot. Please try again.';
    if (data is Map && data['detail'] is String) {
      message = data['detail'] as String;
    }
    return ApiException(message, statusCode: error.response?.statusCode);
  }
}
