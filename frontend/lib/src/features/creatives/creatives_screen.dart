import 'dart:async';

import 'package:adpilot/src/core/models.dart';
import 'package:adpilot/src/core/providers.dart';
import 'package:adpilot/src/features/creatives/creative_table.dart';
import 'package:adpilot/src/shared/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class CreativesScreen extends ConsumerStatefulWidget {
  const CreativesScreen({super.key});
  @override
  ConsumerState<CreativesScreen> createState() => _CreativesScreenState();
}

class _CreativesScreenState extends ConsumerState<CreativesScreen> {
  final _search = TextEditingController();
  Timer? _debounce;
  late Future<List<CreativeMetric>> _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() => _future = ref
      .read(marketingRepositoryProvider)
      .creatives(
        search: _search.text.trim().isEmpty ? null : _search.text.trim(),
      );
  void _reload() => setState(_load);

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        PageHeading(
          title: 'Creatives',
          subtitle:
              'Search and review the latest recommendation for every creative.',
          action: IconButton.filledTonal(
            onPressed: _reload,
            icon: const Icon(Icons.refresh),
          ),
        ),
        const SizedBox(height: 20),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 460),
          child: TextField(
            controller: _search,
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: 'Search creative or campaign',
            ),
            onChanged: (_) {
              _debounce?.cancel();
              _debounce = Timer(const Duration(milliseconds: 350), _reload);
            },
          ),
        ),
        const SizedBox(height: 20),
        Expanded(
          child: FutureBuilder<List<CreativeMetric>>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ErrorPanel(error: snapshot.error!, onRetry: _reload);
              }
              return Card(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(8),
                  child: CreativeTable(items: snapshot.data!),
                ),
              );
            },
          ),
        ),
      ],
    ),
  );
}
