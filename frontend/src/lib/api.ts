export interface Agency {
    id: number;
    name: string;
    api_key: string;
    telegram_chat_id: string;
    is_active: boolean;
    created_at: string;
    plan: 'free' | 'pro' | 'agency';
    task_limit: number;
}

export interface MonitorTask {
    id: number;
    agency: number;
    agency_name: string;
    site: 'vatican' | 'colosseum';
    area_name: string;
    dates: string[];
    preferred_times: string[];
    visitors: number;
    ticket_type: number;

    // ✅ NEW: Vatican ticket selection
    ticket_id?: string;
    ticket_name?: string;

    language: string;
    is_active: boolean;
    last_checked: string | null;
    check_interval: number;
    last_status?: string;
    last_result_summary?: string; // JSON String
    created_at: string;
    // ✅ NEW: Latest check result with slots
    latest_check?: CheckResult | null;
}

export interface CheckResult {
    id: number;
    task: number;
    status: 'available' | 'sold_out' | 'error' | 'closed';
    found_count: number;
    check_time: string;
    screenshot: string | null;
    // ✅ NEW: God-Tier monitor fields
    check_method?: 'headless' | 'browser' | 'hybrid';
    response_time_ms?: number;
    details?: {
        date?: string;
        ticket_id?: string;
        ticket_name?: string;
        language?: string;
        slots?: { time: string; availability: string }[];
        state_changed?: boolean;
        previous_state?: string;
        is_first_check?: boolean;
        check_method?: string;
    };
}

const getApiUrl = () => {
    // 1. Highest priority: Explicit environment variable (Vercel/Docker)
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl) {
        // Ensure it has /api/v1 suffix if missing and not just a base URL
        return envUrl.endsWith('/api/v1') ? envUrl : `${envUrl.replace(/\/$/, '')}/api/v1`;
    }

    // 2. Client-side (Browser) logic
    if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;

        // Dev mode fallback
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000/api/v1';
        }

        // Subdomain/Relative fallback
        return `${protocol}//${hostname}/api/v1`;
    }

    // 3. Server-side (SSR) fallback
    return 'http://backend:8000/api/v1';
};

export const api = {
    getApiUrl: getApiUrl,
    getMyAgency: async (ownerId?: string, email?: string) => {
        const res = await fetch(`${getApiUrl()}/my-agency/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                owner_id: ownerId || 'local-admin',
                email: email || 'admin@local.com'
            }),
        });
        if (!res.ok) throw new Error('Failed to get agency');
        return res.json();
    },
    updateAgency: async (agencyId: number, data: Partial<Agency>) => {
        const res = await fetch(`${getApiUrl()}/agencies/${agencyId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed to update agency');
        return res.json();
    },
    getAgencies: async (): Promise<Agency[]> => {
        const res = await fetch(`${getApiUrl()}/agencies/`);
        if (!res.ok) throw new Error('Failed to fetch agencies');
        return res.json();
    },
    getTasks: async (agencyId?: number): Promise<MonitorTask[]> => {
        const url = agencyId
            ? `${getApiUrl()}/tasks/?agency_id=${agencyId}`
            : `${getApiUrl()}/tasks/`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch tasks');
        return res.json();
    },
    getResults: async (taskId?: number, agencyId?: number): Promise<CheckResult[]> => {
        const baseUrl = getApiUrl();
        let url = `${baseUrl}/results/`;
        const params = new URLSearchParams();
        if (taskId) params.append('task', taskId.toString());
        if (agencyId) params.append('agency_id', agencyId.toString());

        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch results');
        return res.json();
    },
    createTask: async (payload: any): Promise<void> => {
        const res = await fetch(`${getApiUrl()}/tasks/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(JSON.stringify(err));
        }
        if (!res.ok) {
            const err = await res.json();
            throw new Error(JSON.stringify(err));
        }
    },
    deleteTask: async (taskId: number): Promise<void> => {
        const res = await fetch(`${getApiUrl()}/tasks/${taskId}/`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error('Failed to delete task');
    },

    // ✅ NEW: Vatican Ticket Discovery
    getVaticanTickets: async (date: string) => {
        const res = await fetch(`${getApiUrl()}/vatican/tickets/?date=${encodeURIComponent(date)}`);
        if (!res.ok) throw new Error(' Failed to fetch Vatican tickets');
        return res.json();
    }
};
