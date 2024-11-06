import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import SearchPage from './SearchPage';
import SelectionPage from './SelectionPage';
import TripPlanningPage from './TripPlanningPage';  // 确保创建这个文件

const App = () => {
  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Router>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/selection" element={<SelectionPage />} />
          <Route path="/plan" element={<TripPlanningPage />} />
        </Routes>
      </Router>
    </LocalizationProvider>
  );
};

export default App;