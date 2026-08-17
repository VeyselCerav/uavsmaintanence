"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, PieChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([BarChart, PieChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

type Slice = { name: string; value: number; color: string };

export function StatusPieChart({ title, slices }: { title: string; slices: Slice[] }) {
  return (
    <EChartOption
      option={{
        tooltip: { trigger: "item" },
        legend: { bottom: 0, textStyle: { fontSize: 11 } },
        series: [
          {
            name: title,
            type: "pie",
            radius: ["42%", "68%"],
            itemStyle: { borderRadius: 4, borderColor: "#fff", borderWidth: 2 },
            label: { show: false },
            data: slices.map((slice) => ({
              name: slice.name,
              value: slice.value,
              itemStyle: { color: slice.color },
            })),
          },
        ],
      }}
    />
  );
}

export function GroupedBarChart({
  categories,
  series,
}: {
  categories: string[];
  series: { name: string; data: number[]; color: string }[];
}) {
  return (
    <EChartOption
      option={{
        tooltip: { trigger: "axis" },
        legend: { bottom: 0, textStyle: { fontSize: 11 } },
        grid: { left: 36, right: 12, top: 16, bottom: 36 },
        xAxis: { type: "category", data: categories, axisLabel: { fontSize: 11 } },
        yAxis: { type: "value", minInterval: 1 },
        series: series.map((item) => ({
          name: item.name,
          type: "bar",
          data: item.data,
          itemStyle: { color: item.color, borderRadius: [4, 4, 0, 0] },
        })),
      }}
    />
  );
}

function EChartOption({ option }: { option: echarts.EChartsCoreOption }) {
  const ref = useRef<HTMLDivElement>(null);
  const serialized = JSON.stringify(option);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    chart.setOption(JSON.parse(serialized));
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
    };
  }, [serialized]);

  return <div ref={ref} className="h-64 w-full" />;
}
