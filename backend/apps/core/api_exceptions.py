from rest_framework.exceptions import APIException


class InvalidDueRules(APIException):
    status_code = 400
    default_code = "invalid_due_rules"
    message_key = "errors.maintenance.invalid_due_rules"
    default_detail = "Due thresholds must be strictly increasing."


class TemplateNotFound(APIException):
    status_code = 409
    default_code = "maintenance_template_not_found"
    message_key = "errors.maintenance.template_not_found"
    default_detail = "Maintenance template was not found for the given triple."


class FlightCountersAlreadyApplied(APIException):
    status_code = 409
    default_code = "flight_counters_already_applied"
    message_key = "errors.flight.counters_already_applied"
    default_detail = "Flight counters were already applied."


class InvalidFlightInterval(APIException):
    status_code = 400
    default_code = "invalid_flight_interval"
    message_key = "errors.flight.invalid_interval"
    default_detail = "Flight end time must be after start time."


class InvalidStatusTransition(APIException):
    status_code = 409
    default_code = "invalid_status_transition"
    message_key = "errors.work_order.invalid_transition"
    default_detail = "This status transition is not allowed."


class WorkOrderAlreadyOpen(APIException):
    status_code = 409
    default_code = "work_order_already_open"
    message_key = "errors.work_order.already_open"
    default_detail = "An open work order already exists for this due item."


class WorkOrderAlreadyCompleted(APIException):
    status_code = 409
    default_code = "work_order_already_completed"
    message_key = "errors.work_order.already_completed"
    default_detail = "Work order is already completed."


class TechnicianInactive(APIException):
    status_code = 409
    default_code = "technician_inactive"
    message_key = "errors.technician.inactive"
    default_detail = "Technician is not active."


class TechnicianProfileExists(APIException):
    status_code = 409
    default_code = "technician_profile_exists"
    message_key = "errors.technician.profile_exists"
    default_detail = "This user already has a technician profile."


class TechnicianEmailTaken(APIException):
    status_code = 409
    default_code = "technician_email_taken"
    message_key = "errors.technician.email_taken"
    default_detail = "A user with this email already exists."


class SkillCodeTaken(APIException):
    status_code = 409
    default_code = "skill_code_taken"
    message_key = "errors.technician.skill_code_taken"
    default_detail = "A skill with this code already exists."


class TechnicianSkillExists(APIException):
    status_code = 409
    default_code = "technician_skill_exists"
    message_key = "errors.technician.skill_exists"
    default_detail = "This skill is already assigned to the technician."


class InvalidCertificationDates(APIException):
    status_code = 400
    default_code = "invalid_certification_dates"
    message_key = "errors.technician.invalid_dates"
    default_detail = "Expiry date must be on or after the issue or certification date."


class InvalidFailureDates(APIException):
    status_code = 400
    default_code = "invalid_failure_dates"
    message_key = "errors.failure.invalid_dates"
    default_detail = "Resolved time cannot be before the occurrence time."


class InvalidFailureComponent(APIException):
    status_code = 400
    default_code = "invalid_failure_component"
    message_key = "errors.failure.invalid_component"
    default_detail = "Component does not belong to the selected UAV."


class InvalidFailureWorkOrder(APIException):
    status_code = 400
    default_code = "invalid_failure_work_order"
    message_key = "errors.failure.invalid_work_order"
    default_detail = "Work order does not belong to the selected UAV."


class InvalidFailureDowntime(APIException):
    status_code = 400
    default_code = "invalid_failure_downtime"
    message_key = "errors.failure.invalid_downtime"
    default_detail = "Downtime hours cannot be negative."


class FailureModeCodeTaken(APIException):
    status_code = 409
    default_code = "failure_mode_code_taken"
    message_key = "errors.failure.mode_code_taken"
    default_detail = "A failure mode with this code already exists."


class FmeaCodeTaken(APIException):
    status_code = 409
    default_code = "fmea_code_taken"
    message_key = "errors.fmea.code_taken"
    default_detail = "An FMEA with this code already exists."


class FmeaLocked(APIException):
    status_code = 409
    default_code = "fmea_locked"
    message_key = "errors.fmea.locked"
    default_detail = "Approved FMEA records cannot be edited."


class FmeaAlreadyApproved(APIException):
    status_code = 409
    default_code = "fmea_already_approved"
    message_key = "errors.fmea.already_approved"
    default_detail = "FMEA is already approved."


class InvalidFmeaScores(APIException):
    status_code = 400
    default_code = "invalid_fmea_scores"
    message_key = "errors.fmea.invalid_scores"
    default_detail = "Severity, occurrence and detection must be integers from 1 to 10."


class RcmCodeTaken(APIException):
    status_code = 409
    default_code = "rcm_code_taken"
    message_key = "errors.rcm.code_taken"
    default_detail = "An RCM analysis with this code already exists."


class RcmLocked(APIException):
    status_code = 409
    default_code = "rcm_locked"
    message_key = "errors.rcm.locked"
    default_detail = "Approved RCM records cannot be edited."


class RcmAlreadyApproved(APIException):
    status_code = 409
    default_code = "rcm_already_approved"
    message_key = "errors.rcm.already_approved"
    default_detail = "RCM is already approved."


class RcmRationaleRequired(APIException):
    status_code = 400
    default_code = "rcm_rationale_required"
    message_key = "errors.rcm.rationale_required"
    default_detail = "A rationale is required when overriding the decision tree."


class RcmNotApproved(APIException):
    status_code = 409
    default_code = "rcm_not_approved"
    message_key = "errors.rcm.not_approved"
    default_detail = "Only an approved RCM can be copied to a template."


class RcmStrategyConflict(APIException):
    status_code = 409
    default_code = "rcm_strategy_conflict"
    message_key = "errors.rcm.strategy_conflict"
    default_detail = "RCM items do not share a single strategy to copy."


class InvalidReliabilityScope(APIException):
    status_code = 400
    default_code = "reliability_invalid_scope"
    message_key = "errors.reliability.invalid_scope"
    default_detail = "Scope must be fleet, class, uav or component."


class InvalidReliabilityRange(APIException):
    status_code = 400
    default_code = "reliability_invalid_range"
    message_key = "errors.reliability.invalid_range"
    default_detail = "The reliability date range is invalid."


class ReliabilityScopeNotFound(APIException):
    status_code = 404
    default_code = "reliability_scope_not_found"
    message_key = "errors.reliability.scope_not_found"
    default_detail = "The reliability scope target was not found."


class PartNumberTaken(APIException):
    status_code = 409
    default_code = "part_number_taken"
    message_key = "errors.part.number_taken"
    default_detail = "A part with this number already exists."


class PartIncompatible(APIException):
    status_code = 409
    default_code = "part_incompatible"
    message_key = "errors.part.incompatible"
    default_detail = "This part is not compatible with the UAV or component."


class InsufficientStock(APIException):
    status_code = 409
    default_code = "insufficient_stock"
    message_key = "errors.part.insufficient_stock"
    default_detail = "Stock quantity is not enough for this issue."


class InvalidPartQuantity(APIException):
    status_code = 400
    default_code = "invalid_part_quantity"
    message_key = "errors.part.invalid_quantity"
    default_detail = "Quantity must be greater than zero."


class InvalidCostAmount(APIException):
    status_code = 400
    default_code = "invalid_cost_amount"
    message_key = "errors.cost.invalid_amount"
    default_detail = "Cost amounts cannot be negative."


class DocumentTargetRequired(APIException):
    status_code = 400
    default_code = "document_target_required"
    message_key = "errors.document.target_required"
    default_detail = "A document must be linked to a UAV, component, template or work order."


class DocumentFileRequired(APIException):
    status_code = 400
    default_code = "document_file_required"
    message_key = "errors.document.file_required"
    default_detail = "Upload a file or provide a file name and storage key."


class DocumentFileTooLarge(APIException):
    status_code = 400
    default_code = "document_file_too_large"
    message_key = "errors.document.file_too_large"
    default_detail = "The uploaded file exceeds the size limit."


class DocumentFileTypeInvalid(APIException):
    status_code = 400
    default_code = "document_file_type_invalid"
    message_key = "errors.document.file_type_invalid"
    default_detail = "This file type is not allowed."


class DocumentFileMissing(APIException):
    status_code = 409
    default_code = "document_file_missing"
    message_key = "errors.document.file_missing"
    default_detail = "No file is stored for this document."


class DocumentStorageKeyTaken(APIException):
    status_code = 409
    default_code = "document_storage_key_taken"
    message_key = "errors.document.storage_key_taken"
    default_detail = "This storage key is already in use."


class UserEmailTaken(APIException):
    status_code = 409
    default_code = "user_email_taken"
    message_key = "errors.user.email_taken"
    default_detail = "A user with this email already exists."


class LastAdminRequired(APIException):
    status_code = 409
    default_code = "last_admin_required"
    message_key = "errors.user.last_admin"
    default_detail = "The last active administrator cannot be removed."


class InvalidSettingValue(APIException):
    status_code = 400
    default_code = "invalid_setting_value"
    message_key = "errors.settings.invalid_value"
    default_detail = "The setting value is invalid."


class InvalidReportType(APIException):
    status_code = 400
    default_code = "invalid_report_type"
    message_key = "errors.report.invalid_type"
    default_detail = "Unknown report type."


class ReportUavRequired(APIException):
    status_code = 400
    default_code = "report_uav_required"
    message_key = "errors.report.uav_required"
    default_detail = "This report requires a UAV."


class InvalidCurrentPassword(APIException):
    status_code = 400
    default_code = "invalid_current_password"
    message_key = "errors.auth.invalid_current_password"
    default_detail = "Current password is incorrect."


class InvalidLocale(APIException):
    status_code = 400
    default_code = "invalid_locale"
    message_key = "errors.auth.invalid_locale"
    default_detail = "Locale must be tr, en or az."


class InvalidNewPassword(APIException):
    status_code = 400
    default_code = "invalid_new_password"
    message_key = "errors.auth.invalid_new_password"
    default_detail = "The new password does not meet the requirements."


class InvalidResetToken(APIException):
    status_code = 400
    default_code = "invalid_reset_token"
    message_key = "errors.auth.invalid_reset_token"
    default_detail = "Password reset token is invalid or expired."


class ComponentTypeInactive(APIException):
    status_code = 409
    default_code = "component_type_inactive"
    message_key = "errors.component.type_inactive"
    default_detail = "Component type is not active."


class ComponentSerialTaken(APIException):
    status_code = 409
    default_code = "component_serial_taken"
    message_key = "errors.component.serial_taken"
    default_detail = "This serial number is already installed."


class ComponentNotInstalled(APIException):
    status_code = 409
    default_code = "component_not_installed"
    message_key = "errors.component.not_installed"
    default_detail = "Component is not currently installed."


class ComponentHasOpenWorkOrder(APIException):
    status_code = 409
    default_code = "component_open_work_order"
    message_key = "errors.component.open_work_order"
    default_detail = "Open work orders must be closed before removal."


class ComponentUavRetired(APIException):
    status_code = 409
    default_code = "component_uav_retired"
    message_key = "errors.component.uav_retired"
    default_detail = "Components cannot be installed or removed on a retired UAV."


class InvalidComponentDates(APIException):
    status_code = 400
    default_code = "invalid_component_dates"
    message_key = "errors.component.invalid_dates"
    default_detail = "Removal time cannot be before the installation time."
