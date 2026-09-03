import React, { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export const ThemeToggle: React.FC<{ className?: string }> = ({ className = "" }) => {
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("ip_sakti_theme");
      if (stored === "light") return "light";
      if (stored === "dark") return "dark";
      return document.documentElement.classList.contains("dark") ? "dark" : "light";
    }
    return "dark";
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
      localStorage.setItem("ip_sakti_theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("ip_sakti_theme", "light");
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to Bright Mode" : "Switch to Dark Mode"}
      title={isDark ? "Switch to Bright Mode" : "Switch to Dark Mode"}
      className={`relative inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 cursor-pointer shadow-xs border ${
        isDark
          ? "bg-slate-900/90 text-amber-300 border-slate-700/80 hover:bg-slate-800 hover:border-amber-400/40 hover:text-amber-200"
          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100 hover:border-slate-400 hover:text-slate-900"
      } ${className}`}
    >
      {isDark ? (
        <>
          <Sun className="w-3.5 h-3.5 text-amber-400 transition-transform hover:rotate-45" />
          <span className="hidden sm:inline text-[11px] font-bold text-amber-300">Bright</span>
        </>
      ) : (
        <>
          <Moon className="w-3.5 h-3.5 text-indigo-600 transition-transform hover:-rotate-12" />
          <span className="hidden sm:inline text-[11px] font-bold text-slate-700">Dark</span>
        </>
      )}
    </button>
  );
};
