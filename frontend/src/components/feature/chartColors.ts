// Debe mantenerse sincronizado a mano con styles/tokens.css
export const CHART_COLOR_SERIES_A = "#B4B1FE";      // --color-primary (Dark Mode)
export const CHART_COLOR_SERIES_B = "#9C98C2";      // --color-text-muted (Dark Mode)
// CHART_COLOR_SERIES_C original ("#F1F0F9", --color-text en Dark Mode)
// era casi blanco puro — invisible sobre el fondo claro de light mode
// (confirmado con captura real: la 3ra variable comparada no se veía
// en absoluto). Reemplazado por un rojo sutil, con contraste real en
// ambos temas, ya que ningún color de este archivo distingue tema en
// tiempo de ejecución (ver limitación general al inicio del archivo).
export const CHART_COLOR_SERIES_C = "#E08A8A";      // rojo sutil, visible en ambos temas
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

// markArea de la ventana anómala resaltada en MeterHistoryChart: antes
// usaba "rgba(114, 28, 36, 0.15)" hardcodeado (rojo oscuro fijo) que,
// con solo 15% de opacidad sobre un fondo ya oscuro (--color-bg dark),
// prácticamente desaparecía visualmente. Se usa el mismo
// --color-critical-text (más saturado, ya usado arriba) con más
// opacidad para que el área siga siendo claramente visible en dark mode.
export const CHART_COLOR_HIGHLIGHT_AREA = "rgba(245, 169, 190, 0.22)"; // --color-critical-text (Dark Mode) @ 22%
