import 'package:adpilot/src/core/models.dart';
import 'package:adpilot/src/core/providers.dart';
import 'package:adpilot/src/shared/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

class AlertsScreen extends ConsumerStatefulWidget {
  const AlertsScreen({super.key});
  @override
  ConsumerState<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends ConsumerState<AlertsScreen> {
  late Future<List<AlertItem>> _future;
  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() => _future = ref.read(marketingRepositoryProvider).alerts();
  void _reload() => setState(_load);

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(24),
    child: Column(
      children: [
        PageHeading(
          title: 'Alerts',
          subtitle: 'Recommendation deterioration events, newest first.',
          action: IconButton.filledTonal(
            onPressed: _reload,
            icon: const Icon(Icons.refresh),
          ),
        ),
        const SizedBox(height: 20),
        Expanded(
          child: FutureBuilder<List<AlertItem>>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ErrorPanel(error: snapshot.error!, onRetry: _reload);
              }
              final alerts = snapshot.data!;
              if (alerts.isEmpty) {
                return const EmptyPanel(
                  icon: Icons.notifications_none,
                  title: 'No alerts',
                  message:
                      'AdPilot creates an alert only when a recommendation becomes more severe.',
                );
              }
              return ListView.separated(
                itemCount: alerts.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (context, index) {
                  final alert = alerts[index];
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const CircleAvatar(
                            backgroundColor: Color(0xFFFFECEC),
                            child: Icon(
                              Icons.warning_amber,
                              color: Color(0xFFD94B52),
                            ),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  alert.creativeName,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                    fontSize: 16,
                                  ),
                                ),
                                const SizedBox(height: 7),
                                Wrap(
                                  spacing: 8,
                                  crossAxisAlignment: WrapCrossAlignment.center,
                                  children: [
                                    RecommendationChip(alert.previousStatus),
                                    const Icon(Icons.arrow_forward, size: 16),
                                    RecommendationChip(alert.newStatus),
                                  ],
                                ),
                                const SizedBox(height: 10),
                                for (final reason in alert.reasons)
                                  Text('• $reason'),
                              ],
                            ),
                          ),
                          Text(
                            DateFormat.MMMd().add_jm().format(
                              alert.createdAt.toLocal(),
                            ),
                            style: const TextStyle(color: Colors.black54),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              );
            },
          ),
        ),
      ],
    ),
  );
}
