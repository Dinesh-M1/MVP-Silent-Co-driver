interface DashboardHeaderProps {
  status?: string;
}


export default function DashboardHeader({

  status = 'Online',

}: DashboardHeaderProps) {

  return (

    <header className="border-b border-zinc-800 bg-slate-950 px-6 py-5">

      <div className="mx-auto flex max-w-7xl items-center justify-between">

        <div>

          <h1 className="text-2xl font-bold">
            Silent Co-Driver
          </h1>

          <p className="text-sm text-zinc-400">
            AI driver-state analysis and dynamic pit strategy
          </p>

        </div>


        <div className="rounded-full border border-emerald-800 bg-emerald-950/30 px-4 py-2 text-sm text-emerald-400">

          ● {status}

        </div>

      </div>

    </header>
  );
}
