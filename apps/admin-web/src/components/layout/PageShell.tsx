"use client";

type Props = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
};

export function PageShell({ title, subtitle, action, children }: Props) {
  return (
    <div className="gw-page sn-page-shell">
      <header className="card bento-glass sn-page-header-card sn-surface-glass gw-page-header">
        <div className="sn-page-header-card__text">
          <h1 className="sn-page-header-card__title gw-page-title">{title}</h1>
          {subtitle && <p className="sn-page-header-card__subtitle gw-page-subtitle">{subtitle}</p>}
        </div>
        {action ? <div className="sn-page-header-card__actions">{action}</div> : null}
      </header>
      {children}
    </div>
  );
}
