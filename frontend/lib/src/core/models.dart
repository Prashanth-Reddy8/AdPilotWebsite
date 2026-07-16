double jsonDouble(dynamic value) =>
    value == null ? 0 : double.parse(value.toString());
int jsonInt(dynamic value) => value == null ? 0 : int.parse(value.toString());

enum CreativeRecommendation {
  healthy,
  watch,
  turnOffRecommendation;

  static CreativeRecommendation parse(String value) => switch (value) {
    'watch' => watch,
    'turn_off_recommendation' => turnOffRecommendation,
    _ => healthy,
  };

  String get label => switch (this) {
    healthy => 'Healthy',
    watch => 'Watch',
    turnOffRecommendation => 'Turn Off Recommendation',
  };
}

class DashboardSummary {
  const DashboardSummary({
    required this.todaySpend,
    required this.todayRevenue,
    required this.roas,
    required this.healthy,
    required this.watch,
    required this.turnOff,
  });
  factory DashboardSummary.fromJson(Map<String, dynamic> json) =>
      DashboardSummary(
        todaySpend: jsonDouble(json['today_spend']),
        todayRevenue: jsonDouble(json['today_revenue']),
        roas: jsonDouble(json['roas']),
        healthy: jsonInt(json['healthy_creatives']),
        watch: jsonInt(json['watch_creatives']),
        turnOff: jsonInt(json['turn_off_recommendations']),
      );
  final double todaySpend;
  final double todayRevenue;
  final double roas;
  final int healthy;
  final int watch;
  final int turnOff;
}

class CreativeMetric {
  const CreativeMetric({
    required this.id,
    required this.name,
    required this.campaign,
    required this.product,
    required this.ctr,
    required this.cpa,
    required this.frequency,
    required this.roas,
    required this.spend,
    required this.revenue,
    required this.recommendation,
    required this.reasons,
    required this.updatedAt,
  });
  factory CreativeMetric.fromJson(Map<String, dynamic> json) => CreativeMetric(
    id: json['id'] as String,
    name: json['name'] as String,
    campaign: json['campaign'] as String,
    product: json['product'] as String?,
    ctr: jsonDouble(json['ctr']),
    cpa: json['cpa'] == null ? null : jsonDouble(json['cpa']),
    frequency: jsonDouble(json['frequency']),
    roas: jsonDouble(json['roas']),
    spend: jsonDouble(json['spend']),
    revenue: jsonDouble(json['revenue']),
    recommendation: CreativeRecommendation.parse(
      json['recommendation'] as String,
    ),
    reasons: List<String>.from(json['reasons'] as List? ?? const []),
    updatedAt: json['updated_at'] == null
        ? null
        : DateTime.parse(json['updated_at'] as String),
  );
  final String id;
  final String name;
  final String campaign;
  final String? product;
  final double ctr;
  final double? cpa;
  final double frequency;
  final double roas;
  final double spend;
  final double revenue;
  final CreativeRecommendation recommendation;
  final List<String> reasons;
  final DateTime? updatedAt;
}

class AlertItem {
  const AlertItem({
    required this.id,
    required this.creativeName,
    required this.previousStatus,
    required this.newStatus,
    required this.reasons,
    required this.snapshot,
    required this.createdAt,
  });
  factory AlertItem.fromJson(Map<String, dynamic> json) => AlertItem(
    id: json['id'] as String,
    creativeName: json['creative_name'] as String,
    previousStatus: CreativeRecommendation.parse(
      json['previous_status'] as String,
    ),
    newStatus: CreativeRecommendation.parse(json['new_status'] as String),
    reasons: List<String>.from(json['reasons'] as List? ?? const []),
    snapshot: Map<String, dynamic>.from(json['metric_snapshot'] as Map),
    createdAt: DateTime.parse(json['created_at'] as String),
  );
  final String id;
  final String creativeName;
  final CreativeRecommendation previousStatus;
  final CreativeRecommendation newStatus;
  final List<String> reasons;
  final Map<String, dynamic> snapshot;
  final DateTime createdAt;
}

class DashboardData {
  const DashboardData({
    required this.summary,
    required this.creatives,
    required this.alerts,
  });
  factory DashboardData.fromJson(Map<String, dynamic> json) => DashboardData(
    summary: DashboardSummary.fromJson(
      Map<String, dynamic>.from(json['summary'] as Map),
    ),
    creatives: (json['creatives'] as List)
        .map(
          (item) =>
              CreativeMetric.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList(),
    alerts: (json['recent_alerts'] as List)
        .map(
          (item) => AlertItem.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList(),
  );
  final DashboardSummary summary;
  final List<CreativeMetric> creatives;
  final List<AlertItem> alerts;
}

class ProductGroup {
  const ProductGroup({required this.id, required this.name});
  factory ProductGroup.fromJson(Map<String, dynamic> json) =>
      ProductGroup(id: json['id'] as String, name: json['name'] as String);
  final String id;
  final String name;
}

class CampaignItem {
  const CampaignItem({
    required this.id,
    required this.name,
    required this.status,
    required this.productId,
    required this.productName,
  });
  factory CampaignItem.fromJson(Map<String, dynamic> json) => CampaignItem(
    id: json['id'] as String,
    name: json['name'] as String,
    status: json['status'] as String?,
    productId: json['product_id'] as String?,
    productName: json['product_name'] as String?,
  );
  final String id;
  final String name;
  final String? status;
  final String? productId;
  final String? productName;
}

class UserSettings {
  const UserSettings({
    required this.ctrDrop,
    required this.cpaIncrease,
    required this.minimumRoas,
    required this.maximumFrequency,
    required this.spendThreshold,
    required this.slackEnabled,
    required this.slackConfigured,
    required this.emailEnabled,
  });
  factory UserSettings.fromJson(Map<String, dynamic> json) => UserSettings(
    ctrDrop: jsonDouble(json['ctr_drop_threshold_pct']),
    cpaIncrease: jsonDouble(json['cpa_increase_threshold_pct']),
    minimumRoas: jsonDouble(json['minimum_roas']),
    maximumFrequency: jsonDouble(json['maximum_frequency']),
    spendThreshold: jsonDouble(json['spend_threshold']),
    slackEnabled: json['slack_enabled'] as bool,
    slackConfigured: json['slack_configured'] as bool,
    emailEnabled: json['email_enabled'] as bool,
  );
  final double ctrDrop;
  final double cpaIncrease;
  final double minimumRoas;
  final double maximumFrequency;
  final double spendThreshold;
  final bool slackEnabled;
  final bool slackConfigured;
  final bool emailEnabled;
}

class MetaAccount {
  const MetaAccount({
    required this.id,
    required this.externalId,
    required this.name,
    required this.currency,
    required this.lastSyncAt,
  });
  factory MetaAccount.fromJson(Map<String, dynamic> json) => MetaAccount(
    id: json['id'] as String,
    externalId: json['external_account_id'] as String,
    name: json['name'] as String,
    currency: json['currency'] as String,
    lastSyncAt: json['last_sync_at'] == null
        ? null
        : DateTime.parse(json['last_sync_at'] as String),
  );
  final String id;
  final String externalId;
  final String name;
  final String currency;
  final DateTime? lastSyncAt;
}

class MetaAccountOption {
  const MetaAccountOption({
    required this.id,
    required this.name,
    required this.currency,
  });
  factory MetaAccountOption.fromJson(Map<String, dynamic> json) =>
      MetaAccountOption(
        id: json['id'] as String,
        name: json['name'] as String,
        currency: json['currency'] as String,
      );
  final String id;
  final String name;
  final String currency;
}

class MetaConnectionOptions {
  const MetaConnectionOptions({
    required this.sessionId,
    required this.accounts,
  });
  factory MetaConnectionOptions.fromJson(Map<String, dynamic> json) =>
      MetaConnectionOptions(
        sessionId: json['connection_session_id'] as String,
        accounts: (json['accounts'] as List)
            .map(
              (item) => MetaAccountOption.fromJson(
                Map<String, dynamic>.from(item as Map),
              ),
            )
            .toList(),
      );
  final String sessionId;
  final List<MetaAccountOption> accounts;
}
