import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { menuAPI, DailyMenuResponse, Menu } from '../api/menuAPI';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

const MEAL_TYPE_NAMES: { [key: string]: string } = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
};

export default function TodayScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<DailyMenuResponse | null>(null);

  const loadMenus = async () => {
    try {
      setLoading(true);
      const response = await menuAPI.getTodayMenus();
      setData(response);
    } catch (error) {
      console.error('Failed to load menus:', error);
      Alert.alert('오류', '메뉴를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadMenus();
    setRefreshing(false);
  };

  useEffect(() => {
    loadMenus();
  }, []);

  const renderMenuItem = (item: any, index: number) => (
    <View key={index} style={styles.menuItem}>
      <Text style={styles.menuItemName}>{item.name}</Text>
      {item.price && (
        <Text style={styles.menuItemPrice}>{item.price.toLocaleString()}원</Text>
      )}
    </View>
  );

  const renderMenu = (menu: Menu, index: number) => (
    <View key={index} style={styles.menuCard}>
      <View style={styles.menuHeader}>
        <Text style={styles.restaurantName}>{menu.restaurant}</Text>
        <Text style={styles.mealType}>
          {MEAL_TYPE_NAMES[menu.meal_type] || menu.meal_type}
        </Text>
      </View>
      <View style={styles.menuItems}>
        {menu.items.map((item, idx) => renderMenuItem(item, idx))}
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>메뉴를 불러오는 중...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.dateText}>
          {data?.date 
            ? format(new Date(data.date), 'yyyy년 MM월 dd일 (E)', { locale: ko })
            : '오늘'}
        </Text>
        <Text style={styles.subtitle}>
          {data?.menus.length || 0}개의 메뉴
        </Text>
      </View>

      {data?.menus && data.menus.length > 0 ? (
        <View style={styles.menusContainer}>
          {data.menus.map((menu, index) => renderMenu(menu, index))}
        </View>
      ) : (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>오늘의 메뉴가 없습니다</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  dateText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  menusContainer: {
    padding: 15,
  },
  menuCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  menuHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  restaurantName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  mealType: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  menuItems: {
    gap: 8,
  },
  menuItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  menuItemName: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  menuItemPrice: {
    fontSize: 15,
    color: '#666',
    fontWeight: '500',
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
});
