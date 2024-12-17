// Dashboard Components
const SystemEventCard = ({ event }) => (
    <div className="bg-white p-4 rounded-lg shadow mb-4">
        <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-semibold">{event.type}</h3>
            <div className="flex space-x-2">
                <span className="px-2 py-1 rounded text-sm bg-blue-100 text-blue-800">
                    {event.platform}
                </span>
                <span className="px-2 py-1 rounded text-sm bg-purple-100 text-purple-800">
                    {event.category}
                </span>
            </div>
        </div>
        <div className="text-sm text-gray-600">
            <p>Time: {new Date(event.timestamp).toLocaleString()}</p>
            {event.body && event.body.chat_id && (
                <p>Chat ID: {event.body.chat_id}</p>
            )}
            {event.body && event.body.user_id && (
                <p>User ID: {event.body.user_id}</p>
            )}
        </div>
        <div className="mt-2 text-sm">
            {event.body && event.body.text && (
                <div className="border-l-4 border-blue-500 pl-2 mt-2">
                    <p className="font-medium">Message:</p>
                    <p className="text-gray-700">{event.body.text}</p>
                </div>
            )}
            {event.body && event.body.error && (
                <div className="border-l-4 border-red-500 pl-2 mt-2">
                    <p className="font-medium">Error:</p>
                    <p className="text-gray-700">{event.body.error}</p>
                </div>
            )}
            {event.response && (
                <div className="border-l-4 border-green-500 pl-2 mt-2">
                    <p className="font-medium">Response:</p>
                    <p className="text-gray-700">{JSON.stringify(event.response)}</p>
                </div>
            )}
        </div>
    </div>
);

const TriggerEventCard = ({ event }) => (
    <div className="bg-white p-4 rounded-lg shadow mb-4">
        <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-semibold">{event.trigger_type}</h3>
            <span className={`px-2 py-1 rounded text-sm ${
                event.status === 'completed' ? 'bg-green-100 text-green-800' :
                event.status === 'failed' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
            }`}>
                {event.status}
            </span>
        </div>
        <div className="text-sm text-gray-600">
            <p>Platform: {event.platform}</p>
            <p>Time: {new Date(event.timestamp).toLocaleString()}</p>
            {event.metadata && event.metadata.chat_id && (
                <p>Chat ID: {event.metadata.chat_id}</p>
            )}
        </div>
        <div className="mt-2 text-sm">
            {event.content && event.content.message && event.content.message.text && (
                <div className="border-l-4 border-blue-500 pl-2">
                    <p className="font-medium">Message:</p>
                    <p className="text-gray-700">{event.content.message.text}</p>
                </div>
            )}
        </div>
    </div>
);

const Stats = ({ triggerStats, systemStats }) => (
    <div className="space-y-6">
        <div>
            <h2 className="text-xl font-bold mb-4">System Events</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white p-4 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-2">Total Events</h3>
                    <p className="text-3xl font-bold text-blue-600">{systemStats.total}</p>
                </div>
                {Object.entries(systemStats.by_category || {}).map(([category, count]) => (
                    <div key={category} className="bg-white p-4 rounded-lg shadow">
                        <h3 className="text-lg font-semibold mb-2">{category}</h3>
                        <p className="text-3xl font-bold text-blue-600">{count}</p>
                    </div>
                ))}
            </div>
        </div>
        
        <div>
            <h2 className="text-xl font-bold mb-4">Trigger Events</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white p-4 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-2">Total Triggers</h3>
                    <p className="text-3xl font-bold text-blue-600">{triggerStats.total}</p>
                </div>
            </div>
        </div>
    </div>
);

const Dashboard = () => {
    const [systemEvents, setSystemEvents] = React.useState([]);
    const [triggerEvents, setTriggerEvents] = React.useState([]);
    const [stats, setStats] = React.useState({ system_events: {}, trigger_events: {} });
    const [eventTypes, setEventTypes] = React.useState({ types: [], platforms: [], categories: [] });
    const [filter, setFilter] = React.useState({
        eventType: '',
        platform: '',
        category: '',
        status: ''
    });

    const fetchStats = async () => {
        try {
            const response = await fetch('/api/dashboard/stats');
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    };

    const fetchEventTypes = async () => {
        try {
            const response = await fetch('/api/dashboard/event-types');
            const data = await response.json();
            setEventTypes(data);
        } catch (error) {
            console.error('Error fetching event types:', error);
        }
    };

    const fetchSystemEvents = async () => {
        try {
            const params = new URLSearchParams();
            if (filter.eventType) params.append('event_type', filter.eventType);
            if (filter.platform) params.append('platform', filter.platform);
            if (filter.category) params.append('category', filter.category);
            
            const response = await fetch(`/api/dashboard/system-events?${params}`);
            const data = await response.json();
            setSystemEvents(data);
        } catch (error) {
            console.error('Error fetching system events:', error);
        }
    };

    const fetchTriggerEvents = async () => {
        try {
            const params = new URLSearchParams();
            if (filter.eventType) params.append('event_type', filter.eventType);
            if (filter.platform) params.append('platform', filter.platform);
            if (filter.status) params.append('status', filter.status);
            
            const response = await fetch(`/api/dashboard/events?${params}`);
            const data = await response.json();
            setTriggerEvents(data);
        } catch (error) {
            console.error('Error fetching trigger events:', error);
        }
    };

    React.useEffect(() => {
        fetchStats();
        fetchEventTypes();
        fetchSystemEvents();
        fetchTriggerEvents();
        
        const interval = setInterval(() => {
            fetchStats();
            fetchSystemEvents();
            fetchTriggerEvents();
        }, 5000);
        
        return () => clearInterval(interval);
    }, [filter]);

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-8">Event Monitor Dashboard</h1>
            
            <Stats 
                triggerStats={stats.trigger_events || {}} 
                systemStats={stats.system_events || {}} 
            />
            
            <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
                <select
                    className="border p-2 rounded"
                    value={filter.eventType}
                    onChange={(e) => setFilter({...filter, eventType: e.target.value})}
                >
                    <option value="">All Event Types</option>
                    {eventTypes.types.map(type => (
                        <option key={type} value={type}>{type}</option>
                    ))}
                </select>
                
                <select
                    className="border p-2 rounded"
                    value={filter.platform}
                    onChange={(e) => setFilter({...filter, platform: e.target.value})}
                >
                    <option value="">All Platforms</option>
                    {eventTypes.platforms.map(platform => (
                        <option key={platform} value={platform}>{platform}</option>
                    ))}
                </select>
                
                <select
                    className="border p-2 rounded"
                    value={filter.category}
                    onChange={(e) => setFilter({...filter, category: e.target.value})}
                >
                    <option value="">All Categories</option>
                    {eventTypes.categories.map(category => (
                        <option key={category} value={category}>{category}</option>
                    ))}
                </select>
                
                <select
                    className="border p-2 rounded"
                    value={filter.status}
                    onChange={(e) => setFilter({...filter, status: e.target.value})}
                >
                    <option value="">All Statuses</option>
                    <option value="pending">Pending</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                </select>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                    <h2 className="text-2xl font-bold mb-4">System Events</h2>
                    <div className="space-y-4">
                        {systemEvents.map((event) => (
                            <SystemEventCard key={event.id} event={event} />
                        ))}
                    </div>
                </div>
                
                <div>
                    <h2 className="text-2xl font-bold mb-4">Trigger Events</h2>
                    <div className="space-y-4">
                        {triggerEvents.map((event) => (
                            <TriggerEventCard key={event.id} event={event} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

ReactDOM.render(<Dashboard />, document.getElementById('root'));
