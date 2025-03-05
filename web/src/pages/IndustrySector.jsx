import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TablePagination } from '@mui/material';
import axios from 'axios';

const columns = [
  { id: 'ts_code', label: '板块代码', minWidth: 100 },
  { id: 'name', label: '板块名称', minWidth: 130 },
  { id: 'close', label: '收盘点位', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'open', label: '开盘点位', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'high', label: '最高点位', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'low', label: '最低点位', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'pre_close', label: '昨收点位', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'avg_price', label: '平均价', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'price_change', label: '涨跌点', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'pct_change', label: '涨跌幅(%)', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'vol', label: '成交量', minWidth: 120, format: (value) => value.toLocaleString() },
  { id: 'turnover_rate', label: '换手率(%)', minWidth: 100, format: (value) => value.toFixed(2) },
  { id: 'total_mv', label: '总市值(亿)', minWidth: 120, format: (value) => (value / 100000000).toFixed(2) },
  { id: 'float_mv', label: '流通市值(亿)', minWidth: 120, format: (value) => (value / 100000000).toFixed(2) },
];

function IndustrySector({ date }) {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const formattedDate = date.format('YYYYMMDD');
        const response = await axios.get(`/api/industry_sector?date=${formattedDate}`);
        setData(response.data);
      } catch (error) {
        console.error('获取行业板块行情数据失败:', error);
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
                  <TableRow hover tabIndex={-1} key={row.ts_code}>
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

export default IndustrySector;