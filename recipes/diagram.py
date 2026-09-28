import html
import re

_SAFE_ID_PATTERN = re.compile(r'[^A-Za-z0-9_]+')
_PLUGIN_MERMAID_BLOCK_PATTERN = re.compile(r'<pre class="mermaid">(.*?)</pre>', re.DOTALL)
_BRACKET_SEGMENT_PATTERN = re.compile(r'\[[^\]]*\]')
_STEP_IDENTIFIER_PATTERN = re.compile(r'\b(?:Start|End|step\d+)\b')


def _safe_id(value):
    safe = _SAFE_ID_PATTERN.sub('_', str(value))
    return safe or 'n'


def _safe_label(value):
    return str(value).replace('"', '#quot;')


def _quoted_label(*parts):
    return '"' + _safe_label('\n'.join(str(p) for p in parts)) + '"'


def _stage_node_id(index):
    return f'S{_safe_id(index)}'


def _extract_plugin_step_diagram(plugin):
    if not plugin or not plugin.readme:
        return None

    match = _PLUGIN_MERMAID_BLOCK_PATTERN.search(plugin.readme)
    if not match:
        return None

    text = html.unescape(match.group(1))
    lines = [line for line in text.split('\n') if line.strip()]
    if lines and lines[0].strip().lower().startswith('flowchart'):
        lines = lines[1:]

    return lines or None


def _renamespace_step_lines(lines, prefix):
    renamed = []
    for line in lines:
        segments = _BRACKET_SEGMENT_PATTERN.split(line)
        brackets = _BRACKET_SEGMENT_PATTERN.findall(line)

        parts = []
        for index, segment in enumerate(segments):
            parts.append(_STEP_IDENTIFIER_PATTERN.sub(lambda m: prefix + m.group(0), segment))
            if index < len(brackets):
                parts.append(brackets[index])
        renamed.append(''.join(parts))
    return renamed


def _stage_title(index, stage):
    plugin_id = stage.get('pluginId') or '?'
    plugin_version = stage.get('pluginVersion') or ''
    title = f'Stage {index + 1}: {plugin_id}'
    if plugin_version:
        title += f' v{plugin_version}'
    return title


def generate_recipe_diagram(stages, plugin_lookup, expanded_indices=None):
    if not stages:
        return ''

    expanded = set(expanded_indices or [])
    lines = ['flowchart TD']

    for index, stage in enumerate(stages):
        plugin_id = stage.get('pluginId') or '?'
        node_id = _stage_node_id(index)
        title = _stage_title(index, stage)

        if index not in expanded:
            lines.append(f'    {node_id}[{_quoted_label(title)}]')
            continue

        lines.append(f'    subgraph {node_id}_group [{_quoted_label(title)}]')
        lines.append(f'        {node_id}({_quoted_label(plugin_id)})')

        plugin = plugin_lookup.get(plugin_id)
        step_lines = _extract_plugin_step_diagram(plugin) if plugin else None
        if step_lines:
            for line in _renamespace_step_lines(step_lines, f'{node_id}_step_'):
                lines.append(f'        {line}')

        lines.append('    end')

    for index, stage in enumerate(stages):
        bindings = stage.get('bindings') or {}
        for binding in bindings.values():
            source_stage = binding.get('stage') if isinstance(binding, dict) else None
            if source_stage is None:
                continue
            output_name = binding.get('output') or ''
            lines.append(
                f'    {_stage_node_id(source_stage)} -->|{_quoted_label(output_name)}| {_stage_node_id(index)}'
            )

    return '\n'.join(lines)
