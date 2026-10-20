/** @jest-environment node */
import * as auth from "@/lib/auth";

jest.mock("@/lib/auth", () => ({
  getToken: jest.fn(),
  clearToken: jest.fn(),
  redirectToLogin: jest.fn(),
}));

const fetchMock = jest.fn();
const getToken = auth.getToken as jest.Mock;

function reply(status: number, body?: unknown): Response {
  return new Response(body === undefined ? null : JSON.stringify(body), { status });
}

function lastRequest() {
  const [url, init] = fetchMock.mock.calls.at(-1)!;
  return { url: url as string, init: init as RequestInit, headers: init.headers as Headers };
}

/** Loads lib/inventory with NEXT_PUBLIC_INVENTORY_API_URL set (it is read once, at import). */
function load(url?: string): typeof import("@/lib/inventory") {
  if (url === undefined) delete process.env.NEXT_PUBLIC_INVENTORY_API_URL;
  else process.env.NEXT_PUBLIC_INVENTORY_API_URL = url;
  let loaded!: typeof import("@/lib/inventory");
  jest.isolateModules(() => {
    loaded = jest.requireActual("@/lib/inventory");
  });
  return loaded;
}

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch = fetchMock;
  getToken.mockReturnValue("tok123");
});

describe("requests", () => {
  it("calls NEXT_PUBLIC_INVENTORY_API_URL with the Bearer token", async () => {
    const inventory = load("https://api.example.com/");
    fetchMock.mockResolvedValue(reply(200, []));
    await inventory.getProducts();
    expect(lastRequest().url).toBe("https://api.example.com/inventory/products");
    expect(lastRequest().headers.get("Authorization")).toBe("Bearer tok123");
  });

  it("falls back to the same-origin proxy when the variable is not set", async () => {
    const inventory = load();
    fetchMock.mockResolvedValue(reply(200, {}));
    await inventory.getProduct(7);
    expect(lastRequest().url).toBe("/api/inventory/products/7");
  });

  it("posts orders as JSON to the inbound and outbound routes", async () => {
    const inventory = load("https://api.example.com");
    fetchMock.mockImplementation(async () => reply(201, {}));
    await inventory.createInboundOrder({ asset_id: 1, quantity: 3, supplier: "Acme", office: "Valencia" });
    expect(lastRequest().url).toBe("https://api.example.com/inventory/orders/inbound");
    expect(lastRequest().init.method).toBe("POST");
    expect(lastRequest().init.body).toBe('{"asset_id":1,"quantity":3,"supplier":"Acme","office":"Valencia"}');
    await inventory.createOutboundOrder({ asset_id: 1, quantity: 1, exit_type: "consumption", assigned_to: null, office: "Valencia" });
    expect(lastRequest().url).toBe("https://api.example.com/inventory/orders/outbound");
  });
});

describe("errors", () => {
  const outbound = { asset_id: 1, quantity: 99, exit_type: "consumption" as const, assigned_to: null, office: "Valencia" as const };

  it("shows the API's 400 detail (insufficient stock)", async () => {
    const inventory = load("https://api.example.com");
    const detail = "Insufficient stock for asset 'Ratón ergonómico'. Available: 16, requested: 99.";
    fetchMock.mockResolvedValue(reply(400, { detail }));
    await expect(inventory.createOutboundOrder(outbound)).rejects.toMatchObject({ status: 400, message: detail });
  });

  it("maps a 422 to per-field messages", async () => {
    const inventory = load("https://api.example.com");
    fetchMock.mockResolvedValue(
      reply(422, { detail: [{ loc: ["body", "quantity"], msg: "x", type: "greater_than", ctx: { gt: 0 } }] }),
    );
    const error = await inventory.createOutboundOrder(outbound).catch((e) => e);
    expect(error.fieldErrors).toEqual({ quantity: "Debe ser mayor que 0" });
    expect(error.message).toBe("Cantidad: Debe ser mayor que 0");
  });

  it("hides the text of a 500 and tolerates a non-JSON body", async () => {
    const inventory = load("https://api.example.com");
    fetchMock.mockResolvedValue(reply(500, { detail: "Traceback (most recent call last)" }));
    const error = await inventory.getOrders().catch((e) => e);
    expect(error.status).toBe(500);
    expect(error.message).toContain("No se pudo cargar el historial");
    expect(error.message).not.toContain("Traceback");
    fetchMock.mockResolvedValue(new Response("<html>Bad gateway</html>", { status: 502 }));
    await expect(inventory.getOrders()).rejects.toMatchObject({ status: 502 });
  });

  it("turns a network failure into a readable error", async () => {
    const inventory = load("https://api.example.com");
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(inventory.getProducts()).rejects.toMatchObject({ kind: "network", message: expect.stringContaining("conectar con el servidor") });
  });

  it("on 401 clears the token and redirects to login", async () => {
    const inventory = load("https://api.example.com");
    fetchMock.mockResolvedValue(reply(401, { detail: "Invalid or expired token" }));
    await expect(inventory.getProducts()).rejects.toMatchObject({ status: 401 });
    expect(auth.clearToken).toHaveBeenCalledTimes(1);
    expect(auth.redirectToLogin).toHaveBeenCalledTimes(1);
  });
});

describe("stockLevel", () => {
  const { stockLevel, LOW_STOCK_MAX } = load("https://api.example.com");

  it("is out at 0 (or below), low up to the threshold and healthy above it", () => {
    expect(stockLevel(0)).toBe("out");
    expect(stockLevel(-1)).toBe("out");
    expect(stockLevel(1)).toBe("low");
    expect(stockLevel(LOW_STOCK_MAX)).toBe("low");
    expect(stockLevel(LOW_STOCK_MAX + 1)).toBe("healthy");
  });
});
