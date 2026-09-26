import { useEffect, useState } from "react";
import { useAssistant, type RawMessage } from "../../api/queries/useAssistant";
import { MarkdownText } from "../ui/MarkdownText";
import styles from "./AssistantPanel.module.css";

interface DisplayMessage {
  role: "user" | "assistant";
  text: string;
}

interface PendingAction {
  tool: string;
  description: string;
}

export function AssistantPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [conversation, setConversation] = useState<RawMessage[]>([]);
  const [displayMessages, setDisplayMessages] = useState<DisplayMessage[]>([]);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const { mutate, isPending } = useAssistant();

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isPending) return;

    const userMessage: RawMessage = { role: "user", content: text };
    const nextConversation = [...conversation, userMessage];
    setConversation(nextConversation);
    setDisplayMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");

    mutate(
      { conversation: nextConversation, pending_confirmation: null },
      {
        onSuccess: (response) => {
          if (response.pending_action) {
            // El text viene vacío en este caso — no se agrega nada al
            // historial visible todavía. Se guarda el assistant_message
            // crudo en `conversation` para reenviarlo intacto al
            // confirmar/cancelar (SPEC-013 sección 1.2).
            if (response.assistant_message) {
              setConversation((prev) => [...prev, response.assistant_message as RawMessage]);
            }
            setPendingAction(response.pending_action);
            return;
          }
          setConversation((prev) => [...prev, { role: "assistant", content: response.text }]);
          setDisplayMessages((prev) => [...prev, { role: "assistant", text: response.text }]);
        },
      }
    );
  };

  const handleConfirm = (confirmed: boolean) => {
    // Nunca se envía confirmed: true fuera de este handler — es el único
    // punto del componente que dispara la mutation con
    // pending_confirmation. El click explícito del usuario en "Confirmar"
    // es la única vía.
    mutate(
      { conversation, pending_confirmation: { confirmed } },
      {
        onSuccess: (response) => {
          setPendingAction(null);
          setConversation((prev) => [...prev, { role: "assistant", content: response.text }]);
          setDisplayMessages((prev) => [...prev, { role: "assistant", text: response.text }]);
        },
      }
    );
  };

  return (
    <>
      <button
        type="button"
        className={styles.fab}
        aria-expanded={isOpen}
        aria-controls="assistant-panel"
        aria-label={isOpen ? "Cerrar asistente" : "Abrir asistente"}
        onClick={() => setIsOpen((open) => !open)}
      >
        💬
      </button>

      {isOpen && (
        <div id="assistant-panel" className={styles.panel} role="dialog" aria-label="Asistente de Bia Energy">
          <div className={styles.header}>
            <span className={styles.headerIcon} aria-hidden="true">💬</span>
            <h2 className={styles.title}>Asistente</h2>
          </div>

          <div className={styles.messages} aria-live="polite" aria-busy={isPending}>
            {displayMessages.map((msg, i) => (
              <div key={i} className={`${styles.message} ${styles[`message--${msg.role}`]}`}>
                {msg.role === "assistant" ? <MarkdownText content={msg.text} /> : msg.text}
              </div>
            ))}
            {isPending && (
              <div className={`${styles.message} ${styles["message--assistant"]} ${styles.typingIndicator}`}>
                <span className={styles.typingDot} />
                <span className={styles.typingDot} />
                <span className={styles.typingDot} />
              </div>
            )}
          </div>

          {pendingAction && (
            <div className={styles.confirmBox}>
              <p className={styles.confirmText}>{pendingAction.description}</p>
              <div className={styles.confirmActions}>
                <button
                  type="button"
                  className={styles.confirmButton}
                  onClick={() => handleConfirm(true)}
                  disabled={isPending}
                >
                  Confirmar
                </button>
                <button
                  type="button"
                  className={styles.cancelButton}
                  onClick={() => handleConfirm(false)}
                  disabled={isPending}
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          <div className={styles.inputRow}>
            <input
              type="text"
              className={styles.input}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              placeholder="Preguntá algo…"
              disabled={isPending || !!pendingAction}
            />
            <button
              type="button"
              className={styles.sendButton}
              onClick={handleSend}
              disabled={isPending || !!pendingAction || !input.trim()}
            >
              Enviar
            </button>
          </div>
        </div>
      )}
    </>
  );
}
