from __future__ import annotations

from datetime import date

from apps.core.api_exceptions import InvalidReportType
from apps.reports.datasets import (
    PDF_ROW_LIMIT,
    XLSX_ROW_LIMIT,
    ReportDocument,
    ReportQuery,
    components_table,
    costs_table,
    failures_table,
    fleet_table,
    flights_table,
    fmea_table,
    maintenance_table,
    rcm_table,
    reliability_table,
    uav_history_tables,
    work_orders_table,
    approach_comparison_tables,
)
from apps.reports.enums import PdfReportType, XlsxReportType
from apps.reports.labels import labels_for
from apps.reports.renderers import render_pdf, render_xlsx

PDF_BUILDERS = {
    PdfReportType.UAV_HISTORY: ("uav_history", uav_history_tables),
    PdfReportType.MAINTENANCE: ("maintenance", lambda q: [maintenance_table(q)]),
    PdfReportType.WORK_ORDER: ("work_order", lambda q: [work_orders_table(q)]),
    PdfReportType.FAILURE: ("failure", lambda q: [failures_table(q)]),
    PdfReportType.FMEA: ("fmea", lambda q: [fmea_table(q)]),
    PdfReportType.RCM: ("rcm", lambda q: [rcm_table(q)]),
    PdfReportType.FLEET: ("fleet", lambda q: [fleet_table(q)]),
    PdfReportType.RELIABILITY: ("reliability", lambda q: [reliability_table(q)]),
    PdfReportType.COST: ("cost", lambda q: [costs_table(q)]),
    PdfReportType.APPROACH_COMPARISON: ("approach_comparison", approach_comparison_tables),
}

XLSX_BUILDERS = {
    XlsxReportType.UAVS: ("uavs", lambda q: [fleet_table(q)]),
    XlsxReportType.COMPONENTS: ("components", lambda q: [components_table(q)]),
    XlsxReportType.FLIGHTS: ("flights", lambda q: [flights_table(q)]),
    XlsxReportType.MAINTENANCE: ("maintenance", lambda q: [maintenance_table(q)]),
    XlsxReportType.FAILURES: ("failures", lambda q: [failures_table(q)]),
    XlsxReportType.FMEA: ("fmea", lambda q: [fmea_table(q)]),
    XlsxReportType.RCM: ("rcm", lambda q: [rcm_table(q)]),
    XlsxReportType.COSTS: ("costs", lambda q: [costs_table(q)]),
    XlsxReportType.APPROACH_COMPARISON: ("approach_comparison", approach_comparison_tables),
}


class ReportService:
    @staticmethod
    def catalog() -> dict:
        return {
            "pdf": list(PdfReportType.values),
            "xlsx": list(XlsxReportType.values),
        }

    @classmethod
    def build_pdf(cls, *, report_type: str, params, locale: str) -> tuple[bytes, str]:
        if report_type not in PDF_BUILDERS:
            raise InvalidReportType()
        document = cls._document(report_type, params, locale, PDF_ROW_LIMIT, PDF_BUILDERS)
        return render_pdf(document), f"{document.filename_stem}.pdf"

    @classmethod
    def build_xlsx(cls, *, report_type: str, params, locale: str) -> tuple[bytes, str]:
        if report_type not in XLSX_BUILDERS:
            raise InvalidReportType()
        document = cls._document(report_type, params, locale, XLSX_ROW_LIMIT, XLSX_BUILDERS)
        return render_xlsx(document), f"{document.filename_stem}.xlsx"

    @staticmethod
    def _document(
        report_type: str,
        params,
        locale: str,
        limit: int,
        builders: dict,
    ) -> ReportDocument:
        key, builder = builders[report_type]
        query = ReportQuery(params, locale=locale, limit=limit)
        tables = builder(query)
        demo = any(table.demo for table in tables)
        labels = labels_for(query.locale)
        stamp = date.today().isoformat()
        return ReportDocument(
            filename_stem=f"{report_type}-{stamp}",
            title=labels.get(key, report_type),
            locale=query.locale,
            tables=tables,
            demo=demo,
        )
