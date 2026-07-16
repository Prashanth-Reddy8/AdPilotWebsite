import 'package:adpilot/src/core/models.dart';
import 'package:adpilot/src/core/providers.dart';
import 'package:adpilot/src/shared/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});
  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late Future<UserSettings> _future;
  bool _saving = false;
  bool _initialized = false;
  final _formKey = GlobalKey<FormState>();
  final _ctr = TextEditingController();
  final _cpa = TextEditingController();
  final _roas = TextEditingController();
  final _frequency = TextEditingController();
  final _spend = TextEditingController();
  final _webhook = TextEditingController();
  bool _slack = false;
  bool _slackConfigured = false;

  @override
  void initState() {
    super.initState();
    _future = ref.read(marketingRepositoryProvider).settings();
  }

  void _populate(UserSettings settings) {
    if (_initialized) return;
    _initialized = true;
    _ctr.text = settings.ctrDrop.toStringAsFixed(0);
    _cpa.text = settings.cpaIncrease.toStringAsFixed(0);
    _roas.text = settings.minimumRoas.toString();
    _frequency.text = settings.maximumFrequency.toString();
    _spend.text = settings.spendThreshold.toStringAsFixed(0);
    _slack = settings.slackEnabled;
    _slackConfigured = settings.slackConfigured;
  }

  double _value(TextEditingController controller) =>
      double.parse(controller.text.trim());

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      final updated = await ref
          .read(marketingRepositoryProvider)
          .updateSettings(
            ctrDrop: _value(_ctr),
            cpaIncrease: _value(_cpa),
            minimumRoas: _value(_roas),
            maximumFrequency: _value(_frequency),
            spendThreshold: _value(_spend),
            slackEnabled: _slack,
            emailEnabled: false,
            slackWebhookUrl: _webhook.text.trim(),
          );
      _slackConfigured = updated.slackConfigured;
      _webhook.clear();
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Settings saved.')));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    for (final controller in [
      _ctr,
      _cpa,
      _roas,
      _frequency,
      _spend,
      _webhook,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<UserSettings>(
    future: _future,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return ErrorPanel(
          error: snapshot.error!,
          onRetry: () => setState(
            () => _future = ref.read(marketingRepositoryProvider).settings(),
          ),
        );
      }
      _populate(snapshot.data!);
      return Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            PageHeading(
              title: 'Analyzer settings',
              subtitle:
                  'Tune recommendation thresholds for your performance model.',
              action: FilledButton.icon(
                onPressed: _saving ? null : _save,
                icon: _saving
                    ? const SizedBox.square(
                        dimension: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.save_outlined),
                label: const Text('Save'),
              ),
            ),
            const SizedBox(height: 24),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(22),
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final width = constraints.maxWidth >= 800
                        ? (constraints.maxWidth - 20) / 2
                        : constraints.maxWidth;
                    return Wrap(
                      spacing: 20,
                      runSpacing: 18,
                      children: [
                        SizedBox(
                          width: width,
                          child: _numberField(_ctr, 'CTR drop threshold', '%'),
                        ),
                        SizedBox(
                          width: width,
                          child: _numberField(
                            _cpa,
                            'CPA increase threshold',
                            '%',
                          ),
                        ),
                        SizedBox(
                          width: width,
                          child: _numberField(_roas, 'Minimum ROAS', 'x'),
                        ),
                        SizedBox(
                          width: width,
                          child: _numberField(
                            _frequency,
                            'Maximum frequency',
                            'x',
                          ),
                        ),
                        SizedBox(
                          width: width,
                          child: _numberField(
                            _spend,
                            'Zero-purchase spend threshold',
                            '₹',
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'Notifications',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      value: _slack,
                      onChanged: (value) => setState(() => _slack = value),
                      title: const Text(
                        'Slack alerts',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                      subtitle: Text(
                        _slackConfigured
                            ? 'Webhook configured. Enter a URL only to replace it.'
                            : 'Add a Slack incoming webhook URL.',
                      ),
                    ),
                    if (_slack)
                      TextFormField(
                        controller: _webhook,
                        obscureText: true,
                        decoration: InputDecoration(
                          labelText: _slackConfigured
                              ? 'New webhook URL (optional)'
                              : 'Slack webhook URL',
                        ),
                        validator: (value) {
                          if (!_slack || _slackConfigured) return null;
                          final uri = Uri.tryParse(value ?? '');
                          return uri != null && uri.isScheme('https')
                              ? null
                              : 'Enter a valid HTTPS Slack webhook URL';
                        },
                      ),
                    const Divider(height: 30),
                    const ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(Icons.mail_outline),
                      title: Text(
                        'Email alerts',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                      subtitle: Text(
                        'Planned after Slack delivery is validated.',
                      ),
                      trailing: Chip(label: Text('Coming soon')),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    },
  );

  TextFormField _numberField(
    TextEditingController controller,
    String label,
    String suffix,
  ) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label, suffixText: suffix),
      validator: (value) {
        final number = double.tryParse(value ?? '');
        return number == null || number < 0
            ? 'Enter a valid non-negative number'
            : null;
      },
    );
  }
}
