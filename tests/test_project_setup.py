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

def test_cli_default_schedule_output(capsys):
    """Print the default Greedy schedule as JSON and return successful status.

    Args:
        capsys: pytest capture fixture used to inspect the command-line error output.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    assert main([]) == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result['algorithm'] == 'greedy'
    assert len(result['assignments']) == 6
    assert not result['invalid_jobs'] and not result['unscheduled_jobs']
    assert not result['optimality_proven']
    assert captured.err == ''

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


def test_cli_unavailable_csp(capsys):
    """Preserve explicit errors for algorithms whose solver is not implemented.

    Args:
        capsys: pytest output capture fixture.

    Returns:
        None. CSP exits two with a concise error and no schedule on stdout.
    """
    with pytest.raises(SystemExit) as error:
        main(['--algorithm','csp'])
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert 'not implemented' in captured.err
    assert not captured.out


@pytest.mark.parametrize('entry',['module','script'])
def test_cli_entry_points_emit_json(entry, repo_root):
    """Execute each supported Python entry point and parse its JSON schedule.

    Args:
        entry: Module execution or the repository main.py wrapper.
        repo_root: Repository root containing default input files.

    Returns:
        None. Both entry points produce six assignments and exit successfully.
    """
    command = ([sys.executable,'-m','cloud_scheduler'] if entry == 'module'
               else [sys.executable,str(repo_root/'main.py')])
    result = subprocess.run([*command,'--algorithm','greedy'],cwd=repo_root,
                            capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert not result.stderr
    payload = json.loads(result.stdout)
    assert payload['algorithm'] == 'greedy'
    assert len(payload['assignments']) == 6
    assert not payload['timed_out'] and not payload['optimality_proven']


def test_cli_outputs_all_submission_statuses(tmp_path, repo_root, capsys):
    """Include scheduled, invalid and valid-unscheduled records in CLI output.

    Args:
        tmp_path: Temporary directory for a mixed submission batch.
        repo_root: Repository root for explicit config and inventory paths.
        capsys: pytest output capture fixture.

    Returns:
        None. JSON contains each original submission index in exactly one category.
    """
    jobs = [{}, {'job_id':'run','cpu':1,'ram_gb':1,'duration_minutes':15},
            {'job_id':'omit','cpu':1,'ram_gb':1,'gpu':99,'duration_minutes':15}]
    path = tmp_path/'jobs.json'
    path.write_text(json.dumps(jobs),encoding='utf-8')
    assert main(['--jobs',str(path),'--config',str(repo_root/'config/default.json'),
                 '--servers',str(repo_root/'data/servers.json')]) == 0
    captured = capsys.readouterr()
    assert not captured.err
    result = json.loads(captured.out)
    assert [record['input_index'] for record in result['invalid_jobs']] == [0]
    assert [record['input_index'] for record in result['assignments']] == [1]
    assert [record['input_index'] for record in result['unscheduled_jobs']] == [2]
    assert result['invalid_jobs'][0]['error_codes']
    assert result['unscheduled_jobs'][0]['reason'] is None
