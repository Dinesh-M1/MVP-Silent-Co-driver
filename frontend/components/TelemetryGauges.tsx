'use client';


interface TelemetryGaugesProps {
  fatigue: string;
  fatigueScore: number;
  workload: string;
  stressIndex?: number;
  speed: number | null;
  rpm?: number | null;
  gear?: number | null;
}


function percentage(value: number) {

  return Math.min(
    100,
    Math.max(
      0,
      Math.round(
        value * 100
      )
    )
  );
}


export default function TelemetryGauges({

  fatigue,

  fatigueScore,

  workload,

  stressIndex = 0,

  speed,

  rpm = null,

  gear = null,

}: TelemetryGaugesProps) {

  const hasSpeed =
    typeof speed === 'number';


  return (

    <div className="space-y-4">

      <div className="flex items-center justify-between">

        <div>

          <h2 className="text-lg font-semibold">
            Driver Telemetry
          </h2>

          <p className="text-xs text-zinc-500">
            Voice analysis + simulator-ready telemetry
          </p>

        </div>

        <div className="rounded-full border border-zinc-700 bg-black/40 px-3 py-1 text-xs text-zinc-400">
          LIVE STATE
        </div>

      </div>


      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">


        {/* SPEED */}

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-5">

          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Speed
          </p>

          {hasSpeed ? (

            <>

              <p className="mt-3 text-3xl font-bold">

                {speed.toFixed(0)}

                <span className="ml-1 text-sm font-normal text-zinc-500">
                  km/h
                </span>

              </p>

              <p className="mt-2 text-xs text-emerald-400">
                ● Live Simulator
              </p>

            </>

          ) : (

            <>

              <p className="mt-3 text-3xl font-bold text-zinc-500">
                --
              </p>

              <p className="mt-2 text-xs text-zinc-600">
                Waiting for simulator
              </p>

            </>

          )}

        </div>


        {/* DRIVER STRESS */}

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-5">

          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Driver Stress
          </p>

          <p className="mt-3 text-3xl font-bold">
            {percentage(
              stressIndex
            )}
            %
          </p>

          <div className="mt-3 h-2 overflow-hidden rounded-full bg-zinc-800">

            <div
              className="h-full rounded-full bg-red-600 transition-all duration-500"
              style={{
                width: `${percentage(
                  stressIndex
                )}%`,
              }}
            />

          </div>

          <p className="mt-2 text-xs text-zinc-500">
            Voice analysis
          </p>

        </div>


        {/* FATIGUE */}

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-5">

          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Fatigue
          </p>

          <div className="mt-3 flex items-end justify-between">

            <p className="text-3xl font-bold">
              {fatigue}
            </p>

            <p className="text-sm text-zinc-500">
              {percentage(
                fatigueScore
              )}
              %
            </p>

          </div>

          <div className="mt-3 h-2 overflow-hidden rounded-full bg-zinc-800">

            <div
              className="h-full rounded-full bg-orange-500 transition-all duration-500"
              style={{
                width: `${percentage(
                  fatigueScore
                )}%`,
              }}
            />

          </div>

          <p className="mt-2 text-xs text-zinc-500">
            Driver-state analysis
          </p>

        </div>

      </div>


      {/* RPM / GEAR */}

      <div className="grid grid-cols-2 gap-4">

        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">

          <p className="text-xs text-zinc-500">
            RPM
          </p>

          <p className="mt-2 text-xl font-semibold">

            {rpm !== null
              ? rpm.toLocaleString()
              : '--'}

          </p>

        </div>


        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">

          <p className="text-xs text-zinc-500">
            Gear
          </p>

          <p className="mt-2 text-xl font-semibold">

            {gear !== null
              ? gear
              : '--'}

          </p>

        </div>

      </div>


      {/* WORKLOAD */}

      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-5">

        <p className="text-xs uppercase tracking-wider text-zinc-500">
          Driver Workload
        </p>

        <p className="mt-2 text-xl font-semibold">
          {workload}
        </p>

        <p className="mt-2 text-sm text-zinc-500">

          {workload === 'VERY HIGH'

            ? 'Immediate attention required'

            : workload === 'HIGH'

              ? 'Driver under significant load'

              : workload === 'NORMAL'

                ? 'Normal driver workload'

                : 'Waiting for driver analysis'}

        </p>

      </div>

    </div>
  );
}
