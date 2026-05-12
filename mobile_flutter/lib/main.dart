import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000',
);

const mealTypeNames = {
  'breakfast': '\uC544\uCE68',
  'lunch': '\uC810\uC2EC',
  'dinner': '\uC800\uB141',
};

const restaurantNames = {
  '\uC11C\uC6B8_\uD559\uC0DD\uC2DD\uB2F9':
      '\uC11C\uC6B8 \uD559\uC0DD\uC2DD\uB2F9',
  '\uC11C\uC6B8_\uAD50\uC9C1\uC6D0\uC2DD\uB2F9':
      '\uC11C\uC6B8 \uAD50\uC9C1\uC6D0\uC2DD\uB2F9',
  '\uC11C\uC6B8_\uD478\uB4DC\uCF54\uD2B8':
      '\uC11C\uC6B8 \uD478\uB4DC\uCF54\uD2B8',
  '\uCC9C\uC548_\uD559\uC0DD\uC2DD\uB2F9':
      '\uCC9C\uC548 \uD559\uC0DD\uD68C\uAD00',
  '\uCC9C\uC548_\uAD50\uC9C1\uC6D0\uC2DD\uB2F9':
      '\uCC9C\uC548 \uAD50\uC9C1\uC6D0\uC2DD\uB2F9',
};

const weekdays = {
  1: '\uC6D4',
  2: '\uD654',
  3: '\uC218',
  4: '\uBAA9',
  5: '\uAE08',
  6: '\uD1A0',
  7: '\uC77C',
};

const campusNames = [
  '\uC11C\uC6B8\uCEA0\uD37C\uC2A4',
  '\uCC9C\uC548\uCEA0\uD37C\uC2A4',
];

const mealOrder = [
  'breakfast',
  'lunch',
  'dinner',
];

const _lastCampusKey = 'lastCampus';

const _brandInk = Color(0xFF102E5F);
const _brandBlue = Color(0xFF1E5AA8);
const _brandGreen = _brandBlue;
const _warmAccent = Color(0xFFE66D4E);
const _surfaceWash = Color(0xFFF4F7FC);
const _cardSurface = Color(0xFFFFFFFF);
const _lineColor = Color(0xFFDCE5F2);

void main() {
  runApp(const SmuBabApp());
}

class SmuBabApp extends StatelessWidget {
  const SmuBabApp({super.key});

  @override
  Widget build(BuildContext context) {
    const seed = _brandGreen;

    return MaterialApp(
      title: 'SMU-Bab',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: seed,
          secondary: _warmAccent,
        ),
        useMaterial3: true,
        fontFamilyFallback: const [
          'Malgun Gothic',
          'Apple SD Gothic Neo',
          'Noto Sans KR',
          'sans-serif',
        ],
        scaffoldBackgroundColor: _surfaceWash,
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          elevation: 0,
          scrolledUnderElevation: 0,
          backgroundColor: _surfaceWash,
          foregroundColor: _brandInk,
          surfaceTintColor: Colors.transparent,
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: _cardSurface,
          elevation: 0,
          indicatorColor: const Color(0xFFDCEBFF),
          labelTextStyle: WidgetStateProperty.resolveWith((states) {
            final selected = states.contains(WidgetState.selected);
            return TextStyle(
              color: selected ? _brandInk : const Color(0xFF687871),
              fontSize: 12,
              fontWeight: selected ? FontWeight.w900 : FontWeight.w700,
            );
          }),
          iconTheme: WidgetStateProperty.resolveWith((states) {
            final selected = states.contains(WidgetState.selected);
            return IconThemeData(
              color: selected ? _brandGreen : const Color(0xFF687871),
              size: selected ? 25 : 23,
            );
          }),
        ),
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: seed,
          secondary: const Color(0xFFFFA17E),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        fontFamilyFallback: const [
          'Malgun Gothic',
          'Apple SD Gothic Neo',
          'Noto Sans KR',
          'sans-serif',
        ],
      ),
      home: const HomeShell(),
    );
  }
}

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  var index = DateTime.now().weekday >= DateTime.saturday ? 1 : 0;

  @override
  Widget build(BuildContext context) {
    final screens = [
      const TodayMenuScreen(),
      const WeeklyMenuScreen(),
    ];

    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 72,
        titleSpacing: 16,
        title: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: _brandGreen,
                borderRadius: BorderRadius.circular(8),
                boxShadow: [
                  BoxShadow(
                    color: _brandGreen.withValues(alpha: 0.25),
                    blurRadius: 16,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: const Icon(
                Icons.restaurant_rounded,
                color: Colors.white,
                size: 22,
              ),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'SMU-Bab',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: _brandInk,
                        fontWeight: FontWeight.w900,
                        height: 1,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  '\uC0C1\uBA85\uB300 \uD559\uC2DD',
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: const Color(0xFF687871),
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ],
            ),
          ],
        ),
      ),
      body: screens[index],
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.fromLTRB(14, 0, 14, 12),
        child: Container(
          decoration: BoxDecoration(
            color: _cardSurface,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: _lineColor),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.08),
                blurRadius: 22,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: NavigationBar(
              height: 64,
              selectedIndex: index,
              onDestinationSelected: (value) => setState(() => index = value),
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.today_outlined),
                  selectedIcon: Icon(Icons.today),
                  label: '\uC624\uB298',
                ),
                NavigationDestination(
                  icon: Icon(Icons.calendar_month_outlined),
                  selectedIcon: Icon(Icons.calendar_month),
                  label: '\uC8FC\uAC04',
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class MenuApi {
  MenuApi({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Uri _uri(String path, [Map<String, String>? query]) {
    final base = apiBaseUrl.endsWith('/')
        ? apiBaseUrl.substring(0, apiBaseUrl.length - 1)
        : apiBaseUrl;
    return Uri.parse('$base$path').replace(queryParameters: query);
  }

  Future<DailyMenuResponse> getTodayMenus() async {
    final response = await _client.get(_uri('/api/menus/today'));
    return DailyMenuResponse.fromJson(_decode(response));
  }

  Future<MenuResponse> getWeeklyMenus({DateTime? targetDate}) async {
    final query = targetDate == null
        ? null
        : {'target_date': DateFormat('yyyy-MM-dd').format(targetDate)};
    final response = await _client.get(_uri('/api/menus/week', query));
    return MenuResponse.fromJson(_decode(response));
  }

  Map<String, dynamic> _decode(http.Response response) {
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException(
        '\u0041\u0050\u0049 \uC751\uB2F5 \uD615\uC2DD\uC774 \uC62C\uBC14\uB974\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.',
      );
    }
    if (response.statusCode >= 400) {
      throw ApiException(
        decoded['detail']?.toString() ??
            '\u0041\u0050\u0049 \uC694\uCCAD\uC774 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4.',
      );
    }
    return decoded;
  }
}

class ApiException implements Exception {
  const ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class MenuItem {
  const MenuItem({
    required this.name,
    this.price,
  });

  final String name;
  final int? price;

  factory MenuItem.fromJson(Map<String, dynamic> json) {
    return MenuItem(
      name: json['name']?.toString() ?? '',
      price: json['price'] is num ? (json['price'] as num).toInt() : null,
    );
  }
}

class Menu {
  const Menu({
    required this.date,
    required this.restaurant,
    required this.mealType,
    required this.items,
  });

  final DateTime date;
  final String restaurant;
  final String mealType;
  final List<MenuItem> items;

  factory Menu.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return Menu(
      date: DateTime.parse(json['date'].toString()),
      restaurant: json['restaurant']?.toString() ?? '',
      mealType: json['meal_type']?.toString() ?? '',
      items: rawItems
          .whereType<Map<String, dynamic>>()
          .map(MenuItem.fromJson)
          .where((item) => item.name.trim().isNotEmpty)
          .toList(),
    );
  }
}

class DailyMenuResponse {
  const DailyMenuResponse({
    required this.success,
    required this.date,
    required this.menus,
    this.message,
    this.error,
  });

  final bool success;
  final DateTime date;
  final List<Menu> menus;
  final String? message;
  final String? error;

  factory DailyMenuResponse.fromJson(Map<String, dynamic> json) {
    return DailyMenuResponse(
      success: json['success'] == true,
      date: DateTime.parse(json['date'].toString()),
      menus: (json['menus'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(Menu.fromJson)
          .toList(),
      message: json['message']?.toString(),
      error: json['error']?.toString(),
    );
  }
}

class MenuResponse {
  const MenuResponse({
    required this.success,
    required this.data,
    this.message,
    this.error,
  });

  final bool success;
  final List<Menu> data;
  final String? message;
  final String? error;

  factory MenuResponse.fromJson(Map<String, dynamic> json) {
    return MenuResponse(
      success: json['success'] == true,
      data: (json['data'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(Menu.fromJson)
          .toList(),
      message: json['message']?.toString(),
      error: json['error']?.toString(),
    );
  }
}

class TodayMenuScreen extends StatefulWidget {
  const TodayMenuScreen({super.key});

  @override
  State<TodayMenuScreen> createState() => _TodayMenuScreenState();
}

class _TodayMenuScreenState extends State<TodayMenuScreen> {
  final api = MenuApi();
  late Future<DailyMenuResponse> future = api.getTodayMenus();

  Future<void> refresh() async {
    setState(() {
      future = api.getTodayMenus();
    });
    await future;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<DailyMenuResponse>(
      future: future,
      builder: (context, snapshot) {
        return RefreshIndicator(
          onRefresh: refresh,
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 10, 20, 108),
            children: [
              HeaderBlock(
                eyebrow: '\uC0C1\uBA85\uB300\uD559\uAD50 \uD559\uC2DD',
                title: '\uC624\uB298\uC758 \uC2DD\uB2E8',
                subtitle: _dateLabel(DateTime.now()),
              ),
              const SizedBox(height: 16),
              if (snapshot.connectionState == ConnectionState.waiting)
                const LoadingPanel(
                  message:
                      '\uBA54\uB274\uB97C \uBD88\uB7EC\uC624\uB294 \uC911...',
                )
              else if (snapshot.hasError)
                ErrorPanel(message: snapshot.error.toString())
              else
                TodayMenuContent(response: snapshot.data!),
            ],
          ),
        );
      },
    );
  }
}

class TodayMenuContent extends StatefulWidget {
  const TodayMenuContent({required this.response, super.key});

  final DailyMenuResponse response;

  @override
  State<TodayMenuContent> createState() => _TodayMenuContentState();
}

class _TodayMenuContentState extends State<TodayMenuContent> {
  String selectedCampus = campusNames.first;
  late String selectedMeal = _defaultMealForNow(DateTime.now());

  @override
  void initState() {
    super.initState();
    _loadLastCampus();
  }

  Future<void> _loadLastCampus() async {
    final preferences = await SharedPreferences.getInstance();
    final campus = preferences.getString(_lastCampusKey);
    if (!mounted || campus == null || !campusNames.contains(campus)) {
      return;
    }
    setState(() {
      selectedCampus = campus;
    });
  }

  Future<void> _selectCampus(String campus) async {
    setState(() {
      selectedCampus = campus;
    });
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(_lastCampusKey, campus);
  }

  @override
  Widget build(BuildContext context) {
    final sortedMenus = [...widget.response.menus]..sort(_compareMenus);
    final campusMenus = sortedMenus
        .where((menu) => _campusLabel(menu.restaurant) == selectedCampus)
        .toList();
    final availableMealTypes = mealOrder
        .where(
            (mealType) => campusMenus.any((menu) => menu.mealType == mealType))
        .toList();
    final defaultMeal = _defaultMealForNow(DateTime.now());
    final activeMeal = availableMealTypes.contains(selectedMeal)
        ? selectedMeal
        : availableMealTypes.contains(defaultMeal)
            ? defaultMeal
            : availableMealTypes.isNotEmpty
                ? availableMealTypes.first
                : selectedMeal;
    final activeMenus =
        campusMenus.where((menu) => menu.mealType == activeMeal).toList();

    final campusCounts = {
      for (final campus in campusNames)
        campus: sortedMenus
            .where((menu) => _campusLabel(menu.restaurant) == campus)
            .length,
    };
    final mealCounts = {
      for (final mealType in mealOrder)
        mealType: campusMenus.where((menu) => menu.mealType == mealType).length,
    };

    final mealChoices =
        availableMealTypes.isEmpty ? mealOrder : availableMealTypes;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!widget.response.success)
          ErrorPanel(
            message: widget.response.error ??
                widget.response.message ??
                '\uBA54\uB274 \uD655\uC778 \uC911\uC785\uB2C8\uB2E4.',
          ),
        if (widget.response.menus.isEmpty)
          const EmptyPanel(
            message:
                '\uC624\uB298 \uD45C\uC2DC\uD560 \uBA54\uB274\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4.',
          )
        else ...[
          ChoicePillGroup(
            label: '\uCEA0\uD37C\uC2A4',
            choices: campusNames,
            selected: selectedCampus,
            countBuilder: (campus) => campusCounts[campus] ?? 0,
            iconBuilder: (campus) => campus.startsWith('\uCC9C\uC548')
                ? Icons.location_city_rounded
                : Icons.apartment_rounded,
            colorBuilder: _campusAccent,
            onSelected: _selectCampus,
          ),
          const SizedBox(height: 12),
          ChoicePillGroup(
            label: '\uC2DC\uAC04\uB300',
            choices: mealChoices,
            selected: activeMeal,
            titleBuilder: (mealType) => mealTypeNames[mealType] ?? mealType,
            countBuilder: (mealType) => mealCounts[mealType] ?? 0,
            iconBuilder: _mealIcon,
            colorBuilder: _mealColor,
            onSelected: (mealType) => setState(() => selectedMeal = mealType),
          ),
          const SizedBox(height: 16),
          CampusMealSection(
            campus: selectedCampus,
            mealType: activeMeal,
            menus: activeMenus,
          ),
        ],
      ],
    );
  }
}

class WeeklyMenuScreen extends StatefulWidget {
  const WeeklyMenuScreen({super.key});

  @override
  State<WeeklyMenuScreen> createState() => _WeeklyMenuScreenState();
}

class _WeeklyMenuScreenState extends State<WeeklyMenuScreen> {
  final api = MenuApi();
  late Future<MenuResponse> future = api.getWeeklyMenus();

  Future<void> refresh() async {
    setState(() {
      future = api.getWeeklyMenus();
    });
    await future;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<MenuResponse>(
      future: future,
      builder: (context, snapshot) {
        return RefreshIndicator(
          onRefresh: refresh,
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 10, 20, 108),
            children: [
              const HeaderBlock(
                eyebrow:
                    '\uC6D4\uC694\uC77C\uBD80\uD130 \uAE08\uC694\uC77C\uAE4C\uC9C0',
                title: '\uC774\uBC88 \uC8FC \uBA54\uB274',
                subtitle:
                    '\uCEA0\uD37C\uC2A4\uC640 \uC2DD\uB2F9\uBCC4\uB85C \uBAA8\uC544\uBCF4\uAE30',
              ),
              const SizedBox(height: 16),
              if (snapshot.connectionState == ConnectionState.waiting)
                const LoadingPanel(
                  message:
                      '\uC8FC\uAC04 \uBA54\uB274\uB97C \uBD88\uB7EC\uC624\uB294 \uC911...',
                )
              else if (snapshot.hasError)
                ErrorPanel(message: snapshot.error.toString())
              else
                WeeklyMenuContent(response: snapshot.data!),
            ],
          ),
        );
      },
    );
  }
}

class WeeklyMenuContent extends StatelessWidget {
  const WeeklyMenuContent({
    required this.response,
    super.key,
  });

  final MenuResponse response;

  @override
  Widget build(BuildContext context) {
    final grouped = <String, List<Menu>>{};
    final sortedMenus = [...response.data]..sort(_compareMenus);
    for (final menu in sortedMenus) {
      final key = DateFormat('yyyy-MM-dd').format(menu.date);
      grouped.putIfAbsent(key, () => []).add(menu);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!response.success)
          ErrorPanel(
            message: response.error ??
                response.message ??
                '\uC8FC\uAC04 \uBA54\uB274 \uD655\uC778 \uC911\uC785\uB2C8\uB2E4.',
          ),
        WeekSummaryStrip(menus: sortedMenus),
        const SizedBox(height: 16),
        if (grouped.isEmpty)
          const EmptyPanel(
            message:
                '\uC774\uBC88 \uC8FC \uBA54\uB274\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4.',
          )
        else
          ...grouped.entries.map((entry) {
            final date = DateTime.parse(entry.key);
            return DayMenuSection(date: date, menus: entry.value);
          }),
      ],
    );
  }
}

class WeekSummaryStrip extends StatelessWidget {
  const WeekSummaryStrip({required this.menus, super.key});

  final List<Menu> menus;

  @override
  Widget build(BuildContext context) {
    final dateCount = menus
        .map((menu) => DateFormat('yyyy-MM-dd').format(menu.date))
        .toSet()
        .length;
    final restaurantCount = menus.map((menu) => menu.restaurant).toSet().length;
    final itemCount = menus.fold<int>(
      0,
      (total, menu) => total + menu.items.length,
    );

    return Row(
      children: [
        Expanded(
          child: _SummaryTile(
            label: '\uC77C',
            value: dateCount.toString(),
            color: _brandGreen,
            icon: Icons.event_available_rounded,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _SummaryTile(
            label: '\uC2DD\uB2F9',
            value: restaurantCount.toString(),
            color: _warmAccent,
            icon: Icons.storefront_rounded,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _SummaryTile(
            label: '\uD56D\uBAA9',
            value: itemCount.toString(),
            color: const Color(0xFF4D6FA9),
            icon: Icons.format_list_bulleted_rounded,
          ),
        ),
      ],
    );
  }
}

class _SummaryTile extends StatelessWidget {
  const _SummaryTile({
    required this.label,
    required this.value,
    required this.color,
    required this.icon,
  });

  final String label;
  final String value;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 10),
      decoration: BoxDecoration(
        color: _cardSurface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _lineColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.035),
            blurRadius: 14,
            offset: const Offset(0, 7),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 4),
          Text(
            value,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: color,
                  fontWeight: FontWeight.w900,
                ),
          ),
          Text(
            label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: const Color(0xFF596862),
                  fontWeight: FontWeight.w800,
                ),
          ),
        ],
      ),
    );
  }
}

class ChoicePillGroup extends StatelessWidget {
  const ChoicePillGroup({
    required this.label,
    required this.choices,
    required this.selected,
    required this.onSelected,
    required this.iconBuilder,
    required this.colorBuilder,
    this.titleBuilder,
    this.countBuilder,
    super.key,
  });

  final String label;
  final List<String> choices;
  final String selected;
  final ValueChanged<String> onSelected;
  final IconData Function(String choice) iconBuilder;
  final Color Function(String choice) colorBuilder;
  final String Function(String choice)? titleBuilder;
  final int Function(String choice)? countBuilder;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 10),
      decoration: BoxDecoration(
        color: _cardSurface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _lineColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  color: const Color(0xFF64748B),
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: choices.map((choice) {
              final isSelected = choice == selected;
              final color = colorBuilder(choice);
              final title = titleBuilder?.call(choice) ?? choice;
              final count = countBuilder?.call(choice);
              return InkWell(
                borderRadius: BorderRadius.circular(8),
                onTap: () => onSelected(choice),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 10,
                  ),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? color.withValues(alpha: 0.13)
                        : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: isSelected
                          ? color.withValues(alpha: 0.42)
                          : _lineColor,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        iconBuilder(choice),
                        size: 17,
                        color: isSelected ? color : const Color(0xFF64748B),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        title,
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              color:
                                  isSelected ? color : const Color(0xFF334155),
                              fontWeight: isSelected
                                  ? FontWeight.w900
                                  : FontWeight.w800,
                            ),
                      ),
                      if (count != null) ...[
                        const SizedBox(width: 6),
                        Text(
                          count.toString(),
                          style:
                              Theme.of(context).textTheme.labelMedium?.copyWith(
                                    color: isSelected
                                        ? color
                                        : const Color(0xFF64748B),
                                    fontWeight: FontWeight.w900,
                                  ),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

class CampusMealSection extends StatelessWidget {
  const CampusMealSection({
    required this.campus,
    required this.mealType,
    required this.menus,
    super.key,
  });

  final String campus;
  final String mealType;
  final List<Menu> menus;

  @override
  Widget build(BuildContext context) {
    final campusColor = _campusAccent(campus);
    final mealColor = _mealColor(mealType);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 5,
              height: 30,
              decoration: BoxDecoration(
                color: campusColor,
                borderRadius: BorderRadius.circular(999),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    campus,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: _brandInk,
                          fontWeight: FontWeight.w900,
                          height: 1.1,
                        ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    mealTypeNames[mealType] ?? mealType,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: mealColor,
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: mealColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(999),
                border: Border.all(color: mealColor.withValues(alpha: 0.2)),
              ),
              child: Text(
                '${menus.length}\uAC1C \uC2DD\uB2E8',
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: mealColor,
                      fontWeight: FontWeight.w900,
                    ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        if (menus.isEmpty)
          EmptyPanel(
            message:
                '$campus ${mealTypeNames[mealType] ?? mealType} \uC2DD\uB2E8\uC774 \uC544\uC9C1 \uC5C6\uC2B5\uB2C8\uB2E4.',
          )
        else
          ...menus.map(MenuCard.new),
      ],
    );
  }
}

class CampusMenuSection extends StatelessWidget {
  const CampusMenuSection({
    required this.campus,
    required this.menus,
    super.key,
  });

  final String campus;
  final List<Menu> menus;

  @override
  Widget build(BuildContext context) {
    final accent =
        campus.startsWith('\uCC9C\uC548') ? _warmAccent : _brandGreen;
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 5,
                height: 28,
                decoration: BoxDecoration(
                  color: accent,
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  campus,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: _brandInk,
                        fontWeight: FontWeight.w900,
                      ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.11),
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(color: accent.withValues(alpha: 0.18)),
                ),
                child: Text(
                  '${menus.length}\uAC1C \uC2DD\uB2E8',
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: accent,
                        fontWeight: FontWeight.w900,
                      ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ...menus.map(MenuCard.new),
        ],
      ),
    );
  }
}

class HeaderBlock extends StatelessWidget {
  const HeaderBlock({
    required this.eyebrow,
    required this.title,
    required this.subtitle,
    super.key,
  });

  final String eyebrow;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(18, 18, 18, 17),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            _brandInk,
            Color(0xFF1B76D1),
          ],
        ),
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: _brandInk.withValues(alpha: 0.18),
            blurRadius: 24,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.local_dining_rounded,
                  size: 15,
                  color: Colors.white,
                ),
                const SizedBox(width: 6),
                Text(
                  eyebrow,
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w900,
                      ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          Text(
            title,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w900,
                  height: 1.08,
                ),
          ),
          const SizedBox(height: 7),
          Text(
            subtitle,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.white.withValues(alpha: 0.78),
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }
}

class DayMenuSection extends StatelessWidget {
  const DayMenuSection({
    required this.date,
    required this.menus,
    super.key,
  });

  final DateTime date;
  final List<Menu> menus;

  @override
  Widget build(BuildContext context) {
    final isToday = DateFormat('yyyy-MM-dd').format(date) ==
        DateFormat('yyyy-MM-dd').format(DateTime.now());
    return Padding(
      padding: const EdgeInsets.only(bottom: 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: _cardSurface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: _lineColor),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.calendar_today_rounded,
                  size: 18,
                  color: _brandGreen,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _dateLabel(date),
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: _brandInk,
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                ),
                if (isToday)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 9,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: _brandGreen.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      '\uC624\uB298',
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                            color: _brandGreen,
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          ...menus.map((menu) => MenuCard(menu, compact: true)),
        ],
      ),
    );
  }
}

class MenuCard extends StatelessWidget {
  const MenuCard(this.menu, {this.compact = false, super.key});

  final Menu menu;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final mealColor = _mealColor(menu.mealType);
    final mealTint = _mealTint(menu.mealType);
    return Container(
      margin: EdgeInsets.only(bottom: compact ? 8 : 12),
      decoration: BoxDecoration(
        color: _cardSurface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _lineColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: compact ? 0.025 : 0.045),
            blurRadius: compact ? 12 : 18,
            offset: Offset(0, compact ? 5 : 8),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Stack(
        children: [
          Positioned(
            left: 0,
            top: 0,
            bottom: 0,
            width: 5,
            child: ColoredBox(color: mealColor),
          ),
          Padding(
            padding: const EdgeInsets.only(left: 5),
            child: Padding(
              padding: EdgeInsets.all(compact ? 14 : 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.location_on_rounded,
                                  size: 14,
                                  color: _campusColor(menu.restaurant),
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  _campusLabel(menu.restaurant),
                                  style: Theme.of(context)
                                      .textTheme
                                      .labelSmall
                                      ?.copyWith(
                                        color: _campusColor(menu.restaurant),
                                        fontWeight: FontWeight.w900,
                                      ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _restaurantLabel(menu.restaurant),
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(
                                    color: _brandInk,
                                    fontWeight: FontWeight.w900,
                                    height: 1.12,
                                  ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: mealTint,
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(
                              color: mealColor.withValues(alpha: 0.2)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              _mealIcon(menu.mealType),
                              size: 14,
                              color: mealColor,
                            ),
                            const SizedBox(width: 5),
                            Text(
                              mealTypeNames[menu.mealType] ?? menu.mealType,
                              style: Theme.of(context)
                                  .textTheme
                                  .labelMedium
                                  ?.copyWith(
                                    color: mealColor,
                                    fontWeight: FontWeight.w900,
                                  ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (menu.items.isEmpty)
                    Text(
                      '\uB4F1\uB85D\uB41C \uBA54\uB274\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4.',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: const Color(0xFF687871),
                          ),
                    )
                  else
                    ...menu.items.asMap().entries.map((entry) {
                      final item = entry.value;
                      return Container(
                        margin: EdgeInsets.only(top: entry.key == 0 ? 0 : 6),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color:
                              mealTint.withValues(alpha: compact ? 0.45 : 0.58),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 6,
                              height: 6,
                              margin: const EdgeInsets.only(top: 7),
                              decoration: BoxDecoration(
                                color: mealColor,
                                borderRadius: BorderRadius.circular(999),
                              ),
                            ),
                            const SizedBox(width: 9),
                            Expanded(
                              child: Text(
                                item.name,
                                style: Theme.of(context)
                                    .textTheme
                                    .bodyMedium
                                    ?.copyWith(
                                      color: const Color(0xFF27332F),
                                      fontWeight: FontWeight.w700,
                                      height: 1.3,
                                    ),
                              ),
                            ),
                            if (item.price != null) ...[
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 7,
                                  vertical: 3,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.85),
                                  borderRadius: BorderRadius.circular(999),
                                ),
                                child: Text(
                                  '${NumberFormat.decimalPattern().format(item.price)}\uC6D0',
                                  style: Theme.of(context)
                                      .textTheme
                                      .labelMedium
                                      ?.copyWith(
                                        color: _brandInk,
                                        fontWeight: FontWeight.w900,
                                      ),
                                ),
                              ),
                            ],
                          ],
                        ),
                      );
                    }),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class LoadingPanel extends StatelessWidget {
  const LoadingPanel({required this.message, super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 220,
      width: double.infinity,
      decoration: BoxDecoration(
        color: _cardSurface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _lineColor),
      ),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 30,
              height: 30,
              child: CircularProgressIndicator(strokeWidth: 3),
            ),
            const SizedBox(height: 12),
            Text(
              message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: const Color(0xFF687871),
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class ErrorPanel extends StatelessWidget {
  const ErrorPanel({required this.message, super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.errorContainer,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.error.withValues(alpha: 0.16)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.error_outline_rounded, color: colors.onErrorContainer),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: colors.onErrorContainer,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class EmptyPanel extends StatelessWidget {
  const EmptyPanel({required this.message, super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 180,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: _cardSurface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _lineColor),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.no_food_rounded,
            color: _brandGreen.withValues(alpha: 0.55),
            size: 34,
          ),
          const SizedBox(height: 10),
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: const Color(0xFF687871),
                  fontWeight: FontWeight.w800,
                ),
          ),
        ],
      ),
    );
  }
}

String _restaurantLabel(String restaurant) {
  return restaurantNames[restaurant] ?? restaurant.replaceAll('_', ' ');
}

String _campusLabel(String restaurant) {
  return restaurant.startsWith('\uCC9C\uC548')
      ? '\uCC9C\uC548\uCEA0\uD37C\uC2A4'
      : '\uC11C\uC6B8\uCEA0\uD37C\uC2A4';
}

Color _campusColor(String restaurant) {
  return _campusAccent(_campusLabel(restaurant));
}

Color _campusAccent(String campus) {
  return campus.startsWith('\uCC9C\uC548') ? _warmAccent : _brandBlue;
}

Color _mealColor(String mealType) {
  switch (mealType) {
    case 'breakfast':
      return const Color(0xFFC47A16);
    case 'lunch':
      return _brandGreen;
    case 'dinner':
      return const Color(0xFF5269A6);
    default:
      return const Color(0xFF6F7C76);
  }
}

Color _mealTint(String mealType) {
  switch (mealType) {
    case 'breakfast':
      return const Color(0xFFFFF1D9);
    case 'lunch':
      return const Color(0xFFE7F0FF);
    case 'dinner':
      return const Color(0xFFE8ECF8);
    default:
      return const Color(0xFFF0F3F1);
  }
}

String _defaultMealForNow(DateTime now) {
  final minutes = now.hour * 60 + now.minute;
  return minutes < 10 * 60 + 30 ? 'breakfast' : 'lunch';
}

IconData _mealIcon(String mealType) {
  switch (mealType) {
    case 'breakfast':
      return Icons.wb_twilight_rounded;
    case 'lunch':
      return Icons.wb_sunny_rounded;
    case 'dinner':
      return Icons.nights_stay_rounded;
    default:
      return Icons.restaurant_menu_rounded;
  }
}

int _compareMenus(Menu a, Menu b) {
  final campusCompare =
      _campusLabel(a.restaurant).compareTo(_campusLabel(b.restaurant));
  if (campusCompare != 0) {
    return campusCompare;
  }

  final restaurantCompare =
      _restaurantLabel(a.restaurant).compareTo(_restaurantLabel(b.restaurant));
  if (restaurantCompare != 0) {
    return restaurantCompare;
  }

  return _mealOrder(a.mealType).compareTo(_mealOrder(b.mealType));
}

int _mealOrder(String mealType) {
  switch (mealType) {
    case 'breakfast':
      return 0;
    case 'lunch':
      return 1;
    case 'dinner':
      return 2;
    default:
      return 9;
  }
}

String _dateLabel(DateTime date) {
  final weekday = weekdays[date.weekday] ?? '';
  return '${DateFormat('M/d').format(date)} ($weekday)';
}
