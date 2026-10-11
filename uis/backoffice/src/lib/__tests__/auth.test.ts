import { clearToken, getToken, isTokenValid, logout, redirectToLogin, setToken, subscribeToToken } from "@/lib/auth";
import { UserFacingError } from "@/lib/errors";

const KEY = "nexova.accessToken";

/** Unsigned JWT-shaped string with the given payload (the client only reads `exp`). */
function jwtWith(payload: object): string {
  const encode = (value: object) => btoa(JSON.stringify(value)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  return `${encode({ alg: "HS256" })}.${encode(payload)}.signature`;
}

const inSeconds = (seconds: number) => Math.floor(Date.now() / 1000) + seconds;

beforeEach(() => {
  window.localStorage.clear();
  window.history.pushState({}, "", "/");
});

afterEach(() => jest.restoreAllMocks());

describe("token storage", () => {
  it("stores, reads and clears the token", () => {
    expect(getToken()).toBeNull();
    setToken("abc");
    expect(window.localStorage.getItem(KEY)).toBe("abc");
    expect(getToken()).toBe("abc");
    clearToken();
    expect(getToken()).toBeNull();
  });

  it("setToken overwrites the previous token", () => {
    setToken("one");
    setToken("two");
    expect(getToken()).toBe("two");
  });

  it("getToken returns null instead of throwing when storage is blocked", () => {
    jest.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(getToken()).toBeNull();
  });

  it("setToken throws a user-facing error when storage is blocked", () => {
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(() => setToken("abc")).toThrow(UserFacingError);
  });

  it("clearToken does not throw when storage is blocked", () => {
    jest.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(() => clearToken()).not.toThrow();
  });

  it("notifies subscribers in this tab on set and clear, and stops after unsubscribe", () => {
    const onChange = jest.fn();
    const unsubscribe = subscribeToToken(onChange);
    setToken("abc");
    clearToken();
    expect(onChange).toHaveBeenCalledTimes(2);
    unsubscribe();
    setToken("again");
    expect(onChange).toHaveBeenCalledTimes(2);
  });

  it("notifies on storage events for the token key (other tabs) and ignores other keys", () => {
    const onChange = jest.fn();
    const unsubscribe = subscribeToToken(onChange);
    window.dispatchEvent(new StorageEvent("storage", { key: KEY }));
    window.dispatchEvent(new StorageEvent("storage", { key: null }));
    window.dispatchEvent(new StorageEvent("storage", { key: "other" }));
    expect(onChange).toHaveBeenCalledTimes(2);
    unsubscribe();
  });
});

describe("isTokenValid", () => {
  it("accepts a token whose exp is in the future", () => {
    expect(isTokenValid(jwtWith({ exp: inSeconds(60) }))).toBe(true);
  });

  it("rejects a token whose exp is in the past", () => {
    expect(isTokenValid(jwtWith({ exp: inSeconds(-1) }))).toBe(false);
  });

  it("rejects a token without exp or with a non-numeric exp", () => {
    expect(isTokenValid(jwtWith({ sub: "u" }))).toBe(false);
    expect(isTokenValid(jwtWith({ exp: "soon" }))).toBe(false);
  });

  it.each(["", "garbage", "a.b", "a.!!!.c", "a..c"])("rejects the malformed token %p", (token) => {
    expect(isTokenValid(token)).toBe(false);
  });

  it("rejects a payload that is not JSON", () => {
    expect(isTokenValid(`a.${btoa("not json")}.c`)).toBe(false);
  });

  it("reads the stored token by default and rejects when there is none", () => {
    expect(isTokenValid()).toBe(false);
    setToken(jwtWith({ exp: inSeconds(60) }));
    expect(isTokenValid()).toBe(true);
    expect(isTokenValid(null)).toBe(false);
  });
});

describe("redirect and logout", () => {
  it("does not navigate when already on the login page", () => {
    window.history.pushState({}, "", "/login");
    const error = jest.spyOn(console, "error").mockImplementation(() => {});
    redirectToLogin();
    expect(error).not.toHaveBeenCalled();
  });

  it("attempts to navigate to /login from any other page", () => {
    // jsdom cannot navigate: it reports "Not implemented: navigation" through console.error.
    const error = jest.spyOn(console, "error").mockImplementation(() => {});
    redirectToLogin();
    expect(String(error.mock.calls[0]?.[0])).toMatch(/navigation/i);
  });

  it("logout clears the token and redirects", () => {
    setToken("abc");
    const error = jest.spyOn(console, "error").mockImplementation(() => {});
    logout();
    expect(getToken()).toBeNull();
    expect(error).toHaveBeenCalled();
  });
});
