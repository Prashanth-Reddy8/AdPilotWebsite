import 'package:adpilot/src/core/providers.dart';
import 'package:adpilot/src/features/alerts/alerts_screen.dart';
import 'package:adpilot/src/features/campaigns/campaigns_screen.dart';
import 'package:adpilot/src/features/creatives/creatives_screen.dart';
import 'package:adpilot/src/features/dashboard/dashboard_screen.dart';
import 'package:adpilot/src/features/meta/meta_screen.dart';
import 'package:adpilot/src/features/settings/settings_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key});
  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  int _index = 0;
  static const _destinations = [
    (
      label: 'Dashboard',
      icon: Icons.space_dashboard_outlined,
      selected: Icons.space_dashboard,
    ),
    (
      label: 'Creatives',
      icon: Icons.video_library_outlined,
      selected: Icons.video_library,
    ),
    (
      label: 'Campaigns',
      icon: Icons.campaign_outlined,
      selected: Icons.campaign,
    ),
    (
      label: 'Alerts',
      icon: Icons.notifications_none,
      selected: Icons.notifications,
    ),
    (label: 'Meta', icon: Icons.link_outlined, selected: Icons.link),
    (label: 'Settings', icon: Icons.tune_outlined, selected: Icons.tune),
  ];

  @override
  void initState() {
    super.initState();
    if (Uri.base.toString().contains('code=')) _index = 4;
  }

  @override
  Widget build(BuildContext context) {
    const screens = [
      DashboardScreen(),
      CreativesScreen(),
      CampaignsScreen(),
      AlertsScreen(),
      MetaScreen(),
      SettingsScreen(),
    ];
    final wide = MediaQuery.sizeOf(context).width >= 900;
    return Scaffold(
      appBar: wide
          ? null
          : AppBar(
              title: Text(
                _destinations[_index].label,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              actions: [
                IconButton(
                  tooltip: 'Sign out',
                  onPressed: () =>
                      ref.read(authControllerProvider.notifier).logout(),
                  icon: const Icon(Icons.logout),
                ),
              ],
            ),
      body: Row(
        children: [
          if (wide)
            NavigationRail(
              extended: MediaQuery.sizeOf(context).width >= 1180,
              selectedIndex: _index,
              onDestinationSelected: (value) => setState(() => _index = value),
              leading: const Padding(
                padding: EdgeInsets.fromLTRB(12, 20, 12, 30),
                child: _RailBrand(),
              ),
              trailing: Expanded(
                child: Align(
                  alignment: Alignment.bottomCenter,
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: IconButton(
                      tooltip: 'Sign out',
                      onPressed: () =>
                          ref.read(authControllerProvider.notifier).logout(),
                      icon: const Icon(Icons.logout),
                    ),
                  ),
                ),
              ),
              destinations: [
                for (final destination in _destinations)
                  NavigationRailDestination(
                    icon: Icon(destination.icon),
                    selectedIcon: Icon(destination.selected),
                    label: Text(destination.label),
                  ),
              ],
            ),
          if (wide) const VerticalDivider(width: 1),
          Expanded(
            child: IndexedStack(index: _index, children: screens),
          ),
        ],
      ),
      bottomNavigationBar: wide
          ? null
          : NavigationBar(
              selectedIndex: _index,
              onDestinationSelected: (value) => setState(() => _index = value),
              destinations: [
                for (final destination in _destinations.take(5))
                  NavigationDestination(
                    icon: Icon(destination.icon),
                    selectedIcon: Icon(destination.selected),
                    label: destination.label,
                  ),
              ],
            ),
    );
  }
}

class _RailBrand extends StatelessWidget {
  const _RailBrand();
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          color: const Color(0xFF6657E8),
          borderRadius: BorderRadius.circular(11),
        ),
        child: const Icon(
          Icons.auto_graph_rounded,
          color: Colors.white,
          size: 21,
        ),
      ),
      if (MediaQuery.sizeOf(context).width >= 1180) ...[
        const SizedBox(width: 10),
        const Text(
          'AdPilot',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
        ),
      ],
    ],
  );
}
