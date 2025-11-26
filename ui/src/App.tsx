import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { NotificationProvider } from './hooks';
import { Dashboard } from './pages/Dashboard';

const App: React.FC = () => {
  return (
    <NotificationProvider>
      <BrowserRouter basename="/ui">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/cost-log" element={<Dashboard />} />
          <Route path="/graveyard" element={<Dashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </NotificationProvider>
  );
};

export default App;
