import React from 'react';
import { Box } from '@mui/material';
import ActiveAlertsPanel from './ActiveAlertsPanel';
import HistoricalAlertsList from './HistoricalAlertsList';
import type { DashboardLayoutProps } from '../types';

/**
 * DashboardLayout component provides the main two-section layout
 * for Phase 2: Active alerts at the top, historical alerts below
 */
const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  activeAlerts,
  historicalAlerts,
  activeLoading = false,
  historicalLoading = false,
  activeError = null,
  historicalError = null,
  onRefreshActive,
  onRefreshHistorical,
  onSessionClick,
}) => {
  return (
    <Box sx={{ width: '100%' }}>
      {/* Active Alerts Section - Top Priority */}
      <ActiveAlertsPanel
        sessions={activeAlerts}
        loading={activeLoading}
        error={activeError}
        onRefresh={onRefreshActive}
        onSessionClick={onSessionClick}
      />

      {/* Historical Alerts Section - Below Active */}
      <HistoricalAlertsList
        sessions={historicalAlerts}
        loading={historicalLoading}
        error={historicalError}
        onRefresh={onRefreshHistorical}
        onSessionClick={onSessionClick}
      />
    </Box>
  );
};

export default DashboardLayout; 