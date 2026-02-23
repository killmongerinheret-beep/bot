'use client';

import { useState, useEffect } from 'react';
import { MonitorTask } from '@/lib/api';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Clock,
    Calendar,
    Users,
    Play,
    MoreVertical,
    CheckCircle2,
    XCircle,
    AlertCircle,
    Loader2
} from 'lucide-react';

interface TaskCardProps {
    task: MonitorTask;
}

export default function TaskCard({ task }: TaskCardProps) {
    const [timeLeft, setTimeLeft] = useState<string>('...');

    // Status visual logic
    const getStatusVariant = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'available': return 'success';
            case 'sold_out': return 'danger';
            case 'error': return 'warning';
            default: return 'info';
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

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
        >
            <Card className="bg-white/5 border-white/10 backdrop-blur-md overflow-hidden hover:shadow-2xl hover:shadow-purple-500/10 transition-all duration-300 group">
                <div className={`h-1 w-full ${task.last_status === 'available' ? 'bg-emerald-500' :
                        task.last_status === 'sold_out' ? 'bg-rose-500' : 'bg-amber-500'
                    }`} />

                <CardHeader className="pb-3 relative">
                    <div className="flex justify-between items-start">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center text-xl shadow-inner border border-white/5">
                                {task.site === 'vatican' ? '⛪' : '🏛️'}
                            </div>
                            <div>
                                <CardTitle className="text-lg font-bold text-white tracking-tight">{task.area_name}</CardTitle>
                                <CardDescription className="text-xs uppercase tracking-widest font-semibold text-gray-500 flex items-center gap-1">
                                    {task.site} <span className="w-1 h-1 rounded-full bg-gray-600" /> ID: {task.id}
                                </CardDescription>
                            </div>
                        </div>
                        <Badge variant={getStatusVariant(task.last_status || 'checking')} className="uppercase tracking-widest text-[10px]">
                            {task.last_status?.replace('_', ' ') || 'Pending'}
                        </Badge>
                    </div>
                </CardHeader>

                <CardContent className="space-y-4 pb-4">
                    {/* Primary Stats */}
                    <div className="grid grid-cols-2 gap-3">
                        <div className="bg-black/20 rounded-lg p-2.5 flex flex-col gap-1 border border-white/5">
                            <div className="flex items-center gap-1.5 text-gray-400 text-[10px] font-bold uppercase tracking-widest">
                                <Users className="w-3 h-3" /> Visitors
                            </div>
                            <span className="text-lg font-bold text-white leading-none">{task.visitors}</span>
                        </div>
                        <div className="bg-black/20 rounded-lg p-2.5 flex flex-col gap-1 border border-white/5">
                            <div className="flex items-center gap-1.5 text-gray-400 text-[10px] font-bold uppercase tracking-widest">
                                <Clock className="w-3 h-3" /> Interval
                            </div>
                            <span className="text-lg font-bold text-white leading-none">{task.check_interval}s</span>
                        </div>
                    </div>

                    {/* Dates */}
                    <div>
                        <div className="flex items-center gap-1.5 text-gray-400 text-[10px] font-bold uppercase tracking-widest mb-2">
                            <Calendar className="w-3 h-3" /> Monitored Dates
                        </div>
                        <div className="flex flex-wrap gap-1.5 h-[60px] overflow-y-auto custom-scrollbar content-start">
                            {task.dates.map((d, i) => (
                                <Badge key={i} variant="secondary" className="bg-white/5 text-gray-300 border-white/5 hover:bg-white/10 text-[10px]">
                                    {d}
                                </Badge>
                            ))}
                        </div>
                    </div>
                </CardContent>

                <CardFooter className="pt-2 pb-5 border-t border-white/5 flex justify-between items-center bg-black/10">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                        <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                        Next Check: <span className="text-blue-400">{timeLeft}</span>
                    </div>

                    <div className="flex gap-2">
                        <Button size="sm" variant="ghost" className="h-7 text-[10px] uppercase font-bold text-gray-400 hover:text-white hover:bg-white/10"
                            onClick={() => window.location.href = '/dashboard/logs'}
                        >
                            Logs
                        </Button>
                        <Button size="sm" variant="default" className="h-7 w-7 p-0 rounded-full bg-white text-black hover:bg-gray-200 shadow-md">
                            <Play className="w-3 h-3 ml-0.5" />
                        </Button>
                    </div>
                </CardFooter>
            </Card>
        </motion.div>
    );
}
