export type WorkspaceMode = "read";

export type WorkspaceMessageTone = "informative" | "cautious" | "blocked";

export type WorkspaceVerificationStatus =
  | "verified"
  | "stale"
  | "missing"
  | "conflicting"
  | "requires_approval";

export type WorkspaceRetentionClass = "ephemeral" | "audit" | "support_case";

export type WorkspaceBlockPriority = "primary" | "secondary";
export type WorkspaceMetricStatus = "normal" | "warning" | "risk";
export type WorkspaceActionType = "navigate";
export type WorkspaceBlockType =
  | "student_card"
  | "metric_row"
  | "table"
  | "citation_list"
  | "action_list"
  | "error_state";

export interface WorkspaceTurnRequest {
  mode: "read";
  text: string;
  session_id?: string | null;
}

export interface WorkspaceMessage {
  title: string;
  summary: string;
  tone: WorkspaceMessageTone;
}

export interface WorkspaceVerification {
  status: WorkspaceVerificationStatus;
  checked_at: string | null;
  source_systems: string[];
}

export interface WorkspaceApproval {
  required: boolean;
  reason: string | null;
}

export interface WorkspaceRetention {
  retention_class: WorkspaceRetentionClass;
}

export interface WorkspaceSpeech {
  speakable_summary: string;
  language: string;
}

export interface WorkspaceTelemetry {
  used_model: string | null;
  used_fallback: boolean;
  tool_calls: number;
  tool_failures: number;
}

export interface WorkspaceWarning {
  code: string;
  detail: string;
}

export interface WorkspaceError {
  code: string;
  detail: string;
}

export interface WorkspaceCitation {
  label: string;
  source_type: string;
  source_id: string;
  summary: string;
}

export interface WorkspaceAction {
  label: string;
  action_type: WorkspaceActionType;
  href: string;
  permission_gate: string;
  enabled: boolean;
}

export interface StudentCardPayload {
  student_id: string;
  display_name: string;
  class_label: string;
  section_label: string;
  admission_no: string | null;
}

export interface WorkspaceMetricItem {
  label: string;
  value: string | number;
  status: WorkspaceMetricStatus;
}

export interface MetricRowPayload {
  items: WorkspaceMetricItem[];
}

export interface WorkspaceTableColumn {
  key: string;
  label: string;
}

export type WorkspaceTableCell = string | number | boolean | null;

export interface TablePayload {
  columns: WorkspaceTableColumn[];
  rows: Array<Record<string, WorkspaceTableCell>>;
  empty_message: string;
}

export interface CitationListPayload {
  items: WorkspaceCitation[];
}

export interface ActionListPayload {
  items: WorkspaceAction[];
}

export interface ErrorStatePayload {
  code: string;
  headline: string;
  detail: string;
  retryable: boolean;
}

export interface WorkspaceBlockBase {
  id: string;
  title: string | null;
  priority: WorkspaceBlockPriority;
}

export interface StudentCardBlock extends WorkspaceBlockBase {
  type: "student_card";
  payload: StudentCardPayload;
}

export interface MetricRowBlock extends WorkspaceBlockBase {
  type: "metric_row";
  payload: MetricRowPayload;
}

export interface TableBlock extends WorkspaceBlockBase {
  type: "table";
  payload: TablePayload;
}

export interface CitationListBlock extends WorkspaceBlockBase {
  type: "citation_list";
  payload: CitationListPayload;
}

export interface ActionListBlock extends WorkspaceBlockBase {
  type: "action_list";
  payload: ActionListPayload;
}

export interface ErrorStateBlock extends WorkspaceBlockBase {
  type: "error_state";
  payload: ErrorStatePayload;
}

export type WorkspaceBlock =
  | StudentCardBlock
  | MetricRowBlock
  | TableBlock
  | CitationListBlock
  | ActionListBlock
  | ErrorStateBlock;

export interface WorkspaceResponse {
  schema_version: "workspace.response.v1";
  request_id: string;
  correlation_id: string;
  mode: WorkspaceMode;
  message: WorkspaceMessage;
  blocks: WorkspaceBlock[];
  citations: WorkspaceCitation[];
  actions: WorkspaceAction[];
  verification: WorkspaceVerification;
  warnings: WorkspaceWarning[];
  errors: WorkspaceError[];
  approval: WorkspaceApproval;
  data_retention: WorkspaceRetention;
  speech: WorkspaceSpeech | null;
  telemetry: WorkspaceTelemetry;
}