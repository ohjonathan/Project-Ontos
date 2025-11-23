import click
from ontos.groom import check_file_size, check_headers
import os

@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Ontos: The Context Operating System."""
    pass

@cli.command()
@click.argument('directory', type=click.Path(exists=True), default='.')
def groom(directory):
    """Sanitize documentation: Check for monoliths and missing headers."""
    click.echo(f"Grooming documentation in: {directory}")
    
    issues_found = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                
                # Check file size
                size_issue = check_file_size(file_path)
                if size_issue:
                    click.secho(f"[MONOLITH] {file}: {size_issue}", fg="yellow")
                    issues_found += 1
                
                # Check headers
                header_issue = check_headers(file_path)
                if header_issue:
                    click.secho(f"[NO HEADER] {file}: {header_issue}", fg="red")
                    issues_found += 1
    
    if issues_found == 0:
        click.secho("✨ All documents look clean!", fg="green")
    else:
        click.secho(f"\nFound {issues_found} issues.", fg="yellow")

@cli.command()
@click.argument('directory', type=click.Path(exists=True), default='.')
@click.option('--dry-run', is_flag=True, help="Simulate changes without writing.")
def init(directory, dry_run):
    """Initialize ontology: Add metadata to files."""
    from ontos.init import scan_directory, update_frontmatter
    
    click.echo(f"Initializing ontology in: {directory}")
    files = scan_directory(directory)
    
    changes = 0
    for file_path in files:
        updated, msg = update_frontmatter(file_path, dry_run=dry_run)
        if updated:
            click.secho(f"[UPDATED] {os.path.basename(file_path)}: {msg}", fg="green")
            changes += 1
        else:
            click.secho(f"[SKIP] {os.path.basename(file_path)}: {msg}", fg="dim")
            
    if changes > 0:
        click.secho(f"\nUpdated {changes} files.", fg="green")
    else:
        click.secho("\nNo changes made.", fg="yellow")

@cli.command()
@click.argument('directory', type=click.Path(exists=True), default='.')
def map(directory):
    """Visualize the ontology graph."""
    from ontos.graph import build_graph, visualize_graph
    
    click.echo(f"Mapping ontology in: {directory}")
    G = build_graph(directory)
    visualize_graph(G)

@cli.command()
@click.argument('query')
@click.option('--directory', type=click.Path(exists=True), default='.')
@click.option('--stdout', is_flag=True, help="Print context to stdout for piping (suppresses logs).")
def context(query, directory, stdout):
    """Retrieve smart context for a task."""
    from ontos.graph import build_graph
    from ontos.context import retrieve_context, copy_to_clipboard
    
    if not stdout:
        click.echo(f"Retrieving context for: '{query}' in {directory}")
    
    G = build_graph(directory)
    result = retrieve_context(query, G)
    
    if stdout:
        print(result)
    else:
        click.echo("\n--- GENERATED CONTEXT ---\n")
        click.echo(result[:500] + "..." if len(result) > 500 else result) # Preview
        
        if copy_to_clipboard(result):
            click.secho("\n✨ Context copied to clipboard!", fg="green")
        else:
            click.secho("\nFailed to copy to clipboard.", fg="red")

@cli.command()
@click.argument('directory', type=click.Path(exists=True), default='.')
def doctor(directory):
    """Check for documentation drift."""
    from ontos.graph import build_graph
    from ontos.doctor import check_drift
    
    click.echo(f"Checking for drift in: {directory}")
    G = build_graph(directory)
    issues = check_drift(G)
    
    if not issues:
        click.secho("✨ No drift detected. All documents are in sync.", fg="green")
    else:
        click.secho(f"\nFound {len(issues)} drift issues:", fg="yellow")
        for issue in issues:
            click.echo(f"  ⚠️  {issue['child']} is older than {issue['parent']} by {issue['diff_hours']:.1f} hours.")
            click.echo(f"      -> Suggestion: Review {issue['parent']} and update {issue['child']}.")

if __name__ == '__main__':
    cli()
