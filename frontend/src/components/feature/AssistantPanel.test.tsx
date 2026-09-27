import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AssistantPanel } from "./AssistantPanel";
import { useAssistant } from "../../api/queries/useAssistant";

vi.mock("../../api/queries/useAssistant");

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mockUseAssistant = useAssistant as any;

describe("AssistantPanel", () => {
  beforeEach(() => {
    mockUseAssistant.mockReturnValue({ mutate: vi.fn(), isPending: false });
  });

  it("opens the panel when the floating button is clicked", async () => {
    const user = userEvent.setup();
    render(<AssistantPanel />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Abrir asistente" }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("closes the panel on Escape", async () => {
    const user = userEvent.setup();
    render(<AssistantPanel />);
    await user.click(screen.getByRole("button", { name: "Abrir asistente" }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("applies the correct BEM modifier class per message role", async () => {
    const mutateMock = vi.fn((_input, options) => {
      options.onSuccess({ text: "Hola, ¿en qué te ayudo?", pending_action: null, assistant_message: null });
    });
    mockUseAssistant.mockReturnValue({ mutate: mutateMock, isPending: false });

    const user = userEvent.setup();
    render(<AssistantPanel />);
    await user.click(screen.getByRole("button", { name: "Abrir asistente" }));
    await user.type(screen.getByPlaceholderText("Preguntá algo…"), "hola");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    const userMessage = await screen.findByText("hola");
    expect(userMessage).toHaveClass(/assistant-panel__message--user/);
    const assistantMessage = await screen.findByText("Hola, ¿en qué te ayudo?");
    expect(assistantMessage.closest('[class*="assistant-panel__message"]')).toHaveClass(
      /assistant-panel__message--assistant/
    );
  });

  it("sends a message and displays a plain-text response", async () => {
    const mutateMock = vi.fn((_input, options) => {
      options.onSuccess({ text: "Hola, ¿en qué te ayudo?", pending_action: null, assistant_message: null });
    });
    mockUseAssistant.mockReturnValue({ mutate: mutateMock, isPending: false });

    const user = userEvent.setup();
    render(<AssistantPanel />);
    await user.click(screen.getByRole("button", { name: "Abrir asistente" }));

    const input = screen.getByPlaceholderText("Preguntá algo…");
    await user.type(input, "hola");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(mutateMock).toHaveBeenCalledWith(
      { conversation: [{ role: "user", content: "hola" }], pending_confirmation: null },
      expect.anything()
    );
    expect(await screen.findByText("Hola, ¿en qué te ayudo?")).toBeInTheDocument();
  });

  it("shows a confirmation dialog when the response has a pending_action, without executing anything yet", async () => {
    const mutateMock = vi.fn((_input, options) => {
      options.onSuccess({
        text: "",
        pending_action: { tool: "run_analysis", description: "¿Confirmas ejecutar el análisis para todos los medidores?" },
        assistant_message: { role: "assistant", content: [{ type: "tool_use", id: "t1", name: "run_analysis", input: {} }] },
      });
    });
    mockUseAssistant.mockReturnValue({ mutate: mutateMock, isPending: false });

    const user = userEvent.setup();
    render(<AssistantPanel />);
    await user.click(screen.getByRole("button", { name: "Abrir asistente" }));

    const input = screen.getByPlaceholderText("Preguntá algo…");
    await user.type(input, "corré el análisis");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("¿Confirmas ejecutar el análisis para todos los medidores?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
    // El texto vacío de la respuesta con pending_action no se muestra como
    // burbuja de chat de asistente — solo el mensaje de usuario está presente.
    const messages = screen.getAllByText(/./, { selector: "div[class*='message--']" });
    expect(messages).toHaveLength(1);
    expect(messages[0]).toHaveTextContent("corré el análisis");
  });

  it("PUNTO CENTRAL DE SEGURIDAD: clicking 'Cancelar' never sends pending_confirmation.confirmed=true", async () => {
    const mutateMock = vi.fn();
    let callCount = 0;
    mutateMock.mockImplementation((_input, options) => {
      callCount += 1;
      if (callCount === 1) {
        // Primera llamada: el envío del mensaje original, responde con pending_action.
        options.onSuccess({
          text: "",
          pending_action: { tool: "set_triage_status", description: "¿Confirmas marcar la anomalía anomaly-1 como Descartada?" },
          assistant_message: { role: "assistant", content: [{ type: "tool_use", id: "t1", name: "set_triage_status", input: {} }] },
        });
      } else {
        // Segunda llamada: la resolución de la confirmación (cancelar).
        options.onSuccess({ text: "Entendido, no se realizó ningún cambio.", pending_action: null, assistant_message: null });
      }
    });
    mockUseAssistant.mockReturnValue({ mutate: mutateMock, isPending: false });

    const user = userEvent.setup();
    render(<AssistantPanel />);
    await user.click(screen.getByRole("button", { name: "Abrir asistente" }));

    await user.type(screen.getByPlaceholderText("Preguntá algo…"), "descartá esa anomalía");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    await screen.findByText("¿Confirmas marcar la anomalía anomaly-1 como Descartada?");

    await user.click(screen.getByRole("button", { name: "Cancelar" }));

    await waitFor(() => expect(mutateMock).toHaveBeenCalledTimes(2));

    // La llamada de cancelación explícita nunca lleva confirmed: true.
    const cancelCallInput = mutateMock.mock.calls[1][0];
    expect(cancelCallInput.pending_confirmation).toEqual({ confirmed: false });

    // Ninguna llamada a mutate en todo el flujo llevó confirmed: true.
    const anyConfirmedTrue = mutateMock.mock.calls.some(
      (call) => call[0].pending_confirmation?.confirmed === true
    );
    expect(anyConfirmedTrue).toBe(false);

    expect(await screen.findByText("Entendido, no se realizó ningún cambio.")).toBeInTheDocument();
    // El diálogo de confirmación se cierra tras resolver.
    expect(screen.queryByRole("button", { name: "Confirmar" })).not.toBeInTheDocument();
  });

  it("clicking 'Confirmar' sends pending_confirmation.confirmed=true", async () => {
    const mutateMock = vi.fn();
    let callCount = 0;
    mutateMock.mockImplementation((_input, options) => {
      callCount += 1;
      if (callCount === 1) {
        options.onSuccess({
          text: "",
          pending_action: { tool: "run_analysis", description: "¿Confirmas ejecutar el análisis para todos los medidores?" },
          assistant_message: { role: "assistant", content: [{ type: "tool_use", id: "t1", name: "run_analysis", input: {} }] },
        });
      } else {
        options.onSuccess({ text: "Listo, corrí el análisis.", pending_action: null, assistant_message: null });
      }
    });
    mockUseAssistant.mockReturnValue({ mutate: mutateMock, isPending: false });

    const user = userEvent.setup();
    render(<AssistantPanel />);
    await user.click(screen.getByRole("button", { name: "Abrir asistente" }));
    await user.type(screen.getByPlaceholderText("Preguntá algo…"), "corré el análisis");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    await screen.findByText("¿Confirmas ejecutar el análisis para todos los medidores?");
    await user.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() => expect(mutateMock).toHaveBeenCalledTimes(2));
    const confirmCallInput = mutateMock.mock.calls[1][0];
    expect(confirmCallInput.pending_confirmation).toEqual({ confirmed: true });
    // La conversación reenviada incluye el assistant_message crudo guardado.
    expect(confirmCallInput.conversation).toContainEqual({
      role: "assistant",
      content: [{ type: "tool_use", id: "t1", name: "run_analysis", input: {} }],
    });

    expect(await screen.findByText("Listo, corrí el análisis.")).toBeInTheDocument();
  });
});
