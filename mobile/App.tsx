import { Ionicons } from '@expo/vector-icons';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import React from 'react';

import SettingsScreen from './src/screens/SettingsScreen';
import TodayScreen from './src/screens/TodayScreen';
import WeeklyScreen from './src/screens/WeeklyScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <>
      <StatusBar style="auto" />
      <NavigationContainer>
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
            tabBarActiveTintColor: '#007AFF',
            tabBarInactiveTintColor: 'gray',
            headerStyle: {
              backgroundColor: '#007AFF',
            },
            headerTintColor: '#fff',
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
