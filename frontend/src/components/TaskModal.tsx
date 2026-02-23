'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import vaticanTickets from '../data/vatican_tickets.json';
import { X } from 'lucide-react';

interface TaskModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    agencyId: number | null;
}

export default function TaskModal({ isOpen, onClose, onSuccess, agencyId }: TaskModalProps) {
    const [formData, setFormData] = useState({
        site: 'vatican' as 'vatican' | 'colosseum',
        area_name: 'MV-Biglietti',
        ticket_id: '',
        tier: 'monitor' as 'monitor' | 'sniper',
        dates: [] as string[],
        preferred_times: '',
        visitors: 2,
        notification_mode: 'any_change',
        language: 'ENG'
    });
    const [newDate, setNewDate] = useState('');
    const [loading, setLoading] = useState(false);

    // Ticket selection state
    const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
    const [selectedTicketName, setSelectedTicketName] = useState<string | null>(null);
    const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);

    if (!isOpen) return null;

    const addDate = () => {
        if (newDate && !formData.dates.includes(newDate)) {
            setFormData({ ...formData, dates: [...formData.dates, newDate] });
            setNewDate('');
        }
    };

    const removeDate = (dateToRemove: string) => {
        setFormData({ ...formData, dates: formData.dates.filter((d: string) => d !== dateToRemove) });
    };

    const areaOptions = {
        vatican: [
            { label: 'Standard Entry (Biglietti)', value: 'MV-Biglietti' },
            { label: 'Guided Tours (MV-Tour)', value: 'MV-Tour' },
            { label: 'Prime Experience', value: 'MV-Prime' },
        ],
        colosseum: [
            { label: 'Parco 24h (Standard)', value: 'ce1af0d8-41e9-4e97-88cf-938e52ec8dbb' },
            { label: 'Full Experience (Attic)', value: 'fbe87f91-381c-43f5-9388-727e4e11698e' },
            { label: 'Underground/Arena', value: '95806659-399a-42f0-97eb-bd9dcc75d1f0' },
        ]
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!agencyId) {
            alert('Session error. Please logout and login again.');
            return;
        }
        if (formData.dates.length === 0) {
            alert('Please add at least one date.');
            return;
        }
        setLoading(true);
        try {
            const payload = {
                ...formData,
                agency: agencyId,
                preferred_times: formData.preferred_times.split(',').map((t: string) => t.trim()).filter(Boolean),
                ticket_id: selectedTicketId || undefined,
                ticket_name: selectedTicketName || undefined,
                language: selectedLanguage || formData.language,
            };

            await api.createTask(payload);

            onSuccess();
            onClose();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            alert(`Error: ${message}`);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-[#050505]/80 backdrop-blur-xl">
            <div className="bento-card w-full max-w-xl relative overflow-hidden max-h-[90vh] overflow-y-auto">
                {/* Green accent bar */}
                <div className="absolute top-0 left-0 w-full h-1 bg-[#00E37C]" style={{ marginTop: '-32px', marginLeft: '-32px', width: 'calc(100% + 64px)' }}></div>

                <button
                    onClick={onClose}
                    className="absolute top-2 right-2 text-[#888888] hover:text-white transition-colors w-8 h-8 flex items-center justify-center rounded-lg hover:bg-[#262626]"
                >
                    <X size={18} />
                </button>

                <div className="mb-8">
                    <h2 className="text-2xl font-semibold text-white tracking-tight">Enterprise Monitor</h2>
                    <p className="text-[#888888] text-sm mt-1">Configure high-speed automated tracking</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">Target Site</label>
                                <select
                                    value={formData.site}
                                    onChange={(e) => {
                                        const site = e.target.value as 'vatican' | 'colosseum';
                                        setFormData({
                                            ...formData,
                                            site,
                                            area_name: areaOptions[site][0].value
                                        });
                                    }}
                                    className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm"
                                >
                                    <option value="vatican">Vatican Museums</option>
                                    <option value="colosseum">Colosseum</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">Area / Type</label>
                                <select
                                    value={formData.area_name}
                                    onChange={(e) => setFormData({ ...formData, area_name: e.target.value })}
                                    className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm"
                                >
                                    {areaOptions[formData.site].map(opt => (
                                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>


                        <div className="grid grid-cols-2 gap-4">
                            {/* Language selector - only show for Guided Tours */}
                            {formData.area_name === 'MV-Tour' && (
                                <div>
                                    <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">Tour Language</label>
                                    <select
                                        value={formData.language}
                                        onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                                        className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm"
                                    >
                                        <option value="ENG">English</option>
                                        <option value="ITA">Italiano</option>
                                        <option value="SPA">Español</option>
                                        <option value="FRA">Français</option>
                                        <option value="TED">Deutsch</option>
                                    </select>
                                </div>
                            )}
                            <div className={formData.area_name === 'MV-Tour' ? '' : 'col-span-2'}>
                                <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">Visitors (PAX)</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="10"
                                    value={formData.visitors}
                                    onChange={(e) => setFormData({ ...formData, visitors: parseInt(e.target.value) })}
                                    className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">Monitoring Dates</label>
                            <div className="flex gap-2 mb-3">
                                <input
                                    type="date"
                                    value={newDate}
                                    onChange={(e) => setNewDate(e.target.value)}
                                    className="flex-1 bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm"
                                />
                                <button
                                    type="button"
                                    onClick={addDate}
                                    className="px-6 bg-[#00E37C] text-[#050505] font-medium rounded-xl hover:bg-[#00E37C]/80 transition-colors"
                                >
                                    Add
                                </button>
                            </div>
                            <div className="flex flex-wrap gap-2 min-h-[44px] p-3 bg-[#1a1a1a] rounded-xl border border-dashed border-[#262626]">
                                {formData.dates.map(date => (
                                    <span key={date} className="bg-[#262626] border border-[#404040] px-3 py-1.5 rounded-lg text-xs font-mono text-white flex items-center gap-2">
                                        {date}
                                        <button type="button" onClick={() => removeDate(date)} className="text-[#888888] hover:text-[#FF4D4D]">×</button>
                                    </span>
                                ))}
                                {formData.dates.length === 0 && <span className="text-xs text-[#888888]">No dates selected</span>}
                            </div>
                        </div>

                        {formData.site === 'vatican' && (
                            <div className="border-t border-[#262626] pt-6">
                                <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">
                                    Select Ticket Type
                                </label>
                                <select
                                    value={selectedTicketId || ''}
                                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                                        const ticket = vaticanTickets.find((t: any) => t.id === e.target.value);
                                        if (ticket) {
                                            setSelectedTicketId(ticket.id);
                                            setSelectedTicketName(ticket.name);
                                            // Language is handled separately or inferred, not in this JSON
                                            setFormData({ ...formData, area_name: ticket.tag });
                                        }
                                    }}
                                    className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm"
                                >
                                    <option value="">-- Select Ticket --</option>
                                    {vaticanTickets.map((ticket: any) => (
                                        <option key={ticket.id} value={ticket.id}>
                                            {ticket.name}
                                        </option>
                                    ))}
                                </select>

                                {selectedTicketId && selectedTicketId.startsWith('guided_') && (
                                    <div className="mt-4">
                                        <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">
                                            Tour Language
                                        </label>
                                        <select
                                            value={selectedLanguage || ''}
                                            onChange={(e) => setSelectedLanguage(e.target.value || null)}
                                            className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm"
                                        >
                                            <option value="">-- Select Language --</option>
                                            <option value="ENG">English</option>
                                            <option value="ITA">Italian</option>
                                            <option value="FRA">French</option>
                                            <option value="SPA">Spanish</option>
                                            <option value="DEU">German</option>
                                        </select>
                                    </div>
                                )}
                            </div>
                        )}

                        <div>
                            <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">Time Prefs (HH:MM)</label>
                            <input
                                type="text"
                                placeholder="e.g. 09:00, 10:30"
                                value={formData.preferred_times}
                                onChange={(e) => setFormData({ ...formData, preferred_times: e.target.value })}
                                className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm placeholder:text-[#888888]"
                            />
                        </div>
                    </div>

                    <button
                        disabled={loading || !agencyId}
                        type="submit"
                        className="btn-primary w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {!agencyId ? 'Initializing Session...' : loading ? 'Initializing Engine...' : 'Authorize Monitoring'}
                    </button>
                </form>
            </div>
        </div>
    );
}
