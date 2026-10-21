#!/usr/bin/env python3
"""Local stdio MCP server implementing OpenAI's structured settings extension.

The server only reads and saves settings. Vault actions use the official CLI.
"""
import json
import sys
from settings_store import PROPERTIES, settings_document, update_values

VERSION = '1.2.1'
EXTENSION = {'openai/settings': {'readTool': 'settings.read', 'updateTool': 'settings.update'}}
EMPTY = {'type': 'object', 'properties': {}, 'additionalProperties': False}
TOOLS = [
    {
        'name': 'settings.read', 'title': 'Read Obsidian settings',
        'description': 'Read the Obsidian plugin settings schema, current values, and native UI layout.',
        'inputSchema': EMPTY,
        'outputSchema': {'type': 'object', 'properties': {'schema': {'type': 'object'}, 'values': {'type': 'object'}, 'layout': {'type': 'array', 'items': {'type': 'object'}}}, 'required': ['schema', 'values']},
        'annotations': {'readOnlyHint': True, 'openWorldHint': False},
    },
    {
        'name': 'settings.update', 'title': 'Update Obsidian settings',
        'description': 'Save only the requested changes to vault selection, CLI executable, or read-only mode. Preserves other settings.',
        'inputSchema': {'type': 'object', 'properties': {'set': {'type': 'object', 'properties': PROPERTIES, 'minProperties': 1, 'additionalProperties': False}}, 'required': ['set'], 'additionalProperties': False},
        'outputSchema': {'type': 'object', 'properties': {'values': {'type': 'object'}}, 'required': ['values']},
        'annotations': {'readOnlyHint': False, 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False},
    },
]

class RpcError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message

def dispatch(method, params):
    if not isinstance(params, dict):
        raise RpcError(-32602, 'Params must be an object.')
    if method == 'initialize':
        requested = params.get('protocolVersion')
        version = requested if requested in ('2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25') else '2025-11-25'
        return {'protocolVersion': version, 'serverInfo': {'name': 'obsidian', 'title': 'Obsidian', 'version': VERSION}, 'capabilities': {'tools': {}, 'experimental': EXTENSION}}
    if method == 'ping':
        return {}
    if method == 'tools/list':
        return {'tools': TOOLS}
    if method == 'tools/call':
        name, args = params.get('name'), params.get('arguments', {})
        if name not in ('settings.read', 'settings.update'):
            raise RpcError(-32602, 'Unknown tool.')
        if not isinstance(args, dict):
            raise RpcError(-32602, 'Tool arguments must be an object.')
        try:
            if name == 'settings.read':
                if args:
                    raise ValueError('settings.read accepts an empty object.')
                result = settings_document()
            else:
                if set(args) != {'set'}:
                    raise ValueError('settings.update requires exactly a set object.')
                result = {'values': update_values(args['set'])}
            return {'content': [{'type': 'text', 'text': json.dumps(result, ensure_ascii=False)}], 'structuredContent': result, 'isError': False}
        except (ValueError, OSError) as exc:
            return {'content': [{'type': 'text', 'text': str(exc)}], 'isError': True}
    raise RpcError(-32601, 'Method not found.')

def process(line):
    try:
        message = json.loads(line)
    except ValueError:
        return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error.'}}
    if not isinstance(message, dict) or message.get('jsonrpc') != '2.0' or not isinstance(message.get('method'), str):
        return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Invalid request.'}}
    if 'id' not in message:
        return None
    try:
        return {'jsonrpc': '2.0', 'id': message['id'], 'result': dispatch(message['method'], message.get('params', {}))}
    except RpcError as exc:
        return {'jsonrpc': '2.0', 'id': message['id'], 'error': {'code': exc.code, 'message': exc.message}}

def main():
    for line in sys.stdin:
        response = process(line)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
