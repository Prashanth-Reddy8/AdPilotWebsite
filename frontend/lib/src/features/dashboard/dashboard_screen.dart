import 'package:adpilot/src/core/models.dart';
import 'package:adpilot/src/core/providers.dart';
import 'package:adpilot/src/features/creatives/creative_table.dart';
import 'package:adpilot/src/shared/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});
  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  late Future<DashboardData> _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() => _future = ref.read(marketingRepositoryProvider).dashboard();
  void _refresh() => setState(_load);

  @override
  Widget build(BuildContext context) => FutureBuilder<DashboardData>(
    future: _future,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return ErrorPanel(error: snapshot.error!, onRetry: _refresh);
      }
      final data = snapshot.data!;
      return RefreshIndicator(
        onRefresh: () async => _refresh(),
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            PageHeading(
              title: 'Creative performance',
              subtitle: 'Today’s Meta Ads health and recommendations.',
              action: IconButton.filledTonal(
                onPressed: _refresh,
                tooltip: 'Refresh',
                icon: const Icon(Icons.refresh),
              ),
            ),
            const SizedBox(height: 24),
            _SummaryGrid(summary: data.summary),
            const SizedBox(height: 28),
            Text(
              'Creatives requiring attention',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(8),
                child: CreativeTable(items: data.creatives),
              ),
            ),
            const SizedBox(height: 28),
            Text(
              'Recent alerts',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            if (data.alerts.isEmpty)
              const Card(
                child: EmptyPanel(
                  icon: Icons.notifications_none,
                  title: 'No alerts',
                  message: 'Status changes will appear here.',
                ),
              )
            else
              Card(
                child: Column(
                  children: [
                    for (final alert in data.alerts)
                      ListTile(
                        leading: const CircleAvatar(
                          child: Icon(Icons.warning_amber_rounded),
                        ),
                        title: Text(
                          alert.creativeName,
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        subtitle: Text(
                          alert.reasons.join(' • '),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        trailing: Text(
                          DateFormat.MMMd().add_jm().format(
                            alert.createdAt.toLocal(),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      );
    },
  );
}

class _SummaryGrid extends StatelessWidget {
  const _SummaryGrid({required this.summary});
  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final width = constraints.maxWidth >= 1050
          ? (constraints.maxWidth - 60) / 4
          : constraints.maxWidth >= 600
          ? (constraints.maxWidth - 20) / 2
          : constraints.maxWidth;
      final cards = [
        _SummaryCard(
          label: "Today's spend",
          value: currencyFormat.format(summary.todaySpend),
          icon: Icons.payments_outlined,
        ),
        _SummaryCard(
          label: "Today's revenue",
          value: currencyFormat.format(summary.todayRevenue),
          icon: Icons.trending_up,
        ),
        _SummaryCard(
          label: 'ROAS',
          value: summary.roas.toStringAsFixed(2),
          icon: Icons.insights_outlined,
        ),
        _SummaryCard(
          label: 'Healthy creatives',
          value: '${summary.healthy}',
          icon: Icons.check_circle_outline,
          color: const Color(0xFF1B9B69),
        ),
        _SummaryCard(
          label: 'Watch',
          value: '${summary.watch}',
          icon: Icons.visibility_outlined,
          color: const Color(0xFFE19119),
        ),
        _SummaryCard(
          label: 'Turn off recommendations',
          value: '${summary.turnOff}',
          icon: Icons.warning_amber,
          color: const Color(0xFFD94B52),
        ),
      ];
      return Wrap(
        spacing: 20,
        runSpacing: 20,
        children: [
          for (final card in cards) SizedBox(width: width, child: card),
        ],
      );
    },
  );
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({
    required this.label,
    required this.value,
    required this.icon,
    this.color,
  });
  final String label;
  final String value;
  final IconData icon;
  final Color? color;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: (color ?? Theme.of(context).colorScheme.primary)
                  .withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              icon,
              color: color ?? Theme.of(context).colorScheme.primary,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(color: Colors.black54)),
                const SizedBox(height: 5),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 23,
                    fontWeight: FontWeight.w900,
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
