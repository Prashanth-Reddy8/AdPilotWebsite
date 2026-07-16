import 'package:adpilot/src/core/config.dart';
import 'package:adpilot/src/core/models.dart';
import 'package:adpilot/src/core/providers.dart';
import 'package:adpilot/src/shared/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:uuid/uuid.dart';

class MetaScreen extends ConsumerStatefulWidget {
  const MetaScreen({super.key});
  @override
  ConsumerState<MetaScreen> createState() => _MetaScreenState();
}

class _MetaScreenState extends ConsumerState<MetaScreen> {
  late Future<List<MetaAccount>> _future;
  MetaConnectionOptions? _options;
  bool _processingCallback = false;
  String? _callbackError;

  @override
  void initState() {
    super.initState();
    _load();
    WidgetsBinding.instance.addPostFrameCallback((_) => _handleCallback());
  }

  void _load() =>
      _future = ref.read(marketingRepositoryProvider).metaAccounts();
  void _reload() => setState(_load);

  Map<String, String> _oauthParameters() {
    if (Uri.base.queryParameters.containsKey('code')) {
      return Uri.base.queryParameters;
    }
    final fragment = Uri.base.fragment;
    final queryStart = fragment.indexOf('?');
    if (queryStart == -1) return const {};
    return Uri.splitQueryString(fragment.substring(queryStart + 1));
  }

  Future<void> _handleCallback() async {
    final parameters = _oauthParameters();
    final code = parameters['code'];
    if (code == null || _processingCallback) return;
    setState(() => _processingCallback = true);
    try {
      final expectedState = await ref
          .read(sessionStoreProvider)
          .readMetaState();
      if (expectedState == null || expectedState != parameters['state']) {
        throw const FormatException(
          'Meta authorization state did not match. Please try again.',
        );
      }
      await ref.read(sessionStoreProvider).clearMetaState();
      final options = await ref
          .read(marketingRepositoryProvider)
          .exchangeMetaCode(code, AppConfig.metaRedirectUri);
      if (mounted) setState(() => _options = options);
    } catch (error) {
      if (mounted) setState(() => _callbackError = error.toString());
    } finally {
      if (mounted) setState(() => _processingCallback = false);
    }
  }

  Future<void> _authorize() async {
    if (AppConfig.metaAppId.isEmpty) {
      setState(
        () => _callbackError =
            'META_APP_ID is missing. Start Flutter with the required --dart-define.',
      );
      return;
    }
    final state = const Uuid().v4();
    await ref.read(sessionStoreProvider).writeMetaState(state);
    final uri = Uri.https(
      'www.facebook.com',
      '/${AppConfig.metaApiVersion}/dialog/oauth',
      {
        'client_id': AppConfig.metaAppId,
        'redirect_uri': AppConfig.metaRedirectUri,
        'state': state,
        'response_type': 'code',
        'scope': 'ads_read,business_management',
      },
    );
    if (!await launchUrl(uri, webOnlyWindowName: '_self')) {
      setState(() => _callbackError = 'Could not open Meta authorization.');
    }
  }

  Future<void> _complete(MetaAccountOption option) async {
    try {
      await ref
          .read(marketingRepositoryProvider)
          .completeMetaConnection(_options!.sessionId, option.id);
      if (mounted) {
        setState(() {
          _options = null;
          _callbackError = null;
          _load();
        });
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('${option.name} connected.')));
      }
    } catch (error) {
      if (mounted) setState(() => _callbackError = error.toString());
    }
  }

  Future<void> _sync(MetaAccount account) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      messenger.showSnackBar(
        SnackBar(content: Text('Syncing ${account.name}…')),
      );
      final result = await ref
          .read(marketingRepositoryProvider)
          .sync(account.id);
      _reload();
      messenger.showSnackBar(SnackBar(content: Text(result)));
    } catch (error) {
      messenger.showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(24),
    children: [
      PageHeading(
        title: 'Meta Ads connection',
        subtitle:
            'Authorize reporting access and choose the ad accounts AdPilot should monitor.',
        action: FilledButton.icon(
          onPressed: _authorize,
          icon: const Icon(Icons.add_link),
          label: const Text('Connect Meta account'),
        ),
      ),
      if (_processingCallback) ...[
        const SizedBox(height: 24),
        const Card(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 18),
                Text('Completing Meta authorization…'),
              ],
            ),
          ),
        ),
      ],
      if (_callbackError != null) ...[
        const SizedBox(height: 20),
        Card(
          child: ListTile(
            leading: Icon(
              Icons.error_outline,
              color: Theme.of(context).colorScheme.error,
            ),
            title: const Text('Connection failed'),
            subtitle: Text(_callbackError!),
            trailing: IconButton(
              onPressed: () => setState(() => _callbackError = null),
              icon: const Icon(Icons.close),
            ),
          ),
        ),
      ],
      if (_options != null) ...[
        const SizedBox(height: 24),
        Text(
          'Choose an ad account',
          style: Theme.of(
            context,
          ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 10),
        Card(
          child: Column(
            children: [
              for (final option in _options!.accounts)
                ListTile(
                  leading: const CircleAvatar(
                    child: Icon(Icons.business_outlined),
                  ),
                  title: Text(
                    option.name,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text('${option.id} • ${option.currency}'),
                  trailing: FilledButton(
                    onPressed: () => _complete(option),
                    child: const Text('Connect'),
                  ),
                ),
            ],
          ),
        ),
      ],
      const SizedBox(height: 28),
      Text(
        'Connected accounts',
        style: Theme.of(
          context,
        ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
      ),
      const SizedBox(height: 12),
      FutureBuilder<List<MetaAccount>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return ErrorPanel(error: snapshot.error!, onRetry: _reload);
          }
          final accounts = snapshot.data!;
          if (accounts.isEmpty) {
            return const Card(
              child: EmptyPanel(
                icon: Icons.link_off,
                title: 'No Meta account connected',
                message: 'Authorize Meta to begin creative monitoring.',
              ),
            );
          }
          return Column(
            children: [
              for (final account in accounts)
                Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    leading: const CircleAvatar(
                      child: Icon(Icons.business_center_outlined),
                    ),
                    title: Text(
                      account.name,
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    subtitle: Text(
                      '${account.externalId} • ${account.currency}\n'
                      '${account.lastSyncAt == null ? 'Never synchronized' : 'Last sync ${DateFormat.yMMMd().add_jm().format(account.lastSyncAt!.toLocal())}'}',
                    ),
                    isThreeLine: true,
                    trailing: FilledButton.tonalIcon(
                      onPressed: () => _sync(account),
                      icon: const Icon(Icons.sync),
                      label: const Text('Sync now'),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
      const SizedBox(height: 20),
      const Card(
        child: ListTile(
          leading: Icon(Icons.verified_user_outlined),
          title: Text(
            'Read-only monitoring',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          subtitle: Text(
            'AdPilot requests reporting access only. It never pauses or edits campaigns.',
          ),
        ),
      ),
    ],
  );
}
