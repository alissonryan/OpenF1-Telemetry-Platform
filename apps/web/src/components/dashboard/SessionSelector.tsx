'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import type { Meeting, Session } from '@/types';

interface SessionSelectorProps {
  meetings: Meeting[];
  sessions: Session[];
  selectedMeetingKey?: number;
  selectedSessionKey?: number;
  onMeetingChange: (meetingKey: number) => void;
  onSessionChange: (sessionKey: number) => void;
  isLoading?: boolean;
}

const sessionTypeLabels: Record<Session['session_type'], string> = {
  practice: 'Practice',
  qualifying: 'Qualifying',
  sprint: 'Sprint',
  race: 'Race',
};

const sessionTypeColors: Record<Session['session_type'], string> = {
  practice: 'bg-blue-500/20 text-blue-400',
  qualifying: 'bg-purple-500/20 text-purple-400',
  sprint: 'bg-orange-500/20 text-orange-400',
  race: 'bg-f1-red/20 text-f1-red',
};

export default function SessionSelector({
  meetings,
  sessions,
  selectedMeetingKey,
  selectedSessionKey,
  onMeetingChange,
  onSessionChange,
  isLoading = false,
}: SessionSelectorProps) {
  const [isMeetingOpen, setIsMeetingOpen] = useState(false);
  const [isSessionOpen, setIsSessionOpen] = useState(false);

  const selectedMeeting = meetings.find((m) => m.meeting_key === selectedMeetingKey);
  const selectedSession = sessions.find((s) => s.session_key === selectedSessionKey);

  const handleMeetingSelect = useCallback(
    (meetingKey: number) => {
      onMeetingChange(meetingKey);
      setIsMeetingOpen(false);
    },
    [onMeetingChange]
  );

  const handleSessionSelect = useCallback(
    (sessionKey: number) => {
      onSessionChange(sessionKey);
      setIsSessionOpen(false);
    },
    [onSessionChange]
  );

  const filteredSessions = selectedMeetingKey
    ? sessions.filter((s) => s.meeting_key === selectedMeetingKey)
    : sessions;

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
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
          aria-expanded={isMeetingOpen}
          aria-haspopup="listbox"
        >
          <svg
            className="h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
            />
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
              role="listbox"
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
                    role="option"
                    aria-selected={selectedMeetingKey === meeting.meeting_key}
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
          aria-expanded={isSessionOpen}
          aria-haspopup="listbox"
        >
          <svg
            className="h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
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
              role="listbox"
            >
              <div className="max-h-64 overflow-y-auto p-2">
                {filteredSessions.map((session) => (
                  <button
                    key={session.session_key}
                    onClick={() => handleSessionSelect(session.session_key)}
                    className={cn(
                      'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors',
                      selectedSessionKey === session.session_key
                        ? 'bg-f1-red/20 text-f1-red'
                        : 'hover:bg-white/5'
                    )}
                    role="option"
                    aria-selected={selectedSessionKey === session.session_key}
                  >
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-xs font-medium',
                        sessionTypeColors[session.session_type]
                      )}
                    >
                      {sessionTypeLabels[session.session_type]}
                    </span>
                    <div>
                      <p className="font-medium text-white">{session.session_name}</p>
                      <p className="text-xs text-gray-400">
                        {new Date(session.date_start).toLocaleDateString()}
                      </p>
                    </div>
                  </button>
                ))}
                {filteredSessions.length === 0 && (
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
      {selectedSession && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center gap-2 rounded-lg bg-green-500/10 px-3 py-2"
        >
          <div className="live-indicator" />
          <span className="text-sm font-medium text-green-400">Session Active</span>
        </motion.div>
      )}
    </div>
  );
}

// Skeleton loader
export function SessionSelectorSkeleton() {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
      {[1, 2].map((i) => (
        <div
          key={i}
          className="h-[68px] w-72 animate-pulse rounded-lg bg-gray-800/50"
        />
      ))}
    </div>
  );
}
