import type { ActionBlock } from '@/lib/workspace-types';
import { useState } from 'react';
import { createWorkspaceTurn } from '@/lib/workspace-client';

export function ActionCardWidget(props: ActionBlock & { onUpdate: () => void }) {
  const { label, target_tool, onUpdate } = props;
  const [submitting, setSubmitting] = useState(false);

  const handleAction = async () => {
     setSubmitting(true);
     try {
         // Invoke the tool via the workspace engine
         await createWorkspaceTurn({ 
             mode: "read", // Phase 0 constraint: we keep the write capability gated
             text: `Execute tool ${target_tool}`,
         });
         onUpdate();
     } catch (e) {
         console.error("Action failed", e);
     } finally {
         setSubmitting(false);
     }
  };

  return (
    <div className="sn-workspace sn-workspace--primary p-5 rounded-xl border border-line">
       <h3 className="font-bold text-lg mb-4">{label}</h3>
       <button 
         className="btn btn-accent w-full"
         disabled={submitting}
         onClick={async (e) => {
             e.preventDefault();
             await handleAction();
         }}
       >
         {submitting ? "Processing..." : label}
       </button>
    </div>
  );
}
