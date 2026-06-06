// ISO3 → ISO2 per le nazionalità calcistiche più comuni (fallback: testo ISO3).
const ISO3_TO_ISO2: Record<string, string> = {
  ITA: 'IT', FRA: 'FR', ESP: 'ES', DEU: 'DE', GER: 'DE', ENG: 'GB', GBR: 'GB',
  PRT: 'PT', POR: 'PT', NLD: 'NL', NED: 'NL', BEL: 'BE', BRA: 'BR', ARG: 'AR',
  HRV: 'HR', CRO: 'HR', SRB: 'RS', POL: 'PL', AUT: 'AT', CHE: 'CH', SUI: 'CH',
  DNK: 'DK', DEN: 'DK', SWE: 'SE', NOR: 'NO', URY: 'UY', URU: 'UY', COL: 'CO',
  USA: 'US', MEX: 'MX', JPN: 'JP', KOR: 'KR', SEN: 'SN', CIV: 'CI', NGA: 'NG',
  MAR: 'MA', GHA: 'GH', CMR: 'CM', EGY: 'EG', ALG: 'DZ', DZA: 'DZ', TUR: 'TR',
  GRC: 'GR', GRE: 'GR', UKR: 'UA', RUS: 'RU', SCO: 'GB', WAL: 'GB', IRL: 'IE',
  CZE: 'CZ', SVK: 'SK', SVN: 'SI', HUN: 'HU', ROU: 'RO', ALB: 'AL', BIH: 'BA',
  CHL: 'CL', PER: 'PE', ECU: 'EC', PAR: 'PY', VEN: 'VE', AUS: 'AU', CAN: 'CA',
};

export function flagEmoji(iso3?: string | null): string {
  if (!iso3) return '🏳️';
  const iso2 = ISO3_TO_ISO2[iso3.toUpperCase()];
  if (!iso2) return '🏳️';
  const base = 0x1f1e6;
  return String.fromCodePoint(base + (iso2.charCodeAt(0) - 65), base + (iso2.charCodeAt(1) - 65));
}
