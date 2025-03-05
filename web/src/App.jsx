import React, { useState } from 'react';
import { Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Tabs, Tab, Box, Container } from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import dayjs from 'dayjs';

// 导入页面组件（稍后创建）
import IndexMarket from './pages/IndexMarket';
import IndustrySector from './pages/IndustrySector';
import ConceptSector from './pages/ConceptSector';
import StockMarket from './pages/StockMarket';

const menuItems = [
  { label: '指数行情', path: '/', component: IndexMarket },
  { label: '行业板块行情', path: '/industry', component: IndustrySector },
  { label: '概念板块行情', path: '/concept', component: ConceptSector },
  { label: '股票行情', path: '/stock', component: StockMarket },
];

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedDate, setSelectedDate] = useState(dayjs());

  // 获取当前路径对应的Tab索引
  const currentTab = menuItems.findIndex(item => 
    location.pathname === '/' ? item.path === '/' : location.pathname.startsWith(item.path)
  );

  const handleTabChange = (event, newValue) => {
    navigate(menuItems[newValue].path);
  };

  const handleDateChange = (newDate) => {
    setSelectedDate(newDate);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Tabs 
            value={currentTab !== -1 ? currentTab : 0}
            onChange={handleTabChange}
            textColor="inherit"
            indicatorColor="secondary"
          >
            {menuItems.map((item, index) => (
              <Tab key={index} label={item.label} />
            ))}
          </Tabs>
          <DatePicker
            value={selectedDate}
            onChange={handleDateChange}
            format="YYYY-MM-DD"
            sx={{
              bgcolor: 'white',
              borderRadius: 1,
              '& .MuiInputBase-root': {
                height: 40,
              },
            }}
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 3 }}>
        <Routes>
          {menuItems.map((item, index) => (
            <Route
              key={index}
              path={item.path}
              element={
                <item.component date={selectedDate} />
              }
            />
          ))}
        </Routes>
      </Container>
    </Box>
  );
}

export default App;