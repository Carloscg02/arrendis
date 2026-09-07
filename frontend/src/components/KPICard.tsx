import React from 'react';

interface KPICardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  variant: 'success' | 'danger' | 'info';
}

export const KPICard: React.FC<KPICardProps> = ({ title, value, icon, variant }) => {
  return (
    <div className="kpi-card">
      <div className="kpi-header">
        {icon && <span className="kpi-icon">{icon}</span>}
        <span className="kpi-title">{title}</span>
      </div>
      <div className={`kpi-value ${variant}`}>
        {value}
      </div>
    </div>
  );
};
