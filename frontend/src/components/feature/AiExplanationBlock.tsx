import { useEffect, useState, useRef } from "react";
import { MarkdownText } from "../ui/MarkdownText";
import { SourceBadge } from "../ui/SourceBadge";
import styles from "./AiExplanationBlock.module.css";

interface AiExplanationBlockProps {
  reason: string;
  recommendedAction: string;
  explanationSource: string;
  affectedVariables: string[];
  correlatedEvent: string | null;
  isRegenerating: boolean;
  isRegenerateError: boolean;
  onRegenerate: () => void;
}

function Skeleton() {
  return (
    <div className={styles["ai-explanation-block__skeleton"]}>
      <div className={styles["ai-explanation-block__skeleton-line"]} style={{ width: "90%" }} />
      <div className={styles["ai-explanation-block__skeleton-line"]} style={{ width: "70%" }} />
      <div className={styles["ai-explanation-block__skeleton-line"]} style={{ width: "80%" }} />
    </div>
  );
}

export function AiExplanationBlock({
  reason,
  recommendedAction,
  explanationSource,
  affectedVariables,
  correlatedEvent,
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
    <div className={styles["ai-explanation-block__container"]}>
      <div className={styles["ai-explanation-block__header"]}>
        <div className={styles["ai-explanation-block__title-wrapper"]}>
          <h2 className={styles["ai-explanation-block__title"]}>Explicación de IA</h2>
          <SourceBadge source={explanationSource} />
        </div>
        <button
          className={styles["ai-explanation-block__button"]}
          onClick={onRegenerate}
          disabled={isRegenerating}
        >
          {isRegenerating ? "La IA está analizando…" : "Regenerar explicación con IA"}
        </button>
      </div>

      {isRegenerateError && (
        <p className={styles["ai-explanation-block__error-text"]}>Error al regenerar la explicación.</p>
      )}

      <div className={styles["ai-explanation-block__content"]} aria-busy={isRegenerating} aria-live="polite">
        {isRegenerating && (
          <div className={`${styles["ai-explanation-block__loader-status"]} pulse--pulse`}>
            <span className={styles["ai-explanation-block__pulse-dot"]} aria-hidden="true" />
            <span>La IA está analizando…</span>
          </div>
        )}

        <section className={styles["ai-explanation-block__section"]}>
          <h3 className={styles["ai-explanation-block__section-title"]}>Razón</h3>
          {isRegenerating ? (
            <Skeleton />
          ) : (
            <div className={styles["ai-explanation-block__section-entry"]}>
              <MarkdownText content={reason} />
            </div>
          )}
        </section>

        <section className={styles["ai-explanation-block__section"]}>
          <h3 className={styles["ai-explanation-block__section-title"]}>Acción Recomendada</h3>
          {isRegenerating ? (
            <Skeleton />
          ) : (
            <div className={styles["ai-explanation-block__section-entry"]}>
              <MarkdownText content={recommendedAction} />
            </div>
          )}
        </section>

        <section className={styles["ai-explanation-block__section"]}>
          <h3 className={styles["ai-explanation-block__section-title"]}>Variables Afectadas</h3>
          {isRegenerating ? (
            <Skeleton />
          ) : (
            <div className={styles["ai-explanation-block__section-entry"]}>
              {affectedVariables.length > 0 ? (
                <ul className={styles["ai-explanation-block__variable-list"]}>
                  {affectedVariables.map((v) => (
                    <li key={v}>{v}</li>
                  ))}
                </ul>
              ) : (
                <p>Ninguna</p>
              )}
            </div>
          )}
        </section>

        <section className={styles["ai-explanation-block__section"]}>
          <h3 className={styles["ai-explanation-block__section-title"]}>Evento Correlacionado</h3>
          {isRegenerating ? (
            <Skeleton />
          ) : (
            <div className={styles["ai-explanation-block__section-entry"]}>
              {correlatedEvent ? (
                <div className={styles["ai-explanation-block__event-highlight"]}>
                  {correlatedEvent}
                </div>
              ) : (
                <p>Sin evento correlacionado</p>
              )}
            </div>
          )}
        </section>

        {showUpdated && !isRegenerating && (
          <div className={styles["ai-explanation-block__updated-badge"]} onAnimationEnd={() => setShowUpdated(false)}>
            Actualizado ahora
          </div>
        )}
      </div>
    </div>
  );
}
