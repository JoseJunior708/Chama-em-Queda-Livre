import {
  Activity,
  BarChart3,
  BrainCircuit,
  Flame,
  LayoutDashboard,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  activePage: string;
  onNavigate: (page: string) => void;
}

const navigation = [
  {
    id: "overview",
    label: "Visão Geral",
    icon: LayoutDashboard,
  },
  {
    id: "experiments",
    label: "Comparar Experimentos",
    icon: BarChart3,
  },
  {
    id: "summaries",
    label: "Resumos de IA",
    icon: BrainCircuit,
  },
  {
    id: "assistant",
    label: "Assistente Científico",
    icon: Activity,
  },
];

export default function Sidebar({
  collapsed,
  onToggle,
  activePage,
  onNavigate,
}: SidebarProps) {
  return (
    <aside
      className={`fixed left-0 top-0 z-50 flex h-screen flex-col
      border-r border-slate-800 bg-[#0B0F19]
      transition-all duration-300
      ${collapsed ? "w-20" : "w-64"}`}
    >
      <div className="flex h-20 items-center justify-between border-b border-slate-800 px-5">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-cyan-500/10 p-2">
              <Flame className="h-6 w-6 text-cyan-400" />
            </div>

            <div>
              <h1 className="text-sm font-bold tracking-wide text-white">
                NASA FIRE
              </h1>
              <p className="text-[10px] tracking-widest text-slate-500">
                RESEARCH SYSTEM
              </p>
            </div>
          </div>
        )}

        {collapsed && (
          <Flame className="mx-auto h-7 w-7 text-cyan-400" />
        )}
      </div>

      <div className="flex-1 px-3 py-7">
        {!collapsed && (
          <p className="mb-4 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            Workspace
          </p>
        )}

        <nav className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = activePage === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                title={collapsed ? item.label : undefined}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition
                ${
                  active
                    ? "border border-cyan-500/20 bg-cyan-500/10 text-cyan-400"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <Icon size={20} />

                {!collapsed && (
                  <span className="text-sm font-medium">
                    {item.label}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="border-t border-slate-800 p-4">
        <button
          onClick={onToggle}
          className="flex w-full items-center justify-center gap-3 rounded-xl p-3 text-slate-400 transition hover:bg-slate-800 hover:text-white"
        >
          {collapsed ? (
            <PanelLeftOpen size={20} />
          ) : (
            <>
              <PanelLeftClose size={20} />
              <span className="text-sm">Recolher menu</span>
            </>
          )}
        </button>

        {!collapsed && (
          <p className="mt-3 text-center text-[10px] text-slate-600">
            SPACE RESEARCH PLATFORM
          </p>
        )}
      </div>
    </aside>
  );
}