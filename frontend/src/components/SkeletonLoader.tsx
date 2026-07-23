import React from 'react';

interface SkeletonLoaderProps {
  variant: 'card' | 'table' | 'kpi';
  count?: number;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ variant, count = 1 }) => {
  const skeletons = Array.from({ length: count }, (_, i) => (
    <div key={i} className={`skeleton skeleton-${variant}`}></div>
  ));

  if (variant === 'card') {
    return <div className="property-grid">{skeletons}</div>;
  }
  
  if (variant === 'kpi') {
    return <div className="kpi-grid">{skeletons}</div>;
  }

  return <>{skeletons}</>;
};
