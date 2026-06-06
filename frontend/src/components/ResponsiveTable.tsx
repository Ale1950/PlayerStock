import { Ionicons } from '@expo/vector-icons';
import { type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { useResponsive } from '@/src/hooks/use-responsive';
import { useTheme } from '@/src/theme/ThemeProvider';
import { borderW, spacing, typography } from '@/src/theme/spacing';

export interface Column<T> {
  key: string;
  label: string;
  width?: number;        // larghezza fissa colonna (px); assente = flex
  flex?: number;
  align?: 'left' | 'right' | 'center';
  sortable?: boolean;
  render: (item: T) => ReactNode;
}

export type SortState = { key: string; dir: 'asc' | 'desc' } | null;

/**
 * Primitivo RESPONSIVE riusabile: TABELLA a colonne su desktop, CARD su mobile.
 * Stessa sorgente dati; il chiamante fornisce le colonne (desktop) e `renderCard`
 * (mobile). Header colonne ordinabili. Tutto via token (scuro/chiaro).
 */
export function ResponsiveTable<T>({
  data, columns, renderCard, keyExtractor, sort, onSort, header, rowStyle, onRowPress,
}: {
  data: T[];
  columns: Column<T>[];
  renderCard: (item: T) => ReactNode;
  keyExtractor: (item: T) => string;
  sort?: SortState;
  onSort?: (key: string) => void;
  header?: ReactNode;
  rowStyle?: (item: T) => ViewStyle | undefined;
  onRowPress?: (item: T) => void;
}) {
  const { colors } = useTheme();
  const { isDesktop } = useResponsive();

  if (!isDesktop) {
    return (
      <View style={{ gap: spacing.md }}>
        {header}
        {data.map((item) => <View key={keyExtractor(item)}>{renderCard(item)}</View>)}
      </View>
    );
  }

  const cellStyle = (c: Column<T>) => ([
    c.width ? { width: c.width } : { flex: c.flex ?? 1 },
    { alignItems: c.align === 'right' ? 'flex-end' : c.align === 'center' ? 'center' : 'flex-start' } as const,
  ]);

  return (
    <View>
      {header}
      <View style={[styles.table, { borderColor: colors.border, backgroundColor: colors.surface }]}>
        {/* header row */}
        <View style={[styles.headRow, { borderBottomColor: colors.border, backgroundColor: colors.surfaceAlt }]}>
          {columns.map((c) => {
            const active = sort?.key === c.key;
            const inner = (
              <View style={styles.headCell}>
                <Text style={[typography.caption, { color: active ? colors.cyan : colors.muted }]}>{c.label}</Text>
                {c.sortable && (
                  <Ionicons
                    name={active ? (sort?.dir === 'asc' ? 'caret-up' : 'caret-down') : 'swap-vertical'}
                    size={12} color={active ? colors.cyan : colors.muted}
                  />
                )}
              </View>
            );
            return c.sortable && onSort ? (
              <Pressable key={c.key} onPress={() => onSort(c.key)} style={cellStyle(c)}>{inner}</Pressable>
            ) : (
              <View key={c.key} style={cellStyle(c)}>{inner}</View>
            );
          })}
        </View>
        {/* body rows */}
        {data.map((item, i) => {
          const rowChildren = columns.map((c) => <View key={c.key} style={cellStyle(c)}>{c.render(item)}</View>);
          const base = [styles.bodyRow, { borderBottomColor: colors.border }, i % 2 === 1 && { backgroundColor: colors.surfaceAlt + '55' }, rowStyle?.(item)];
          return onRowPress ? (
            <Pressable key={keyExtractor(item)} onPress={() => onRowPress(item)}
              style={({ pressed }) => [...base, styles.clickable, pressed && { backgroundColor: colors.surfaceAlt }]}>
              {rowChildren}
            </Pressable>
          ) : (
            <View key={keyExtractor(item)} style={base}>{rowChildren}</View>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  table: { borderWidth: borderW, borderRadius: 14, overflow: 'hidden' },
  headRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderBottomWidth: 1, gap: spacing.sm },
  headCell: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  bodyRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderBottomWidth: 1, gap: spacing.sm },
  clickable: { cursor: 'pointer' } as ViewStyle,
});
