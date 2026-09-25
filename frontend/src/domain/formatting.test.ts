import { describe, it, expect } from "vitest";
import { severityToColorToken } from "./formatting";

describe("severityToColorToken", () => {
  it("maps LOW to neutral", () => {
    expect(severityToColorToken("LOW")).toBe("neutral");
  });

  it("maps MEDIUM to warning", () => {
    expect(severityToColorToken("MEDIUM")).toBe("warning");
  });

  it("maps HIGH to critical", () => {
    expect(severityToColorToken("HIGH")).toBe("critical");
  });

  it("maps an unrecognized value to neutral", () => {
    expect(severityToColorToken("UNKNOWN")).toBe("neutral");
  });
});
