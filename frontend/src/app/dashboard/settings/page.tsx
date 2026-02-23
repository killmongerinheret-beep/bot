'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from 'react';
import { api, Agency } from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useUser } from "@clerk/nextjs";
import { Save, User, Bell, Shield } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function SettingsPage() {
    const { user, isLoaded } = useUser();
    const [agency, setAgency] = useState<Agency | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    // Form States
    const [name, setName] = useState('');
    const [chatId, setChatId] = useState('');

    useEffect(() => {
        const fetchSettings = async () => {
            if (!user) return;
            try {
                const data = await api.getMyAgency(user.id, user.primaryEmailAddress?.emailAddress || '');
                setAgency(data);
                setName(data.name);
                setChatId(data.telegram_chat_id || '');
            } catch (e) {
                console.error("Failed to load settings", e);
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, [user]);

    const handleSave = async () => {
        if (!agency) return;
        setSaving(true);
        try {
            await api.updateAgency(agency.id, {
                name,
                telegram_chat_id: chatId
            });
            alert('Settings saved successfully!');
        } catch (e) {
            alert('Failed to save settings');
        } finally {
            setSaving(false);
        }
    };

    if (!isLoaded || loading) {
        return (
            <div className="flex h-screen bg-[#050505] items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#00E37C]"></div>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-[#050505] text-white font-sans selection:bg-[#00E37C]/30">
            <Sidebar activeTab="settings" />

            <main className="flex-1 overflow-y-auto p-8 lg:p-12">
                <div className="max-w-4xl mx-auto space-y-8">

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <h1 className="text-3xl font-semibold tracking-tight mb-2 text-white">Settings</h1>
                        <p className="text-[#888888]">Manage your agency profile and notification preferences.</p>
                    </motion.div>

                    <div className="grid gap-6">
                        {/* Profile Section */}
                        <div className="bg-[#0F0F0F] border border-[#262626] rounded-xl p-6">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                                    <User className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-medium text-white">Agency Profile</h3>
                                    <p className="text-sm text-[#888888]">Your organization details.</p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-[#CCCCCC]">Agency Name</label>
                                    <Input
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="bg-[#050505] border-[#262626] text-white focus:border-blue-500/50"
                                        placeholder="My Travel Agency"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-[#CCCCCC]">Contact Email</label>
                                    <Input
                                        disabled
                                        value={user?.primaryEmailAddress?.emailAddress || ''}
                                        className="bg-[#050505] border-[#262626] text-[#666666] cursor-not-allowed"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Notifications Section */}
                        <div className="bg-[#0F0F0F] border border-[#262626] rounded-xl p-6">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                                    <Bell className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-medium text-white">Notifications</h3>
                                    <p className="text-sm text-[#888888]">Configure alerts for available tickets.</p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <label className="text-sm font-medium text-[#CCCCCC]">Telegram Chat ID</label>
                                        <Badge variant="outline" className="text-[10px] border-purple-500/20 text-purple-400 bg-purple-500/10 hover:bg-purple-500/10">Recommended</Badge>
                                    </div>
                                    <div className="flex gap-3">
                                        <Input
                                            value={chatId}
                                            onChange={(e) => setChatId(e.target.value)}
                                            className="bg-[#050505] border-[#262626] text-white focus:border-purple-500/50"
                                            placeholder="123456789"
                                        />
                                        <Button variant="secondary" className="bg-[#262626] hover:bg-[#333333] text-white border border-[#333333]">Test</Button>
                                    </div>
                                    <p className="text-xs text-[#666666]">
                                        Start a chat with <strong className="text-[#888888]">@TravelAgentBot</strong> and send <code className="bg-[#262626] px-1 rounded">/start</code> to get your ID.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Security Section (Read Only) */}
                        <div className="bg-[#0F0F0F] border border-[#262626] rounded-xl p-6 opacity-75">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
                                    <Shield className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-medium text-white">API Configuration</h3>
                                    <p className="text-sm text-[#888888]">System level configuration.</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs font-bold text-[#666666] uppercase">Status</label>
                                    <div className="text-emerald-400 font-medium flex items-center gap-2 mt-1">
                                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                        Active
                                    </div>
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-[#666666] uppercase">Provider</label>
                                    <div className="text-white font-medium mt-1">Internal API</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end pt-4">
                        <Button
                            onClick={handleSave}
                            disabled={saving}
                            className="bg-white text-black hover:bg-gray-200 px-8 rounded-full font-bold transition-all"
                        >
                            {saving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </div>

                </div>
            </main>
        </div>
    );
}
