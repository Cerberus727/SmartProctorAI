import React, { createContext, useState, useEffect, useRef } from 'react';
import api from '../api/api';

export const AlertContext = createContext();

export const AlertProvider = ({ children }) => {
    const [alerts, setAlerts] = useState([]);
    const lastTrigger = useRef({});
    // Store if we have initialized to avoid spamming past alerts on reload
    const isInitialized = useRef(false);
    const lastProcessedIndex = useRef(0);

    const shouldTrigger = (event) => {
        const now = Date.now();
        if (!lastTrigger.current[event] || now - lastTrigger.current[event] > 3000) {
            lastTrigger.current[event] = now;
            return true;
        }
        return false;
    };

    const addAlert = (alert) => {
        const newAlert = {
            id: Date.now() + Math.random(),
            ...alert
        };
        
        console.log("ALERT SENT:", newAlert);
        
        setAlerts((prev) => [...prev, newAlert]);

        // Dispatch a custom event to tell TestPage.jsx about the violation
        window.dispatchEvent(new CustomEvent("violation_detected", { detail: newAlert }));

        // Log to backend DB so it shows up in reports
        const match = window.location.pathname.match(/\/test\/(\d+)/);
        if (match) {
            api.post("/proctor/log_violation", { 
                test_id: parseInt(match[1]), 
                event_type: alert.event 
            }).catch(e => console.error("Failed to log to DB:", e));
        }
        
        setTimeout(() => {
            setAlerts((prev) => prev.filter(a => a.id !== newAlert.id));
        }, 4000);
    };

    const getSeverity = (event) => {
        if (["PHONE", "MULTIPLE_FACES_DETECTED"].includes(event)) return "high";
        if (["LOOKING_AWAY", "NOT_FACING_FORWARD"].includes(event)) return "medium";
        return "low";
    };

    useEffect(() => {
        const fetchDetections = async () => {
            try {
                const res = await api.get('/proctor/logs');
                if (res.data && res.data.success && res.data.data) {
                    const allLogs = res.data.data;
                    
                    // On first load, skip all historical logs and only watch for NEW ones
                    if (!isInitialized.current) {
                        lastProcessedIndex.current = allLogs.length;
                        isInitialized.current = true;
                        return;
                    }

                    // Process only new events
                    if (allLogs.length > lastProcessedIndex.current) {
                        const newLogs = allLogs.slice(lastProcessedIndex.current);
                        lastProcessedIndex.current = allLogs.length;

                        newLogs.forEach(log => {
                            const { event } = log;
                            
                            console.log(`DETECTION TRIGGERED: ${event}`);

                            if (shouldTrigger(event)) {
                                addAlert({
                                    event: event,
                                    title: event.replace(/_/g, ' '),
                                    message: `Violation detected: ${event.replace(/_/g, ' ')}`,
                                    severity: getSeverity(event)
                                });
                            }
                        });
                    }
                }
            } catch (error) {
                console.error("Error fetching proctor logs:", error);
            }
        };

        const interval = setInterval(fetchDetections, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <AlertContext.Provider value={{ alerts, addAlert }}>
            {children}
            {alerts.length > 0 && (
                <div className="alert-container fixed top-5 right-5 z-[999999] flex flex-col gap-2 pointer-events-none">
                  {alerts.map(alert => (
                    <div key={alert.id} className={`p-4 border-l-4 rounded shadow-lg bg-white pointer-events-auto transition-all animate-slide-in ${
                        alert.severity === 'high' ? 'border-red-500 text-red-700' :
                        alert.severity === 'medium' ? 'border-yellow-500 text-yellow-700' :
                        'border-blue-500 text-blue-700'
                    }`}>
                      <strong>{alert.title}</strong>
                      <p className="text-sm">{alert.message}</p>
                    </div>
                  ))}
                </div>
            )}
        </AlertContext.Provider>
    );
};
