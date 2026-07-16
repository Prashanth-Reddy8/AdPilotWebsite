import 'package:adpilot/src/core/models.dart';
import 'package:adpilot/src/core/providers.dart';
import 'package:adpilot/src/shared/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class CampaignsScreen extends ConsumerStatefulWidget {
  const CampaignsScreen({super.key});
  @override
  ConsumerState<CampaignsScreen> createState() => _CampaignsScreenState();
}

class _CampaignsScreenState extends ConsumerState<CampaignsScreen> {
  late Future<(List<CampaignItem>, List<ProductGroup>)> _future;
  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    final repository = ref.read(marketingRepositoryProvider);
    _future = Future.wait([repository.campaigns(), repository.products()]).then(
      (values) =>
          (values[0] as List<CampaignItem>, values[1] as List<ProductGroup>),
    );
  }

  void _reload() => setState(_load);

  Future<void> _createProduct() async {
    final controller = TextEditingController();
    final name = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create product group'),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLength: 160,
          decoration: const InputDecoration(labelText: 'Product name'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('Create'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (name == null || name.isEmpty) return;
    try {
      await ref.read(marketingRepositoryProvider).createProduct(name);
      _reload();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(24),
    child: Column(
      children: [
        PageHeading(
          title: 'Campaign product groups',
          subtitle:
              'Assign campaigns to products for focused dashboard filtering.',
          action: FilledButton.icon(
            onPressed: _createProduct,
            icon: const Icon(Icons.add),
            label: const Text('New product'),
          ),
        ),
        const SizedBox(height: 20),
        Expanded(
          child: FutureBuilder<(List<CampaignItem>, List<ProductGroup>)>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return ErrorPanel(error: snapshot.error!, onRetry: _reload);
              }
              final (campaigns, products) = snapshot.data!;
              if (campaigns.isEmpty) {
                return const EmptyPanel(
                  icon: Icons.campaign_outlined,
                  title: 'No campaigns yet',
                  message:
                      'Campaigns will appear after your first Meta synchronization.',
                );
              }
              return Card(
                child: ListView.separated(
                  itemCount: campaigns.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final campaign = campaigns[index];
                    return ListTile(
                      leading: const CircleAvatar(
                        child: Icon(Icons.campaign_outlined),
                      ),
                      title: Text(
                        campaign.name,
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                      subtitle: Text(campaign.status ?? 'Status unavailable'),
                      trailing: SizedBox(
                        width: 220,
                        child: DropdownButtonFormField<String?>(
                          initialValue: campaign.productId,
                          decoration: const InputDecoration(
                            labelText: 'Product',
                            isDense: true,
                          ),
                          items: [
                            const DropdownMenuItem<String?>(
                              value: null,
                              child: Text('Unassigned'),
                            ),
                            for (final product in products)
                              DropdownMenuItem(
                                value: product.id,
                                child: Text(product.name),
                              ),
                          ],
                          onChanged: (value) async {
                            try {
                              await ref
                                  .read(marketingRepositoryProvider)
                                  .assignProduct(campaign.id, value);
                              _reload();
                            } catch (error) {
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text(error.toString())),
                                );
                              }
                            }
                          },
                        ),
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    ),
  );
}
