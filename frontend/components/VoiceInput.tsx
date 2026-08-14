'use client';

import {
  useEffect,
  useRef,
  useState,
} from 'react';


interface VoiceInputProps {

  value: string;

  onChange: (
    value: string
  ) => void;

  disabled?: boolean;

}


const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  'http://127.0.0.1:8000';


const AUDIO_ENDPOINT =
  `${BACKEND_URL}/api/v1/analyze-audio`;


export default function VoiceInput({
  value,
  onChange,
  disabled = false,
}: VoiceInputProps) {

  const mediaRecorderRef =
    useRef<MediaRecorder | null>(
      null,
    );

  const streamRef =
    useRef<MediaStream | null>(
      null,
    );

  const chunksRef =
    useRef<Blob[]>([]);

  const timerRef =
    useRef<number | null>(
      null,
    );


  const [
    recording,
    setRecording,
  ] = useState(false);


  const [
    processing,
    setProcessing,
  ] = useState(false);


  const [
    duration,
    setDuration,
  ] = useState(0);


  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  // ==========================================================
  // CLEANUP
  // ==========================================================

  useEffect(() => {

    return () => {

      if (
        timerRef.current !== null
      ) {

        window.clearInterval(
          timerRef.current,
        );

        timerRef.current = null;
      }


      if (
        streamRef.current
      ) {

        streamRef.current
          .getTracks()
          .forEach(
            (track) => {
              track.stop();
            },
          );

        streamRef.current = null;
      }

    };

  }, []);


  // ==========================================================
  // TIMER
  // ==========================================================

  const startTimer = () => {

    setDuration(0);

    timerRef.current =
      window.setInterval(
        () => {

          setDuration(
            previous =>
              previous + 1,
          );

        },
        1000,
      );
  };


  const stopTimer = () => {

    if (
      timerRef.current !== null
    ) {

      window.clearInterval(
        timerRef.current,
      );

      timerRef.current = null;
    }
  };


  // ==========================================================
  // START RECORDING
  // ==========================================================

  const startRecording =
    async () => {

      if (disabled) {
        return;
      }


      setError(null);


      if (
        !navigator.mediaDevices ||
        !navigator.mediaDevices
          .getUserMedia
      ) {

        setError(
          "This browser doesn't support microphone recording.",
        );

        return;
      }


      try {

        const stream =
          await navigator
            .mediaDevices
            .getUserMedia({
              audio: {
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
              },
            });


        streamRef.current =
          stream;


        let mimeType = '';


        if (
          MediaRecorder.isTypeSupported(
            'audio/webm;codecs=opus',
          )
        ) {

          mimeType =
            'audio/webm;codecs=opus';

        } else if (
          MediaRecorder.isTypeSupported(
            'audio/webm',
          )
        ) {

          mimeType =
            'audio/webm';

        } else if (
          MediaRecorder.isTypeSupported(
            'audio/mp4',
          )
        ) {

          mimeType =
            'audio/mp4';
        }


        const recorder =
          mimeType
            ? new MediaRecorder(
                stream,
                {
                  mimeType,
                },
              )
            : new MediaRecorder(
                stream,
              );


        chunksRef.current = [];


        recorder.ondataavailable =
          event => {

            if (
              event.data &&
              event.data.size > 0
            ) {

              chunksRef.current.push(
                event.data,
              );
            }
          };


        recorder.onerror =
          event => {

            console.error(
              'MediaRecorder error:',
              event,
            );

            setError(
              'Microphone recording failed.',
            );

            setRecording(false);

            stopTimer();
          };


        recorder.onstop =
          async () => {

            stopTimer();

            setRecording(false);


            if (
              streamRef.current
            ) {

              streamRef.current
                .getTracks()
                .forEach(
                  track =>
                    track.stop(),
                );

              streamRef.current = null;
            }


            const blob =
              new Blob(
                chunksRef.current,
                {
                  type:
                    recorder.mimeType ||
                    'audio/webm',
                },
              );


            if (
              blob.size === 0
            ) {

              setError(
                'No audio was recorded.',
              );

              return;
            }


            await uploadAudio(
              blob,
            );
          };


        mediaRecorderRef.current =
          recorder;


        recorder.start(250);

        setRecording(true);

        startTimer();

      } catch (error) {

        console.error(
          'Microphone error:',
          error,
        );

        setError(
          'Microphone permission was denied or the microphone is unavailable.',
        );
      }
    };


  // ==========================================================
  // STOP RECORDING
  // ==========================================================

  const stopRecording = () => {

    const recorder =
      mediaRecorderRef.current;


    if (!recorder) {
      return;
    }


    if (
      recorder.state !==
      'inactive'
    ) {

      recorder.stop();
    }
  };


  // ==========================================================
  // UPLOAD
  // ==========================================================

  const uploadAudio =
    async (
      blob: Blob,
    ) => {

      setProcessing(true);

      setError(null);


      try {

        const formData =
          new FormData();


        const extension =
          blob.type.includes(
            'mp4',
          )
            ? 'mp4'
            : 'webm';


        const file =
          new File(
            [blob],
            `driver-radio.${extension}`,
            {
              type:
                blob.type ||
                'audio/webm',
            },
          );


        formData.append(
          'audio',
          file,
        );


        formData.append(
          'driver_id',
          'DRIVER_01',
        );


        const lapInput =
          document.querySelector(
            'input[name="lap_number"]',
          ) as
            | HTMLInputElement
            | null;


        formData.append(
          'lap_number',
          lapInput?.value ||
            '18',
        );


        const response =
          await fetch(
            AUDIO_ENDPOINT,
            {
              method: 'POST',
              body: formData,
            },
          );


        const text =
          await response.text();


        let data: any = {};


        try {

          data =
            JSON.parse(text);

        } catch {

          data = {
            detail: text,
          };
        }


        if (
          !response.ok
        ) {

          throw new Error(
            data.detail ||
              `Audio analysis failed (${response.status})`,
          );
        }


        if (
          !data.transcript
        ) {

          throw new Error(
            'Whisper returned an empty transcript.',
          );
        }


        onChange(
          data.transcript,
        );

      } catch (error) {

        console.error(
          'Audio analysis error:',
          error,
        );


        setError(
          error instanceof Error
            ? error.message
            : 'Unable to analyze driver audio.',
        );

      } finally {

        setProcessing(false);
      }
    };


  // ==========================================================
  // TIME
  // ==========================================================

  const minutes =
    Math.floor(
      duration / 60,
    );

  const seconds =
    duration % 60;


  const formattedDuration =
    `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;


  // ==========================================================
  // UI
  // ==========================================================

  return (

    <div className="mt-4">

      <div className="flex flex-wrap items-center gap-3">

        {!recording ? (

          <button
            type="button"
            onClick={
              startRecording
            }
            disabled={
              disabled ||
              processing
            }
            className="flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-medium text-zinc-300 transition hover:border-red-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >

            <span className="h-2.5 w-2.5 rounded-full bg-red-500" />

            {processing
              ? 'Analyzing Audio...'
              : 'Record Driver Radio'}

          </button>

        ) : (

          <button
            type="button"
            onClick={
              stopRecording
            }
            className="flex items-center gap-2 rounded-lg border border-red-500 bg-red-600 px-4 py-2 text-sm font-medium text-white"
          >

            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-white" />

            Stop Recording

            <span className="ml-1 text-xs opacity-80">
              {formattedDuration}
            </span>

          </button>

        )}


        {processing && (

          <div className="flex items-center gap-2 text-xs text-zinc-500">

            <span className="h-3 w-3 animate-spin rounded-full border border-zinc-700 border-t-red-500" />

            Whisper is transcribing...

          </div>

        )}

      </div>


      <div className="mt-2">

        <p className="text-[10px] uppercase tracking-wider text-zinc-600">

          {recording
            ? 'MICROPHONE ACTIVE'
            : processing
              ? 'HUGGING FACE WHISPER'
              : 'AUDIO → WHISPER → DRIVER STATE'}

        </p>

      </div>


      {error && (

        <div className="mt-3 rounded-lg border border-red-900/60 bg-red-950/20 p-3">

          <p className="text-xs font-semibold text-red-400">
            Driver Voice Input
          </p>

          <p className="mt-1 text-xs leading-relaxed text-red-500/80">
            {error}
          </p>

          <p className="mt-2 text-[10px] text-zinc-600">
            You can type the driver radio message manually.
          </p>

        </div>

      )}


      {value && (

        <div className="mt-3 rounded-lg border border-zinc-800 bg-black/30 p-3">

          <p className="text-[10px] uppercase tracking-wider text-zinc-600">
            DRIVER RADIO TRANSCRIPT
          </p>

          <p className="mt-1 text-xs text-zinc-400">
            {value}
          </p>

        </div>

      )}

    </div>
  );
}
