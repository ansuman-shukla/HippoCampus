import React from 'react';
import { motion } from 'framer-motion';
import LoaderPillars from '../../components/LoaderPillars';
import type { AnalyticsCardsProps } from '../types/admin.types';
import { formatCurrency, formatPercentage } from '../utils/adminHelpers';

/**
 * Analytics Cards Component
 * Displays key subscription and user metrics in card format
 */
const AnalyticsCards: React.FC<AnalyticsCardsProps> = ({ analytics, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, index) => (
          <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-200 flex justify-center items-center min-h-[80px]">
            <LoaderPillars />
          </div>
        ))}
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-red-50 rounded-lg p-4 border border-red-200 col-span-full">
          <p className="text-red-800 font-SansMono400 text-sm text-center">
            Failed to load analytics data
          </p>
        </div>
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Users',
      value: analytics.total_users.toLocaleString(),
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-800',
      valueColor: 'text-blue-900',
      icon: '👥'
    },
    {
      title: 'Pro Users',
      value: analytics.pro_users.toLocaleString(),
      subtitle: `${analytics.free_users.toLocaleString()} Free`,
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-800',
      valueColor: 'text-green-900',
      icon: '⭐'
    },
    {
      title: 'Conversion Rate',
      value: formatPercentage(analytics.conversion_rate),
      subtitle: `${analytics.active_subscriptions} active`,
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      textColor: 'text-purple-800',
      valueColor: 'text-purple-900',
      icon: '📈'
    },
    {
      title: 'Revenue Est.',
      value: formatCurrency(analytics.revenue_estimate),
      subtitle: 'Monthly',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-800',
      valueColor: 'text-yellow-900',
      icon: '💰'
    }
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"
    >
      {cards.map((card, index) => (
        <motion.div
          key={card.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className={`${card.bgColor} rounded-lg p-4 border ${card.borderColor} hover:shadow-md transition-shadow`}
        >
          <div className="flex items-center justify-between mb-2">
            <h3 className={`font-SansMono400 text-sm ${card.textColor}`}>
              {card.title}
            </h3>
            <span className="text-lg">{card.icon}</span>
          </div>
          
          <div className="space-y-1">
            <p className={`text-2xl font-NanumMyeongjo ${card.valueColor}`}>
              {card.value}
            </p>
            {card.subtitle && (
              <p className={`text-xs font-SansMono400 ${card.textColor} opacity-80`}>
                {card.subtitle}
              </p>
            )}
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
};

export default AnalyticsCards; 