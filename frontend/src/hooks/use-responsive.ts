import { useWindowDimensions } from 'react-native';

export const BREAKPOINT_DESKTOP = 760;

/** Layout responsive: web largo (desktop) → tabella; stretto/mobile → card. */
export function useResponsive() {
  const { width } = useWindowDimensions();
  return { width, isDesktop: width >= BREAKPOINT_DESKTOP };
}
