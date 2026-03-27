
import click
import os
from indyforge.agents.mapreduce_graph import run
from indyforge.lang import t

def _save_repo_docs(repo_result: dict, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    
    docs_path = os.path.join(out_dir, "overview.md")
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(repo_result.get("docs", ""))
    click.echo(t("cli_docs", path=docs_path))
    
    sections = {
        "dependencies.md": "deps",
        "api.md": "api",
        "events.md": "events",
        "security.md": "security",
        "sequences.md": "sequences",
        "config.md": "config"
    }
    
    for filename, key in sections.items():
        content = repo_result.get(key)
        if content:
            file_path = os.path.join(out_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(t("cli_file", path=file_path))


@click.group()
def cli():
    pass

@cli.command()
@click.argument("repos", nargs=-1, required=True)
@click.option("--out", default="./docs", help="Output directory")
@click.option("--no-cache", is_flag=True, help="Disable and delete cache")
def scan(repos, out, no_cache):
    """Scan one or more microservices and generate full documentation."""
    click.echo(t("cli_title"))
    
    import shutil
    cache_dir = ".indyforge_cache"
    if os.path.exists(cache_dir) and os.listdir(cache_dir):
        if no_cache:
            shutil.rmtree(cache_dir)
            click.echo(t("cache_flag"))
        else:
            if click.confirm(t("cache_found"), default=True):
                click.echo(t("cache_used"))
            else:
                shutil.rmtree(cache_dir)
                click.echo(t("cache_deleted"))
    
    click.echo(t("cli_scan", repos=list(repos)))
    click.echo("")

    result = run(list(repos))

    os.makedirs(out, exist_ok=True)

    if "system_overview" in result:
        sys_path = os.path.join(out, "system-overview.md")
        with open(sys_path, "w", encoding="utf-8") as f:
            f.write(result["system_overview"])
        click.echo(t("cli_sysdocs", path=sys_path))
        
        for repo_docs in result.get("repo_docs", []):
            repo_name = os.path.basename(os.path.abspath(repo_docs["repo"]))
            repo_out = os.path.join(out, repo_name)
            _save_repo_docs(repo_docs, repo_out)
    else:
        _save_repo_docs(result, out)

def main():
    cli()

if __name__ == "__main__":
    main()
