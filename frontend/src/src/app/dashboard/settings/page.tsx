'use client';

import { useEffect, useState } from 'react';
import { api, Agency } from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useUser } from "@clerk/nextjs";
import { Save, User, Bell, Shield } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function SettingsPage() {
    const { user } = useUser();
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

    return (
        <div className="flex h-screen bg-[#0a0a0a] text-white selection:bg-purple-500/30">
            <Sidebar activeTab="settings" />

            <main className="flex-1 overflow-y-auto p-8 lg:p-12">
                <div className="max-w-4xl mx-auto space-y-8">

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <h1 className="text-4xl font-black tracking-tight mb-2">Settings</h1>
                        <p className="text-gray-400">Manage your agency profile and notification preferences.</p>
                    </motion.div>

                    <div className="grid gap-6">
                        {/* Profile Section */}
                        <Card className="bg-white/5 border-white/10 backdrop-blur-lg">
                            <CardHeader>
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                                        <User className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <CardTitle>Agency Profile</CardTitle>
                                        <CardDescription className="text-gray-400">Your organization details visible on reports.</CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-300">Agency Name</label>
                                    <Input
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="bg-black/20 border-white/10 text-white focus:border-blue-500/50"
                                        placeholder="My Travel Agency"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-300">Contact Email</label>
                                    <Input
                                        disabled
                                        value={user?.primaryEmailAddress?.emailAddress || ''}
                                        className="bg-black/20 border-white/10 text-gray-500 cursor-not-allowed"
                                    />
                                </div>
                            </CardContent>
                        </Card>

                        {/* Notifications Section */}
                        <Card className="bg-white/5 border-white/10 backdrop-blur-lg">
                            <CardHeader>
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-purple-500/20 rounded-lg text-purple-400">
                                        <Bell className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <CardTitle>Notifications</CardTitle>
                                        <CardDescription className="text-gray-400">Configure how you receive alerts for available tickets.</CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <label className="text-sm font-medium text-gray-300">Telegram Chat ID</label>
                                        <Badge variant="outline" className="text-[10px] border-purple-500/20 text-purple-400">Recommended</Badge>
                                    </div>
                                    <div className="flex gap-3">
                                        <Input
                                            value={chatId}
                                            onChange={(e) => setChatId(e.target.value)}
                                            className="bg-black/20 border-white/10 text-white focus:border-purple-500/50"
                                            placeholder="123456789"
                                        />
                                        <Button variant="secondary" className="bg-white/10 hover:bg-white/20 text-white border border-white/10">Test</Button>
                                    </div>
                                    <p className="text-xs text-gray-500">
                                        Start a chat with <strong>@TravelAgentBot</strong> and send <code>/start</code> to get your ID.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Security Section (Read Only) */}
                        <Card className="bg-white/5 border-white/10 backdrop-blur-lg opacity-75">
                            <CardHeader>
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-emerald-500/20 rounded-lg text-emerald-400">
                                        <Shield className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <CardTitle>API Configuration</CardTitle>
                                        <CardDescription className="text-gray-400">System level configuration.</CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs font-bold text-gray-500 uppercase">Status</label>
                                    <div className="text-emerald-400 font-medium flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                        Active
                                    </div>
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-gray-500 uppercase">Provider</label>
                                    <div className="text-white font-medium">Internal API</div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="flex justify-end pt-4">
                        <Button
                            onClick={handleSave}
                            disabled={saving}
                            className="bg-white text-black hover:bg-gray-200 px-8 rounded-full font-bold shadow-lg shadow-white/10"
                        >
                            {saving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </div>

                </div>
            </main>
        </div>
    );
}
