import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import Navigation from "./Navigation.jsx";

const THEME_KEY = "telc-theme";

export default function Layout({ disclaimerAccepted, onAcceptDisclaimer }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState(() => {
    const attrTheme = document.documentElement.getAttribute("data-theme");
    return attrTheme === "dark" ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      // ignore storage failures
    }
  }, [theme]);

  return (
    <div className="layout">
      <div className="layout__banner">
        Demo-Modus: Backend verwendet aktuell Demo-User/Admin.
      </div>
      <div className={`app-shell ${collapsed ? "app-shell--collapsed" : ""}`.trim()}>
        <Navigation
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed((v) => !v)}
          mobileOpen={mobileOpen}
          onOpenMobile={() => setMobileOpen(true)}
          onCloseMobile={() => setMobileOpen(false)}
          theme={theme}
          onToggleTheme={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
          disclaimerAccepted={disclaimerAccepted}
        />
        <main className="layout__content">
          <div className="layout__main">
            <Outlet context={{ disclaimerAccepted, onAcceptDisclaimer }} />
          </div>
        </main>
      </div>
    </div>
  );
}
