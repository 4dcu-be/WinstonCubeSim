from cubedata import RichCubeData as CubeData
import click


@click.command()
@click.option('--url', is_flag=True)
@click.argument('path', required=True, type=str)
def run(path, url):
    cube_data = CubeData(draft_size=90)
    if url:
        cube_data.read_cube_url(path)
    else:
        cube_data.read_cube_csv(path)
    cube_data.start_game()


if __name__ == "__main__":
    run()
