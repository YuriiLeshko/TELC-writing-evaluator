import { NavLink } from "react-router-dom";
import {
  Archive,
  BookOpen,
  House,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  PencilLine,
  Moon,
  Settings,
  Sun,
  User,
  X,
} from "lucide-react";

const topLinks = [
  { to: "/", label: "Main", end: true, icon: House },
  { to: "/assessment-guide", label: "Ratgeber", icon: BookOpen },
  { to: "/training", label: "Training", icon: PencilLine, requiresConsent: true },
  { to: "/archive", label: "Archive", icon: Archive, requiresConsent: true },
];

const bottomLinks = [
  { to: "/profile", label: "Profile", icon: User },
  { to: "/admin", label: "Admin", icon: Settings },
];

export default function Navigation({
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onOpenMobile,
  onCloseMobile,
  theme,
  onToggleTheme,
  disclaimerAccepted,
}) {
  const sidebarCls = [
    "sidebar",
    collapsed ? "sidebar--collapsed" : "",
    mobileOpen ? "sidebar--mobile-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const itemClassName = ({ isActive }) =>
    `sidebar__link ${isActive ? "sidebar__link--active" : ""}`.trim();

  const renderLink = ({ to, label, end, icon: Icon, requiresConsent }) => {
    const disabled = requiresConsent && !disclaimerAccepted;
    if (disabled) {
      return (
        <span
          key={to}
          className="sidebar__link sidebar__link--disabled"
          title="Bitte zuerst den Hinweis auf der Startseite bestätigen."
        >
          <Icon size={18} className="sidebar__icon" aria-hidden />
          <span className="sidebar__label">{label}</span>
        </span>
      );
    }
    return (
      <NavLink key={to} to={to} end={end} className={itemClassName} onClick={onCloseMobile}>
        <Icon size={18} className="sidebar__icon" aria-hidden />
        <span className="sidebar__label">{label}</span>
      </NavLink>
    );
  };

  return (
    <>
      <button
        type="button"
        className="sidebar-mobile-toggle"
        onClick={onOpenMobile}
        aria-label="Navigation öffnen"
      >
        <Menu size={20} aria-hidden />
      </button>

      {mobileOpen ? <button type="button" className="sidebar-backdrop" onClick={onCloseMobile} aria-label="Navigation schließen" /> : null}

      <aside className={sidebarCls} aria-label="Hauptnavigation">
        <button
          type="button"
          className="sidebar__collapse"
          onClick={onToggleCollapse}
          aria-label={collapsed ? "Sidebar erweitern" : "Sidebar einklappen"}
        >
          {collapsed ? <PanelLeftOpen size={18} aria-hidden /> : <PanelLeftClose size={18} aria-hidden />}
        </button>
        <button type="button" className="sidebar__close-mobile" onClick={onCloseMobile} aria-label="Navigation schließen">
          <X size={18} aria-hidden />
        </button>

        <div className="sidebar__top">
          {topLinks.map(renderLink)}
        </div>
        <div className="sidebar__bottom">
          <button
            type="button"
            className="sidebar__theme-toggle"
            onClick={onToggleTheme}
            aria-label={theme === "light" ? "Dark theme aktivieren" : "Light theme aktivieren"}
            title={theme === "light" ? "Dark mode" : "Light mode"}
          >
            {theme === "light" ? <Moon size={18} className="sidebar__icon" aria-hidden /> : <Sun size={18} className="sidebar__icon" aria-hidden />}
            <span className="sidebar__label">{theme === "light" ? "Dark mode" : "Light mode"}</span>
          </button>
          {bottomLinks.map(renderLink)}
        </div>
      </aside>
    </>
  );
}
