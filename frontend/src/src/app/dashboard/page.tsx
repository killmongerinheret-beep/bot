'use client';

import { useEffect, useState } from 'react';
import { api, Agency, MonitorTask } from '@/lib/api';
import TaskModal from '@/components/TaskModal';
import TaskCard from '@/components/TaskCard';
import Sidebar from '@/components/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  ChevronRight,
  Globe,
  Terminal,
  Activity,
  LogOut
} from 'lucide-react';

import { useUser, UserButton, SignIn } from "@clerk/nextjs";

export default function Dashboard() {
  const { user, isLoaded, isSignedIn } = useUser();
  const [tasks, setTasks] = useState<MonitorTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'matrix'>('matrix');
  const [agencyName, setAgencyName] = useState('');
  const [agencyId, setAgencyId] = useState<number | null>(null);

  useEffect(() => {
    if (!isLoaded) return;

    if (!isSignedIn) {
      setLoading(false);
      return;
    }

    const initDashboard = async () => {
      try {
        // Fetch or Create Agency for this User
        const agency = await api.getMyAgency(user.id, user.primaryEmailAddress?.emailAddress || 'unknown');
        setAgencyName(agency.name);
        setAgencyId(agency.id);

        // Fetch tasks
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
  }, [isLoaded, isSignedIn, user, agencyId]); // Dependency on agencyId for polling

  const refreshTasks = async () => {
    if (!agencyId) return;
    try {
      const tasksData = await api.getTasks(agencyId);
      setTasks(tasksData);
    } catch (err) {
      console.error(err);
    }
  };

  if (!isLoaded) return null;

  if (!isSignedIn) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#FDFDFD]">
        <SignIn />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#FDFDFD]">
        <div className="flex flex-col items-center gap-6">
          <div className="w-12 h-12 rounded-2xl bg-white shadow-lg flex items-center justify-center">
            <Activity className="w-6 h-6 text-blue-500 animate-pulse" />
          </div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-gray-400">Loading Dashboard</div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex h-screen overflow-hidden bg-[#FDFDFD] selection:bg-blue-100 selection:text-blue-900">

      {/* Sidebar sibling - Flex Item (Fixed width, full height) */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        className="flex-shrink-0 z-20"
      />

      {/* Main Content sibling - Flex Grow (Scrollable) */}
      <main className="flex-1 overflow-y-auto relative">
        <div className="p-8 lg:p-16 max-w-[1800px] mx-auto min-h-full">

          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex justify-between items-end mb-12"
          >
            <div>
              <div className="flex items-center gap-2 text-sm font-bold text-gray-400 mb-4 uppercase tracking-widest">
                <span>Dashboard</span>
                <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
                <span className="text-gray-900 capitalize">Overview</span>
              </div>
              <h1 className="text-4xl font-black text-gray-900 tracking-tight mb-3">
                {agencyName ? `${agencyName} Portal` : 'Monitoring Console'}
              </h1>
              <p className="text-lg text-gray-500 font-medium max-w-xl leading-relaxed">
                Live status of all automated ticket checking tasks for your agency.
              </p>
            </div>

            <div className="flex gap-4">
              <div className="flex items-center">
                <UserButton afterSignOutUrl="/" />
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsModalOpen(true)}
                className="px-8 py-4 bg-gray-900 hover:bg-gray-800 text-white rounded-full font-bold shadow-xl shadow-gray-200 transition-colors flex items-center gap-3"
              >
                <Plus className="w-5 h-5" />
                <span>New Monitor</span>
              </motion.button>
            </div>
          </motion.div>

          {/* Content Area with Transitions */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === 'matrix' && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8 lg:gap-10 pb-12 px-2">
                  {tasks.map((task, i) => (
                    <motion.div
                      key={task.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                    >
                      <TaskCard task={task} />
                    </motion.div>
                  ))}
                  {tasks.length === 0 && (
                    <div className="col-span-full bg-white rounded-[2.5rem] p-24 border border-gray-100 shadow-sm flex flex-col items-center justify-center text-center">
                      <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-6">
                        <Globe className="w-8 h-8 text-gray-400" />
                      </div>
                      <h3 className="text-2xl font-bold text-gray-900 mb-2">No Active Monitors</h3>
                      <p className="text-gray-500 max-w-md">Initialize a new monitoring task to begin tracking ticket availability.</p>
                    </div>
                  )}
                </div>
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
