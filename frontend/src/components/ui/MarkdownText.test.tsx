import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MarkdownText } from "./MarkdownText";

describe("MarkdownText", () => {
  it("renders empty string without crashing", () => {
    const { container } = render(<MarkdownText content="" />);
    expect(container).toBeInTheDocument();
  });

  it("renders normal text without markdown without crashing", () => {
    render(<MarkdownText content="Just normal text" />);
    expect(screen.getByText("Just normal text")).toBeInTheDocument();
  });

  it("renders bold text", () => {
    render(<MarkdownText content="This is **bold**" />);
    expect(screen.getByText("bold")).toHaveClass(/markdown-text__strong/);
  });

  it("renders malformed markdown without crashing", () => {
    // Malformed markdown: bold not closed properly, table with uneven columns
    const content = `
This is **unclosed bold
    
| Col 1 | Col 2 |
|---|---|
| A |
| B | C | D |
`;
    const { container } = render(<MarkdownText content={content} />);
    expect(container).toBeInTheDocument();
    expect(screen.getByText("Col 1")).toBeInTheDocument();
  });
});
