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
        site: 'vatican' as 'vatican',
        dates: [] as string[],
        preferred_times: '',
        visitors: 2
    });
    const [newDate, setNewDate] = useState('');
    const [loading, setLoading] = useState(false);

    // Ticket selection state
    const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);

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
        if (!selectedTicketId) {
            alert('Please select a ticket type.');
            return;
        }
        
        setLoading(true);
        try {
            // Get ticket details from selected ticket
            const selectedTicket = vaticanTickets.find((t: any) => t.id === selectedTicketId);
            if (!selectedTicket) {
                throw new Error('Invalid ticket selection');
            }
            
            const ticketType = selectedTicket.ticket_type;
            const languageValue = selectedTicket.language;
            const ticketNameValue = selectedTicket.name.includes('Standard') 
                ? 'Musei Vaticani - Biglietti d\'ingresso'
                : 'Musei Vaticani - Visita Guidata';
            const areaName = selectedTicket.tag;
            
            const payload = {
                site: formData.site,
                area_name: areaName,
                dates: formData.dates,
                preferred_times: formData.preferred_times.split(',').map((t: string) => t.trim()).filter(Boolean),
                visitors: formData.visitors,
                agency: agencyId,
                ticket_type: ticketType,
                ticket_name: ticketNameValue,
                language: languageValue || undefined,
                notification_mode: 'available_only', // Default to only notify when available
                // ✅ CRITICAL: Do NOT send ticket_id - let the system resolve fresh IDs
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
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center sm:p-6 bg-[#050505]/80 backdrop-blur-xl">
            <div className="bento-card w-full sm:max-w-xl relative overflow-hidden max-h-[92vh] overflow-y-auto rounded-b-none sm:rounded-2xl">
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
                        {/* Ticket Selector - Primary Selection */}
                        <div>
                            <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">
                                Select Ticket Type
                            </label>
                            <select
                                value={selectedTicketId || ''}
                                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                                    setSelectedTicketId(e.target.value || null);
                                }}
                                className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm"
                                required
                            >
                                <option value="">-- Select Ticket Type --</option>
                                {vaticanTickets.map((ticket: any) => (
                                    <option key={ticket.id} value={ticket.id}>
                                        {ticket.name}
                                    </option>
                                ))}
                            </select>
                            <p className="text-xs text-[#666666] mt-2">
                                Choose between standard entry or guided tours in different languages
                            </p>
                        </div>

                        {/* Visitors */}
                        <div>
                            <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">Number of Visitors</label>
                            <input
                                type="number"
                                min="1"
                                max="10"
                                value={formData.visitors}
                                onChange={(e) => setFormData({ ...formData, visitors: parseInt(e.target.value) })}
                                className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm"
                                required
                            />
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

                        {/* Preferred Times */}
                        <div>
                            <label className="block text-xs font-medium text-[#888888] uppercase tracking-wider mb-2">Preferred Times (Optional)</label>
                            <input
                                type="text"
                                placeholder="e.g. 09:00, 10:30, 14:00"
                                value={formData.preferred_times}
                                onChange={(e) => setFormData({ ...formData, preferred_times: e.target.value })}
                                className="w-full bg-[#1a1a1a] border border-[#262626] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#00E37C]/50 text-sm placeholder:text-[#888888]"
                            />
                            <p className="text-xs text-[#666666] mt-2">
                                You'll be notified of all available slots, but preferred times will be highlighted
                            </p>
                        </div>
                    </div>

                    <button
                        disabled={loading || !agencyId || !selectedTicketId}
                        type="submit"
                        className="btn-primary w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {!agencyId ? 'Initializing Session...' : loading ? 'Creating Monitor...' : 'Create Monitor'}
                    </button>
                </form>
            </div>
        </div>
    );
}
