import React, { useState, useEffect } from 'react';
import { AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

export default function ProctorAlerts({ alerts, removeAlert }) {
  console.log("ProctorAlerts rendering with alerts count:", alerts.length);
  return (
    <div className="fixed top-5 right-5 z-[9999] flex flex-col gap-3 max-w-sm w-full font-sans pointer-events-none">
      {alerts.map((alert) => (
        <AlertItem key={alert.id} alert={alert} removeAlert={removeAlert} />
      ))}
    </div>
  );
}

function AlertItem({ alert, removeAlert }) {
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    // Play sound if high risk
    if (alert.severity === 'high') {
      try {
        const audio = new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU' /* small beep beep */);
        audio.play().catch(e => console.log('Audio blocked', e));
      } catch(e) {}
    }

    const timer = setTimeout(() => {
      closeAlert();
    }, 4500);

    return () => clearTimeout(timer);
  }, []);

  const closeAlert = () => {
    setIsClosing(true);
    setTimeout(() => removeAlert(alert.id), 400); // Wait for exit animation
  };

  const severityStyles = {
    high: 'bg-red-50 border-red-500 text-red-800',
    medium: 'bg-yellow-50 border-yellow-400 text-yellow-800',
    info: 'bg-blue-50 border-blue-400 text-blue-800',
  };

  const SeverityIcon = {
    high: AlertTriangle,
    medium: AlertCircle,
    info: Info,
  }[alert.severity] || Info;

  const iconColors = {
    high: 'text-red-500',
    medium: 'text-yellow-500',
    info: 'text-blue-500'
  };

  return (
    <div 
      className={`pointer-events-auto relative flex items-start p-4 border-l-4 rounded-xl shadow-lg transform transition-all duration-300 ease-in-out
        ${severityStyles[alert.severity]}
        ${isClosing ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0 animate-slide-in'}
      `}
    >
      <div className="flex-shrink-0">
        <SeverityIcon className={`h-6 w-6 ${iconColors[alert.severity]}`} />
      </div>
      <div className="ml-3 w-0 flex-1 pt-0.5">
        <p className="text-sm font-bold uppercase tracking-wide">
          {alert.title}
        </p>
        <p className="mt-1 text-sm opacity-90">
          {alert.message}
        </p>
        {alert.timestamp && (
          <p className="mt-1 text-xs opacity-60 font-mono">
            {new Date(alert.timestamp).toLocaleTimeString()}
          </p>
        )}
      </div>
      <div className="ml-4 flex-shrink-0 flex">
        <button
          onClick={closeAlert}
          className={`inline-flex rounded-md p-1 focus:outline-none focus:ring-2 focus:ring-offset-2 ${iconColors[alert.severity]} hover:bg-black/5 transition-colors`}
        >
          <span className="sr-only">Close</span>
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
