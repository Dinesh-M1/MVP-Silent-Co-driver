'use client';

import {
  ChangeEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';

import LapPerformanceChart from '../components/LapPerformanceChart';


/* ============================================================
   CONFIGURATION
   ============================================================ */

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  'http://127.0.0.1:8000';


/* ============================================================
   TYPES
   ============================================================ */

interface Telemetry {
  speed_kmh: number | null;
  speed_available: boolean;
  rpm: number | null;
  gear: number | null;
  throttle: number | null;
  brake: number | null;
  fatigue: string;
  fatigue_score: number;
  workload: string;
  telemetry_source: string;
  udp_connected?: boolean;
  udp_packet_format?: number | null;
  udp_game_year?: number | null;
  udp_game_major?: number | null;
  udp_game_minor?: number | null;
}

interface AnalysisResult {
  transcript: string;

  stress_index: number;

  alert_level: string;

  emotion_label: string;

  confidence: number;

  inference_source?: string | null;

  detected_signals: string[];

  driver_message: string;

  telemetry: Telemetry;

  strategy: {
    action: string;
    target_compound: string;
    recommended_pit_lap: number | null;
  };

  voice_analysis: {
    emotion: string;
    tone: string;
    energy: number;
    speech_rate: string;
    voice_confidence: number;
  };

  driver_state: {
    state: string;
    stress: number;
    fatigue: string;
    fatigue_score: number;
    workload: string;
    confidence: number;
  };

  important_events: Array<{
    lap: number;
    event_type: string;
    title: string;
    description: string;
    severity: string;
    confidence: number;
  }>;

  lap_performance: Array<{
    lap: number;
    lap_time: number | null;
    stress: number;
    fatigue: number;
    driver_state: string;
    event: string | null;
    event_type: string | null;
    confidence: number;
  }>;

  decision: {
    priority: string;
    action: string;
    reason: string;
    confidence: number;
  };

  co_driver_response: string;

  audio_filename?: string;

  audio_content_type?: string;

  driver_id?: string;

  lap_number?: number;

  asr_model?: string;

  asr_provider?: string;

  processing_time_seconds?: number;
}

interface TelemetryState extends Telemetry {
  lap_number: number | null;
  lap_time: number | null;
}


/* ============================================================
   HELPERS
   ============================================================ */

function percent(
  value: number | null | undefined,
): number {

  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return 0;
  }

  return Math.round(
    Math.max(
      0,
      Math.min(
        1,
        value,
      ),
    ) * 100,
  );
}


function formatNumber(
  value: number | null,
  digits = 0,
): string {

  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return '--';
  }

  return value.toFixed(digits);
}


function formatLapTime(
  value: number | null,
): string {

  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return '--';
  }

  const minutes =
    Math.floor(value / 60);

  const seconds =
    value % 60;

  return (
    `${minutes}:${seconds
      .toFixed(3)
      .padStart(6, '0')}`
  );
}


function severityClass(
  severity: string,
): string {

  const value =
    severity.toUpperCase();

  if (value === 'CRITICAL') {
    return 'border-red-700 bg-red-950/40 text-red-300';
  }

  if (value === 'HIGH') {
    return 'border-orange-800 bg-orange-950/30 text-orange-300';
  }

  if (value === 'MEDIUM') {
    return 'border-yellow-800 bg-yellow-950/20 text-yellow-300';
  }

  return 'border-zinc-800 bg-zinc-950 text-zinc-400';
}


function stateClass(
  state: string,
): string {

  const value =
    state.toUpperCase();

  if (value === 'CRITICAL') {
    return 'border-red-700 bg-red-950/30 text-red-300';
  }

  if (value === 'ELEVATED') {
    return 'border-yellow-800 bg-yellow-950/20 text-yellow-300';
  }

  return 'border-green-900 bg-green-950/20 text-green-400';
}


function readableSignal(
  signal: string,
): string {

  return signal
    .replaceAll('_', ' ')
    .replace(/\b\w/g, char =>
      char.toUpperCase(),
    );
}


/* ============================================================
   PAGE
   ============================================================ */

export default function Page() {

  /* ==========================================================
     STATE
     ========================================================== */

  const [
    analysis,
    setAnalysis,
  ] = useState<AnalysisResult | null>(
    null,
  );


  const [
    telemetry,
    setTelemetry,
  ] = useState<TelemetryState>({
    speed_kmh: null,
    speed_available: false,
    rpm: null,
    gear: null,
    throttle: null,
    brake: null,
    fatigue: 'LOW',
    fatigue_score: 0,
    workload: 'NORMAL',
    telemetry_source:
      'No live simulator connected',
    lap_number: null,
    lap_time: null,
  });


  const [
    backendOnline,
    setBackendOnline,
  ] = useState(false);


  const [
    backendError,
    setBackendError,
  ] = useState<string | null>(
    null,
  );


  const [
    transcriptInput,
    setTranscriptInput,
  ] = useState('');


  const [
    selectedAudio,
    setSelectedAudio,
  ] = useState<File | null>(
    null,
  );


  const [
    audioUrl,
    setAudioUrl,
  ] = useState<string | null>(
    null,
  );


  const [
    isAnalyzing,
    setIsAnalyzing,
  ] = useState(false);


  const [
    isRecording,
    setIsRecording,
  ] = useState(false);


  const [
    voiceError,
    setVoiceError,
  ] = useState<string | null>(
    null,
  );


  const [
    audioError,
    setAudioError,
  ] = useState<string | null>(
    null,
  );


  const [
    isSpeaking,
    setIsSpeaking,
  ] = useState(false);


  const audioInputRef =
    useRef<HTMLInputElement | null>(
      null,
    );


  /* ==========================================================
     BACKEND HEALTH
     ========================================================== */

  const checkBackend =
    useCallback(
      async () => {

        try {

          const response =
            await fetch(
              `${BACKEND_URL}/health`,
              {
                method: 'GET',
                cache: 'no-store',
              },
            );

          if (!response.ok) {
            throw new Error(
              `Backend returned ${response.status}`,
            );
          }

          setBackendOnline(true);
          setBackendError(null);

        } catch (error) {

          console.error(
            'Backend health check failed:',
            error,
          );

          setBackendOnline(false);

          setBackendError(
            'Backend connection unavailable. Retrying automatically.',
          );
        }
      },
      [],
    );


  useEffect(() => {

    checkBackend();

    const timer =
      window.setInterval(
        checkBackend,
        5000,
      );

    return () => {
      window.clearInterval(timer);
    };

  }, [checkBackend]);


  /* ==========================================================
     TELEMETRY POLLING
     ========================================================== */

  const loadTelemetry =
    useCallback(
      async () => {

        try {

          const response =
            await fetch(
              `${BACKEND_URL}/api/v1/telemetry`,
              {
                cache: 'no-store',
              },
            );

          if (!response.ok) {
            return;
          }

          const data =
            await response.json();

          setTelemetry({
            speed_kmh:
              typeof data.speed_kmh === 'number'
                ? data.speed_kmh
                : null,

            speed_available:
              Boolean(
                data.speed_available &&
                data.udp_connected,
              ),

            rpm:
              typeof data.rpm === 'number'
                ? data.rpm
                : null,

            gear:
              typeof data.gear === 'number'
                ? data.gear
                : null,

            throttle:
              typeof data.throttle === 'number'
                ? data.throttle
                : null,

            brake:
              typeof data.brake === 'number'
                ? data.brake
                : null,

            fatigue:
              typeof data.fatigue === 'string'
                ? data.fatigue
                : 'LOW',

            fatigue_score:
              typeof data.fatigue_score === 'number'
                ? data.fatigue_score
                : 0,

            workload:
              typeof data.workload === 'string'
                ? data.workload
                : 'NORMAL',

            telemetry_source:
              typeof data.telemetry_source === 'string'
                ? data.telemetry_source
                : 'No live simulator connected',

            lap_number:
              typeof data.lap_number === 'number' &&
              data.lap_number > 0
                ? data.lap_number
                : null,

            lap_time:
              typeof data.lap_time === 'number'
                ? data.lap_time
                : null,

            udp_connected:
              Boolean(data.udp_connected),

            udp_packet_format:
              typeof data.udp_packet_format === 'number'
                ? data.udp_packet_format
                : null,

            udp_game_year:
              typeof data.udp_game_year === 'number'
                ? data.udp_game_year
                : null,

            udp_game_major:
              typeof data.udp_game_major === 'number'
                ? data.udp_game_major
                : null,

            udp_game_minor:
              typeof data.udp_game_minor === 'number'
                ? data.udp_game_minor
                : null,
          });

        } catch (error) {

          console.error(
            'Telemetry fetch failed:',
            error,
          );
        }
      },
      [],
    );


  useEffect(() => {

    loadTelemetry();

    const timer =
      window.setInterval(
        loadTelemetry,
        2000,
      );

    return () => {
      window.clearInterval(timer);
    };

  }, [loadTelemetry]);


  /* ==========================================================
     AUDIO FILE SELECTION
     ========================================================== */

  const handleAudioSelect =
    (
      event: ChangeEvent<HTMLInputElement>,
    ) => {

      const file =
        event.target.files?.[0];

      if (!file) {
        return;
      }

      setAudioError(null);
      setVoiceError(null);

      setSelectedAudio(file);

      if (audioUrl) {
        URL.revokeObjectURL(
          audioUrl,
        );
      }

      const url =
        URL.createObjectURL(file);

      setAudioUrl(url);
    };


  /* ==========================================================
     TEXT ANALYSIS
     ========================================================== */

   const analyzeText =
  useCallback(
    async () => {

      const text =
        transcriptInput.trim();

      if (!text) {

        setVoiceError(
          'Enter a driver radio message first.',
        );

        return;
      }

      if (!backendOnline) {

        setVoiceError(
          'Backend is offline. Start FastAPI on port 8000.',
        );

        return;
      }

      setIsAnalyzing(true);

      setVoiceError(null);

      setAudioError(null);

      try {

        const response =
          await fetch(
            `${BACKEND_URL}/api/v1/analyze`,
            {
              method: 'POST',

              headers: {
                'Content-Type':
                  'application/json',

                Accept:
                  'application/json',
              },

              body: JSON.stringify({
                text_input:
                  text,

                driver_id:
                  'DRIVER_01',
              }),
            },
          );

        const raw =
          await response.text();

        let data:
          | AnalysisResult
          | {
              detail?: string;
            };

        try {

          data =
            JSON.parse(
              raw,
            );

        } catch {

          throw new Error(
            raw ||
            `Backend returned ${response.status}`,
          );
        }

        if (!response.ok) {

          throw new Error(
            (
              data as {
                detail?: string;
              }
            ).detail ||
            `Text analysis failed: ${response.status}`,
          );
        }

        const result =
          data as AnalysisResult;

        setAnalysis(
          result,
        );

        setTranscriptInput(
          result.transcript ||
          text,
        );

        setTelemetry(
          previous => ({
            ...previous,

            ...(result.telemetry ||
              {}),
          }),
        );

      } catch (error) {

        console.error(
          'Text analysis failed:',
          error,
        );

        const message =
          error instanceof TypeError &&
          error.message ===
            'Failed to fetch'

            ? `Cannot reach backend at ${BACKEND_URL}. Check that FastAPI is running on port 8000.`

            : error instanceof Error

              ? error.message

              : 'Driver analysis failed.';

        setVoiceError(
          message,
        );

      } finally {

        setIsAnalyzing(
          false,
        );
      }

    },
    [
      backendOnline,
      transcriptInput,
    ],
  );
  /* ==========================================================
     AUDIO ANALYSIS
     ========================================================== */

  const analyzeAudio =
    useCallback(
      async () => {

        if (!selectedAudio) {

          setAudioError(
            'Select a driver radio audio file first.',
          );

          return;
        }

        if (!backendOnline) {

          setAudioError(
            'Backend is offline. Start FastAPI on port 8000.',
          );

          return;
        }

        setIsAnalyzing(true);

        setAudioError(null);
        setVoiceError(null);

        try {

          const formData =
            new FormData();

          /*
           * IMPORTANT:
           * Backend expects the UploadFile parameter
           * to be named "audio".
           */

          formData.append(
            'audio',
            selectedAudio,
            selectedAudio.name,
          );

          formData.append(
            'driver_id',
            'DRIVER_01',
          );

          if (
            telemetry.udp_connected &&
            telemetry.lap_number !== null &&
            telemetry.lap_number > 0
          ) {
            formData.append(
              'lap_number',
              String(
                telemetry.lap_number,
              ),
            );
          }


          const response =
            await fetch(
              `${BACKEND_URL}/api/v1/analyze-audio`,
              {
                method: 'POST',
                body: formData,
              },
            );


          const raw =
            await response.text();


          let data:
            | AnalysisResult
            | { detail?: unknown };


          try {

            data =
              JSON.parse(raw);

          } catch {

            throw new Error(
              raw ||
              `Backend returned ${response.status}`,
            );
          }


          if (!response.ok) {

            const detail =
              (
                data as {
                  detail?: unknown;
                }
              ).detail;

            throw new Error(
              typeof detail === 'string'
                ? detail
                : JSON.stringify(
                    detail ||
                    `Audio analysis failed: ${response.status}`,
                  ),
            );
          }


          const result =
            data as AnalysisResult;


          setAnalysis(result);


          /*
           * Whisper transcript becomes available
           * immediately in the radio message box.
           */

          setTranscriptInput(
            result.transcript ||
            '',
          );


          // The 2-second telemetry poll is authoritative for
          // live vehicle values. Do not overwrite it with the
          // voice-analysis snapshot, which may contain stale data.
          if (
            result.telemetry &&
            result.telemetry.udp_connected
          ) {
            setTelemetry(
              previous => ({
                ...previous,
                ...result.telemetry,
              }),
            );
          }


        } catch (error) {

          console.error(
            'Audio analysis failed:',
            error,
          );

          setAudioError(
            error instanceof Error
              ? error.message
              : 'Driver audio analysis failed.',
          );

        } finally {

          setIsAnalyzing(false);
        }

      },
      [
        backendOnline,
        selectedAudio,
        telemetry.lap_number,
      ],
    );


  /* ==========================================================
     BROWSER SPEECH RECOGNITION
     ========================================================== */

  const startRecording =
    async () => {

      setVoiceError(null);

      try {

        if (
          typeof window ===
          'undefined'
        ) {
          return;
        }


        type RecognitionResult =
          ArrayLike<
            ArrayLike<{
              transcript: string;
            }>
          >;


        type RecognitionInstance = {
          lang: string;
          interimResults: boolean;
          continuous: boolean;

          start: () => void;

          stop: () => void;

          onresult:
            | ((
                event: {
                  results: RecognitionResult;
                },
              ) => void)
            | null;

          onerror:
            | ((
                event: {
                  error?: string;
                },
              ) => void)
            | null;

          onend:
            | (() => void)
            | null;
        };


        type RecognitionConstructor =
          new () => RecognitionInstance;


        const browserWindow =
          window as typeof window & {
            SpeechRecognition?: RecognitionConstructor;

            webkitSpeechRecognition?: RecognitionConstructor;
          };


        const SpeechRecognition =
          browserWindow.SpeechRecognition ||
          browserWindow.webkitSpeechRecognition;


        if (!SpeechRecognition) {

          setVoiceError(
            'Browser speech recognition is unavailable. Type the radio message or upload an audio file instead.',
          );

          return;
        }


        const recognition =
          new SpeechRecognition();


        recognition.lang =
          'en-US';

        recognition.interimResults =
          false;

        recognition.continuous =
          false;


        recognition.onresult =
          event => {

            const transcript =
              Array.from(
                event.results,
              )
                .map(
                  result =>
                    result[0]
                      ?.transcript ||
                    '',
                )
                .join(' ')
                .trim();


            if (transcript) {

              setTranscriptInput(
                transcript,
              );
            }
          };


        recognition.onerror =
          event => {

            console.error(
              'Browser speech recognition:',
              event,
            );

            setVoiceError(
              'Browser speech recognition is unavailable. Use Upload Audio for reliable Whisper analysis.',
            );

            setIsRecording(false);
          };


        recognition.onend =
          () => {
            setIsRecording(false);
          };


        recognition.start();

        setIsRecording(true);

      } catch (error) {

        console.error(
          'Recording error:',
          error,
        );

        setIsRecording(false);

        setVoiceError(
          'Unable to start browser speech recognition. Upload an audio file instead.',
        );
      }
    };


  const stopRecording =
    () => {

      setIsRecording(false);
    };


  /* ==========================================================
     CO-DRIVER SPEECH
     ========================================================== */

  const speakResponse =
    () => {

      const message =
        analysis?.co_driver_response ||
        analysis?.driver_message;

      if (!message) {
        return;
      }

      if (
        typeof window ===
        'undefined' ||
        !window.speechSynthesis
      ) {
        return;
      }

      window.speechSynthesis.cancel();


      const utterance =
        new SpeechSynthesisUtterance(
          message,
        );


      utterance.rate = 1.05;
      utterance.pitch = 0.85;
      utterance.volume = 1;


      utterance.onstart =
        () => {
          setIsSpeaking(true);
        };


      utterance.onend =
        () => {
          setIsSpeaking(false);
        };


      utterance.onerror =
        () => {
          setIsSpeaking(false);
        };


      window.speechSynthesis.speak(
        utterance,
      );
    };


  /* ==========================================================
     CLEANUP
     ========================================================== */

  useEffect(() => {

    return () => {

      if (audioUrl) {
        URL.revokeObjectURL(
          audioUrl,
        );
      }

      if (
        typeof window !==
        'undefined'
      ) {
        window.speechSynthesis?.cancel();
      }
    };

  }, [audioUrl]);


  /* ==========================================================
     CURRENT VALUES
     ========================================================== */

  // F1 UDP is the only authoritative lap source.
  // No simulator = no lap.
  const currentLap =
    telemetry.udp_connected &&
    telemetry.lap_number !== null
      ? telemetry.lap_number
      : null;


  const stress =
    analysis?.stress_index ??
    0;


  const fatigue =
    analysis?.driver_state
      ?.fatigue_score ??
    telemetry.fatigue_score ??
    0;


  const driverState =
    analysis?.driver_state
      ?.state ??
    'NORMAL';


  const latestEvent =
    analysis?.important_events?.at(-1);


  const signals =
    analysis?.detected_signals ??
    [];


  const telemetryConnected =
    Boolean(
      telemetry.udp_connected,
    );


  const statusText =
    isAnalyzing
      ? 'ANALYZING'
      : backendOnline
        ? 'ONLINE'
        : 'OFFLINE';


  /* ==========================================================
     RENDER
     ========================================================== */

  return (
    <main className="min-h-screen bg-black text-white">

      {/* ======================================================
          HEADER
          ====================================================== */}

      <header className="sticky top-0 z-50 border-b border-zinc-900 bg-black/95 backdrop-blur">

        <div className="mx-auto flex max-w-[1800px] items-center justify-between px-5 py-4">

          <div>

            <div className="flex items-center gap-3">

              <span className="text-lg font-black tracking-[0.2em]">
                SILENT CO-DRIVER
              </span>

              <span className="rounded-full border border-zinc-800 px-2 py-1 text-[8px] font-bold tracking-widest text-zinc-500">
                AI RACE INTELLIGENCE
              </span>

            </div>

            <p className="mt-1 text-[9px] uppercase tracking-[0.25em] text-zinc-600">
              Driver state • Voice intelligence • Race strategy • Engineer monitoring
            </p>

          </div>


          <div className="flex items-center gap-3">

            <span
              className={`h-2.5 w-2.5 rounded-full ${
                backendOnline
                  ? 'animate-pulse bg-green-500'
                  : 'bg-red-500'
              }`}
            />

            <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
              {statusText}
            </span>

          </div>

        </div>

      </header>


      <div className="mx-auto max-w-[1800px] px-5 py-5">

        {/* ====================================================
            BACKEND ERROR
            ==================================================== */}

        {backendError && (

          <div className="mb-4 rounded-xl border border-red-950 bg-red-950/20 px-4 py-3">

            <div className="flex items-center justify-between gap-3">

              <div>

                <p className="text-xs font-semibold text-red-300">
                  BACKEND CONNECTION
                </p>

                <p className="mt-1 text-[10px] text-red-400/70">
                  {backendError}
                </p>

              </div>

              <button
                type="button"
                onClick={checkBackend}
                className="rounded-lg border border-red-900 px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-red-300 hover:bg-red-950"
              >
                Retry
              </button>

            </div>

          </div>
        )}


        {/* ====================================================
            MAIN HORIZONTAL ENGINEER DASHBOARD
            ==================================================== */}

        <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">


          {/* ==================================================
              DRIVER RADIO
              ================================================== */}

          <section className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5">

            <div className="flex items-start justify-between gap-4">

              <div>

                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-600">
                  DRIVER RADIO
                </p>

                <h1 className="mt-1 text-xl font-bold">
                  Voice Input
                </h1>

              </div>


              {selectedAudio && (

                <span className="max-w-[220px] truncate rounded-lg border border-zinc-800 px-3 py-2 text-[9px] text-zinc-500">
                  {selectedAudio.name}
                </span>

              )}

            </div>


            {/* INPUT CONTROLS */}

            <div className="mt-5 grid grid-cols-2 gap-3">

              <button
                type="button"
                onClick={
                  isRecording
                    ? stopRecording
                    : startRecording
                }
                className={`rounded-xl border px-4 py-4 text-xs font-bold uppercase tracking-widest transition ${
                  isRecording
                    ? 'border-red-600 bg-red-950/30 text-red-300'
                    : 'border-zinc-800 bg-black text-zinc-300 hover:border-zinc-600'
                }`}
              >
                {isRecording
                  ? '■ Stop Recording'
                  : '🎙 Record'}
              </button>


              <button
                type="button"
                onClick={() =>
                  audioInputRef.current?.click()
                }
                className="rounded-xl border border-zinc-800 bg-black px-4 py-4 text-xs font-bold uppercase tracking-widest text-zinc-300 transition hover:border-zinc-600"
              >
                📁 Upload Audio
              </button>


              <input
                ref={audioInputRef}
                type="file"
                accept="audio/*,.mp3,.wav,.webm,.m4a,.ogg,.flac"
                className="hidden"
                onChange={handleAudioSelect}
              />

            </div>


            {/* AUDIO PLAYER */}

            {audioUrl && (

              <div className="mt-4 rounded-xl border border-zinc-800 bg-black p-3">

                <audio
                  controls
                  src={audioUrl}
                  className="w-full"
                />

              </div>

            )}


            {/* TRANSCRIPT */}

            <div className="mt-5">

              <div className="mb-2 flex items-center justify-between">

                <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-zinc-600">
                  Radio Message
                </p>

                <span className="text-[9px] text-zinc-700">
                  Whisper / Text
                </span>

              </div>


              <textarea
                value={transcriptInput}
                onChange={event =>
                  setTranscriptInput(
                    event.target.value,
                  )
                }
                placeholder="Driver radio message..."
                rows={3}
                className="w-full resize-none rounded-xl border border-zinc-800 bg-black p-4 text-sm text-zinc-200 outline-none transition placeholder:text-zinc-700 focus:border-zinc-600"
              />

            </div>


            {voiceError && (

              <div className="mt-3 rounded-lg border border-yellow-950 bg-yellow-950/20 px-3 py-2 text-[10px] text-yellow-500">
                {voiceError}
              </div>

            )}


            {audioError && (

              <div className="mt-3 rounded-lg border border-red-950 bg-red-950/20 px-3 py-2 text-[10px] text-red-400">
                {audioError}
              </div>

            )}


            {/* ANALYZE */}

            <div className="mt-4 grid gap-3 sm:grid-cols-2">

              <button
                type="button"
                disabled={
                  isAnalyzing ||
                  !backendOnline ||
                  !selectedAudio
                }
                onClick={analyzeAudio}
                className="rounded-xl bg-white px-4 py-4 text-xs font-black uppercase tracking-widest text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-30"
              >
                {isAnalyzing
                  ? 'Analyzing Audio...'
                  : 'Analyze Audio'}
              </button>


              <button
                type="button"
                disabled={
                  isAnalyzing ||
                  !backendOnline ||
                  !transcriptInput.trim()
                }
                onClick={analyzeText}
                className="rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-4 text-xs font-black uppercase tracking-widest text-white transition hover:border-zinc-500 disabled:cursor-not-allowed disabled:opacity-30"
              >
                {isAnalyzing
                  ? 'Analyzing...'
                  : 'Analyze Radio'}
              </button>

            </div>

          </section>


          {/* ==================================================
              ENGINEER MONITOR
              ================================================== */}

          <section className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5">

            <div className="flex items-center justify-between">

              <div>

                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-600">
                  RACE ENGINEER MONITOR
                </p>

                <p className="mt-1 text-xs text-zinc-700">
                  Current driver condition
                </p>

              </div>


              <span
                className={`rounded-full border px-3 py-1 text-[9px] font-bold tracking-widest ${stateClass(
                  driverState,
                )}`}
              >
                {driverState}
              </span>

            </div>


            {/* STATE */}

            <div className="mt-5 flex items-end justify-between">

              <div>

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  DRIVER STATE
                </p>

                <p className="mt-1 text-4xl font-black">
                  {driverState}
                </p>

              </div>


              <div className="text-right">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  LAP
                </p>

                <p className="mt-1 text-3xl font-black">
                  {currentLap ?? '--'}
                </p>

              </div>

            </div>


            {/* METRICS */}

            <div className="mt-6 grid grid-cols-3 gap-3">

              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Stress
                </p>

                <p className="mt-2 text-2xl font-black text-red-400">
                  {percent(stress)}%
                </p>

              </div>


              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Fatigue
                </p>

                <p className="mt-2 text-2xl font-black text-yellow-400">
                  {percent(fatigue)}%
                </p>

              </div>


              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Confidence
                </p>

                <p className="mt-2 text-2xl font-black text-cyan-400">
                  {percent(
                    analysis?.confidence,
                  )}%
                </p>

              </div>

            </div>


            {/* LOAD BARS */}

            <div className="mt-5 space-y-4">

              <div>

                <div className="mb-1 flex justify-between text-[9px] uppercase tracking-widest">

                  <span className="text-zinc-600">
                    Stress Load
                  </span>

                  <span className="text-red-400">
                    {percent(stress)}%
                  </span>

                </div>

                <div className="h-2 overflow-hidden rounded-full bg-zinc-900">

                  <div
                    className="h-full rounded-full bg-red-500 transition-all duration-700"
                    style={{
                      width:
                        `${percent(stress)}%`,
                    }}
                  />

                </div>

              </div>


              <div>

                <div className="mb-1 flex justify-between text-[9px] uppercase tracking-widest">

                  <span className="text-zinc-600">
                    Fatigue Load
                  </span>

                  <span className="text-yellow-400">
                    {percent(fatigue)}%
                  </span>

                </div>

                <div className="h-2 overflow-hidden rounded-full bg-zinc-900">

                  <div
                    className="h-full rounded-full bg-yellow-400 transition-all duration-700"
                    style={{
                      width:
                        `${percent(fatigue)}%`,
                    }}
                  />

                </div>

              </div>

            </div>


            {/* VOICE ANALYSIS */}

            <div className="mt-5 grid grid-cols-3 gap-3 border-t border-zinc-900 pt-5">

              <div>

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Tone
                </p>

                <p className="mt-1 text-sm font-bold">
                  {analysis?.voice_analysis?.tone || '--'}
                </p>

              </div>


              <div>

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Emotion
                </p>

                <p className="mt-1 text-sm font-bold">
                  {analysis?.voice_analysis?.emotion ||
                    analysis?.emotion_label ||
                    '--'}
                </p>

              </div>


              <div>

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Energy
                </p>

                <p className="mt-1 text-sm font-bold">
                  {percent(
                    analysis?.voice_analysis?.energy,
                  )}%
                </p>

              </div>

            </div>

          </section>

        </div>


        {/* ====================================================
            ENGINEER DECISION + TELEMETRY
            ==================================================== */}

        <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1.5fr]">


          {/* ENGINEER DECISION */}

          <section className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5">

            <div className="flex items-center justify-between">

              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-600">
                ENGINEER DECISION
              </p>

              {analysis?.decision && (

                <span className="rounded-full border border-red-900 bg-red-950/20 px-3 py-1 text-[9px] font-bold uppercase tracking-widest text-red-400">
                  {analysis.decision.priority}
                </span>

              )}

            </div>


            <p className="mt-4 text-base font-bold leading-relaxed text-white">

              {analysis?.decision?.action ||
                analysis?.strategy?.action ||
                'Continue monitoring driver and vehicle state.'}

            </p>


            {analysis?.decision?.reason && (

              <p className="mt-3 text-xs leading-relaxed text-zinc-600">
                {analysis.decision.reason}
              </p>

            )}


            <div className="mt-5 grid grid-cols-2 gap-3">

              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Target Compound
                </p>

                <p className="mt-1 text-sm font-bold">
                  {analysis?.strategy?.target_compound ||
                    '--'}
                </p>

              </div>


              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Recommended Pit
                </p>

                <p className="mt-1 text-sm font-bold">
                  {analysis?.strategy?.recommended_pit_lap ??
                    '--'}
                </p>

              </div>

            </div>

          </section>


          {/* TELEMETRY */}

          <section className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5">

            <div className="flex items-center justify-between">

              <div>

                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-600">
                  LIVE VEHICLE TELEMETRY
                </p>

                <p className="mt-1 text-xs text-zinc-700">
                  {telemetry.telemetry_source}
                </p>

              </div>


              <span
                className={`rounded-full border px-3 py-1 text-[9px] font-bold uppercase tracking-widest ${
                  telemetryConnected
                    ? 'border-green-900 bg-green-950/20 text-green-400'
                    : 'border-zinc-800 text-zinc-600'
                }`}
              >
                {telemetryConnected
                  ? 'SIMULATOR CONNECTED'
                  : 'NO SIMULATOR'}
              </span>

            </div>


            <div className="mt-5 grid grid-cols-3 gap-3 sm:grid-cols-6">

              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Speed
                </p>

                <p className="mt-2 text-xl font-black">
                  {formatNumber(
                    telemetry.speed_kmh,
                  )}

                  <span className="ml-1 text-[9px] text-zinc-700">
                    KM/H
                  </span>
                </p>

              </div>


              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  RPM
                </p>

                <p className="mt-2 text-xl font-black">
                  {telemetry.rpm ?? '--'}
                </p>

              </div>


              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Gear
                </p>

                <p className="mt-2 text-xl font-black">
                  {telemetry.gear ?? '--'}
                </p>

              </div>


              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Throttle
                </p>

                <p className="mt-2 text-xl font-black">
                  {telemetry.throttle === null
                    ? '--'
                    : `${percent(
                        telemetry.throttle,
                      )}%`}
                </p>

              </div>


              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Brake
                </p>

                <p className="mt-2 text-xl font-black">
                  {telemetry.brake === null
                    ? '--'
                    : `${percent(
                        telemetry.brake,
                      )}%`}
                </p>

              </div>


              <div className="rounded-xl border border-zinc-800 bg-black p-3">

                <p className="text-[9px] uppercase tracking-widest text-zinc-600">
                  Lap Time
                </p>

                <p className="mt-2 text-xl font-black">
                  {formatLapTime(
                    telemetry.lap_time,
                  )}
                </p>

              </div>

            </div>

          </section>

        </div>


        {/* ====================================================
            MAIN ENGINEER GRAPH
            ==================================================== */}

        <div className="mt-4">

          <LapPerformanceChart
            backendUrl={BACKEND_URL}
            currentLap={
              currentLap ??
              undefined
            }
            latestAnalysis={
              analysis &&
              currentLap !== null
                ? {
                    lap:
                      currentLap,

                    stress_index:
                      analysis.stress_index,

                    confidence:
                      analysis.confidence,

                    driver_state:
                      analysis.driver_state,

                    important_events:
                      analysis.important_events,

                    lap_performance:
                      analysis.lap_performance,

                    strategy: {
                      action:
                        analysis.strategy.action,

                      target_compound:
                        analysis.strategy.target_compound,

                      recommended_pit_lap:
                        analysis.strategy
                          .recommended_pit_lap ??
                        undefined,
                    },

                    decision:
                      analysis.decision,
                  }
                : undefined
            }
          />

        </div>


        {/* ====================================================
            EVENTS + RADIO
            ==================================================== */}

        <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">


          {/* EVENTS */}

          <section className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5">

            <div className="flex items-center justify-between">

              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-600">
                RACE EVENTS
              </p>

              <span className="text-[9px] text-zinc-700">
                {analysis?.important_events?.length || 0} detected
              </span>

            </div>


            <div className="mt-4 space-y-2">

              {analysis?.important_events?.length ? (

                analysis.important_events
                  .slice(-5)
                  .reverse()
                  .map(event => (

                    <div
                      key={`${event.lap}-${event.title}`}
                      className="rounded-xl border border-zinc-800 bg-black p-4"
                    >

                      <div className="flex items-center justify-between gap-3">

                        <div className="flex items-center gap-2">

                          <span
                            className={`h-2 w-2 rounded-full ${
                              event.severity.toUpperCase() ===
                              'CRITICAL'
                                ? 'bg-red-500'
                                : event.severity.toUpperCase() ===
                                    'HIGH'
                                  ? 'bg-orange-400'
                                  : 'bg-yellow-400'
                            }`}
                          />

                          <span className="text-xs font-bold text-white">
                            {event.title}
                          </span>

                        </div>


                        <span className="text-[9px] uppercase tracking-widest text-zinc-600">
                          LAP {event.lap}
                        </span>

                      </div>


                      <p className="mt-2 text-xs leading-relaxed text-zinc-500">
                        {event.description}
                      </p>


                      <div className="mt-3 flex gap-2">

                        <span
                          className={`rounded-lg border px-2 py-1 text-[8px] font-bold uppercase tracking-widest ${severityClass(
                            event.severity,
                          )}`}
                        >
                          {event.severity}
                        </span>


                        <span className="rounded-lg border border-zinc-800 px-2 py-1 text-[8px] font-bold uppercase tracking-widest text-zinc-600">
                          {Math.round(
                            event.confidence * 100,
                          )}% CONF
                        </span>

                      </div>

                    </div>

                  ))

              ) : (

                <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center">

                  <p className="text-sm text-zinc-600">
                    No significant race events detected.
                  </p>

                </div>

              )}

            </div>

          </section>


          {/* CO-DRIVER */}

          <section className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5">

            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-600">
              SILENT CO-DRIVER
            </p>


            <p className="mt-5 text-lg font-bold leading-relaxed text-zinc-200">

              {analysis?.co_driver_response ||
                analysis?.driver_message ||
                'Awaiting driver-state analysis...'}

            </p>


            {signals.length > 0 && (

              <div className="mt-5">

                <p className="mb-2 text-[9px] uppercase tracking-widest text-zinc-600">
                  Detected Signals
                </p>


                <div className="flex flex-wrap gap-2">

                  {signals.map(
                    signal => (

                      <span
                        key={signal}
                        className="rounded-lg border border-zinc-800 bg-black px-3 py-2 text-[9px] font-bold uppercase tracking-wider text-zinc-400"
                      >
                        {readableSignal(
                          signal,
                        )}
                      </span>

                    ),
                  )}

                </div>

              </div>

            )}


            <button
              type="button"
              disabled={
                !analysis?.co_driver_response &&
                !analysis?.driver_message
              }
              onClick={speakResponse}
              className="mt-6 rounded-xl border border-zinc-700 bg-black px-5 py-4 text-xs font-black uppercase tracking-widest text-white transition hover:border-zinc-500 disabled:cursor-not-allowed disabled:opacity-30"
            >
              {isSpeaking
                ? '🔊 Speaking...'
                : '🔊 Play Co-Driver Response'}
            </button>

          </section>

        </div>


        {/* ====================================================
            IMPORTANT EVENT
            ==================================================== */}

        {latestEvent && (

          <section className="mt-4 rounded-2xl border border-red-950 bg-red-950/10 p-5">

            <div className="flex flex-wrap items-start justify-between gap-4">

              <div>

                <p className="text-[9px] font-bold uppercase tracking-[0.25em] text-red-500">
                  IMPORTANT RACE EVENT
                </p>

                <h2 className="mt-2 text-xl font-black text-white">
                  {latestEvent.title}
                </h2>

                <p className="mt-2 max-w-4xl text-sm leading-relaxed text-zinc-400">
                  {latestEvent.description}
                </p>

              </div>


              <div className="flex gap-2">

                <span
                  className={`rounded-lg border px-3 py-2 text-[9px] font-bold uppercase tracking-widest ${severityClass(
                    latestEvent.severity,
                  )}`}
                >
                  {latestEvent.severity}
                </span>


                <span className="rounded-lg border border-zinc-800 bg-black px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-zinc-500">
                  LAP {latestEvent.lap}
                </span>

              </div>

            </div>

          </section>

        )}

      </div>

    </main>
  );
}
