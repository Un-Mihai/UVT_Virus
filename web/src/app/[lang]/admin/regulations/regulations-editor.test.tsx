import { Children, isValidElement, type ReactNode } from "react";
import { expect, it, vi } from "vitest";

import { en } from "@/i18n/dictionaries/en";

import { RegulationsEditor } from "./regulations-editor";

vi.mock("@/i18n/dictionary", () => ({
  currentLocale: async () => "en",
  getDictionary: async () => en,
}));
vi.mock("@/lib/auth/current-user", () => ({
  currentUser: async () => ({ roles: ["admin"] }),
}));
vi.mock("@/lib/api/server", () => ({
  api: {
    GET: async (path: string) => ({
      data: path === "/api/regulations" ? { documents: [], rules: [] } : [],
    }),
  },
}));

it("gives the PDF and written-rule editors unique keys that reset when scope changes", async () => {
  async function editorKeys(scope: string) {
    const tree = await RegulationsEditor({
      searchParams: Promise.resolve({ type: "1", scope }),
    });
    const children = Children.toArray(tree.props.children);
    const section = children.find(
      (child) => isValidElement(child) && child.type === "section",
    );
    expect(isValidElement(section)).toBe(true);
    if (!isValidElement<{ children: ReactNode }>(section))
      throw new Error("Missing editor");
    return Children.toArray(section.props.children)
      .filter(
        (child) => isValidElement(child) && typeof child.type !== "string",
      )
      .map((child) => (isValidElement(child) ? child.key : null));
  }

  const client = await editorKeys("client");
  const reviewer = await editorKeys("reviewer");
  expect(client).toHaveLength(3); // level heading and the two editors
  expect(new Set(client).size).toBe(client.length);
  expect(client[1]).not.toBe(reviewer[1]);
  expect(client[2]).not.toBe(reviewer[2]);
});
