import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smubab_flutter/main.dart';

void main() {
  testWidgets('renders the shared menu header', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: HeaderBlock(
            eyebrow: 'SMU',
            title: 'SMU-Bab',
            subtitle: 'Campus menus',
          ),
        ),
      ),
    );

    expect(find.text('SMU-Bab'), findsOneWidget);
    expect(find.byType(HeaderBlock), findsOneWidget);
  });
}
