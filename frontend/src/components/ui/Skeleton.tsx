import styles from "./Skeleton.module.css";

interface SkeletonProps {
  width?: string;
  height?: string;
  className?: string;
}

/** Placeholder de carga con animación shimmer, para reemplazar el patrón
 * `<div>Cargando...</div>` de texto plano por rectángulos con la forma
 * aproximada del contenido real. Presentación pura, sin datos. */
export function Skeleton({ width = "100%", height = "1rem", className = "" }: SkeletonProps) {
  return (
    <div
      className={`${styles.skeleton} ${className}`}
      style={{ width, height }}
      data-testid="skeleton"
      aria-hidden="true"
    />
  );
}
