import { useEffect, useState } from "react";
import { StageProvider } from "./stage/StageProvider";
import { NeuralCanvas } from "./stage/NeuralCanvas";
import { useUIScale } from "./hooks/useUIScale";

export default function App() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem("kali.theme") ?? "midnight",
  );
  const [canvasAutoExpand, setCanvasAutoExpand] = useState(
    () => localStorage.getItem("kali.canvasAutoExpand") !== "false",
  );
  const { scale, setScale } = useUIScale();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("kali.theme", theme);
  }, [theme]);

  useEffect(() => {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      const bg = getComputedStyle(document.documentElement).getPropertyValue("--bg").trim();
      if (bg) meta.setAttribute("content", bg);
    }
  }, [theme]);

  return (
    <StageProvider>
      <NeuralCanvas
        theme={theme}
        onThemeChange={setTheme}
        canvasAutoExpand={canvasAutoExpand}
        onCanvasAutoExpandChange={(v) => {
          setCanvasAutoExpand(v);
          localStorage.setItem("kali.canvasAutoExpand", String(v));
        }}
        uiScale={scale}
        onUIScaleChange={setScale}
      />
    </StageProvider>
  );
}