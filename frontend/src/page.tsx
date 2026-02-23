'use client';

import { useEffect, useState } from 'react';
import { api, CheckResult } from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import { motion } from 'framer-motion';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { RefreshCcw } from "lucide-react";
import { Button } from '@/components/ui/button';
import { useUser } from "@clerk/nextjs";

export default function LogsPage() {
    const { user, isLoaded } = useUser();
    const [logs, setLogs] = useState<(CheckResult & { taskName: string })[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchLogs = async () => {
        if (!user) return;
        setLoading(true);
        try {
            const agency = await api.getMyAgency(user.id, user.primaryEmailAddress?.emailAddress || '');
            const tasks = await api.getTasks(agency.id);

            const allLogs: (CheckResult & { taskName: string })[] = [];
            for (const task of tasks) {
                const l = await api.getResults(task.id);
                // Add task name to log
                const taskLogs = l.map((item: CheckResult) => ({ ...item, taskName: task.area_name })) as (CheckResult & { taskName: string })[];
                allLogs.push(...taskLogs);
            }

            // Sort by time desc
            allLogs.sort((a, b) => new Date(b.check_time).getTime() - new Date(a.check_time).getTime());

            setLogs(allLogs);
        } catch (error) {
            console.error("Failed to fetch logs", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isLoaded && user) {
            fetchLogs();
        }
    }, [isLoaded, user]);

    if (!isLoaded || loading && logs.length === 0) {
        return (
            <div className="flex h-screen bg-[#FDFBF7] items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-[#FDFBF7] text-gray-900 font-sans selection:bg-blue-100">
            <Sidebar activeTab="logs" />

            <main className="flex-1 overflow-y-auto p-8 lg:p-12">
                <div className="max-w-7xl mx-auto space-y-8">

                    {/* Header */}
                    <div className="flex justify-between items-end">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <h1 className="text-4xl font-black tracking-tight mb-2 text-gray-900">
                                System Logs
                            </h1>
                            <p className="text-gray-500 font-medium">
                                Real-time activity stream from all monitoring agents.
                            </p>
                        </motion.div>

                        <Button variant="outline" onClick={fetchLogs} disabled={loading} className="gap-2 border-gray-200 hover:bg-white bg-white text-gray-900 shadow-sm">
                            <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            Refresh
                        </Button>
                    </div>

                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Card className="glass-panel bg-white/40 backdrop-blur-md border-black/10 shadow-sm">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-xs font-bold text-gray-400 uppercase tracking-widest">Total Checks Today</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-black text-gray-900">{logs.length}</div>
                            </CardContent>
                        </Card>
                        <Card className="bg-white border-gray-100 shadow-sm">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-xs font-bold text-gray-400 uppercase tracking-widest">Successful Finds</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-black text-emerald-600">
                                    {logs.filter(l => l.status === 'available').length}
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="glass-panel bg-white/40 backdrop-blur-md border-black/10 shadow-sm">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-xs font-bold text-gray-400 uppercase tracking-widest">Errors</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-black text-rose-600">
                                    {logs.filter(l => l.status === 'error').length}
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Table */}
                    <Card className="glass-panel bg-white/40 backdrop-blur-md border-black/10 shadow-md overflow-hidden rounded-2xl">
                        <CardHeader className="border-b border-gray-50 bg-gray-50/50">
                            <CardTitle className="text-lg font-bold text-gray-900">Activity Log</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <Table>
                                <TableHeader className="bg-gray-50/50">
                                    <TableRow className="border-gray-100 hover:bg-transparent">
                                        <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-wider">Time</TableHead>
                                        <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-wider">Task</TableHead>
                                        <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-wider">Status</TableHead>
                                        <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-wider">Details</TableHead>
                                        <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-wider text-right">Bot</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading && logs.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="h-24 text-center text-gray-400 font-medium">
                                                Loading logs...
                                            </TableCell>
                                        </TableRow>
                                    ) : logs.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="h-24 text-center text-gray-400 font-medium">
                                                No logs found.
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        logs.slice(0, 50).map((log, i) => (
                                            <TableRow key={i} className="border-gray-50 hover:bg-gray-50/50 transition-colors group">
                                                <TableCell className="font-mono text-xs text-gray-500 font-medium">
                                                    {new Date(log.check_time).toLocaleTimeString()} <br />
                                                    <span className="opacity-50 text-[10px]">{new Date(log.check_time).toLocaleDateString()}</span>
                                                </TableCell>
                                                <TableCell className="font-bold text-gray-900">
                                                    {log.taskName || 'Unknown Task'}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant={
                                                        log.status === 'available' ? 'default' : // Emerald mapped to default/success in theme? Need to check.
                                                            log.status === 'sold_out' ? 'destructive' : 'secondary'
                                                    } className={`uppercase tracking-widest text-[10px] font-bold shadow-none ${log.status === 'available' ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200' :
                                                        log.status === 'sold_out' ? 'bg-rose-100 text-rose-700 hover:bg-rose-200' :
                                                            'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                                        }`}>
                                                        {log.status.toUpperCase()}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="max-w-[300px] truncate text-xs text-gray-500 font-mono">
                                                    {JSON.stringify(log.details)}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Badge variant="outline" className="border-gray-200 text-gray-400 text-[10px] font-medium">
                                                        HYDRA v2
                                                    </Badge>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </div>
            </main>
        </div>
    );
}
