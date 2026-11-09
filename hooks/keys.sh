#!/usr/bin/env bash
# SessionStart: the API keys the user gave in the plugin's settings (userConfig, kept in the OS's credential store) handed to the
# shell commands Claude runs in this session, under the names the scripts read. A key set there wins over one already in the
# environment; a key not set there leaves the environment's as it is. Nothing is printed.
[ -n "$CLAUDE_ENV_FILE" ] || exit 0
put() {   # put NAME VALUE: one plain assignment, single-quoted (a quote inside closed and reopened)
  [ -n "$2" ] || return 0
  printf "export %s='%s'\n" "$1" "$(printf '%s' "$2" | sed "s/'/'\\\\''/g")" >> "$CLAUDE_ENV_FILE"
}
put OPENAI_API_KEY "$CLAUDE_PLUGIN_OPTION_OPENAI_API_KEY"
put TRIPO_API_KEY "$CLAUDE_PLUGIN_OPTION_TRIPO_API_KEY"
put MESHY_API_KEY "$CLAUDE_PLUGIN_OPTION_MESHY_API_KEY"
exit 0
