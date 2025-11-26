import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { NotificationProvider } from './hooks';
import { Dashboard, CostLogPage, GraveyardPage, SettingsPage, DomainDetailPage } from './pages';

const App: React.FC = () => {
  return (
    <NotificationProvider>
      <BrowserRouter basename="/ui">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/cost-log" element={<CostLogPage />} />
          <Route path="/graveyard" element={<GraveyardPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/domain/:name" element={<DomainDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </NotificationProvider>
  );
};

export default App;
