import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { AiExplanationBlock } from "./AiExplanationBlock";

describe("AiExplanationBlock", () => {
  it("renders reposo state correctly for both reason and recommended action", () => {
    const onRegenerate = vi.fn();
    render(
      <AiExplanationBlock
        reason="Normal reason"
        recommendedAction="Normal action"
        explanationSource="template"
        affectedVariables={[]}
        correlatedEvent={null}
        isRegenerating={false}
        isRegenerateError={false}
        onRegenerate={onRegenerate}
      />
    );
    expect(screen.getByText("Regenerar explicación con IA")).toBeInTheDocument();
    expect(screen.getByText("Normal reason")).toBeInTheDocument();
    expect(screen.getByText("Normal action")).toBeInTheDocument();
  });

  it("calls onRegenerate when clicked", async () => {
    const user = userEvent.setup();
    const onRegenerate = vi.fn();
    render(
      <AiExplanationBlock
        reason="Normal reason"
        recommendedAction="Normal action"
        explanationSource="template"
        affectedVariables={[]}
        correlatedEvent={null}
        isRegenerating={false}
        isRegenerateError={false}
        onRegenerate={onRegenerate}
      />
    );
    await user.click(screen.getByRole("button", { name: "Regenerar explicación con IA" }));
    expect(onRegenerate).toHaveBeenCalled();
  });

  it("renders generating state: replaces both sections with skeletons, no stale content (CB-08)", () => {
    render(
      <AiExplanationBlock
        reason="Old reason"
        recommendedAction="Old action"
        explanationSource="template"
        affectedVariables={[]}
        correlatedEvent={null}
        isRegenerating={true}
        isRegenerateError={false}
        onRegenerate={vi.fn()}
      />
    );
    // Button text changes
    expect(screen.getAllByText("La IA está analizando…").length).toBeGreaterThan(0);
    // aria-busy
    expect(screen.getByRole("button")).toBeDisabled();
    // Neither stale field is rendered while regenerating — both replaced by skeleton
    expect(screen.queryByText("Old reason")).not.toBeInTheDocument();
    expect(screen.queryByText("Old action")).not.toBeInTheDocument();
    // Shared aria-busy container wraps the loader indicator
    const loaderTexts = screen.getAllByText("La IA está analizando…");
    const loaderSpan = loaderTexts.find((el) => el.tagName === "SPAN");
    const contentContainer = loaderSpan?.closest('[aria-busy="true"]');
    expect(contentContainer).toBeInTheDocument();
  });

  it("renders error state", () => {
    render(
      <AiExplanationBlock
        reason="Old reason"
        recommendedAction="Old action"
        explanationSource="template"
        affectedVariables={[]}
        correlatedEvent={null}
        isRegenerating={false}
        isRegenerateError={true}
        onRegenerate={vi.fn()}
      />
    );
    expect(screen.getByText("Error al regenerar la explicación.")).toBeInTheDocument();
  });

  it("shows a single updated badge when regeneration completes, covering both fields", () => {
    const { rerender } = render(
      <AiExplanationBlock
        reason="Old reason"
        recommendedAction="Old action"
        explanationSource="template"
        affectedVariables={[]}
        correlatedEvent={null}
        isRegenerating={true}
        isRegenerateError={false}
        onRegenerate={vi.fn()}
      />
    );

    rerender(
      <AiExplanationBlock
        reason="New reason"
        recommendedAction="New action"
        explanationSource="template"
        affectedVariables={[]}
        correlatedEvent={null}
        isRegenerating={false}
        isRegenerateError={false}
        onRegenerate={vi.fn()}
      />
    );

    expect(screen.getAllByText("Actualizado ahora").length).toBe(1);
    expect(screen.getByText("New reason")).toBeInTheDocument();
    expect(screen.getByText("New action")).toBeInTheDocument();
  });
});
