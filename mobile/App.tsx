import { Ionicons } from '@expo/vector-icons';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { DarkTheme, DefaultTheme, NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { useColorScheme } from 'react-native';

import SettingsScreen from './src/screens/SettingsScreen';
import TodayScreen from './src/screens/TodayScreen';
import WeeklyScreen from './src/screens/WeeklyScreen';
import { getThemeColors } from './src/theme/colors';

const Tab = createBottomTabNavigator();

export default function App() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  const colors = getThemeColors(colorScheme);

  const navigationTheme = isDark
    ? {
        ...DarkTheme,
        colors: {
          ...DarkTheme.colors,
          primary: colors.accent,
          background: colors.background,
          card: colors.surface,
          text: colors.textPrimary,
          border: colors.border,
          notification: colors.accent,
        },
      }
    : {
        ...DefaultTheme,
        colors: {
          ...DefaultTheme.colors,
          primary: colors.accent,
          background: colors.background,
          card: colors.surface,
          text: colors.textPrimary,
          border: colors.border,
          notification: colors.accent,
        },
      };

  return (
    <>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <NavigationContainer theme={navigationTheme}>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: ({ focused, color, size }) => {
              let iconName: any = 'home';

              if (route.name === '오늘') {
                iconName = focused ? 'today' : 'today-outline';
              } else if (route.name === '주간') {
                iconName = focused ? 'calendar' : 'calendar-outline';
              } else if (route.name === '설정') {
                iconName = focused ? 'settings' : 'settings-outline';
              }

              return <Ionicons name={iconName} size={size} color={color} />;
            },
            tabBarActiveTintColor: colors.accent,
            tabBarInactiveTintColor: colors.tabInactive,
            tabBarStyle: {
              backgroundColor: colors.surface,
              borderTopColor: colors.border,
            },
            headerStyle: {
              backgroundColor: colors.surface,
            },
            headerTintColor: colors.textPrimary,
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          })}
        >
          <Tab.Screen 
            name="오늘" 
            component={TodayScreen}
            options={{
              title: 'SMU-Bab',
            }}
          />
          <Tab.Screen 
            name="주간" 
            component={WeeklyScreen}
            options={{
              title: '주간 메뉴',
            }}
          />
          <Tab.Screen 
            name="설정" 
            component={SettingsScreen}
            options={{
              title: '설정',
            }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </>
  );
}
