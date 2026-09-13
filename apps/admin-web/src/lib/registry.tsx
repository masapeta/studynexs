import { StudentCardWidget } from '@/components/widgets/StudentCardWidget';
import { ActionCardWidget } from '@/components/widgets/ActionCardWidget';
import { MetricRowWidget } from '@/components/widgets/MetricRowWidget';
import { TableWidget } from '@/components/widgets/TableWidget';
import { CitationListWidget } from '@/components/widgets/CitationListWidget';
import { ActionListWidget } from '@/components/widgets/ActionListWidget';
import { ErrorStateWidget } from '@/components/widgets/ErrorStateWidget';

export const COMPONENT_REGISTRY: Record<string, React.ComponentType<any>> = {
  student_card: StudentCardWidget,
  metric_row: MetricRowWidget,
  table: TableWidget,
  citation_list: CitationListWidget,
  action_list: ActionListWidget,
  error_state: ErrorStateWidget,
  action: ActionCardWidget,
};
