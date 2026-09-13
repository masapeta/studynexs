import type { ActionBlock } from '@/lib/workspace-types';
import { useState } from 'react';
import { createWorkspaceTurn } from '@/lib/workspace-client';

export function ActionCardWidget(props: ActionBlock & { onUpdate: () => void }) {
  const { label, payload_schema, onUpdate } = props;
  const [submitting, setSubmitting] = useState(false);

  const handleAction = async () => {
    setSubmitting(true);
    try {
      const flagId = payload_schema?.flag_id;
      await createWorkspaceTurn({ 
          mode: "read", 
          text: `mark evidence for ${flagId} as reviewed`,
      });
      onUpdate();
    } catch (e) {
      console.error("Action failed", e);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card" style={{ margin: 0, padding: 20 }}>
      <h3 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", marginBottom: 16 }}>
        {label}
      </h3>
      <button
        type="button"
        className="btn btn-primary"
        disabled={submitting}
        onClick={async (e) => {
          e.preventDefault();
          await handleAction();
        }}
      >
        {submitting ? "Processing…" : label}
      </button>
    </div>
  );
}
