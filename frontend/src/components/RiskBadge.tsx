import { RiskLevel } from '../api/types';

interface RiskBadgeProps {
  level: RiskLevel;
}

export function RiskBadge({ level }: RiskBadgeProps) {
  const colors = {
    LOW: 'bg-green-100 text-green-800 border-green-200',
    MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    HIGH: 'bg-red-100 text-red-800 border-red-200',
  };

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${colors[level]}`}
    >
      {level}
    </span>
  );
}
