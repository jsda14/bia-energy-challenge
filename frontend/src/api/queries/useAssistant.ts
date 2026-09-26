import { useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { apiClient } from "../client";

// Mensajes crudos del SDK de Anthropic — {"role": ..., "content": str |
// list[dict]}. El frontend nunca interpreta la forma interna de `content`,
// solo la guarda y la reenvía tal cual (contrato "mensaje crudo",
// SPEC-013 sección 1.2). z.unknown() es deliberado: no hay estructura que
// validar de este lado.
const rawMessageSchema = z.object({
  role: z.string(),
  content: z.unknown(),
});

export type RawMessage = z.infer<typeof rawMessageSchema>;

const assistantAskResponseSchema = z.object({
  text: z.string(),
  pending_action: z
    .object({
      tool: z.string(),
      description: z.string(),
    })
    .nullable(),
  assistant_message: rawMessageSchema.nullable(),
});

export type AssistantAskResponse = z.infer<typeof assistantAskResponseSchema>;

interface AskAssistantInput {
  conversation: RawMessage[];
  pending_confirmation: { confirmed: boolean } | null;
}

export function useAssistant() {
  return useMutation({
    mutationFn: async ({ conversation, pending_confirmation }: AskAssistantInput) => {
      const data = await apiClient.post("/assistant/ask", { conversation, pending_confirmation });
      return assistantAskResponseSchema.parse(data);
    },
  });
}
