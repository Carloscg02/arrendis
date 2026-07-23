import React from 'react';

interface KPICardProps {
  title: string;
  value: string | number;
  icon: string;
  variant: 'success' | 'danger' | 'info';
}

export const KPICard: React.FC<KPICardProps> = ({ title, value, icon, variant }) => {
  return (
    <div className="kpi-card">
      <div className="kpi-header">
        <span>{icon}</span>
        <span>{title}</span>
      </div>
      <div className={`kpi-value ${variant}`}>
        {value}
      </div>
    </div>
  );
};
