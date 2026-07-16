import 'package:adpilot/src/core/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('dashboard response parses decimal strings from the API', () {
    final data = DashboardData.fromJson({
      'summary': {
        'today_spend': '2500.50',
        'today_revenue': '7500.00',
        'roas': '2.9994',
        'healthy_creatives': 4,
        'watch_creatives': 2,
        'turn_off_recommendations': 1,
      },
      'creatives': <Object>[],
      'recent_alerts': <Object>[],
    });

    expect(data.summary.todaySpend, 2500.5);
    expect(data.summary.roas, closeTo(2.9994, 0.00001));
    expect(data.summary.turnOff, 1);
  });

  test('recommendation values map to user-facing labels', () {
    expect(
      CreativeRecommendation.parse('turn_off_recommendation').label,
      'Turn Off Recommendation',
    );
    expect(
      CreativeRecommendation.parse('healthy'),
      CreativeRecommendation.healthy,
    );
  });
}
