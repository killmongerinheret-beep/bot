'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from 'react';
import { api, Agency, MonitorTask } from '@/lib/api';
import TaskModal from '@/components/TaskModal';
import TaskCard from '@/components/TaskCard';
import LogsView from '@/components/LogsView';
import Sidebar from '@/components/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  ChevronRight,
  Globe,
  Activity,
  Zap,
  BarChart3,
  Bell,
  Shield
} from 'lucide-react';
import { ModeToggle } from '@/components/ThemeToggle';

import { useUser, UserButton, SignIn } from "@clerk/nextjs";

export default function Dashboard() {
  const { user, isLoaded, isSignedIn } = useUser();
  const [tasks, setTasks] = useState<MonitorTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'matrix' | 'logs' | 'settings'>('matrix');
  const [agencyName, setAgencyName] = useState('');
  const [agencyId, setAgencyId] = useState<number | null>(null);
  const [agencyPlan, setAgencyPlan] = useState<'free' | 'pro' | 'agency'>('free');
  const [taskLimit, setTaskLimit] = useState(2);

  useEffect(() => {
    if (!isLoaded) return;

    if (!isSignedIn) {
      setLoading(false);
      return;
    }

    const initDashboard = async () => {
      try {
        const agency = await api.getMyAgency(user.id, user.primaryEmailAddress?.emailAddress || 'unknown');
        setAgencyName(agency.name);
        setAgencyId(agency.id);
        setAgencyPlan(agency.plan || 'free');
        setTaskLimit(agency.task_limit || 2);

        const tasksData = await api.getTasks(agency.id);
        setTasks(tasksData);
      } catch (error) {
        console.error('Failed to init dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    initDashboard();
    const interval = setInterval(async () => {
      if (agencyId) {
        const tasksData = await api.getTasks(agencyId);
        setTasks(tasksData);
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [isLoaded, isSignedIn, user, agencyId]);

  const refreshTasks = async () => {
    if (!agencyId) return;
    try {
      const tasksData = await api.getTasks(agencyId);
      setTasks(tasksData);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    try {
      const oldTasks = [...tasks];
      setTasks(tasks.filter(t => t.id !== taskId));
      await api.deleteTask(taskId);
    } catch (err) {
      console.error(err);
      alert('Failed to delete task');
      refreshTasks();
    }
  };

  if (!isLoaded) return null;

  if (!isSignedIn) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#050505]">
        <SignIn />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#050505]">
        <div className="flex flex-col items-center gap-6">
          <div className="w-12 h-12 rounded-2xl bg-[#0F0F0F] border border-[#262626] flex items-center justify-center">
            <Activity className="w-6 h-6 text-[#00E37C] animate-pulse" />
          </div>
          <div className="text-xs font-medium uppercase tracking-[0.2em] text-[#888888]">Loading Dashboard</div>
        </div>
      </div>
    );
  }

  // Stats calculation
  const activeTasks = tasks.filter(t => t.is_active).length;
  const totalTasks = tasks.length;

  return (
    <div className="relative flex h-screen overflow-hidden bg-[#050505]">

      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        className="flex-shrink-0 z-20"
      />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto relative">
        <div className="p-8 lg:p-12 max-w-[1600px] mx-auto min-h-full">

          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex justify-between items-start mb-10"
          >
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-[#888888] mb-3">
                <span>Dashboard</span>
                <ChevronRight className="w-3.5 h-3.5" />
                <span className="text-white">Overview</span>
              </div>
              <h1 className="text-3xl font-semibold text-white tracking-tight mb-2">
                {agencyName ? `${agencyName}` : 'Monitoring Console'}
              </h1>
              <p className="text-[#888888] max-w-xl">
                Live status of all automated ticket checking tasks.
              </p>
            </div>

            <div className="flex items-center gap-4">
              {/* Usage Indicator */}
              <div className="px-3 py-1.5 bg-[#0F0F0F] border border-[#262626] rounded-full flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${tasks.length >= taskLimit ? 'bg-red-500' : 'bg-[#00E37C]'}`}></div>
                <span className="text-sm font-medium text-[#888888]">
                  {tasks.length}/{taskLimit} Monitors
                </span>
                {agencyPlan === 'free' && (
                  <span className="text-xs px-1.5 py-0.5 bg-[#00E37C]/10 text-[#00E37C] rounded-full uppercase font-semibold">Trial</span>
                )}
              </div>
              <ModeToggle />
              <UserButton afterSignOutUrl="/" />
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setIsModalOpen(true)}
                className="btn-primary"
              >
                <Plus className="w-4 h-4" />
                <span>New Monitor</span>
              </motion.button>
            </div>
          </motion.div>

          {/* Stats Bar */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10"
          >
            <div className="bento-card !p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#00E37C]/10 rounded-xl flex items-center justify-center">
                  <Activity className="w-5 h-5 text-[#00E37C]" />
                </div>
                <div>
                  <div className="text-2xl font-semibold text-white">{activeTasks}</div>
                  <div className="text-sm text-[#888888]">Active</div>
                </div>
              </div>
            </div>
            <div className="bento-card !p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <div className="text-2xl font-semibold text-white">{totalTasks}</div>
                  <div className="text-sm text-[#888888]">Total Tasks</div>
                </div>
              </div>
            </div>
            {/* Monitor Mode Indicator */}
            <div className="bento-card !p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center">
                  <Shield className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <div className="text-lg font-semibold text-white">Hybrid</div>
                  <div className="text-sm text-[#888888]">Monitor Mode</div>
                </div>
              </div>
            </div>
            {/* Speed Indicator */}
            <div className="bento-card !p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-500/10 rounded-xl flex items-center justify-center">
                  <Zap className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <div className="text-lg font-semibold text-white">10x</div>
                  <div className="text-sm text-[#888888]">Speed Boost</div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Content Area */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === 'matrix' && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-12">
                  {tasks.map((task, i) => (
                    <motion.div
                      key={task.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <TaskCard task={task} onDelete={handleDeleteTask} />
                    </motion.div>
                  ))}
                  {tasks.length === 0 && (
                    <div className="col-span-full bento-card flex flex-col items-center justify-center text-center py-20">
                      <div className="w-16 h-16 bg-[#262626] rounded-full flex items-center justify-center mb-6">
                        <Globe className="w-7 h-7 text-[#888888]" />
                      </div>
                      <h3 className="text-xl font-semibold text-white mb-2">No Active Monitors</h3>
                      <p className="text-[#888888] max-w-md mb-6">
                        Initialize a new monitoring task to begin tracking ticket availability.
                      </p>
                      <button
                        onClick={() => setIsModalOpen(true)}
                        className="btn-primary"
                      >
                        <Plus className="w-4 h-4" />
                        Create First Monitor
                      </button>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'logs' && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <LogsView agencyId={agencyId} />
                </motion.div>
              )}
            </motion.div>
          </AnimatePresence>

        </div>
      </main>

      <TaskModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={refreshTasks}
        agencyId={agencyId}
      />
    </div>
  );
}
