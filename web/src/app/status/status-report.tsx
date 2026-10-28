import type { ReactNode } from "react";

import { api } from "@/lib/api/server";
import type { components } from "@/lib/api/schema";
import {
  formatClockUtc,
  formatCount,
  formatDuration,
  formatUsd,
} from "@/lib/format";

type Health = components["schemas"]["Health"];
type Usage = components["schemas"]["Usage"];
type User = components["schemas"]["User"];
type State = "ok" | "warn" | "bad";

const apiUrl = process.env.API_URL ?? "http://localhost:8000";

async function load() {
  try {
    const [health, usage, me] = await Promise.all([
      api.GET("/health"),
      api.GET("/api/ai/usage"),
      api.GET("/api/me"),
    ]);
    return {
      reachable: true,
      health: health.data ?? null,
      usage: usage.data ?? null,
      me: me.data ?? null,
      meStatus: me.response.status,
    };
  } catch {
    return {
      reachable: false,
      health: null,
      usage: null,
      me: null,
      meStatus: 0,
    };
  }
}

export async function StatusReport() {
  const { reachable, health, usage, me, meStatus } = await load();

  return (
    <>
      <Section title="Services">
        <ul className="divide-y divide-line border-y border-line">
          <ServiceRow name="Web" state="ok" status="Serving">
            Next.js 16 · React 19
          </ServiceRow>
          <SignInRow reachable={reachable} me={me} status={meStatus} />
          <ServiceRow
            name="API"
            state={reachable ? "ok" : "bad"}
            status={reachable ? "Answering" : "Unreachable"}
          >
            {reachable ? (
              <code>{apiUrl}</code>
            ) : (
              <>
                No answer from <code>{apiUrl}</code>. Start it with{" "}
                <code>docker compose up api</code>.
              </>
            )}
          </ServiceRow>
          <DatabaseRow reachable={reachable} health={health} />
          <AiRow usage={usage} />
        </ul>
      </Section>
      {usage && <Spend usage={usage} />}
      {usage && <Calls calls={usage.recent_calls} />}
    </>
  );
}

function SignInRow({
  reachable,
  me,
  status,
}: {
  reachable: boolean;
  me: User | null;
  status: number;
}) {
  if (me) {
    return (
      <ServiceRow name="Sign-in" state="ok" status="Verified">
        Keycloak · the API accepted the token for <code>{me.username}</code>
        {me.roles.length > 0 && <> ({me.roles.join(", ")})</>}
      </ServiceRow>
    );
  }
  if (!reachable) {
    return (
      <ServiceRow name="Sign-in" state="warn" status="Unknown">
        Checked through the API, which is not answering.
      </ServiceRow>
    );
  }
  return (
    <ServiceRow name="Sign-in" state="bad" status="Rejected">
      {status === 503 ? (
        <>
          The API cannot reach Keycloak&rsquo;s signing keys. Check{" "}
          <code>AUTH_JWKS_URL</code>.
        </>
      ) : (
        <>
          The API rejected the access token. Check <code>AUTH_ISSUER</code> on
          the web app and the API.
        </>
      )}
    </ServiceRow>
  );
}

function DatabaseRow({
  reachable,
  health,
}: {
  reachable: boolean;
  health: Health | null;
}) {
  if (!reachable) {
    return (
      <ServiceRow name="Database" state="warn" status="Unknown">
        Checked through the API, which is not answering.
      </ServiceRow>
    );
  }
  if (health?.database !== "ok") {
    return (
      <ServiceRow name="Database" state="bad" status="Unreachable">
        The API cannot reach PostgreSQL. Check <code>DATABASE_URL</code> and{" "}
        <code>docker compose ps db</code>.
      </ServiceRow>
    );
  }
  return (
    <ServiceRow name="Database" state="ok" status="Ready">
      PostgreSQL · pgvector {health.pgvector ?? "not installed"}
    </ServiceRow>
  );
}

function AiRow({ usage }: { usage: Usage | null }) {
  if (!usage) {
    return (
      <ServiceRow name="AI provider" state="warn" status="Unknown">
        Checked through the API, which is not answering.
      </ServiceRow>
    );
  }
  if (!usage.configured) {
    return (
      <ServiceRow name="AI provider" state="warn" status="Not set up">
        Set <code>AI_BASE_URL</code> and <code>AI_API_KEY</code> in{" "}
        <code>.env</code>, then restart the API.
      </ServiceRow>
    );
  }
  const accounts =
    usage.providers.length === 1
      ? "1 account"
      : `${usage.providers.length} accounts`;
  return (
    <ServiceRow name="AI provider" state="ok" status={accounts}>
      <code>{usage.chat_model}</code> for chat,{" "}
      <code>{usage.embedding_model}</code> for embeddings
    </ServiceRow>
  );
}

function Spend({ usage }: { usage: Usage }) {
  const share =
    usage.daily_budget_usd > 0
      ? usage.spent_today_usd / usage.daily_budget_usd
      : 1;
  const percent = Math.min(100, Math.round(share * 100));

  return (
    <Section title="AI spend today">
      <p className="text-ink-2">
        <span className="font-semibold text-ink tabular-nums">
          {formatUsd(usage.spent_today_usd)}
        </span>{" "}
        of the {formatUsd(usage.daily_budget_usd)} daily budget. Calls stop at
        the limit; raise <code>AI_DAILY_BUDGET_USD</code> to continue.
      </p>
      <div
        role="meter"
        aria-label="Share of today's AI budget used"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        className="mt-4 h-1.5 max-w-md overflow-hidden rounded-full bg-surface-2"
      >
        <div
          className={`h-full rounded-full ${percent >= 90 ? "bg-bad" : "bg-accent"}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </Section>
  );
}

function Calls({ calls }: { calls: Usage["recent_calls"] }) {
  return (
    <Section title="Recent AI calls">
      {calls.length === 0 ? (
        <p className="max-w-prose text-ink-2">
          No AI calls yet. Run the AI check above, or call <code>AIClient</code>{" "}
          from the API: every call is logged here with its tokens, cost and
          duration.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[44rem] text-left text-sm">
            <thead className="border-b border-line-strong text-ink-3">
              <tr>
                <th className="py-2 pr-4 font-medium">Time</th>
                <th className="py-2 pr-4 font-medium">Purpose</th>
                <th className="py-2 pr-4 font-medium">Account</th>
                <th className="py-2 pr-4 font-medium">Model</th>
                <th className="py-2 pr-4 text-right font-medium">
                  Tokens in / out
                </th>
                <th className="py-2 pr-4 text-right font-medium">Cost</th>
                <th className="py-2 pr-4 text-right font-medium">Duration</th>
                <th className="py-2 font-medium">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line tabular-nums">
              {calls.map((call) => (
                <tr key={call.id}>
                  <td className="py-2.5 pr-4 whitespace-nowrap">
                    {formatClockUtc(call.created_at)}
                  </td>
                  <td className="py-2.5 pr-4">{call.purpose}</td>
                  <td className="py-2.5 pr-4">{call.provider}</td>
                  <td className="py-2.5 pr-4">
                    <code>{call.model}</code>
                  </td>
                  <td className="py-2.5 pr-4 text-right whitespace-nowrap">
                    {formatCount(call.input_tokens)} /{" "}
                    {formatCount(call.output_tokens)}
                  </td>
                  <td className="py-2.5 pr-4 text-right">
                    {formatUsd(call.cost_usd)}
                  </td>
                  <td className="py-2.5 pr-4 text-right whitespace-nowrap">
                    {formatDuration(call.duration_ms)}
                  </td>
                  <td
                    className={`py-2.5 ${call.error ? "text-bad" : "text-ink-2"}`}
                  >
                    {call.error ?? "OK"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Section>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-12">
      <h2 className="mb-4 text-lg font-semibold tracking-tight">{title}</h2>
      {children}
    </section>
  );
}

const dot: Record<State, string> = {
  ok: "bg-ok",
  warn: "bg-warn",
  bad: "bg-bad",
};
const label: Record<State, string> = {
  ok: "text-ink-2",
  warn: "text-warn",
  bad: "text-bad",
};

function ServiceRow({
  name,
  state,
  status,
  children,
}: {
  name: string;
  state: State;
  status: string;
  children: ReactNode;
}) {
  return (
    <li className="grid grid-cols-[auto_1fr_auto] items-baseline gap-x-4 gap-y-1 py-3.5 sm:grid-cols-[auto_9rem_1fr_auto]">
      <span
        aria-hidden
        className={`size-2 translate-y-[-0.1em] rounded-full ${dot[state]}`}
      />
      <span className="font-medium">{name}</span>
      <span className="col-start-2 row-start-2 text-ink-2 sm:col-start-3 sm:row-start-1">
        {children}
      </span>
      <span
        className={`col-start-3 row-start-1 text-sm sm:col-start-4 ${label[state]}`}
      >
        {status}
      </span>
    </li>
  );
}

export function StatusReportSkeleton() {
  return (
    <section className="mt-12" aria-busy="true">
      <h2 className="mb-4 text-lg font-semibold tracking-tight">Services</h2>
      <p className="text-ink-3">Asking the API, database and AI provider…</p>
    </section>
  );
}
