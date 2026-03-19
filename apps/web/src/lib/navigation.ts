export interface NavigationItem {
  href: string;
  label: string;
  description: string;
}

export const primaryNavigation: NavigationItem[] = [
  {
    href: '/dashboard',
    label: 'Dashboard',
    description: 'Live race snapshot with positions, weather and map',
  },
  {
    href: '/telemetry',
    label: 'Telemetry',
    description: 'Driver telemetry charts and race control feed',
  },
  {
    href: '/predictions',
    label: 'Predictions',
    description: 'Pit, position and strategy forecasts from live context',
  },
  {
    href: '/drivers',
    label: 'Drivers',
    description: 'Live roster plus historical driver profiles from F1DB',
  },
  {
    href: '/circuits',
    label: 'Circuits',
    description: 'Circuit database, recent races and track weather',
  },
  {
    href: '/fantasy',
    label: 'Fantasy',
    description: 'AI-powered team builder, predictions and value plays',
  },
  {
    href: '/historical',
    label: 'Historical',
    description: 'FastF1 session analysis with telemetry and comparisons',
  },
];

export const secondaryNavigation: NavigationItem[] = [
  {
    href: '/settings',
    label: 'Settings',
    description: 'Local experience controls and environment references',
  },
  {
    href: '/help',
    label: 'Help',
    description: 'Platform notes, data sources and model behavior',
  },
];
