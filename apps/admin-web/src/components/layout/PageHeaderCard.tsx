"use client";

type Props = {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
};

export function PageHeaderCard({ title, subtitle, children }: Props) {
  return (
    <div className="card bento-glass sn-page-header-card sn-surface-glass">
      <div className="sn-page-header-card__text">
        <h1 className="sn-page-header-card__title">{title}</h1>
        {subtitle && <p className="sn-page-header-card__subtitle">{subtitle}</p>}
      </div>
      {children ? <div className="sn-page-header-card__actions">{children}</div> : null}
    </div>
  );
}
