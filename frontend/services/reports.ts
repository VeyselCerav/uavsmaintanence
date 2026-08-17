import { getAccessToken } from "@/lib/auth";
import { ApiClientError, type ApiError } from "@/services/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const PDF_TYPES = [
  "uav-history",
  "maintenance",
  "work-order",
  "failure",
  "fmea",
  "rcm",
  "fleet",
  "reliability",
  "cost",
  "approach-comparison",
] as const;

export const XLSX_TYPES = [
  "uavs",
  "components",
  "flights",
  "maintenance",
  "failures",
  "fmea",
  "rcm",
  "costs",
  "approach-comparison",
] as const;

export type PdfReportType = (typeof PDF_TYPES)[number];
export type XlsxReportType = (typeof XLSX_TYPES)[number];

function filenameFromDisposition(header: string | null, fallback: string) {
  if (!header) return fallback;
  const match = /filename="([^"]+)"/.exec(header);
  return match?.[1] ?? fallback;
}

export async function downloadReport(
  kind: "pdf" | "xlsx",
  reportType: string,
  params: Record<string, string> = {},
) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) search.set(key, value);
  });
  const query = search.toString() ? `?${search.toString()}` : "";
  const token = getAccessToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}/reports/${kind}/${reportType}/${query}`, { headers });
  if (!response.ok) {
    const payload = (await response.json()) as ApiError;
    const error = payload.error ?? {
      code: "ERROR",
      message_key: "errors.generic",
      details: {},
    };
    throw new ApiClientError(error.code, error.message_key, error.details);
  }
  const blob = await response.blob();
  const filename = filenameFromDisposition(
    response.headers.get("Content-Disposition"),
    `${reportType}.${kind === "pdf" ? "pdf" : "xlsx"}`,
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
