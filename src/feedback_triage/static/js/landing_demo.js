// Landing page mini demo (FU1) -- PR 3.4.
//
// Fully client-side "playable screenshot" of the inbox: a small
// hardcoded list of feedback items, a search box, and the ability
// to bump a row's status. Refresh resets to the seed (no
// localStorage). Per docs/project/spec/v2/core-idea.md -- Mini
// demo (FU1).
//
// Vanilla JS, no framework, no fetch. The demo MUST NOT touch any
// /api/v1/ endpoint -- the DoD says viewing it makes no API call.

(function () {
    "use strict";

    const SEED = [
        {
            id: 1,
            title: "Add CSV export of feedback",
            status: "new",
            priority: "medium",
            pain: 3,
        },
        {
            id: 2,
            title: "Mobile sidebar collapses on tap",
            status: "needs_info",
            priority: "low",
            pain: 2,
        },
        {
            id: 3,
            title: "Bug: tag chips wrap weirdly on Safari",
            status: "reviewing",
            priority: "high",
            pain: 4,
        },
        {
            id: 4,
            title: "Email digest of weekly intake",
            status: "planned",
            priority: "medium",
            pain: 3,
        },
        {
            id: 5,
            title: "Dark mode for the dashboard",
            status: "in_progress",
            priority: "low",
            pain: 2,
        },
        {
            id: 6,
            title: "Onboarding tour for new owners",
            status: "new",
            priority: "low",
            pain: 1,
        },
        {
            id: 7,
            title: "Slow load on the inbox > 1k items",
            status: "reviewing",
            priority: "high",
            pain: 5,
        },
        {
            id: 8,
            title: "Webhook for status changes",
            status: "needs_info",
            priority: "medium",
            pain: 3,
        },
        {
            id: 9,
            title: "Deletion is too easy to fat-finger",
            status: "new",
            priority: "medium",
            pain: 4,
        },
        {
            id: 10,
            title: "Add markdown to release notes",
            status: "shipped",
            priority: "low",
            pain: 2,
        },
    ];

    const STATUS_FORWARD = {
        new: "needs_info",
        needs_info: "reviewing",
        reviewing: "planned",
        planned: "in_progress",
        in_progress: "shipped",
        shipped: "new",
    };

    const STATUS_LABEL = {
        new: "New",
        needs_info: "Needs info",
        reviewing: "Reviewing",
        planned: "Planned",
        in_progress: "In progress",
        shipped: "Shipped",
    };

    function init() {
        const root = document.getElementById("landing-demo");
        if (!root) return;

        const search = root.querySelector('[data-demo="search"]');
        const tbody = root.querySelector('[data-demo="rows"]');
        const empty = root.querySelector('[data-demo="empty"]');
        if (!search || !tbody || !empty) return;

        // Per-page in-memory copy so the bump button mutates locally.
        // Refresh re-runs init() and resets to SEED.
        const items = SEED.map((row) => ({ ...row }));

        function escapeHtml(value) {
            return String(value)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;");
        }

        function render() {
            const query = search.value.trim().toLowerCase();
            const rows = items.filter(
                (item) => !query || item.title.toLowerCase().includes(query),
            );

            if (rows.length === 0) {
                tbody.innerHTML = "";
                empty.hidden = false;
                return;
            }
            empty.hidden = true;

            tbody.innerHTML = rows
                .map((item) => {
                    const dots =
                        "●".repeat(item.pain) + "○".repeat(5 - item.pain);
                    return `
                    <tr data-id="${item.id}">
                      <td>${escapeHtml(item.title)}</td>
                      <td>
                        <span class="sn-pill-status sn-pill-status--${item.status}">
                          ${STATUS_LABEL[item.status]}
                        </span>
                      </td>
                      <td>
                        <span class="sn-pill-priority sn-pill-priority--${item.priority}">
                          ${escapeHtml(item.priority)}
                        </span>
                      </td>
                      <td>
                        <span class="sn-pain-dots" aria-label="Pain ${item.pain} of 5">${dots}</span>
                      </td>
                      <td>
                        <button
                          type="button"
                          class="sn-button sn-button-secondary"
                          data-demo-bump="${item.id}"
                        >
                          Bump status
                        </button>
                      </td>
                    </tr>`;
                })
                .join("");
        }

        search.addEventListener("input", render);

        tbody.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof HTMLElement)) return;
            const bump = target.closest("[data-demo-bump]");
            if (!bump) return;
            const id = Number(bump.getAttribute("data-demo-bump"));
            const item = items.find((row) => row.id === id);
            if (!item) return;
            item.status = STATUS_FORWARD[item.status] || "new";
            render();
        });

        render();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
