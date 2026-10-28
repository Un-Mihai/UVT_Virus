// Runs a command against the local app as the signed-in demo reviewer, for tools that cannot sign
// in themselves (`impeccable detect` cannot send cookies). It signs in through Keycloak, then
// serves the app on a free localhost port with that session; arguments that start with the app's
// URL are pointed at that port.
// Usage: node scripts/signed_in.mjs http://localhost:3000 <command> [args...]
import { spawn } from "node:child_process";
import http from "node:http";
import net from "node:net";

const [appUrl, ...command] = process.argv.slice(2);
const app = new URL(appUrl);
const jar = new Map();

async function request(url, init = {}) {
  const cookie = [...jar].map(([name, value]) => `${name}=${value}`).join("; ");
  const response = await fetch(url, {
    ...init,
    redirect: "manual",
    headers: { ...init.headers, cookie },
  }).catch((error) => {
    console.error(
      `${url}: ${error.cause?.code ?? error.message}. Is the stack up (make up)?`,
    );
    process.exit(1);
  });
  for (const line of response.headers.getSetCookie()) {
    const pair = line.split(";")[0];
    jar.set(
      pair.slice(0, pair.indexOf("=")),
      pair.slice(pair.indexOf("=") + 1),
    );
  }
  return response;
}

async function follow(response) {
  for (let hops = 0; response.status >= 300 && response.status < 400; hops++) {
    if (hops === 10) throw new Error(`Too many redirects at ${response.url}`);
    response = await request(
      new URL(response.headers.get("location"), response.url),
    );
  }
  return response;
}

// The local demo account (compose.yaml, infra/keycloak/realm-app.json).
const page = await follow(
  await request(new URL("/auth/login?returnTo=/", app)),
);
const form = /<form[^>]*\bid="kc-form-login"[^>]*>/.exec(
  await page.text(),
)?.[0];
const action = form && /\baction="([^"]+)"/.exec(form)?.[1];
if (!action) {
  console.error(
    `No Keycloak sign-in form at ${page.url}. Is the stack up (make up)?`,
  );
  process.exit(1);
}
await follow(
  await request(action.replaceAll("&amp;", "&"), {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: "reviewer", password: "demo" }),
  }),
);
if (!jar.get("app_session")) {
  console.error(
    "Signing in as reviewer / demo failed. Check the user in Keycloak's admin console.",
  );
  process.exit(1);
}

const cookie = ["app_session", "app_access"]
  .map((name) => `${name}=${jar.get(name)}`)
  .join("; ");
const headers = (incoming) => ({ ...incoming, host: app.host, cookie });
const server = http.createServer((req, res) => {
  const upstream = http.request(
    {
      hostname: app.hostname,
      port: app.port,
      method: req.method,
      path: req.url,
      headers: headers(req.headers),
    },
    (answer) => {
      res.writeHead(answer.statusCode, answer.headers);
      answer.pipe(res);
    },
  );
  upstream.on("error", () => res.destroy());
  req.pipe(upstream);
});
// Next.js dev's hot-reload websocket; without it the dev client keeps reconnecting.
server.on("upgrade", (req, socket, head) => {
  const upstream = net.connect(Number(app.port), app.hostname, () => {
    const lines = Object.entries(headers(req.headers)).map(
      ([name, value]) => `${name}: ${value}\r\n`,
    );
    upstream.write(
      `${req.method} ${req.url} HTTP/1.1\r\n${lines.join("")}\r\n`,
    );
    upstream.write(head);
    upstream.pipe(socket).pipe(upstream);
  });
  upstream.on("error", () => socket.destroy());
  socket.on("error", () => upstream.destroy());
});

// localhost, not 127.0.0.1: Next.js dev blocks other origins from its dev assets (allowedDevOrigins).
server.listen(0, "localhost", () => {
  const signedIn = `http://localhost:${server.address().port}`;
  const args = command.map((arg) =>
    arg.startsWith(app.origin) ? signedIn + arg.slice(app.origin.length) : arg,
  );
  spawn(args[0], args.slice(1), { stdio: "inherit" }).on("exit", (code) =>
    process.exit(code ?? 1),
  );
});
