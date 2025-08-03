
import React, { useRef, useEffect, useState } from "react";
import { ChartCanvas, Chart } from "react-financial-charts";
import {
  CandlestickSeries,
  XAxis,
  YAxis,
  CrossHairCursor,
  MouseCoordinateX,
  MouseCoordinateY,
  EdgeIndicator,
  OHLCTooltip,
  CurrentCoordinate,
} from "react-financial-charts";
import { timeParse, timeFormat } from "d3-time-format";
import * as d3 from "d3";

const parseDate = timeParse("%Y-%m-%d");

function toChartData(data) {
  return data.map(d => ({
    ...d,
    date: parseDate(d.date),
  }));
}

const StockCandleChart = ({ data, height = 300, margin = { left: 50, right: 70, top: 20, bottom: 30 } }) => {
  const containerRef = useRef(null);
  const [width, setWidth] = useState(900);

  useEffect(() => {
    function updateWidth() {
      if (containerRef.current) {
        setWidth(containerRef.current.offsetWidth || 900);
      }
    }
    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  if (!data || data.length === 0) return null;
  const chartData = toChartData(data);

  return (
    <div ref={containerRef} style={{ width: "100%", height }}>
      <ChartCanvas
        height={height}
        width={width}
        ratio={1}
        margin={margin}
        data={chartData}
        seriesName="가격"
        xAccessor={d => d.date}
        xScale={d3.scaleTime()}
        xExtents={[
          chartData[chartData.length - 30]?.date || chartData[0].date,
          chartData[chartData.length - 1].date
        ]}
      >
        <Chart id={1} yExtents={d => [d.high, d.low]}>
          <XAxis showGridLines tickFormat={timeFormat("%m/%d")} />
          <YAxis showGridLines tickFormat={v => v.toLocaleString()} />
          <MouseCoordinateX displayFormat={timeFormat("%Y-%m-%d")} />
          <MouseCoordinateY displayFormat={v => v.toLocaleString()} />
          <CandlestickSeries />
          <EdgeIndicator itemType="last" orient="right" edgeAt="right" yAccessor={d => d.close} fill={d => d.close > d.open ? "#6BA583" : "#F44336"} />
          <OHLCTooltip origin={[8, 16]} />
          <CurrentCoordinate yAccessor={d => d.close} fill="#3f51b5" />
        </Chart>
        <CrossHairCursor />
      </ChartCanvas>
    </div>
  );
};

export default StockCandleChart;
