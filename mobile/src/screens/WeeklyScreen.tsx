import { addDays, format, startOfWeek } from 'date-fns';
import { ko } from 'date-fns/locale';
import React, { useEffect, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    RefreshControl,
    ScrollView,
    StyleSheet,
    Text,
    useColorScheme,
    View,
} from 'react-native';
import { Menu, menuAPI } from '../api/menuAPI';
import { AppThemeColors, getThemeColors } from '../theme/colors';

const MEAL_TYPE_NAMES: { [key: string]: string } = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
};

export default function WeeklyScreen() {
  const colorScheme = useColorScheme();
  const colors = getThemeColors(colorScheme);
  const styles = React.useMemo(() => createStyles(colors), [colors]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [menus, setMenus] = useState<Menu[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date());

  const loadWeeklyMenus = async () => {
    try {
      setLoading(true);
      const monday = startOfWeek(selectedDate, { weekStartsOn: 1 });
      const dateStr = format(monday, 'yyyy-MM-dd');
      const response = await menuAPI.getWeeklyMenus(dateStr);
      setMenus(response.data || []);
    } catch (error) {
      console.error('Failed to load weekly menus:', error);
      Alert.alert('오류', '주간 메뉴를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadWeeklyMenus();
    setRefreshing(false);
  };

  useEffect(() => {
    loadWeeklyMenus();
  }, [selectedDate]);

  const getMenusForDate = (date: Date): Menu[] => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return menus.filter(menu => menu.date === dateStr);
  };

  const renderDayMenus = (date: Date) => {
    const dayMenus = getMenusForDate(date);
    const isToday = format(date, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');

    return (
      <View key={date.toISOString()} style={styles.dayCard}>
        <View style={[styles.dayHeader, isToday && styles.todayHeader]}>
          <Text style={[styles.dayText, isToday && styles.todayText]}>
            {format(date, 'M/d (E)', { locale: ko })}
          </Text>
          {isToday && <Text style={styles.todayBadge}>오늘</Text>}
        </View>
        
        {dayMenus.length > 0 ? (
          dayMenus.map((menu, index) => (
            <View key={index} style={styles.mealSection}>
              <View style={styles.mealHeader}>
                <Text style={styles.mealType}>
                  {MEAL_TYPE_NAMES[menu.meal_type] || menu.meal_type}
                </Text>
                <Text style={styles.restaurant}>{menu.restaurant}</Text>
              </View>
              <View style={styles.itemsList}>
                {menu.items.map((item, idx) => (
                  <View key={idx} style={styles.itemRow}>
                    <Text style={styles.itemName}>{item.name}</Text>
                    {item.price && (
                      <Text style={styles.itemPrice}>
                        {item.price.toLocaleString()}원
                      </Text>
                    )}
                  </View>
                ))}
              </View>
            </View>
          ))
        ) : (
          <Text style={styles.noMenu}>메뉴 정보 없음</Text>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.accent} />
        <Text style={styles.loadingText}>주간 메뉴를 불러오는 중...</Text>
      </View>
    );
  }

  const monday = startOfWeek(selectedDate, { weekStartsOn: 1 });
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(monday, i));

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={colors.accent}
          colors={[colors.accent]}
        />
      }
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>이번 주 메뉴</Text>
        <Text style={styles.headerSubtitle}>
          {format(monday, 'M/d')} ~ {format(addDays(monday, 6), 'M/d')}
        </Text>
      </View>

      <View style={styles.weekContainer}>
        {weekDays.map(date => renderDayMenus(date))}
      </View>
    </ScrollView>
  );
}

const createStyles = (colors: AppThemeColors) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    centerContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: colors.background,
    },
    loadingText: {
      marginTop: 10,
      fontSize: 16,
      color: colors.textSecondary,
    },
    header: {
      backgroundColor: colors.surface,
      padding: 20,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    headerTitle: {
      fontSize: 24,
      fontWeight: 'bold',
      color: colors.textPrimary,
      marginBottom: 5,
    },
    headerSubtitle: {
      fontSize: 14,
      color: colors.textSecondary,
    },
    weekContainer: {
      padding: 15,
    },
    dayCard: {
      backgroundColor: colors.surface,
      borderRadius: 12,
      padding: 15,
      marginBottom: 15,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 3,
    },
    dayHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
      paddingBottom: 10,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    todayHeader: {
      borderBottomColor: colors.accent,
      borderBottomWidth: 2,
    },
    dayText: {
      fontSize: 18,
      fontWeight: 'bold',
      color: colors.textPrimary,
    },
    todayText: {
      color: colors.accent,
    },
    todayBadge: {
      marginLeft: 8,
      backgroundColor: colors.accent,
      color: colors.badgeText,
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 10,
      fontSize: 12,
      fontWeight: '600',
    },
    mealSection: {
      marginBottom: 12,
    },
    mealHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 8,
    },
    mealType: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.accent,
    },
    restaurant: {
      fontSize: 14,
      color: colors.textSecondary,
    },
    itemsList: {
      gap: 4,
    },
    itemRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 2,
    },
    itemName: {
      fontSize: 15,
      color: colors.textPrimary,
      flex: 1,
    },
    itemPrice: {
      fontSize: 14,
      color: colors.textSecondary,
    },
    noMenu: {
      fontSize: 14,
      color: colors.textMuted,
      textAlign: 'center',
      paddingVertical: 10,
    },
  });
