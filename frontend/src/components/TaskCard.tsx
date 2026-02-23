'use client';

import { useState, useEffect } from 'react';
import { MonitorTask, api } from '@/lib/api';
import { motion } from 'framer-motion';
import {
    Clock,
    Calendar,
    Play,
    Trash2,
    ExternalLink,
    Zap,
    Globe,
    Check
} from 'lucide-react';

interface TaskCardProps {
    task: MonitorTask;
    onDelete?: (id: number) => Promise<void>;
}

export default function TaskCard({ task, onDelete }: TaskCardProps) {
    const [timeLeft, setTimeLeft] = useState<string>('...');

    // Status colors
    const getStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'available': return 'bg-[#00E37C]';
            case 'sold_out': return 'bg-[#FF4D4D]';
            case 'closed': return 'bg-[#888888]';
            case 'error': return 'bg-orange-500';
            default: return 'bg-blue-500';
        }
    };

    const getStatusBadgeStyle = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'available':
                return 'bg-[#00E37C]/10 text-[#00E37C] border-[#00E37C]/20';
            case 'sold_out':
                return 'bg-[#FF4D4D]/10 text-[#FF4D4D] border-[#FF4D4D]/20';
            case 'closed':
                return 'bg-[#888888]/10 text-[#888888] border-[#888888]/20';
            case 'error':
                return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
            default:
                return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
        }
    };

    // Countdown logic
    useEffect(() => {
        const interval = setInterval(() => {
            if (!task.last_checked) {
                setTimeLeft('Pending');
                return;
            }
            const lastDate = new Date(task.last_checked);
            const checkInt = task.check_interval || 60;
            const nextDate = new Date(lastDate.getTime() + checkInt * 1000);
            const now = new Date();
            const diff = nextDate.getTime() - now.getTime();

            if (diff <= 0) {
                setTimeLeft('Now');
            } else {
                const mins = Math.floor(diff / 60000);
                const secs = Math.floor((diff % 60000) / 1000);
                setTimeLeft(`${mins}:${secs < 10 ? '0' : ''}${secs}`);
            }
        }, 1000);
        return () => clearInterval(interval);
    }, [task.last_checked, task.check_interval]);

    // Parse last result summary for additional info
    const getLastCheckInfo = () => {
        if (!task.last_result_summary) return null;
        try {
            const summary = JSON.parse(task.last_result_summary);
            return {
                checkMethod: summary.updates?.[Object.keys(summary.updates || {})[0]]?.[0]?.check_method || 'browser',
                responseTime: summary.response_time_ms,
                totalSlots: summary.updates ? Object.values(summary.updates).flat().reduce((acc: number, item: any) => 
                    acc + (item.slots?.length || 0), 0) : 0
            };
        } catch {
            return null;
        }
    };

    // Get available slots from latest_check
    const getAvailableSlots = (): string[] => {
        if (!task.latest_check?.details?.slots) return [];
        const slots = task.latest_check.details.slots;
        // slots can be array of strings or array of objects with 'time' property
        return slots.map((slot: any) => {
            if (typeof slot === 'string') return slot;
            return slot.time || slot;
        }).filter(Boolean);
    };

    const checkInfo = getLastCheckInfo();
    const availableSlots = getAvailableSlots();
    const isAvailable = task.last_status?.toLowerCase() === 'available';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -2, transition: { duration: 0.2 } }}
            className="bento-card group"
        >
            {/* Status Bar */}
            <div className={`h-1 w-full -mt-8 -mx-8 mb-6 ${getStatusColor(task.last_status || 'checking')}`}
                style={{ width: 'calc(100% + 64px)' }} />

            {/* Header */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-lg font-semibold text-white mb-1">{task.area_name}</h3>
                    <p className="text-xs text-[#888888] uppercase tracking-wider">
                        {task.site === 'vatican' ? 'Vatican Museums' : 'Colosseum'}
                    </p>
                </div>
                <div className="flex flex-col items-end gap-2">
                    <span className={`px-3 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${getStatusBadgeStyle(task.last_status || 'checking')}`}>
                        {task.last_status?.replace('_', ' ') || 'Pending'}
                    </span>
                    {/* Check Method Badge */}
                    {checkInfo && (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium border ${
                            checkInfo.checkMethod === 'headless' || checkInfo.checkMethod === 'god_tier_headless'
                                ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                                : 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                        }`}>
                            {checkInfo.checkMethod === 'headless' || checkInfo.checkMethod === 'god_tier_headless' ? (
                                <><Zap className="w-3 h-3" /> Headless</>
                            ) : (
                                <><Globe className="w-3 h-3" /> Browser</>
                            )}
                        </span>
                    )}
                </div>
            </div>

            {/* Ticket Info (if available) */}
            {(task.ticket_name || task.ticket_id) && (
                <div className="mb-4 p-3 bg-[#1a1a1a] rounded-lg border border-[#262626]">
                    <div className="text-xs text-[#888888] uppercase tracking-wider mb-1">Selected Ticket</div>
                    <div className="text-sm text-white font-medium truncate">{task.ticket_name || 'Unknown Ticket'}</div>
                    {task.ticket_id && (
                        <div className="text-xs text-[#888888] font-mono mt-0.5">ID: {task.ticket_id}</div>
                    )}
                    {task.language && (
                        <div className="mt-2">
                            <span className="px-2 py-0.5 rounded-full text-[10px] bg-[#262626] text-[#888888]">
                                Language: {task.language}
                            </span>
                        </div>
                    )}
                </div>
            )}

            {/* Dates */}
            <div className="mb-4">
                <div className="flex items-center gap-2 text-[#888888] text-xs mb-3">
                    <Calendar className="w-3.5 h-3.5" />
                    <span className="uppercase tracking-wider font-medium">Target Dates</span>
                </div>
                <div className="flex flex-wrap gap-2">
                    {task.dates.slice(0, 4).map((d, i) => (
                        <span
                            key={i}
                            className="bg-[#1a1a1a] border border-[#262626] text-[#888888] px-3 py-1.5 rounded-lg text-xs font-mono"
                        >
                            {d}
                        </span>
                    ))}
                    {task.dates.length > 4 && (
                        <span className="bg-[#1a1a1a] border border-[#262626] text-[#888888] px-3 py-1.5 rounded-lg text-xs">
                            +{task.dates.length - 4} more
                        </span>
                    )}
                </div>
            </div>

            {/* Available Slots - NEW SECTION */}
            {isAvailable && availableSlots.length > 0 && (
                <div className="mb-4 p-3 bg-[#00E37C]/5 rounded-lg border border-[#00E37C]/20">
                    <div className="flex items-center gap-2 text-[#00E37C] text-xs mb-3">
                        <Check className="w-3.5 h-3.5" />
                        <span className="uppercase tracking-wider font-medium">
                            Available Slots ({availableSlots.length})
                        </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {availableSlots.slice(0, 6).map((slot, i) => (
                            <span
                                key={i}
                                className="bg-[#00E37C]/10 border border-[#00E37C]/20 text-[#00E37C] px-2.5 py-1 rounded-lg text-xs font-mono"
                            >
                                {slot}
                            </span>
                        ))}
                        {availableSlots.length > 6 && (
                            <span className="text-[#00E37C]/70 text-xs px-1 py-1">
                                +{availableSlots.length - 6} more
                            </span>
                        )}
                    </div>
                </div>
            )}

            {/* Footer */}
            <div className="flex justify-between items-center pt-4 border-t border-[#262626]">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 text-xs text-[#888888]">
                        <div className={`w-2 h-2 rounded-full ${timeLeft === 'Now' ? 'bg-[#00E37C] animate-pulse' : 'bg-[#888888]'}`} />
                        <Clock className="w-3 h-3" />
                        <span className="font-mono text-white">{timeLeft}</span>
                    </div>
                    {/* Response Time Indicator */}
                    {checkInfo?.responseTime && (
                        <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                            checkInfo.responseTime < 1000 
                                ? 'bg-emerald-500/10 text-emerald-400' 
                                : 'bg-yellow-500/10 text-yellow-400'
                        }`}>
                            {checkInfo.responseTime < 1000 
                                ? `⚡ ${checkInfo.responseTime}ms` 
                                : `⏱️ ${(checkInfo.responseTime / 1000).toFixed(1)}s`
                            }
                        </span>
                    )}
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={() => window.location.href = '/dashboard/logs'}
                        className="h-8 px-3 rounded-lg bg-[#1a1a1a] border border-[#262626] text-[#888888] text-xs font-medium hover:text-white hover:border-[#404040] transition-colors"
                    >
                        History
                    </button>
                    <button className="h-8 w-8 rounded-lg bg-[#00E37C] text-[#050505] flex items-center justify-center hover:bg-[#00E37C]/80 transition-colors">
                        <Play className="w-3 h-3 ml-0.5" />
                    </button>
                    <button
                        onClick={async () => {
                            if (confirm('Delete this task?')) {
                                if (onDelete) await onDelete(task.id);
                            }
                        }}
                        className="h-8 w-8 rounded-lg bg-[#FF4D4D]/10 border border-[#FF4D4D]/20 text-[#FF4D4D] flex items-center justify-center hover:bg-[#FF4D4D]/20 transition-colors"
                    >
                        <Trash2 className="w-3 h-3" />
                    </button>
                </div>
            </div>
        </motion.div>
    );
}
