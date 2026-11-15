import {
  Bell,
  CircleDot,
  Orbit,
  ShieldCheck,
} from "lucide-react";

interface HeaderProps {
  sidebarCollapsed: boolean;
}

export default function Header({
  sidebarCollapsed,
}: HeaderProps) {
  return (
    <header
      className={`fixed right-0 top-0 z-40 flex h-20 items-center justify-between
      border-b border-slate-800 bg-[#0B0F19]/95 px-5 backdrop-blur-xl
      transition-all duration-300
      ${sidebarCollapsed ? "left-20" : "left-64"}`}
    >
      <div className="flex items-center gap-3">
        <div className="hidden rounded-lg border border-slate-800 bg-slate-900 p-2 sm:block">
          <Orbit className="h-5 w-5 text-cyan-400" />
        </div>

        <div>
          <h2 className="text-sm font-semibold text-white sm:text-base">
            Microgravity Fire Analysis
          </h2>

          <p className="text-[10px] text-slate-500 sm:text-xs">
            NASA SPACE EXPLORATION RESEARCH
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 sm:gap-5">
        <div className="hidden items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 sm:flex">
          <CircleDot className="h-3 w-3 text-emerald-400" />

          <span className="text-xs font-medium text-emerald-400">
            Sistema operacional
          </span>
        </div>

        <button
          title="Notificações"
          className="rounded-lg border border-slate-800 p-2 text-slate-400 transition hover:bg-slate-800 hover:text-white"
        >
          <Bell size={18} />
        </button>

        <div className="hidden items-center gap-2 border-l border-slate-800 pl-4 md:flex">
          <ShieldCheck className="h-5 w-5 text-cyan-400" />

          <span className="text-xs text-slate-400">
            Research Mode
          </span>
        </div>
      </div>
    </header>
  );
}