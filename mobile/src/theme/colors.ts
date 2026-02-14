import { ColorSchemeName } from 'react-native';

export type AppThemeColors = {
  background: string;
  surface: string;
  surfaceSecondary: string;
  border: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  accent: string;
  tabInactive: string;
  badgeText: string;
};

const lightColors: AppThemeColors = {
  background: '#f5f5f5',
  surface: '#ffffff',
  surfaceSecondary: '#f5f5f5',
  border: '#e0e0e0',
  textPrimary: '#333333',
  textSecondary: '#666666',
  textMuted: '#999999',
  accent: '#007AFF',
  tabInactive: '#8e8e93',
  badgeText: '#ffffff',
};

const darkColors: AppThemeColors = {
  background: '#000000',
  surface: '#1c1c1e',
  surfaceSecondary: '#2c2c2e',
  border: '#3a3a3c',
  textPrimary: '#f2f2f7',
  textSecondary: '#c7c7cc',
  textMuted: '#8e8e93',
  accent: '#0A84FF',
  tabInactive: '#8e8e93',
  badgeText: '#ffffff',
};

export function getThemeColors(colorScheme: ColorSchemeName): AppThemeColors {
  return colorScheme === 'dark' ? darkColors : lightColors;
}