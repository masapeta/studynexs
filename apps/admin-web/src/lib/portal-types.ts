/** Shared types for parent/student portal pages. */

export interface PortalChild {
  student_id: string;
  name: string;
  class_label: string;
  roll_no?: string | null;
  attendance_pct?: number | null;
  fee_pending: number;
  weak_topic_count: number;
}

export interface PortalContext {
  portal: string;
  role: string;
  children?: PortalChild[];
  student_id?: string;
  student_name?: string;
  class_label?: string;
}

export interface ParentFeeRecord {
  id: string;
  fee_type?: string | null;
  amount: number;
  status: string;
  due_date?: string | null;
}

export interface ParentChildFees {
  student_id: string;
  name: string;
  records: ParentFeeRecord[];
}

export interface MasteryTopic {
  topic: string;
  mastery_pct: number;
}

export type WeakTopic = MasteryTopic & { subject: string };

export interface MasterySubject {
  subject_name: string;
  topics?: MasteryTopic[];
}

export interface MasteryData {
  subjects?: MasterySubject[];
}

export interface ChildSummary {
  student_id: string;
  name: string;
  class_label: string;
  roll_no?: string | null;
  attendance_pct?: number | null;
  fee_pending: number;
  weak_topic_count?: number;
}

export interface ParentWeakTopic {
  subject_name: string;
  topic: string;
  topic_display: string;
  mastery_pct: number;
}

export interface ParentFeedback {
  topic: string;
  topic_display: string;
  subject_name: string;
  narrative: string;
  notified_at?: string | null;
}

export interface ParentChildProgress extends ChildSummary {
  weak_topics: ParentWeakTopic[];
  feedbacks: ParentFeedback[];
}
