// Debe mantenerse sincronizado a mano con styles/tokens.css
export const CHART_COLOR_SERIES_A = "#B4B1FE";      // --color-primary (Dark Mode)
export const CHART_COLOR_SERIES_B = "#9C98C2";      // --color-text-muted (Dark Mode)
export const CHART_COLOR_SERIES_C = "#F1F0F9";      // --color-text (Dark Mode)
export const CHART_COLOR_SERIES_D = "#F2C572";      // --color-warning-text (Dark Mode)
export const CHART_COLOR_BASELINE = "#7C6FFF";      // --color-pulse (Dark Mode)

// ECharts renderiza sobre <canvas> (zrender), que NO resuelve custom
// properties de CSS — un string "var(--color-x)" pasado a itemStyle.color
// no es un color válido para el motor de Canvas 2D y produce negro/vacío
// (confirmado empíricamente: MeterStatusDistribution quedó totalmente
// negro al usar var(--color-neutral) directo). Todo color dentro de
// `option` de ECharts DEBE ser un literal (#hex/rgb/rgba), nunca var().
// Se usan las variantes "-text" (más saturadas, pensadas para contraste
// sobre fondo) en vez de los tokens de fondo pastel de Badge
// (--color-neutral/-warning/-critical), que en dark mode son casi
// invisibles contra --color-bg.
export const CHART_COLOR_STATUS_HEALTHY = "#B3AFDD";  // --color-neutral-text (Dark Mode)
export const CHART_COLOR_STATUS_WARNING = "#F2C572";  // --color-warning-text (Dark Mode)
export const CHART_COLOR_STATUS_CRITICAL = "#F5A9BE"; // --color-critical-text (Dark Mode)
