import { ApiError, getUserMessage, getUserMessages, isTransient, statusMessage, UNEXPECTED_ERROR, UserFacingError } from "@/lib/errors";

describe("getUserMessage", () => {
  it("shows the message of a user-facing error", () => {
    expect(getUserMessage(new UserFacingError("Listo para mostrar"))).toBe("Listo para mostrar");
  });

  it.each([new Error("TypeError: x is undefined at line 3"), "string", null, undefined, new UserFacingError("")])(
    "hides internals of %p behind the generic message",
    (error) => {
      expect(getUserMessage(error)).toBe(UNEXPECTED_ERROR);
    },
  );
});

describe("getUserMessages", () => {
  it("returns one line per problem for an ApiError", () => {
    expect(getUserMessages(new ApiError(422, ["a", "b"]))).toEqual(["a", "b"]);
  });

  it("falls back to a single generic line", () => {
    expect(getUserMessages(new Error("boom"))).toEqual([UNEXPECTED_ERROR]);
    expect(getUserMessages(new ApiError(500, []))).toEqual([UNEXPECTED_ERROR]);
  });
});

describe("statusMessage", () => {
  it.each([
    [401, "sesión"],
    [403, "permiso"],
    [404, "encontrado"],
    [409, "Ya existe"],
    [429, "demasiadas"],
    [503, "no está disponible"],
    [500, "servidor"],
    [422, "no son válidos"],
  ])("status %i mentions %s", (status, text) => {
    expect(statusMessage(status)).toContain(text);
  });

  it("uses the kind over the status for network, timeout and parse failures", () => {
    expect(statusMessage(0, "network")).toContain("conectar");
    expect(statusMessage(200, "timeout")).toContain("tardando");
    expect(statusMessage(200, "parse")).toContain("inesperada");
  });

  it("falls back to the unexpected-error text for non-error statuses", () => {
    expect(statusMessage(200)).toBe(UNEXPECTED_ERROR);
  });
});

describe("isTransient", () => {
  it("is true for server errors and connection problems", () => {
    expect(isTransient(new ApiError(503, ["x"]))).toBe(true);
    expect(isTransient(new ApiError(0, ["x"], {}, "network"))).toBe(true);
  });

  it("is false for client errors and non-API errors", () => {
    expect(isTransient(new ApiError(422, ["x"]))).toBe(false);
    expect(isTransient(new Error("x"))).toBe(false);
  });
});
