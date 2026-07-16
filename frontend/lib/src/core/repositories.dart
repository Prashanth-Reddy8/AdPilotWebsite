import 'package:adpilot/src/core/api_client.dart';
import 'package:adpilot/src/core/models.dart';

class AuthRepository {
  AuthRepository(this._api, this._sessionStore);
  final ApiClient _api;
  final SessionStore _sessionStore;

  Future<void> login(String email, String password) async {
    final data = Map<String, dynamic>.from(
      await _api.post(
            '/auth/login',
            data: {'email': email.trim(), 'password': password},
          )
          as Map,
    );
    await _sessionStore.writeToken(data['access_token'] as String);
  }

  Future<bool> hasSession() async => (await _sessionStore.readToken()) != null;
  Future<void> logout() => _sessionStore.clearToken();
}

class MarketingRepository {
  MarketingRepository(this._api);
  final ApiClient _api;

  Future<DashboardData> dashboard() async => DashboardData.fromJson(
    Map<String, dynamic>.from(await _api.get('/dashboard') as Map),
  );

  Future<List<CreativeMetric>> creatives({String? search}) async {
    final data = Map<String, dynamic>.from(
      await _api.get('/creatives', query: {'search': search, 'page_size': 100})
          as Map,
    );
    return (data['items'] as List)
        .map(
          (item) =>
              CreativeMetric.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<List<AlertItem>> alerts() async {
    final data = Map<String, dynamic>.from(
      await _api.get('/alerts', query: {'page_size': 100}) as Map,
    );
    return (data['items'] as List)
        .map(
          (item) => AlertItem.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList();
  }

  Future<List<CampaignItem>> campaigns({String? search}) async =>
      (await _api.get('/campaigns', query: {'search': search, 'limit': 500})
              as List)
          .map(
            (item) =>
                CampaignItem.fromJson(Map<String, dynamic>.from(item as Map)),
          )
          .toList();

  Future<List<ProductGroup>> products() async =>
      (await _api.get('/products') as List)
          .map(
            (item) =>
                ProductGroup.fromJson(Map<String, dynamic>.from(item as Map)),
          )
          .toList();

  Future<ProductGroup> createProduct(String name) async =>
      ProductGroup.fromJson(
        Map<String, dynamic>.from(
          await _api.post('/products', data: {'name': name}) as Map,
        ),
      );

  Future<void> assignProduct(String campaignId, String? productId) async {
    await _api.put(
      '/campaigns/$campaignId/product',
      data: {'product_id': productId},
    );
  }

  Future<UserSettings> settings() async => UserSettings.fromJson(
    Map<String, dynamic>.from(await _api.get('/settings') as Map),
  );

  Future<UserSettings> updateSettings({
    required double ctrDrop,
    required double cpaIncrease,
    required double minimumRoas,
    required double maximumFrequency,
    required double spendThreshold,
    required bool slackEnabled,
    required bool emailEnabled,
    String? slackWebhookUrl,
  }) async => UserSettings.fromJson(
    Map<String, dynamic>.from(
      await _api.put(
            '/settings',
            data: {
              'ctr_drop_threshold_pct': ctrDrop,
              'cpa_increase_threshold_pct': cpaIncrease,
              'minimum_roas': minimumRoas,
              'maximum_frequency': maximumFrequency,
              'spend_threshold': spendThreshold,
              'slack_enabled': slackEnabled,
              'email_enabled': emailEnabled,
              if (slackWebhookUrl?.isNotEmpty ?? false)
                'slack_webhook_url': slackWebhookUrl,
            },
          )
          as Map,
    ),
  );

  Future<List<MetaAccount>> metaAccounts() async =>
      (await _api.get('/meta/accounts') as List)
          .map(
            (item) =>
                MetaAccount.fromJson(Map<String, dynamic>.from(item as Map)),
          )
          .toList();

  Future<MetaConnectionOptions> exchangeMetaCode(
    String code,
    String redirectUri,
  ) async => MetaConnectionOptions.fromJson(
    Map<String, dynamic>.from(
      await _api.post(
            '/meta/connect/options',
            data: {'authorization_code': code, 'redirect_uri': redirectUri},
          )
          as Map,
    ),
  );

  Future<MetaAccount> completeMetaConnection(
    String sessionId,
    String accountId,
  ) async => MetaAccount.fromJson(
    Map<String, dynamic>.from(
      await _api.post(
            '/meta/connect/complete',
            data: {'connection_session_id': sessionId, 'account_id': accountId},
          )
          as Map,
    ),
  );

  Future<String> sync(String accountId) async {
    final data = Map<String, dynamic>.from(
      await _api.post('/sync', data: {'meta_account_id': accountId}) as Map,
    );
    return '${data['rows_imported']} metric rows imported, '
        '${data['alerts_created']} alerts created.';
  }
}
