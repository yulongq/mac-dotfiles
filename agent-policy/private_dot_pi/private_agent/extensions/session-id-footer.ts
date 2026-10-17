// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Entwining contributors
import {
  type AgentSession,
  type ExtensionAPI,
  FooterComponent,
} from "@earendil-works/pi-coding-agent";
import { truncateToWidth } from "@earendil-works/pi-tui";

export default function sessionIdFooter(pi: ExtensionAPI) {
  pi.on("session_start", (_event, ctx) => {
    ctx.ui.setFooter((_tui, theme, footerData) => {
      const baseFooter = new FooterComponent(
        // Pi exposes the footer's session fields through separate extension APIs.
        {
          sessionManager: ctx.sessionManager,
          get model() {
            return ctx.model;
          },
          get routedModel() {
            if (ctx.model?.api !== "pi-virtual") return undefined;
            const latest = ctx.sessionManager.buildSessionProjection().messages.findLast(
              (message) =>
                message.role === "assistant" &&
                message.stopReason !== "error" &&
                message.stopReason !== "aborted",
            );
            if (latest?.role !== "assistant") return undefined;
            const model = ctx.modelRegistry.find(latest.provider, latest.model);
            return model && model.api !== "pi-virtual"
              ? { model, thinkingLevel: latest.thinkingLevel }
              : undefined;
          },
          state: ctx,
          getContextUsage: () => ctx.getContextUsage(),
          modelRuntime: {
            isUsingSubscription: (provider: string) => {
              const model = ctx.model;
              return (
                model !== undefined &&
                ctx.modelRegistry.isUsingOAuth(model) &&
                ctx.modelRegistry.getProvider(provider)?.auth.oauth?.isSubscription === true
              );
            },
          },
        } as unknown as AgentSession,
        footerData,
      );

      return {
        invalidate() {
          baseFooter.invalidate();
        },
        render(width: number): string[] {
          baseFooter.setAutoCompactEnabled(pi.getSettings().compaction?.enabled !== false);
          const lines = baseFooter.render(width);
          const sessionLine = truncateToWidth(
            theme.fg("dim", ctx.sessionManager.getSessionId()),
            width,
            theme.fg("dim", "..."),
          );
          return [...lines.slice(0, 1), sessionLine, ...lines.slice(1)];
        },
      };
    });
  });
}
