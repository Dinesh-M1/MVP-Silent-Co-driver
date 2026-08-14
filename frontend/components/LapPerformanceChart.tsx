'use client';

import {
  useEffect,
  useMemo,
  useState,
} from 'react';


/* ============================================================
   TYPES
   ============================================================ */

export interface LapPoint {
  lap: number;

  lap_time:
    | number
    | null;

  stress: number;

  fatigue: number;

  driver_state: string;

  event:
    | string
    | null;

  event_type:
    | string
    | null;

  confidence?: number;
}


interface Props {
  backendUrl?: string;

  refreshMs?: number;

  currentLap?: number;

  latestAnalysis?: {
    lap?: number;

    stress_index?: number;

    confidence?: number;

    driver_state?: {
      state?: string;
      stress?: number;
      fatigue_score?: number;
    };

    important_events?: Array<{
      lap?: number;
      event_type?: string;
      title?: string;
      description?: string;
      severity?: string;
      confidence?: number;
    }>;

    lap_performance?: LapPoint[];

    strategy?: {
      action?: string;
      target_compound?: string;
      recommended_pit_lap?: number;
    };

    decision?: {
      priority?: string;
      action?: string;
      reason?: string;
      confidence?: number;
    };
  };
}


/* ============================================================
   CONSTANTS
   ============================================================ */

const DEFAULT_BACKEND =
  'http://127.0.0.1:8000';

const MAX_POINTS = 24;


/* ============================================================
   HELPERS
   ============================================================ */

function clamp(
  value: number,
): number {

  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.max(
    0,
    Math.min(
      1,
      value,
    ),
  );
}


function percent(
  value: number,
): number {

  return Math.round(
    clamp(value) * 100,
  );
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


function stateClass(
  state: string,
): string {

  const value =
    state.toUpperCase();

  if (value === 'CRITICAL') {
    return 'text-red-400';
  }

  if (value === 'ELEVATED') {
    return 'text-yellow-400';
  }

  return 'text-green-400';
}


/* ============================================================
   COMPONENT
   ============================================================ */

export default function LapPerformanceChart({
  backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    DEFAULT_BACKEND,

  refreshMs = 3000,

  currentLap,

  latestAnalysis,
}: Props) {


  /* ==========================================================
     STATE
     ========================================================== */

  const [
    history,
    setHistory,
  ] = useState<LapPoint[]>([]);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  /* ==========================================================
     FETCH HISTORY
     ========================================================== */

  useEffect(() => {

    let cancelled = false;


    const loadHistory =
      async () => {

        try {

          const response =
            await fetch(
              `${backendUrl}/api/v1/telemetry/history`,
              {
                cache: 'no-store',
              },
            );


          if (!response.ok) {

            throw new Error(
              `Backend returned ${response.status}`,
            );
          }


          const result =
            await response.json();


          const laps =
            Array.isArray(
              result.laps,
            )
              ? result.laps
              : [];


          if (!cancelled) {

            setHistory(
              laps,
            );

            setError(null);
          }

        } catch (err) {

          if (!cancelled) {

            console.error(
              'Lap history error:',
              err,
            );

            setError(
              'Backend connection unavailable.',
            );
          }

        } finally {

          if (!cancelled) {

            setLoading(
              false,
            );
          }
        }
      };


    loadHistory();


    const interval =
      window.setInterval(
        loadHistory,
        refreshMs,
      );


    return () => {

      cancelled = true;

      window.clearInterval(
        interval,
      );
    };

  }, [
    backendUrl,
    refreshMs,
  ]);


  /* ==========================================================
     MERGE BACKEND HISTORY + CURRENT ANALYSIS
     ========================================================== */

  const chartData =
    useMemo(() => {

      const merged =
        new Map<
          number,
          LapPoint
        >();


      /* ------------------------------------------------------
         BACKEND HISTORY
         ------------------------------------------------------ */

      for (
        const point of history
      ) {

        if (
          !point ||
          !Number.isFinite(
            point.lap,
          )
        ) {
          continue;
        }


        merged.set(
          point.lap,
          {
            lap:
              point.lap,

            lap_time:
              point.lap_time ??
              null,

            stress:
              clamp(
                point.stress,
              ),

            fatigue:
              clamp(
                point.fatigue,
              ),

            driver_state:
              point.driver_state ||
              'NORMAL',

            event:
              point.event ??
              null,

            event_type:
              point.event_type ??
              null,

            confidence:
              clamp(
                point.confidence ??
                0,
              ),
          },
        );
      }


      /* ------------------------------------------------------
         CURRENT ANALYSIS
         ------------------------------------------------------ */

      if (latestAnalysis) {

        const analysisLap =
          latestAnalysis.lap ??
          currentLap ??
          18;


        const analysisPoint =
          latestAnalysis
            .lap_performance
            ?.find(
              point =>
                point.lap ===
                analysisLap,
            );


        const existing =
          merged.get(
            analysisLap,
          );


        const state =
          latestAnalysis
            .driver_state
            ?.state ??
          analysisPoint
            ?.driver_state ??
          existing
            ?.driver_state ??
          'NORMAL';


        const stress =
          latestAnalysis
            .stress_index ??
          latestAnalysis
            .driver_state
            ?.stress ??
          analysisPoint
            ?.stress ??
          existing
            ?.stress ??
          0;


        const fatigue =
          latestAnalysis
            .driver_state
            ?.fatigue_score ??
          analysisPoint
            ?.fatigue ??
          existing
            ?.fatigue ??
          0;


        const event =
          latestAnalysis
            .important_events
            ?.find(
              item =>
                item.lap ===
                analysisLap,
            );


        merged.set(
          analysisLap,
          {
            lap:
              analysisLap,

            lap_time:
              analysisPoint
                ?.lap_time ??
              existing
                ?.lap_time ??
              null,

            stress:
              clamp(
                stress,
              ),

            fatigue:
              clamp(
                fatigue,
              ),

            driver_state:
              state,

            event:
              event?.title ??
              analysisPoint
                ?.event ??
              existing
                ?.event ??
              null,

            event_type:
              event?.event_type ??
              analysisPoint
                ?.event_type ??
              existing
                ?.event_type ??
              null,

            confidence:
              clamp(
                event?.confidence ??
                analysisPoint
                  ?.confidence ??
                existing
                  ?.confidence ??
                latestAnalysis
                  .confidence ??
                0,
              ),
          },
        );
      }


      return Array.from(
        merged.values(),
      )
        .sort(
          (a, b) =>
            a.lap - b.lap,
        )
        .slice(
          -MAX_POINTS,
        );

    }, [
      history,
      latestAnalysis,
      currentLap,
    ]);


  /* ==========================================================
     CURRENT POINT
     ========================================================== */

  const activeLap =
    currentLap ??
    latestAnalysis?.lap ??
    chartData.at(-1)?.lap ??
    null;


  const activePoint =
    activeLap !== null
      ? chartData.find(
          point =>
            point.lap ===
            activeLap,
        )
      : undefined;


  /* ==========================================================
     EMPTY STATE
     ========================================================== */

  if (
    !loading &&
    chartData.length === 0
  ) {

    return (

      <section className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5">

        <div className="flex items-center justify-between">

          <div>

            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-600">
              DRIVER LOAD MONITOR
            </p>

            <h2 className="mt-1 text-lg font-bold">
              Lap Performance
            </h2>

          </div>

          <span className="text-[9px] uppercase tracking-widest text-zinc-700">
            Waiting for data
          </span>

        </div>


        <div className="mt-5 flex h-64 items-center justify-center rounded-xl border border-dashed border-zinc-800">

          <div className="text-center">

            <div className="text-3xl">
              🏁
            </div>

            <p className="mt-3 text-sm text-zinc-500">
              No lap data yet
            </p>

            <p className="mt-2 text-xs text-zinc-700">
              Analyze driver radio to create the first lap point.
            </p>

          </div>

        </div>

      </section>
    );
  }


  /* ==========================================================
     CHART DIMENSIONS
     ========================================================== */

  const width = 1200;

  const height = 430;

  const left = 65;

  const right = 30;

  const top = 35;

  const bottom = 55;

  const plotWidth =
    width -
    left -
    right;

  const plotHeight =
    height -
    top -
    bottom;


  const minLap =
    chartData.length
      ? Math.min(
          ...chartData.map(
            point =>
              point.lap,
          ),
        )
      : 1;


  const maxLap =
    chartData.length
      ? Math.max(
          ...chartData.map(
            point =>
              point.lap,
          ),
        )
      : 1;


  const lapRange =
    Math.max(
      1,
      maxLap - minLap,
    );


  const x = (
    lap: number,
  ) => {

    if (
      minLap === maxLap
    ) {

      return (
        left +
        plotWidth / 2
      );
    }


    return (
      left +
      (
        (lap - minLap) /
        lapRange
      ) *
      plotWidth
    );
  };


  const y = (
    value: number,
  ) => {

    return (
      top +
      (
        1 -
        clamp(value)
      ) *
      plotHeight
    );
  };


  /* ==========================================================
     PATHS
     ========================================================== */

  const makePath =
    (
      getValue:
        (point: LapPoint) =>
          number,
    ) => {

      return chartData
        .map(
          (
            point,
            index,
          ) => {

            const command =
              index === 0
                ? 'M'
                : 'L';

            return (
              `${command} ${x(point.lap)} ${y(
                getValue(point),
              )}`
            );
          },
        )
        .join(' ');
    };


  const stressPath =
    makePath(
      point =>
        point.stress,
    );


  const fatiguePath =
    makePath(
      point =>
        point.fatigue,
    );


  /* ==========================================================
     ZONES
     ========================================================== */

  const zoneHeight =
    plotHeight;


  const criticalY =
    y(1);


  const highY =
    y(0.75);


  const elevatedY =
    y(0.60);


  const normalY =
    y(0.30);


  /* ==========================================================
     RENDER
     ========================================================== */

  return (

    <section className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-5">


      {/* ======================================================
          HEADER
          ====================================================== */}

      <div className="flex flex-wrap items-end justify-between gap-4">

        <div>

          <div className="flex items-center gap-2">

            <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" />

            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-600">
              DRIVER LOAD vs LAP PERFORMANCE
            </p>

          </div>


          <h2 className="mt-1 text-xl font-bold">
            Engineer Driver Monitor
          </h2>


          <p className="mt-1 text-xs text-zinc-600">
            Higher load means greater driver stress/fatigue risk.
          </p>

        </div>


        {activePoint && (

          <div className="flex flex-wrap items-center gap-4">

            <div>

              <p className="text-[8px] uppercase tracking-widest text-zinc-700">
                LAP
              </p>

              <p className="text-xl font-black">
                {activePoint.lap}
              </p>

            </div>


            <div>

              <p className="text-[8px] uppercase tracking-widest text-zinc-700">
                STATE
              </p>

              <p
                className={`text-sm font-black ${stateClass(
                  activePoint.driver_state,
                )}`}
              >
                {activePoint.driver_state}
              </p>

            </div>


            <div>

              <p className="text-[8px] uppercase tracking-widest text-zinc-700">
                LOAD
              </p>

              <p className="text-xl font-black">
                {Math.max(
                  percent(
                    activePoint.stress,
                  ),
                  percent(
                    activePoint.fatigue,
                  ),
                )}%
              </p>

            </div>

          </div>

        )}

      </div>


      {/* ======================================================
          QUICK INTERPRETATION
          ====================================================== */}

      <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">

        <div className="rounded-xl border border-green-950 bg-green-950/10 px-3 py-2">

          <p className="text-[8px] uppercase tracking-widest text-green-600">
            LOW
          </p>

          <p className="mt-1 text-xs text-zinc-500">
            0–30%
          </p>

        </div>


        <div className="rounded-xl border border-yellow-950 bg-yellow-950/10 px-3 py-2">

          <p className="text-[8px] uppercase tracking-widest text-yellow-600">
            ELEVATED
          </p>

          <p className="mt-1 text-xs text-zinc-500">
            30–60%
          </p>

        </div>


        <div className="rounded-xl border border-orange-950 bg-orange-950/10 px-3 py-2">

          <p className="text-[8px] uppercase tracking-widest text-orange-500">
            HIGH
          </p>

          <p className="mt-1 text-xs text-zinc-500">
            60–75%
          </p>

        </div>


        <div className="rounded-xl border border-red-950 bg-red-950/10 px-3 py-2">

          <p className="text-[8px] uppercase tracking-widest text-red-500">
            CRITICAL
          </p>

          <p className="mt-1 text-xs text-zinc-500">
            75–100%
          </p>

        </div>

      </div>


      {/* ======================================================
          CURRENT METRICS
          ====================================================== */}

      {activePoint && (

        <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">

          <div className="rounded-xl border border-zinc-800 bg-black p-3">

            <p className="text-[8px] uppercase tracking-widest text-zinc-600">
              Stress
            </p>

            <p className="mt-1 text-xl font-black text-red-400">
              {percent(
                activePoint.stress,
              )}%
            </p>

          </div>


          <div className="rounded-xl border border-zinc-800 bg-black p-3">

            <p className="text-[8px] uppercase tracking-widest text-zinc-600">
              Fatigue
            </p>

            <p className="mt-1 text-xl font-black text-yellow-400">
              {percent(
                activePoint.fatigue,
              )}%
            </p>

          </div>


          <div className="rounded-xl border border-zinc-800 bg-black p-3">

            <p className="text-[8px] uppercase tracking-widest text-zinc-600">
              Lap Time
            </p>

            <p className="mt-1 text-xl font-black">
              {formatLapTime(
                activePoint.lap_time,
              )}
            </p>

          </div>


          <div className="rounded-xl border border-zinc-800 bg-black p-3">

            <p className="text-[8px] uppercase tracking-widest text-zinc-600">
              Confidence
            </p>

            <p className="mt-1 text-xl font-black text-cyan-400">
              {percent(
                activePoint.confidence ??
                0,
              )}%
            </p>

          </div>

        </div>

      )}


      {/* ======================================================
          CHART
          ====================================================== */}

      <div className="mt-5 w-full">

        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-auto w-full"
          role="img"
          aria-label="Driver stress and fatigue by racing lap"
        >

          {/* --------------------------------------------------
              BACKGROUND ZONES
              -------------------------------------------------- */}

          <rect
            x={left}
            y={criticalY}
            width={plotWidth}
            height={zoneHeight * 0.25}
            className="fill-red-950/10"
          />


          <rect
            x={left}
            y={highY}
            width={plotWidth}
            height={
              zoneHeight * 0.15
            }
            className="fill-orange-950/10"
          />


          <rect
            x={left}
            y={elevatedY}
            width={plotWidth}
            height={
              zoneHeight * 0.30
            }
            className="fill-yellow-950/10"
          />


          <rect
            x={left}
            y={normalY}
            width={plotWidth}
            height={
              zoneHeight * 0.30
            }
            className="fill-green-950/10"
          />


          {/* --------------------------------------------------
              GRID
              -------------------------------------------------- */}

          {[0, 0.25, 0.5, 0.75, 1].map(
            value => (

              <g key={value}>

                <line
                  x1={left}
                  x2={
                    width -
                    right
                  }
                  y1={y(value)}
                  y2={y(value)}
                  stroke="currentColor"
                  className="text-zinc-900"
                />


                <text
                  x={left - 10}
                  y={y(value) + 4}
                  textAnchor="end"
                  className="fill-zinc-600 text-[10px]"
                >
                  {percent(value)}%
                </text>

              </g>
            ),
          )}


          {/* --------------------------------------------------
              ZONE LABELS
              -------------------------------------------------- */}

          <text
            x={
              width -
              right -
              5
            }
            y={y(0.875)}
            textAnchor="end"
            className="fill-red-700 text-[9px] uppercase"
          >
            CRITICAL
          </text>


          <text
            x={
              width -
              right -
              5
            }
            y={y(0.675)}
            textAnchor="end"
            className="fill-orange-700 text-[9px] uppercase"
          >
            HIGH
          </text>


          <text
            x={
              width -
              right -
              5
            }
            y={y(0.45)}
            textAnchor="end"
            className="fill-yellow-700 text-[9px] uppercase"
          >
            ELEVATED
          </text>


          {/* --------------------------------------------------
              AXES
              -------------------------------------------------- */}

          <line
            x1={left}
            x2={left}
            y1={top}
            y2={
              height -
              bottom
            }
            stroke="currentColor"
            className="text-zinc-700"
          />


          <line
            x1={left}
            x2={
              width -
              right
            }
            y1={
              height -
              bottom
            }
            y2={
              height -
              bottom
            }
            stroke="currentColor"
            className="text-zinc-700"
          />


          {/* --------------------------------------------------
              STRESS
              -------------------------------------------------- */}

          <path
            d={stressPath}
            fill="none"
            stroke="currentColor"
            className="text-red-500"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />


          {/* --------------------------------------------------
              FATIGUE
              -------------------------------------------------- */}

          <path
            d={fatiguePath}
            fill="none"
            stroke="currentColor"
            className="text-yellow-400"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="8 6"
          />


          {/* --------------------------------------------------
              DATA POINTS
              -------------------------------------------------- */}

          {chartData.map(
            point => (

              <g
                key={`${point.lap}-${point.event || 'normal'}`}
              >

                <circle
                  cx={x(point.lap)}
                  cy={y(point.stress)}
                  r={
                    point.lap ===
                    activeLap
                      ? 7
                      : 4
                  }
                  className="fill-red-500"
                />


                <circle
                  cx={x(point.lap)}
                  cy={y(point.fatigue)}
                  r={
                    point.lap ===
                    activeLap
                      ? 6
                      : 3.5
                  }
                  className="fill-yellow-400"
                />


                {/* EVENT MARKER */}

                {point.event && (

                  <line
                    x1={x(point.lap)}
                    x2={x(point.lap)}
                    y1={top}
                    y2={
                      height -
                      bottom
                    }
                    stroke="currentColor"
                    className="text-red-800"
                    strokeDasharray="4 5"
                  />

                )}


                {/* LAP LABEL */}

                <text
                  x={x(point.lap)}
                  y={
                    height -
                    bottom +
                    22
                  }
                  textAnchor="middle"
                  className="fill-zinc-500 text-[10px]"
                >
                  {point.lap}
                </text>

              </g>
            ),
          )}


          {/* --------------------------------------------------
              AXIS LABELS
              -------------------------------------------------- */}

          <text
            x="15"
            y={height / 2}
            transform={`rotate(-90 15 ${
              height / 2
            })`}
            textAnchor="middle"
            className="fill-zinc-600 text-[9px] uppercase"
          >
            Driver Load
          </text>


          <text
            x={width / 2}
            y={height - 8}
            textAnchor="middle"
            className="fill-zinc-600 text-[9px] uppercase"
          >
            Racing Lap
          </text>

        </svg>

      </div>


      {/* ======================================================
          LEGEND
          ====================================================== */}

      <div className="mt-2 flex flex-wrap gap-5 text-[9px] uppercase tracking-widest text-zinc-500">

        <span className="flex items-center gap-2">
          <span className="h-1 w-7 rounded-full bg-red-500" />
          Stress
        </span>


        <span className="flex items-center gap-2">
          <span className="h-1 w-7 rounded-full bg-yellow-400" />
          Fatigue
        </span>


        <span className="text-zinc-700">
          Vertical marker = race event
        </span>

      </div>


      {/* ======================================================
          RECENT EVENTS
          ====================================================== */}

      <div className="mt-5 border-t border-zinc-900 pt-4">

        <div className="flex items-center justify-between">

          <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-zinc-600">
            RECENT ENGINEER EVENTS
          </p>

          <p className="text-[9px] text-zinc-700">
            {chartData.filter(
              point =>
                Boolean(point.event),
            ).length}{' '}
            events
          </p>

        </div>


        <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-4">

          {chartData
            .filter(
              point =>
                Boolean(point.event),
            )
            .slice(-4)
            .reverse()
            .map(point => (

              <div
                key={`${point.lap}-${point.event}`}
                className="rounded-xl border border-zinc-800 bg-black p-3"
              >

                <div className="flex items-center justify-between">

                  <span className="text-[8px] font-bold uppercase tracking-widest text-zinc-600">
                    LAP {point.lap}
                  </span>

                  <span className="text-[8px] font-bold uppercase tracking-widest text-red-500">
                    {point.event_type ||
                      'EVENT'}
                  </span>

                </div>


                <p className="mt-2 text-xs font-semibold text-zinc-300">
                  {point.event}
                </p>


                <div className="mt-2 flex justify-between text-[8px] text-zinc-600">

                  <span>
                    Load{' '}
                    {Math.max(
                      percent(
                        point.stress,
                      ),
                      percent(
                        point.fatigue,
                      ),
                    )}%
                  </span>

                  <span>
                    Conf{' '}
                    {percent(
                      point.confidence ??
                      0,
                    )}%
                  </span>

                </div>

              </div>

            ))}


          {chartData.filter(
            point =>
              Boolean(point.event),
          ).length === 0 && (

            <div className="md:col-span-2 xl:col-span-4 rounded-xl border border-dashed border-zinc-800 p-4 text-center">

              <p className="text-xs text-zinc-600">
                No significant events detected.
              </p>

            </div>

          )}

        </div>

      </div>


      {error && (

        <p className="mt-3 text-[9px] text-zinc-700">
          {error} Retrying automatically.
        </p>

      )}

    </section>
  );
}
