'use client';

import { useEffect, useState } from 'react';

interface CoDriverAudioAlertProps {
  message: string;
  alertLevel?: string;
}

export default function CoDriverAudioAlert({
  message,
  alertLevel = 'NORMAL',
}: CoDriverAudioAlertProps) {
  const [speaking, setSpeaking] = useState(false);

  const speakResponse = () => {
    if (!message.trim()) return;

    if (
      typeof window === 'undefined' ||
      !('speechSynthesis' in window)
    ) {
      return;
    }

    // Stop any previous speech.
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(
      message
    );

    utterance.rate = 1.05;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      setSpeaking(true);
    };

    utterance.onend = () => {
      setSpeaking(false);
    };

    utterance.onerror = () => {
      setSpeaking(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  useEffect(() => {
    return () => {
      if (
        typeof window !== 'undefined' &&
        'speechSynthesis' in window
      ) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const levelClass =
    alertLevel === 'CRITICAL'
      ? 'border-red-800 bg-red-950/30'
      : alertLevel === 'ELEVATED'
        ? 'border-yellow-800 bg-yellow-950/20'
        : 'border-zinc-800 bg-zinc-900/80';

  const levelText =
    alertLevel === 'CRITICAL'
      ? 'CRITICAL'
      : alertLevel === 'ELEVATED'
        ? 'ELEVATED'
        : 'NORMAL';

  return (
    <div
      className={`rounded-2xl border p-6 ${levelClass}`}
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">
            Co-Driver Radio
          </h2>

          <p className="mt-1 text-xs text-zinc-500">
            Essential actionable response
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="rounded-full border border-zinc-700 bg-black/40 px-3 py-1 text-xs font-semibold">
            {levelText}
          </span>

          {speaking && (
            <span className="text-xs text-emerald-400">
              ● SPEAKING
            </span>
          )}
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-zinc-800 bg-black/50 p-5">
        <p className="text-lg font-semibold leading-relaxed">
          {message}
        </p>
      </div>

      <button
        type="button"
        onClick={speakResponse}
        disabled={speaking || !message.trim()}
        className="mt-4 rounded-lg bg-red-600 px-5 py-2 text-sm font-semibold transition hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {speaking
          ? 'Speaking...'
          : '🔊 Repeat Co-Driver'}
      </button>
    </div>
  );
}
