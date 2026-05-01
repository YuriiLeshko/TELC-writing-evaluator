import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./styles/global.css";

const THEME_KEY = "telc-theme";
const savedTheme = (() => {
  try {
    return localStorage.getItem(THEME_KEY);
  } catch {
    return null;
  }
})();
const initialTheme = savedTheme === "dark" ? "dark" : "light";
document.documentElement.setAttribute("data-theme", initialTheme);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
