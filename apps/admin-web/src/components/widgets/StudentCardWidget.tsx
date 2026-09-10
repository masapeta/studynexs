import type { StudentCardBlock } from '@/lib/workspace-types';

export function StudentCardWidget(block: StudentCardBlock) {
  const { payload } = block;
  return (
    <section className={block.priority === "primary" ? "sn-workspace sn-workspace--primary" : "sn-workspace sn-workspace--secondary"} style={{ padding: 18 }}>
      <div className="grid gap-3 grid-cols-2">
        <div>
          <div className="text-xs text-muted">Student</div>
          <div className="font-bold text-lg">{payload.display_name}</div>
        </div>
        <div>
          <div className="text-xs text-muted">Class</div>
          <div className="font-medium">{payload.class_label}</div>
        </div>
        <div>
          <div className="text-xs text-muted">Section</div>
          <div className="font-medium">{payload.section_label}</div>
        </div>
        <div>
          <div className="text-xs text-muted">Admission no.</div>
          <div className="font-medium">{payload.admission_no || 'Not available'}</div>
        </div>
      </div>
    </section>
  );
}
