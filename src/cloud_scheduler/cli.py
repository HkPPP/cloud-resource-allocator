"""Command-line interface for scheduling configuration and execution."""
import argparse
from .io import load_config, load_jobs, load_servers
from .schedulers.csp import CSPScheduler
from .schedulers.greedy import GreedyScheduler

def main(argv: list[str] | None = None) -> int:
    """Parse explicit paths relative to the current directory and run the pipeline.

    Unavailable features exit with status 2 and an explanatory message.
    File and validation errors receive concise messages. Schedule execution and
    result serialization are not yet implemented; argument help is available.
    """
    parser = argparse.ArgumentParser(description="Intelligent Cloud Resource Scheduler")
    parser.add_argument("--config", default="config/default.json")
    parser.add_argument("--jobs", default="data/jobs.json")
    parser.add_argument("--servers", default="data/servers.json")
    parser.add_argument("--algorithm", choices=("greedy", "csp"), default="greedy")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        jobs = load_jobs(args.jobs)
        servers = load_servers(args.servers)
        scheduler = GreedyScheduler() if args.algorithm == "greedy" else CSPScheduler()
        result = scheduler.schedule(jobs, servers, config)
        raise NotImplementedError('Schedule result serialization is not implemented.')
    except (NotImplementedError, ValueError, OSError) as error:
        parser.exit(2, f"{error}\n")
