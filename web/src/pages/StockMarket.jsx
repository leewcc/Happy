import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TablePagination } from '@mui/material';
import axios from 'axios';

const columns = [
  { id: 'stock_code', label: '股票代码', minWidth: 100 },
  { id: 'stock_name', label: '股票名称', minWidth: 130 },
  { id: 'close_price', label: '收盘价', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'open_price', label: '开盘价', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'high_price', label: '最高价', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'low_price', label: '最低价', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'previous_close_price', label: '昨收价', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'price_change_rate', label: '涨跌幅(%)', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'turnover_amount', label: '成交额(元)', minWidth: 120, format: (value) => value.toLocaleString() },
  { id: 'trading_volume', label: '成交量', minWidth: 120, format: (value) => value.toLocaleString() },
  { id: 'turnover_rate', label: '换手率(%)', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'total_mv', label: '总市值(亿)', minWidth: 120, format: (value) => (value / 100000000).toFixed(2) },
  { id: 'circ_mv', label: '流通市值(亿)', minWidth: 120, format: (value) => (value / 100000000).toFixed(2) },
  { id: 'pe', label: '市盈率', minWidth: 100, format: (value) => value?.toFixed(2) || '-' },
  { id: 'pb', label: '市净率', minWidth: 100, format: (value) => value?.toFixed(2) || '-' },
];

function StockMarket({ date }) {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const formattedDate = date.format('YYYY-MM-DD');
        const response = await axios.get(`/api/stock_market?date=${formattedDate}`);
        setData(response.data);
      } catch (error) {
        console.error('获取股票行情数据失败:', error);
      }
    };

    if (date) {
      fetchData();
    }
  }, [date]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <TableContainer sx={{ maxHeight: 'calc(100vh - 200px)' }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  style={{ minWidth: column.minWidth }}
                >
                  {column.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((row) => {
                return (
                  <TableRow hover tabIndex={-1} key={row.stock_code}>
                    {columns.map((column) => {
                      const value = row[column.id];
                      return (
                        <TableCell key={column.id}>
                          {column.format && typeof value === 'number'
                            ? column.format(value)
                            : value}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 25, 100]}
        component="div"
        count={data.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        labelRowsPerPage="每页行数:"
      />
    </Paper>
  );
}

export default StockMarket;