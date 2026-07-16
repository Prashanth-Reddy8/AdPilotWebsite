import 'package:flutter/material.dart';

ThemeData buildAdPilotTheme() {
  const seed = Color(0xFF6657E8);
  final scheme = ColorScheme.fromSeed(
    seedColor: seed,
    brightness: Brightness.light,
    surface: const Color(0xFFF7F8FC),
  );
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: const Color(0xFFF7F8FC),
    fontFamily: 'Arial',
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFFE9EAF1)),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFFDADCE7)),
      ),
    ),
    dataTableTheme: const DataTableThemeData(
      headingTextStyle: TextStyle(
        fontWeight: FontWeight.w700,
        color: Color(0xFF4F5265),
      ),
      dividerThickness: 0.5,
    ),
  );
}
