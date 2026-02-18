// frontend/app/dashboard/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  DollarSign, 
  Activity, 
  BarChart3,
  AlertTriangle,
  CheckCircle 
} from 'lucide-react';
import { api } from '@/lib/auth';

interface DashboardStats {
  balance: number;
  equity: number;
  daily_profit: number;
  win_rate: number;
  active_trades: number;
  daily_loss: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    balance: 0,
    equity: 0,
    daily_profit: 0,
    win_rate: 0,
    active_trades: 0,
    daily_loss: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get('/trading/balance');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400">Welcome back to Revolution X</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Account Balance"
          value={`$${stats.balance.toLocaleString()}`}
          change={`+$${stats.daily_profit.toFixed(2)} today`}
          icon={DollarSign}
          color="gold"
          positive
        />
        <StatCard
          title="Equity"
          value={`$${stats.equity.toLocaleString()}`}
          change="Real-time"
          icon={Activity}
          color="blue"
        />
        <StatCard
          title="Daily P&L"
          value={`${stats.daily_profit >= 0 ? '+' : ''}$${stats.daily_profit.toFixed(2)}`}
          change={`${stats.daily_loss > 0 ? `-$${stats.daily_loss.toFixed(2)} loss` : 'No losses today'}`}
          icon={TrendingUp}
          color={stats.daily_profit >= 0 ? 'emerald' : 'rose'}
          positive={stats.daily_profit >= 0}
        />
        <StatCard
          title="Win Rate"
          value={`${stats.win_rate}%`}
          change="Last 30 days"
          icon={BarChart3}
          color="purple"
        />
        <StatCard
          title="Active Trades"
          value={stats.active_trades.toString()}
          change="Currently open"
          icon={Activity}
          color="orange"
        />
        <StatCard
          title="System Status"
          value="Operational"
          change="All systems normal"
          icon={CheckCircle}
          color="emerald"
          positive
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-revolution-card border border-revolution-border rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <button className="px-4 py-2 bg-gold-500/20 text-gold-400 border border-gold-500/30 rounded-lg hover:bg-gold-500/30 transition-colors">
            New Trade
          </button>
          <button className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors">
            View Positions
          </button>
          <button className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors">
            AI Scanner
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-revolution-card border border-revolution-border rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
          <button className="text-gold-400 text-sm hover:text-gold-300">View All</button>
        </div>
        <div className="space-y-3">
          <ActivityItem
            type="trade"
            title="New position opened"
            description="BUY XAU/USD @ 2,945.50"
            time="2 minutes ago"
            positive
          />
          <ActivityItem
            type="alert"
            title="Take Profit reached"
            description="XAG/USD +$45.20"
            time="15 minutes ago"
            positive
          />
          <ActivityItem
            type="system"
            title="AI Guardian update"
            description="Strategy parameters optimized"
            time="1 hour ago"
          />
        </div>
      </div>
    </div>
  );
}

// Components
function StatCard({ 
  title, 
  value, 
  change, 
  icon: Icon,
  color,
  positive 
}: { 
  title: string;
  value: string;
  change: string;
  icon: any;
  color: string;
  positive?: boolean;
}) {
  const colorClasses: Record<string, string> = {
    gold: 'from-gold-500/20 to-gold-600/20 text-gold-400',
    emerald: 'from-emerald-500/20 to-emerald-600/20 text-emerald-400',
    blue: 'from-blue-500/20 to-blue-600/20 text-blue-400',
    purple: 'from-purple-500/20 to-purple-600/20 text-purple-400',
    orange: 'from-orange-500/20 to-orange-600/20 text-orange-400',
    rose: 'from-rose-500/20 to-rose-600/20 text-rose-400',
  };

  return (
    <div className="bg-revolution-card border border-revolution-border rounded-xl p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-white">{value}</h3>
          <p className={`text-sm mt-1 ${positive ? 'text-emerald-400' : 'text-slate-400'}`}>
            {change}
          </p>
        </div>
        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

function ActivityItem({ 
  type, 
  title, 
  description, 
  time,
  positive 
}: { 
  type: 'trade' | 'alert' | 'system';
  title: string;
  description: string;
  time: string;
  positive?: boolean;
}) {
  const icons = {
    trade: TrendingUp,
    alert: AlertTriangle,
    system: CheckCircle,
  };

  const Icon = icons[type];

  return (
    <div className="flex items-start space-x-3 p-3 bg-revolution-dark/50 rounded-lg">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
        type === 'trade' ? 'bg-gold-500/20 text-gold-400' :
        type === 'alert' ? (positive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400') :
        'bg-blue-500/20 text-blue-400'
      }`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-white font-medium text-sm">{title}</p>
        <p className="text-slate-400 text-sm">{description}</p>
      </div>
      <span className="text-slate-500 text-xs flex-shrink-0">{time}</span>
    </div>
  );
}
