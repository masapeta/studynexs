import type { StudentCardBlock } from '@/lib/workspace-types';

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)" }}>{value}</div>
    </div>
  );
}

export function StudentCardWidget(block: StudentCardBlock) {
  const { payload } = block;
  return (
    <section className="card" style={{ margin: 0, padding: 18 }}>
      <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
        <Field label="Student" value={payload.display_name} />
        <Field label="Class" value={payload.class_label} />
        <Field label="Section" value={payload.section_label} />
        <Field label="Admission no." value={payload.admission_no || "Not available"} />
      </div>
    </section>
  );
}
