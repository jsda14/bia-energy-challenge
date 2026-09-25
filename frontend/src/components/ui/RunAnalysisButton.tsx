import { useRunAnalysis } from "../../api/queries/useRunAnalysis";
import { useAnalysisStore } from "../../stores/useAnalysisStore";
import styles from "./RunAnalysisButton.module.css";

interface RunAnalysisButtonProps {
  /** meter_id específico, o null para analizar todos los medidores (comportamiento del Dashboard). */
  meterId: string | null;
}

export function RunAnalysisButton({ meterId }: RunAnalysisButtonProps) {
  const { mutate } = useRunAnalysis();
  const isRunning = useAnalysisStore((state) => state.isRunning);

  const handleClick = () => {
    mutate(meterId);
  };

  return (
    <button
      className={styles.button}
      onClick={handleClick}
      disabled={isRunning}
      type="button"
    >
      {isRunning ? "Analizando..." : "Ejecutar análisis"}
    </button>
  );
}
