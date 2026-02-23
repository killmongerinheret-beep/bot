'use client';

import { useState, useEffect } from 'react';
import { Agency, api } from '@/lib/api';

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
        dates: [] as string[],
        preferred_times: '',
        visitors: 2,
        notification_mode: 'any_change',
        language: 'en'
    });
    const [newDate, setNewDate] = useState('');
    const [loading, setLoading] = useState(false);

    if (!isOpen) return null;

    const addDate = () => {
        if (newDate && !formData.dates.includes(newDate)) {
            setFormData({ ...formData, dates: [...formData.dates, newDate] });
            setNewDate('');
        }
    };

    const removeDate = (dateToRemove: string) => {
        setFormData({ ...formData, dates: formData.dates.filter(d => d !== dateToRemove) });
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
                preferred_times: formData.preferred_times.split(',').map(t => t.trim()).filter(Boolean),
            };

            await api.createTask(payload);

            onSuccess();
            onClose();
        } catch (err: any) {
            alert(`Error: ${err.message || err}`);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-gray-900/40 backdrop-blur-xl">
            <div className="bg-white border border-gray-100 w-full max-w-xl rounded-[2.5rem] p-10 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-500"></div>
                <button
                    onClick={onClose}
                    className="absolute top-6 right-6 text-gray-400 hover:text-gray-900 transition-colors w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100"
                >
                    ✕
                </button>

                <div className="mb-8">
                    <h2 className="text-2xl font-black text-gray-900 tracking-tight">Enterprise Monitor</h2>
                    <p className="text-gray-500 text-sm font-medium mt-1">Configure high-speed automated tracking</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-2">Target Site</label>
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
                                    className="w-full bg-gray-50 border border-gray-100 rounded-2xl px-5 py-4 text-gray-900 focus:outline-none focus:border-blue-500/50 appearance-none font-bold text-sm"
                                >
                                    <option value="vatican">Vatican Museums</option>
                                    <option value="colosseum">Colosseum</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-2">Area / Ticket Type</label>
                                <select
                                    value={formData.area_name}
                                    onChange={(e) => setFormData({ ...formData, area_name: e.target.value })}
                                    className="w-full bg-gray-50 border border-gray-100 rounded-2xl px-5 py-4 text-gray-900 focus:outline-none focus:border-blue-500/50 appearance-none font-bold text-sm"
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
                                    <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-2">Tour Language</label>
                                    <select
                                        value={formData.language}
                                        onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                                        className="w-full bg-gray-50 border border-gray-100 rounded-2xl px-5 py-4 text-gray-900 focus:outline-none focus:border-blue-500/50 appearance-none font-bold text-sm"
                                    >
                                        <option value="ENG">English</option>
                                        <option value="ITA">Italiano</option>
                                        <option value="SPA">Español</option>
                                        <option value="FRA">Français</option>
                                        <option value="DEU">Deutsch</option>
                                    </select>
                                </div>
                            )}
                            <div className={formData.area_name === 'MV-Tour' ? '' : 'col-span-2'}>
                                <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-2">Visitors (PAX)</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="10"
                                    value={formData.visitors}
                                    onChange={(e) => setFormData({ ...formData, visitors: parseInt(e.target.value) })}
                                    className="w-full bg-gray-50 border border-gray-100 rounded-2xl px-5 py-4 text-gray-900 focus:outline-none focus:border-blue-500/50 font-bold text-sm"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-2">Monitoring Dates</label>
                            <div className="flex gap-2 mb-3">
                                <input
                                    type="date"
                                    value={newDate}
                                    onChange={(e) => setNewDate(e.target.value)}
                                    className="flex-1 bg-gray-50 border border-gray-100 rounded-2xl px-5 py-4 text-gray-900 focus:outline-none focus:border-blue-500/50 font-bold text-sm"
                                />
                                <button
                                    type="button"
                                    onClick={addDate}
                                    className="px-6 bg-blue-500 text-white font-bold rounded-2xl hover:bg-blue-600 transition-colors"
                                >
                                    Add
                                </button>
                            </div>
                            <div className="flex flex-wrap gap-2 min-h-[44px] p-2 bg-gray-50/50 rounded-2xl border border-dashed border-gray-200">
                                {formData.dates.map(date => (
                                    <span key={date} className="bg-white border border-gray-100 px-3 py-1.5 rounded-xl text-xs font-bold text-gray-700 flex items-center gap-2 shadow-sm">
                                        {date}
                                        <button type="button" onClick={() => removeDate(date)} className="text-gray-400 hover:text-red-500">✕</button>
                                    </span>
                                ))}
                                {formData.dates.length === 0 && <span className="text-[11px] text-gray-300 font-medium p-1">No dates selected</span>}
                            </div>
                        </div>

                        <div>
                            <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-2">Time Prefs (HH:MM)</label>
                            <input
                                type="text"
                                placeholder="e.g. 09:00, 10:30"
                                value={formData.preferred_times}
                                onChange={(e) => setFormData({ ...formData, preferred_times: e.target.value })}
                                className="w-full bg-gray-50 border border-gray-100 rounded-2xl px-5 py-4 text-gray-900 focus:outline-none focus:border-blue-500/50 font-bold text-sm placeholder:text-gray-300"
                            />
                        </div>
                    </div>

                    <button
                        disabled={loading}
                        type="submit"
                        className="w-full bg-gray-900 hover:bg-gray-800 text-white font-black py-5 rounded-[1.5rem] transition-all shadow-xl shadow-gray-200 disabled:opacity-50 uppercase tracking-widest text-xs transform active:scale-95"
                    >
                        {loading ? 'Initializing Engine...' : 'Authorize Monitoring'}
                    </button>
                </form>
            </div>
        </div>
    );
}
