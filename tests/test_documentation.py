"""Regression checks for the documented callable interface contract."""
import ast


def test_package_functions_describe_arguments_and_returns(repo_root):
    """Require purpose, argument descriptions and return semantics on package functions.

    Args:
        repo_root: Absolute repository root supplied by the shared test fixture.

    Returns:
        None. Missing sections or parameter descriptions produce assertion failures.
    """
    for path in (repo_root / 'src' / 'cloud_scheduler').rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            context = f'{path.relative_to(repo_root)}:{node.lineno} {node.name}'
            doc = ast.get_docstring(node)
            assert doc and doc.splitlines()[0].strip(), context
            assert 'Args:' in doc, context
            assert 'Returns:' in doc, context
            arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            args_section = doc.split('Args:', 1)[1].split('Returns:', 1)[0]
            for argument in arguments:
                if argument.arg not in ('self', 'cls'):
                    assert f'{argument.arg}:' in args_section, (context, argument.arg)
