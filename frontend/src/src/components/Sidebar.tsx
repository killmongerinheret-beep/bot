'use client';

import {
    LayoutDashboard,
    LogOut,
    Users,
    Globe,
    Settings,
    ShieldCheck,
    Server,
    Activity,
    Terminal
} from 'lucide-react';

interface SidebarProps {
    activeTab: 'matrix' | 'logs' | 'settings';
    setActiveTab?: (tab: string) => void;
    className?: string;
}

export default function Sidebar({ activeTab, setActiveTab, className = '' }: SidebarProps) {
    const isClient = typeof window !== 'undefined';
    return (
        <aside className={`w-72 min-w-[18rem] bg-white border-r border-gray-100 flex flex-col p-8 ${className}`}>
            <div className="flex items-center gap-4 mb-12 px-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-blue-200 shadow-lg flex items-center justify-center text-white font-bold text-lg">V</div>
                <div>
                    <h1 className="text-lg font-bold text-gray-900 tracking-tight leading-none">VaticanPro</h1>
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">Enterprise</p>
                </div>
            </div>

            {/* Replaced the original nav with the new structure */}
            <div className="flex-1 px-4 py-8 space-y-2">
                <SidebarItem
                    active={activeTab === 'matrix'}
                    onClick={() => isClient && (window.location.href = '/dashboard')}
                    icon={<Activity className="w-5 h-5" />}
                    label="Overview"
                />
                <SidebarItem
                    active={activeTab === 'logs'}
                    onClick={() => isClient && (window.location.href = '/dashboard/logs')}
                    icon={<Terminal className="w-5 h-5" />}
                    label="Logs"
                />
                <div className="pt-4 pb-2">
                    <div className="w-full h-px bg-white/5" />
                </div>
                <SidebarItem
                    active={activeTab === 'settings'}
                    onClick={() => isClient && (window.location.href = '/dashboard/settings')}
                    icon={<Settings className="w-5 h-5" />}
                    label="Settings"
                />
            </div>
            {/* The following div was part of the original nav and seems to be misplaced in the instruction snippet.
                It's being re-added here to maintain the "System" heading structure if intended.
                However, the instruction's snippet seems to replace the entire nav.
                Given the instruction's intent to add specific links, I'm interpreting the new div block as the primary navigation.
                The "System" heading and subsequent items from the original nav are being removed as they are not present in the new structure.
            */}
            {/* Original content removed:
            <nav className="flex-1 space-y-2">
                <SidebarItem
                    icon={<LayoutDashboard className="w-5 h-5" />}
                    label="Overview"
                    active={activeTab === 'matrix'}
                    onClick={() => setActiveTab('matrix')}
                />

                <div className="pt-8 mb-4 px-6 text-[10px] font-bold text-gray-400 uppercase tracking-widest">System</div>
                <SidebarItem icon={<Globe className="w-5 h-5" />} label="Network" />
                <SidebarItem icon={<Settings className="w-5 h-5" />} label="Settings" />
            </nav>
            */}

            <div className="mt-auto">
                <div className="bg-emerald-50 rounded-2xl p-5 border border-emerald-100">
                    <div className="flex items-center gap-3 mb-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                        <span className="text-[10px] font-bold uppercase text-emerald-800 tracking-widest">Secure</span>
                    </div>
                    <p className="text-[11px] text-emerald-700 font-medium">
                        TLS Spoofing Active
                    </p>
                </div>
            </div>
        </aside >
    );
}

function SidebarItem({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-4 px-6 py-4 rounded-2xl text-sm font-bold transition-all duration-200 ${active
                ? 'bg-gray-100 text-gray-900 shadow-sm'
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                }`}
        >
            <span className={active ? 'text-gray-900' : 'text-gray-400'}>{icon}</span>
            {label}
        </button>
    );
}
