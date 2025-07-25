import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

/**
 * data: [{ date: '2025-07-19', open, high, low, close, volume, market_cap }, ...]
 */
const StockChart = ({ data }) => {
  // Recharts는 문자열로 된 date축도 잘 그리지만,
  // 포맷팅이 필요하면 data.map(d=>({...d, date: d.date.slice(5)}))처럼 가공하세요.
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid stroke="#eee" strokeDasharray="5 5" />
        <XAxis dataKey="date" />
        <YAxis domain={['auto', 'auto']} />
        <Tooltip
          formatter={(value, name) => {
            if (name === 'close') return [`${value.toLocaleString()}원`, '종가'];
            return [value, name];
          }}
          labelFormatter={label => `날짜: ${label}`}
        />
        <Line
          type="monotone"
          dataKey="close"
          stroke="#3f51b5"
          dot={false}
          name="종가"
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default StockChart;
