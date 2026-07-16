import 'package:adpilot/src/core/providers.dart';
import 'package:adpilot/src/core/theme.dart';
import 'package:adpilot/src/features/auth/login_screen.dart';
import 'package:adpilot/src/features/shell/app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AdPilotApp extends ConsumerWidget {
  const AdPilotApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(authControllerProvider);
    return MaterialApp(
      title: 'AdPilot',
      debugShowCheckedModeBanner: false,
      theme: buildAdPilotTheme(),
      home: session.when(
        data: (authenticated) =>
            authenticated ? const AppShell() : const LoginScreen(),
        error: (error, _) => LoginScreen(initialError: error.toString()),
        loading: () => const _AppLoadingScreen(),
      ),
    );
  }
}

class _AppLoadingScreen extends StatelessWidget {
  const _AppLoadingScreen();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}
