import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
} from 'react-native';
import * as Notifications from 'expo-notifications';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export default function SettingsScreen() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [breakfastNotif, setBreakfastNotif] = useState(false);
  const [lunchNotif, setLunchNotif] = useState(false);
  const [dinnerNotif, setDinnerNotif] = useState(false);

  useEffect(() => {
    checkNotificationPermission();
  }, []);

  const checkNotificationPermission = async () => {
    const { status } = await Notifications.getPermissionsAsync();
    setNotificationsEnabled(status === 'granted');
  };

  const requestNotificationPermission = async () => {
    const { status } = await Notifications.requestPermissionsAsync();
    setNotificationsEnabled(status === 'granted');
    
    if (status !== 'granted') {
      Alert.alert('알림 권한', '알림 권한이 거부되었습니다. 설정에서 권한을 허용해주세요.');
    }
  };

  const scheduleNotification = async (
    title: string,
    body: string,
    hour: number,
    minute: number
  ) => {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        sound: true,
      },
      trigger: {
        hour,
        minute,
        repeats: true,
      },
    });
  };

  const handleBreakfastNotif = async (value: boolean) => {
    setBreakfastNotif(value);
    if (value && notificationsEnabled) {
      await scheduleNotification(
        '아침 메뉴 알림',
        '오늘의 아침 메뉴를 확인해보세요!',
        7,
        30
      );
    }
  };

  const handleLunchNotif = async (value: boolean) => {
    setLunchNotif(value);
    if (value && notificationsEnabled) {
      await scheduleNotification(
        '점심 메뉴 알림',
        '오늘의 점심 메뉴를 확인해보세요!',
        11,
        30
      );
    }
  };

  const handleDinnerNotif = async (value: boolean) => {
    setDinnerNotif(value);
    if (value && notificationsEnabled) {
      await scheduleNotification(
        '저녁 메뉴 알림',
        '오늘의 저녁 메뉴를 확인해보세요!',
        17,
        0
      );
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>알림 설정</Text>
        
        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>알림 허용</Text>
            <Text style={styles.settingDescription}>
              학식 메뉴 알림을 받으시겠습니까?
            </Text>
          </View>
          <Switch
            value={notificationsEnabled}
            onValueChange={(value) => {
              if (value) {
                requestNotificationPermission();
              } else {
                setNotificationsEnabled(false);
              }
            }}
          />
        </View>

        {notificationsEnabled && (
          <>
            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>아침 알림</Text>
                <Text style={styles.settingDescription}>오전 7:30</Text>
              </View>
              <Switch value={breakfastNotif} onValueChange={handleBreakfastNotif} />
            </View>

            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>점심 알림</Text>
                <Text style={styles.settingDescription}>오전 11:30</Text>
              </View>
              <Switch value={lunchNotif} onValueChange={handleLunchNotif} />
            </View>

            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>저녁 알림</Text>
                <Text style={styles.settingDescription}>오후 5:00</Text>
              </View>
              <Switch value={dinnerNotif} onValueChange={handleDinnerNotif} />
            </View>
          </>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>앱 정보</Text>
        
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>버전</Text>
          <Text style={styles.infoValue}>1.0.0</Text>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>학교</Text>
          <Text style={styles.infoValue}>상명대학교</Text>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>개발자</Text>
          <Text style={styles.infoValue}>SMU-Bab Team</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>지원</Text>
        
        <TouchableOpacity 
          style={styles.linkButton}
          onPress={() => Alert.alert('문의', '개발 중인 기능입니다.')}
        >
          <Text style={styles.linkText}>문의하기</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.linkButton}
          onPress={() => Alert.alert('리뷰', '개발 중인 기능입니다.')}
        >
          <Text style={styles.linkText}>리뷰 작성</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.linkButton}
          onPress={() => Alert.alert('오픈소스', '개발 중인 기능입니다.')}
        >
          <Text style={styles.linkText}>오픈소스 라이선스</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  section: {
    backgroundColor: '#fff',
    marginTop: 20,
    paddingVertical: 10,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#f5f5f5',
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  settingInfo: {
    flex: 1,
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 13,
    color: '#666',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  infoLabel: {
    fontSize: 16,
    color: '#333',
  },
  infoValue: {
    fontSize: 16,
    color: '#666',
  },
  linkButton: {
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  linkText: {
    fontSize: 16,
    color: '#007AFF',
  },
});
