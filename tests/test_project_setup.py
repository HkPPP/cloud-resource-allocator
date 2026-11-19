"""Checks for completed packaging and declarations, without executing algorithms."""
import json
import subprocess
import sys
import pytest
from cloud_scheduler.cli import main

def test_cli_help():
    """Verify cli help.

    Args:
        None.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    result=subprocess.run([sys.executable,'-m','cloud_scheduler','--help'],capture_output=True,text=True)
    assert result.returncode==0
    assert '--algorithm' in result.stdout

def test_cli_unavailable_feature(capsys):
    """Verify cli unavailable feature.

    Args:
        capsys: pytest capture fixture used to inspect the command-line error output.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(SystemExit) as e: main([])
    assert e.value.code==2
    assert 'not implemented' in capsys.readouterr().err

def test_scenario_shapes(repo_root):
    """Verify scenario shapes.

    Args:
        repo_root: Absolute repository root, derived from the test location rather than
            the working directory.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    for path in (repo_root/'data/scenarios').glob('*.json'):
        value=json.loads(path.read_text(encoding='utf-8'))
        assert len(value['servers'])==3
        assert 5<=len(value['jobs'])<=8
        assert value['expected']['greedy_count']<=value['expected']['csp_max_count']


@pytest.mark.parametrize('source,payload,message', [
    ('config', [], 'Configuration must be a JSON object'),
    ('config', {'objectives': 'max_jobs'}, 'objectives must be a JSON array'),
    ('config', {'slot_minutes': 0}, 'slot_minutes must be a positive integer'),
    ('jobs', {}, 'Job input must be a JSON array'),
    ('servers', {}, 'Server inventory must be a JSON array'),
    ('servers', [False], 'Server at index 0 must be a JSON object'),
    ('servers', [{}], 'Invalid server fields at index 0'),
])
def test_cli_reports_invalid_input_without_traceback(source, payload, message, tmp_path):
    """Report loader type and value errors as concise CLI failures with exit code two.

    Args:
        source: Input file containing the malformed value: config, jobs or servers.
        payload: JSON value exercising a loader structure or semantic validation error.
        message: Expected diagnostic text in standard error.
        tmp_path: Isolated directory containing explicit CLI input files.

    Returns:
        None. The command exits with status two, the expected error, and no traceback.
    """
    inputs = {'config': {}, 'jobs': [], 'servers': []}
    inputs[source] = payload
    arguments = []
    for name, value in inputs.items():
        path = tmp_path / f'{name}.json'
        path.write_text(json.dumps(value), encoding='utf-8')
        arguments.extend([f'--{name}', str(path)])
    result = subprocess.run(
        [sys.executable, '-m', 'cloud_scheduler', *arguments],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert message in result.stderr
    assert 'Traceback' not in result.stderr
    assert not result.stdout
