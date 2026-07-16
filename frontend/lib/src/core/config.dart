class AppConfig {
  const AppConfig._();

  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );
  static const metaAppId = String.fromEnvironment('META_APP_ID');
  static const metaApiVersion = String.fromEnvironment(
    'META_API_VERSION',
    defaultValue: 'v23.0',
  );
  static const metaRedirectUri = String.fromEnvironment(
    'META_REDIRECT_URI',
    defaultValue: 'http://localhost:8080/#/meta',
  );
}
