import re

_SAFE_ID_PATTERN = re.compile(r'[^A-Za-z0-9_]+')


def _safe_id(value):
    safe = _SAFE_ID_PATTERN.sub('_', str(value))
    return safe or 'n'


def _safe_label(value):
    return str(value).replace('"', '#quot;')


def _quoted_label(*parts):
    return '"' + _safe_label('\n'.join(str(p) for p in parts)) + '"'


def _stage_node_id(index):
    return f'S{_safe_id(index)}'


def generate_recipe_overview_diagram(stages):
    if not stages:
        return ''

    lines = ['flowchart TD']

    for index, stage in enumerate(stages):
        plugin_id = stage.get('pluginId') or '?'
        plugin_version = stage.get('pluginVersion') or ''
        label = f'Stage {index + 1}: {plugin_id}'
        if plugin_version:
            label += f' v{plugin_version}'
        lines.append(f'    {_stage_node_id(index)}[{_quoted_label(label)}]')

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
