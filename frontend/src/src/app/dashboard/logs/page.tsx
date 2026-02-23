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
import { Activity, RefreshCcw } from "lucide-react";
import { Button } from '@/components/ui/button';

export default function LogsPage() {
    const [logs, setLogs] = useState<(CheckResult & { taskName: string })[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchLogs = async () => {
        setLoading(true);
        try {
            // Need an API method to get ALL logs, or we fetch for all tasks?
            // Checking api.ts next to see what is available.
            // For now assuming we might need to iterate or adding a new endpoint.
            // TEMPORARY: Fetching logs for task 1 as placeholder if global not avail
            const allLogs: (CheckResult & { taskName: string })[] = [];
            // fetching tasks first
            const tasks = await api.getTasks(1); // Hardcoded ID 1 for now or get from context

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
        fetchLogs();
    }, []);

    return (
        <div className="flex h-screen bg-[#0a0a0a] text-white selection:bg-purple-500/30">
            <Sidebar activeTab="logs" />

            <main className="flex-1 overflow-y-auto p-8 lg:p-12">
                <div className="max-w-7xl mx-auto space-y-8">

                    {/* Header */}
                    <div className="flex justify-between items-end">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <h1 className="text-4xl font-black tracking-tight mb-2 bg-gradient-to-r from-white to-gray-500 bg-clip-text text-transparent">
                                System Logs
                            </h1>
                            <p className="text-gray-400">
                                Real-time activity stream from all monitoring agents.
                            </p>
                        </motion.div>

                        <Button variant="outline" onClick={fetchLogs} disabled={loading} className="gap-2 border-white/10 hover:bg-white/5">
                            <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            Refresh
                        </Button>
                    </div>

                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Card className="bg-white/5 border-white/10 backdrop-blur-lg">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-gray-400 uppercase tracking-widest">Total Checks Today</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold text-white">{logs.length}</div>
                            </CardContent>
                        </Card>
                        <Card className="bg-white/5 border-white/10 backdrop-blur-lg">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-gray-400 uppercase tracking-widest">Successful Finds</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold text-emerald-400">
                                    {logs.filter(l => l.status === 'available').length}
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="bg-white/5 border-white/10 backdrop-blur-lg">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-gray-400 uppercase tracking-widest">Errors</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold text-rose-400">
                                    {logs.filter(l => l.status === 'error').length}
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Table */}
                    <Card className="bg-white/5 border-white/10 backdrop-blur-lg overflow-hidden">
                        <CardHeader>
                            <CardTitle className="text-lg">Activity Log</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <Table>
                                <TableHeader className="bg-white/5">
                                    <TableRow className="border-white/5 hover:bg-transparent">
                                        <TableHead className="text-gray-400">Time</TableHead>
                                        <TableHead className="text-gray-400">Task</TableHead>
                                        <TableHead className="text-gray-400">Status</TableHead>
                                        <TableHead className="text-gray-400">Details</TableHead>
                                        <TableHead className="text-gray-400 text-right">Bot</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="h-24 text-center text-gray-500">
                                                Loading logs...
                                            </TableCell>
                                        </TableRow>
                                    ) : logs.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="h-24 text-center text-gray-500">
                                                No logs found.
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        logs.slice(0, 50).map((log, i) => (
                                            <TableRow key={i} className="border-white/5 hover:bg-white/5 transition-colors">
                                                <TableCell className="font-mono text-xs text-gray-400">
                                                    {new Date(log.check_time).toLocaleTimeString()} <br />
                                                    <span className="opacity-50">{new Date(log.check_time).toLocaleDateString()}</span>
                                                </TableCell>
                                                <TableCell className="font-medium text-white">
                                                    {log.taskName || 'Unknown Task'}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant={
                                                        log.status === 'available' ? 'success' :
                                                            log.status === 'sold_out' ? 'danger' : 'warning'
                                                    }>
                                                        {log.status.toUpperCase()}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="max-w-[300px] truncate text-xs text-gray-300">
                                                    {JSON.stringify(log.details)}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Badge variant="outline" className="border-white/10 text-gray-400 text-[10px]">
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
