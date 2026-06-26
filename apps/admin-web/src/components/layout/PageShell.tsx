"use client";

type Props = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
};

export function PageShell({ title, subtitle, action, children }: Props) {
  return (
    <div className="gw-page">
      <header className="gw-page-header">
        <div>
          <h1 className="gw-page-title">{title}</h1>
          {subtitle && <p className="gw-page-subtitle">{subtitle}</p>}
        </div>
        {action}
      </header>
      {children}
    </div>
  );
}
