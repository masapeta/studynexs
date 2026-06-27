"use client";

export type FilterPillTab = {
  key: string;
  label: string;
  count?: number;
};

type Props = {
  tabs: FilterPillTab[];
  activeKey: string;
  onChange: (key: string) => void;
  ariaLabel: string;
};

export function FilterPillBar({ tabs, activeKey, onChange, ariaLabel }: Props) {
  return (
    <div className="sn-filter-pills" role="tablist" aria-label={ariaLabel}>
      {tabs.map((tab) => {
        const active = activeKey === tab.key;
        const text =
          tab.count !== undefined ? `${tab.label} (${tab.count})` : tab.label;
        return (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={active}
            className={`btn sn-filter-pill${active ? " btn-primary" : " btn-ghost"}`}
            onClick={() => onChange(tab.key)}
          >
            {text}
          </button>
        );
      })}
    </div>
  );
}
