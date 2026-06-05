import { Redirect } from 'expo-router';
import { ActivityIndicator, View } from 'react-native';

import { colors } from '@/src/theme/colors';

export default function Index() {
  // _layout.tsx handles the redirect logic; show a spinner during bootstrap.
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.bg }}>
      <ActivityIndicator size="large" color={colors.accent} testID="splash-spinner" />
    </View>
  );
}
