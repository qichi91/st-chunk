import React from 'react';
import { Routes, Route, Outlet } from 'react-router-dom';
import ButtonAppBar from './components/AppBar';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import ContactPage from './pages/ContactPage';
import { Box } from '@mui/material';
import './App.css'
// 

const Layout: React.FC = () => {
  return (
    <>
      <ButtonAppBar />
      <Box component="main" sx={{ p: 3 }}>
        <Outlet />
      </Box>
    </>
  );
}

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="about" element={<AboutPage />} />
        <Route path="contact" element={<ContactPage />} />
        {/* 他のページルートもここに追加できます */}
      </Route>
    </Routes>
  );
}

export default App;