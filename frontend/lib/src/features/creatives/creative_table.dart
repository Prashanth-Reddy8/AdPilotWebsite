import 'package:adpilot/src/core/models.dart';
import 'package:adpilot/src/shared/widgets.dart';
import 'package:flutter/material.dart';

class CreativeTable extends StatelessWidget {
  const CreativeTable({super.key, required this.items});
  final List<CreativeMetric> items;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const EmptyPanel(
        icon: Icons.video_library_outlined,
        title: 'No creative metrics yet',
        message: 'Connect a Meta ad account and run the first synchronization.',
      );
    }
    if (MediaQuery.sizeOf(context).width < 850) {
      return Column(
        children: [for (final item in items) _CreativeCard(item: item)],
      );
    }
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columns: const [
          DataColumn(label: Text('Creative')),
          DataColumn(label: Text('Campaign')),
          DataColumn(label: Text('Product')),
          DataColumn(label: Text('CTR')),
          DataColumn(label: Text('CPA')),
          DataColumn(label: Text('Frequency')),
          DataColumn(label: Text('ROAS')),
          DataColumn(label: Text('Recommendation')),
        ],
        rows: [
          for (final item in items)
            DataRow(
              cells: [
                DataCell(
                  SizedBox(
                    width: 170,
                    child: Text(
                      item.name,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                  ),
                ),
                DataCell(
                  SizedBox(
                    width: 170,
                    child: Text(item.campaign, overflow: TextOverflow.ellipsis),
                  ),
                ),
                DataCell(Text(item.product ?? 'Unassigned')),
                DataCell(Text('${item.ctr.toStringAsFixed(2)}%')),
                DataCell(
                  Text(
                    item.cpa == null ? '—' : currencyFormat.format(item.cpa),
                  ),
                ),
                DataCell(Text(item.frequency.toStringAsFixed(2))),
                DataCell(Text(item.roas.toStringAsFixed(2))),
                DataCell(RecommendationChip(item.recommendation)),
              ],
            ),
        ],
      ),
    );
  }
}

class _CreativeCard extends StatelessWidget {
  const _CreativeCard({required this.item});
  final CreativeMetric item;
  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 12),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  item.name,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
              RecommendationChip(item.recommendation),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '${item.campaign} • ${item.product ?? 'Unassigned'}',
            style: const TextStyle(color: Colors.black54),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 22,
            runSpacing: 10,
            children: [
              _metric('CTR', '${item.ctr.toStringAsFixed(2)}%'),
              _metric(
                'CPA',
                item.cpa == null ? '—' : currencyFormat.format(item.cpa),
              ),
              _metric('Frequency', item.frequency.toStringAsFixed(2)),
              _metric('ROAS', item.roas.toStringAsFixed(2)),
            ],
          ),
        ],
      ),
    ),
  );

  Widget _metric(String label, String value) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(label, style: const TextStyle(color: Colors.black45, fontSize: 12)),
      Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
    ],
  );
}
