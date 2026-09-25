import { useEffect, useState, useRef } from "react";
import { MarkdownText } from "../ui/MarkdownText";
import { SourceBadge } from "../ui/SourceBadge";
import styles from "./AiExplanationBlock.module.css";

interface AiExplanationBlockProps {
  reason: string;
  recommendedAction: string;
  explanationSource: string;
  isRegenerating: boolean;
  isRegenerateError: boolean;
  onRegenerate: () => void;
}

function Skeleton() {
  return (
    <div className={styles.skeleton}>
      <div className={styles.skeletonLine} style={{ width: "90%" }} />
      <div className={styles.skeletonLine} style={{ width: "70%" }} />
      <div className={styles.skeletonLine} style={{ width: "80%" }} />
    </div>
  );
}

export function AiExplanationBlock({
  reason,
  recommendedAction,
  explanationSource,
  isRegenerating,
  isRegenerateError,
  onRegenerate,
}: AiExplanationBlockProps) {
  const [showUpdated, setShowUpdated] = useState(false);
  const wasRegeneratingRef = useRef(isRegenerating);

  useEffect(() => {
    if (wasRegeneratingRef.current && !isRegenerating && !isRegenerateError) {
      setShowUpdated(true);
    }
    wasRegeneratingRef.current = isRegenerating;
  }, [isRegenerating, isRegenerateError]);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.titleWrapper}>
          <h2 className={styles.title}>Explicación de IA</h2>
          <SourceBadge source={explanationSource} />
        </div>
        <button
          className={styles.button}
          onClick={onRegenerate}
          disabled={isRegenerating}
        >
          {isRegenerating ? "La IA está analizando…" : "Regenerar explicación con IA"}
        </button>
      </div>

      {isRegenerateError && (
        <p className={styles.errorText}>Error al regenerar la explicación.</p>
      )}

      <div className={styles.content} aria-busy={isRegenerating} aria-live="polite">
        {isRegenerating && (
          <div className={`${styles.loaderStatus} pulse--pulse`}>
            <span className={styles.pulseDot} aria-hidden="true" />
            <span>La IA está analizando…</span>
          </div>
        )}

        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>Razón</h3>
          {isRegenerating ? (
            <Skeleton />
          ) : (
            <div className={styles.sectionEntry}>
              <MarkdownText content={reason} />
            </div>
          )}
        </section>

        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>Acción Recomendada</h3>
          {isRegenerating ? (
            <Skeleton />
          ) : (
            <div className={styles.sectionEntry}>
              <MarkdownText content={recommendedAction} />
            </div>
          )}
        </section>

        {showUpdated && !isRegenerating && (
          <div className={styles.updatedBadge} onAnimationEnd={() => setShowUpdated(false)}>
            Actualizado ahora
          </div>
        )}
      </div>
    </div>
  );
}
