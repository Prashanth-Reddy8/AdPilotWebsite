import 'package:adpilot/src/core/api_client.dart';
import 'package:adpilot/src/core/config.dart';
import 'package:adpilot/src/core/repositories.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final sessionStoreProvider = Provider<SessionStore>(
  (ref) => SessionStore(const FlutterSecureStorage()),
);

final apiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(
    baseUrl: AppConfig.apiBaseUrl,
    sessionStore: ref.watch(sessionStoreProvider),
  ),
);

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    ref.watch(apiClientProvider),
    ref.watch(sessionStoreProvider),
  ),
);

final marketingRepositoryProvider = Provider<MarketingRepository>(
  (ref) => MarketingRepository(ref.watch(apiClientProvider)),
);

class AuthController extends AsyncNotifier<bool> {
  @override
  Future<bool> build() => ref.read(authRepositoryProvider).hasSession();

  Future<void> login(String email, String password) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      await ref.read(authRepositoryProvider).login(email, password);
      return true;
    });
  }

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    state = const AsyncData(false);
  }
}

final authControllerProvider = AsyncNotifierProvider<AuthController, bool>(
  AuthController.new,
);
