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
            <Card className="glass-panel border-black/10 overflow-hidden hover:shadow-xl hover:shadow-gray-200/50 transition-all duration-300 group rounded-[2rem] bg-white/40 backdrop-blur-md">
                <div className={`h-1.5 w-full ${task.last_status === 'available' ? 'bg-emerald-500' :
                    task.last_status === 'sold_out' ? 'bg-rose-500' : 'bg-amber-500'
                    }`} />

                <CardHeader className="pb-2 pt-6 px-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <CardTitle className="text-xl font-black text-black tracking-tight mb-1">{task.area_name}</CardTitle>
                            <CardDescription className="text-xs uppercase tracking-widest font-bold text-gray-400 flex items-center gap-1.5">
                                {task.site === 'vatican' ? 'Vatican Museums' : 'Colosseum'}
                            </CardDescription>
                        </div>
                        <Badge variant={getStatusVariant(task.last_status || 'checking')} className="rounded-lg px-3 py-1 text-[10px] uppercase tracking-widest font-bold shadow-none">
                            {task.last_status?.replace('_', ' ') || 'Pending'}
                        </Badge>
                    </div>
                </CardHeader>

                <CardContent className="space-y-6 px-6 pb-6">
                    {/* Dates Only - Clean List */}
                    <div>
                        <div className="flex items-center gap-1.5 text-gray-400 text-[10px] font-bold uppercase tracking-widest mb-3">
                            <Calendar className="w-3 h-3" /> Targeted Dates
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {task.dates.map((d, i) => (
                                <span key={i} className="bg-gray-50 border border-gray-100 text-gray-600 px-3 py-1.5 rounded-lg text-xs font-bold font-mono">
                                    {d}
                                </span>
                            ))}
                        </div>
                    </div>
                </CardContent>

                <CardFooter className="pt-4 pb-6 px-6 border-t border-gray-50 flex justify-between items-center bg-gray-50/50">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                        <div className={`w-2 h-2 rounded-full ${timeLeft === 'Now' ? 'bg-emerald-500 animate-pulse' : 'bg-gray-300'}`}></div>
                        Next: <span className="text-black font-mono">{timeLeft}</span>
                    </div>

                    <div className="flex gap-2">
                        <Button size="sm" variant="ghost" className="h-8 text-xs font-bold text-gray-500 hover:text-gray-900 hover:bg-gray-100"
                            onClick={() => window.location.href = '/dashboard/logs'}
                        >
                            History
                        </Button>
                        <Button size="sm" variant="default" className="h-8 w-8 p-0 rounded-full bg-gray-900 text-white hover:bg-gray-800 shadow-md">
                            <Play className="w-3 h-3 ml-0.5" />
                        </Button>
                    </div>
                </CardFooter>
            </Card>
        </motion.div>
    );
}
