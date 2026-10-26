"""``sfsu-agents setup`` — print the MCP-registration snippet for common agents."""

from __future__ import annotations

SNIPPETS = {
    "claude-code": {
        "file": "~/.claude.json (or project .mcp.json)",
        "json": {
            "mcpServers": {
                "sfsu": {"command": "sfsu-agents", "args": ["mcp"]}
            }
        },
    },
    "cursor": {
        "file": "~/.cursor/mcp.json",
        "json": {
            "mcpServers": {
                "sfsu": {"command": "sfsu-agents", "args": ["mcp"]}
            }
        },
    },
    "codex": {
        "file": "~/.codex/config.toml",
        "toml": '[mcp_servers.sfsu]\ncommand = "sfsu-agents"\nargs = ["mcp"]\n',
    },
    "generic-stdio": {
        "file": "any MCP client supporting stdio servers",
        "json": {
            "command": "sfsu-agents", "args": ["mcp"], "transport": "stdio"
        },
    },
}


def run() -> int:
    import json
    print("Register the sfsu MCP server with your agent:\n")
    for name, spec in SNIPPETS.items():
        print(f"== {name} ({spec['file']})")
        if "json" in spec:
            print(json.dumps(spec["json"], indent=2))
        else:
            print(spec["toml"])
        print()
    print("Then ask your agent, e.g.: 'use the sfsu tools to find open CSC sections this fall'.")
    return 0
