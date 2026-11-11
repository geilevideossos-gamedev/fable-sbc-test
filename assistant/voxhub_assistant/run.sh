#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
# All options are read by the Python application from /data/options.json; bashio is
# used here only for early, readable failures.
set -e

if ! bashio::config.has_value 'anthropic_api_key'; then
    bashio::exit.nok "No Anthropic API key configured. Set 'anthropic_api_key' in the add-on configuration."
fi

if [ -z "${SUPERVISOR_TOKEN:-}" ]; then
    bashio::log.warning "SUPERVISOR_TOKEN is not set; Home Assistant tools will not work."
fi

bashio::log.info "Starting VoxHub Assistant (model: $(bashio::config 'model'), wake word: $(bashio::config 'wake_word'))"

cd /app
exec python3 -m voxhub_assistant
