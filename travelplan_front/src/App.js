import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SearchPage from './SearchPage';
import SelectionPage from './SelectionPage';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/selection" element={<SelectionPage />} />
      </Routes>
    </Router>
  );
};

export default App;