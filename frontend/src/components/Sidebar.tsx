'use client';

import React from 'react';
import {
    LayoutDashboard,
    Terminal,
    Settings,
    ShieldCheck,
    Zap
} from 'lucide-react';
import { useRouter } from 'next/navigation';

type TabType = 'matrix' | 'logs' | 'settings';

interface SidebarProps {
    activeTab: 'matrix' | 'logs' | 'settings';
    setActiveTab?: (tab: any) => void;
    className?: string;
}

export default function Sidebar({ activeTab, setActiveTab, className = '' }: SidebarProps) {
    const router = useRouter();

    return (
        <aside className={`w-72 min-w-[18rem] bg-[#0F0F0F] border-r border-[#262626] flex flex-col p-6 ${className}`}>
            {/* Logo */}
            <div className="flex items-center gap-3 mb-12 px-2">
                <div className="w-10 h-10 rounded-xl bg-[#00E37C] flex items-center justify-center">
                    <Zap size={20} className="text-[#050505]" />
                </div>
                <div>
                    <h1 className="text-lg font-semibold text-white tracking-tight leading-none">HYDRA</h1>
                    <p className="text-[10px] font-medium text-[#888888] uppercase tracking-widest mt-1">Enterprise</p>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1">
                <SidebarItem
                    active={activeTab === 'matrix'}
                    onClick={() => router.push('/dashboard')}
                    icon={<LayoutDashboard className="w-5 h-5" />}
                    label="Overview"
                />
                <SidebarItem
                    active={activeTab === 'logs'}
                    onClick={() => router.push('/dashboard/logs')}
                    icon={<Terminal className="w-5 h-5" />}
                    label="Logs"
                />

                <div className="pt-6 pb-2">
                    <div className="w-full h-px bg-[#262626]" />
                </div>

                <SidebarItem
                    active={activeTab === 'settings'}
                    onClick={() => router.push('/dashboard/settings')}
                    icon={<Settings className="w-5 h-5" />}
                    label="Settings"
                />
            </nav>

        </aside>
    );
}

function SidebarItem({
    icon,
    label,
    active = false,
    onClick
}: {
    icon: React.ReactNode;
    label: string;
    active?: boolean;
    onClick?: () => void;
}) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-4 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${active
                ? 'bg-[#262626] text-white'
                : 'text-[#888888] hover:text-white hover:bg-[#1a1a1a]'
                }`}
        >
            <span className={active ? 'text-[#00E37C]' : 'text-[#888888]'}>{icon}</span>
            {label}
        </button>
    );
}
