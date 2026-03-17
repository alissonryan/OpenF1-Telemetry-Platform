'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SimpleSessionSelectorProps {
  onSelect: (sessionKey: number) => void;
  className?: string;
}

interface Meeting {
  meeting_key: number;
  meeting_name: string;
  circuit_short_name: string;
  year: number;
}

interface Session {
  session_key: number;
  session_name: string;
  session_type: string;
  meeting_key: number;
  date_start: string;
}

export default function SimpleSessionSelector({ onSelect, className }: SimpleSessionSelectorProps) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedMeetingKey, setSelectedMeetingKey] = useState<number | null>(null);
  const [selectedSessionKey, setSelectedSessionKey] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMeetingOpen, setIsMeetingOpen] = useState(false);
  const [isSessionOpen, setIsSessionOpen] = useState(false);

  // Fetch meetings on mount
  useEffect(() => {
    fetchMeetings();
  }, []);

  // Fetch sessions when meeting is selected
  useEffect(() => {
    if (selectedMeetingKey) {
      fetchSessions(selectedMeetingKey);
    }
  }, [selectedMeetingKey]);

  const fetchMeetings = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/sessions/meetings?year=2024');
      const data = await response.json();
      setMeetings(data.slice(0, 10)); // Limit to recent meetings
    } catch (error) {
      console.error('Failed to fetch meetings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSessions = async (meetingKey: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/sessions/sessions?meeting_key=${meetingKey}`);
      const data = await response.json();
      setSessions(data);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  };

  const handleMeetingSelect = (meetingKey: number) => {
    setSelectedMeetingKey(meetingKey);
    setSelectedSessionKey(null);
    setIsMeetingOpen(false);
  };

  const handleSessionSelect = (sessionKey: number) => {
    setSelectedSessionKey(sessionKey);
    setIsSessionOpen(false);
    onSelect(sessionKey);
  };

  const selectedMeeting = meetings.find((m) => m.meeting_key === selectedMeetingKey);
  const selectedSession = sessions.find((s) => s.session_key === selectedSessionKey);

  const sessionTypeColors: Record<string, string> = {
    Practice: 'bg-blue-500/20 text-blue-400',
    Qualifying: 'bg-purple-500/20 text-purple-400',
    Sprint: 'bg-orange-500/20 text-orange-400',
    Race: 'bg-f1-red/20 text-f1-red',
  };

  return (
    <div className={cn('flex flex-col gap-4 sm:flex-row sm:items-center', className)}>
      {/* Meeting Selector */}
      <div className="relative">
        <button
          onClick={() => setIsMeetingOpen(!isMeetingOpen)}
          disabled={isLoading}
          className={cn(
            'flex items-center gap-3 rounded-lg border border-white/10 bg-gray-800/50 px-4 py-3',
            'text-left transition-colors hover:bg-gray-800/70',
            isLoading && 'opacity-50 cursor-not-allowed'
          )}
        >
          <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <div className="flex-1">
            <p className="text-xs text-gray-400">Meeting</p>
            <p className="font-medium text-white">
              {selectedMeeting?.meeting_name || 'Select Meeting'}
            </p>
          </div>
          <motion.svg
            animate={{ rotate: isMeetingOpen ? 180 : 0 }}
            className="h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </motion.svg>
        </button>

        <AnimatePresence>
          {isMeetingOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute z-50 mt-2 w-72 rounded-lg border border-white/10 bg-gray-900 shadow-xl"
            >
              <div className="max-h-64 overflow-y-auto p-2">
                {meetings.map((meeting) => (
                  <button
                    key={meeting.meeting_key}
                    onClick={() => handleMeetingSelect(meeting.meeting_key)}
                    className={cn(
                      'w-full rounded-lg px-3 py-2 text-left transition-colors',
                      selectedMeetingKey === meeting.meeting_key
                        ? 'bg-f1-red/20 text-f1-red'
                        : 'hover:bg-white/5'
                    )}
                  >
                    <p className="font-medium text-white">{meeting.meeting_name}</p>
                    <p className="text-xs text-gray-400">
                      {meeting.circuit_short_name} • {meeting.year}
                    </p>
                  </button>
                ))}
                {meetings.length === 0 && (
                  <p className="px-3 py-4 text-center text-sm text-gray-400">
                    No meetings available
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Session Selector */}
      <div className="relative">
        <button
          onClick={() => setIsSessionOpen(!isSessionOpen)}
          disabled={isLoading || !selectedMeetingKey}
          className={cn(
            'flex items-center gap-3 rounded-lg border border-white/10 bg-gray-800/50 px-4 py-3',
            'text-left transition-colors hover:bg-gray-800/70',
            (isLoading || !selectedMeetingKey) && 'opacity-50 cursor-not-allowed'
          )}
        >
          <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="flex-1">
            <p className="text-xs text-gray-400">Session</p>
            <p className="font-medium text-white">
              {selectedSession?.session_name || 'Select Session'}
            </p>
          </div>
          <motion.svg
            animate={{ rotate: isSessionOpen ? 180 : 0 }}
            className="h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </motion.svg>
        </button>

        <AnimatePresence>
          {isSessionOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute z-50 mt-2 w-72 rounded-lg border border-white/10 bg-gray-900 shadow-xl"
            >
              <div className="max-h-64 overflow-y-auto p-2">
                {sessions.map((session) => (
                  <button
                    key={session.session_key}
                    onClick={() => handleSessionSelect(session.session_key)}
                    className={cn(
                      'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors',
                      selectedSessionKey === session.session_key
                        ? 'bg-f1-red/20 text-f1-red'
                        : 'hover:bg-white/5'
                    )}
                  >
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-xs font-medium',
                        sessionTypeColors[session.session_type] || 'bg-gray-500/20 text-gray-400'
                      )}
                    >
                      {session.session_type}
                    </span>
                    <div>
                      <p className="font-medium text-white">{session.session_name}</p>
                      <p className="text-xs text-gray-400">
                        {new Date(session.date_start).toLocaleDateString()}
                      </p>
                    </div>
                  </button>
                ))}
                {sessions.length === 0 && (
                  <p className="px-3 py-4 text-center text-sm text-gray-400">
                    No sessions available
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Live indicator */}
      {selectedSessionKey && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center gap-2 rounded-lg bg-green-500/10 px-3 py-2"
        >
          <div className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
          <span className="text-sm font-medium text-green-400">Session Active</span>
        </motion.div>
      )}
    </div>
  );
}
