import { StudentCardWidget } from '@/components/widgets/StudentCardWidget';

export const COMPONENT_REGISTRY: Record<string, React.ComponentType<any>> = {
  // Map block_type to frontend components for the dynamic Canvas
  student_card: StudentCardWidget,
  metric_row: () => <div>Not implemented: metric_row</div>,
  table: () => <div>Not implemented: table</div>,
  citation_list: () => <div>Not implemented: citation_list</div>,
  action_list: () => <div>Not implemented: action_list</div>,
  error_state: () => <div>Not implemented: error_state</div>,
  // action: ActionPanelWidget, // Placeholder for Phase 1
};
